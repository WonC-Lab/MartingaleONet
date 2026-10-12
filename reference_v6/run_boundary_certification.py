"""CPU-only v6 frozen-input executor. Resume cached raw evaluations verbatim."""
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import csv
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import time
import traceback
import zipfile
from reference_v6 import policy
from reference_v6.mp_backend import evaluate, FIELDS

ROOT=Path(__file__).resolve().parent
P=json.loads((ROOT/'BOUNDARY_CERT_PROTOCOL.json').read_text(encoding='utf-8'))
D=policy.D


def serial(z):
    if isinstance(z,Decimal): return str(z)
    if isinstance(z,dict): return {k:serial(v) for k,v in z.items()}
    if isinstance(z,(tuple,list)): return [serial(v) for v in z]
    return z


def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(serial(value),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    os.replace(temp,path)


def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fingerprint():
    names=['mp_backend.py','run_boundary_certification.py','requirements-colab.txt']
    return {name:digest(ROOT/name) for name in names}


def preflight(output):
    receipt=policy.verify_freeze(ROOT)
    for name,expected in P['reproducibility']['old_gate_sources'].items():
        if digest(ROOT.parent/name)!=expected: raise RuntimeError('Baseline gate mismatch: '+name)
    gate=json.loads((ROOT.parent/'reference_v4/FINAL_GATE_DECISION.json').read_text())
    summary=json.loads((ROOT.parent/'reference_v4/RECONCILIATION_SUMMARY.json').read_text())
    if gate['CORE']!='PASS' or summary['core_pointwise']!={'NUMERICALLY_RESOLVED':1734}:
        raise RuntimeError('CORE baseline not resolved')
    inputs=(ROOT/'BOUNDARY_BLINDED_INPUTS.jsonl').read_text().splitlines()
    if len(inputs)!=128: raise RuntimeError('Expected exactly 128 inputs')
    version={'protocol_SHA256':receipt['protocol_SHA256'],'input_SHA256':receipt['blinded_input_SHA256'],
             'executor_SHA256':fingerprint(),'CORE_recomputed':0,'old_boundary_recomputed':0}
    output=Path(output).resolve()
    # Never allow the output to shadow any source or historical evidence.
    for protected in [ROOT,ROOT.parent/'reference',*[ROOT.parent/f'reference_v{i}' for i in range(2,6)]]:
        if output==protected or protected in output.parents: raise ValueError('Protected output directory')
    output.mkdir(parents=True,exist_ok=True)
    version_file=output/'RUN_IDENTITY.json'
    if version_file.exists() and json.loads(version_file.read_text())!=version:
        raise RuntimeError('Resume identity differs; use a new output directory')
    write(version_file,version)
    env={'UTC':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'python':platform.python_version(),
         'platform':platform.platform(),'cpu_count':os.cpu_count(),'git_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT.parent,text=True).strip()}
    import importlib.metadata
    env['packages']={k:importlib.metadata.version(k) for k in ['mpmath','gmpy2','numpy','scipy','matplotlib','QuantLib']}
    expected=dict(line.strip().split('==') for line in (ROOT/'requirements-colab.txt').read_text().splitlines() if line.strip())
    if any(env['packages'].get(k)!=v for k,v in expected.items()): raise RuntimeError('Pinned package version mismatch')
    write(output/'ENVIRONMENT.json',env)
    return [json.loads(z,parse_float=str,parse_int=str) for z in inputs],output


class ResourceStop(Exception): pass
class RefinementFailure(Exception): pass


class CaseRunner:
    def __init__(self,row,output,deadline):
        self.row=row; self.output=Path(output)/'cases'/row['case_id'];self.output.mkdir(parents=True,exist_ok=True)
        self.start=time.process_time();self.deadline=deadline
        self.stats={'cached_evaluations':0,'new_evaluations':0}
        # Exact input-only maximum of the frozen span formula over all stencils.
        max_x=max(abs(D(row['x'])+D('.96').ln()),abs(D(row['x'])+D('1.04').ln()))
        max_t=D(row['tau'])*(1+D(2)/64);max_v=D('.01')*D('.02')*4
        self.span=str(max_x+D('.04')+abs(D(row['r']))*max_t+
                      abs(D(row['rho']))*(max_v+D(row['kappa'])*D(row['theta'])*max_t)/max(D(row['sigma']),D('.1')))

    def tick(self):
        if (self.output.parent.parent/'RUN_INVALID.json').exists():raise RuntimeError('Run invalidated by another worker')
        if time.process_time()-self.start>=P['stopping']['case_CPU_seconds']: raise ResourceStop('case CPU cap')
        if time.monotonic()>=self.deadline: raise ResourceStop('batch wall cap')

    def raw(self,route,cfg,coords):
        self.tick();coords=[list(map(str,q)) for q in coords]
        key=hashlib.sha256(json.dumps([route,cfg,coords],sort_keys=True).encode()).hexdigest()
        path=self.output/'raw'/f'{key}.json'
        if path.exists():
            z=json.loads(path.read_text());self.stats['cached_evaluations']+=1
            if z['route']!=route or z['config']!=cfg or z['coordinates']!=coords: raise RuntimeError('checkpoint identity mismatch')
            check=z.pop('checkpoint_SHA256')
            if hashlib.sha256(json.dumps(z,sort_keys=True).encode()).hexdigest()!=check: raise RuntimeError('checkpoint corrupted')
            return z
        partial=path.with_suffix('.partial.json')
        state=json.loads(partial.read_text()) if partial.exists() else None
        if state:
            check=state.pop('checkpoint_SHA256')
            if hashlib.sha256(json.dumps(state,sort_keys=True).encode()).hexdigest()!=check:raise RuntimeError('Partial checkpoint corrupted')
        def save_partial(state):
            state['checkpoint_SHA256']=hashlib.sha256(json.dumps(state,sort_keys=True).encode()).hexdigest()
            write(partial,state)
        began=time.monotonic();z=evaluate(self.row,route,cfg,coords,self.tick,saved=state,checkpoint=save_partial)
        z['elapsed_seconds']=time.monotonic()-began
        z['checkpoint_SHA256']=hashlib.sha256(json.dumps(z,sort_keys=True).encode()).hexdigest()
        write(path,z);self.stats['new_evaluations']+=1
        print(f"{self.row['case_id']} {route} raw checkpoint saved: {cfg}, {z['nodes']} nodes, {z['elapsed_seconds']:.1f}s",flush=True)
        return z

    def converge(self,route,coords,targets):
        """Decoupled axes, final last-three recomputed with other axes fixed.

        targets are precision goals at least as strict as the frozen component
        budgets; they never change an acceptance threshold. Uncertainty sums
        the two final differences of every axis, not their maximum across axes.
        """
        ladders=({'cutoff':P['refinement']['cutoffs'],'degree':P['refinement']['quadrature_degrees'],'dps':P['refinement']['MP_digits']}
                 if route=='E1' else {'N':P['refinement']['COS_N'],'L':P['refinement']['COS_L'],'dps':P['refinement']['MP_digits']})
        indices={axis:2 for axis in ladders}
        if route=='E1': cfg={'cutoff':256,'degree':64,'dps':120,'span':self.span}
        else: cfg={'N':16384,'L':32,'dps':120}
        while True:
            self.tick(); errors={}; sequences={}; failed=[]
            for axis,ladder in ladders.items():
                idx=indices[axis];seq=[]
                for v in ladder[idx-2:idx+1]:
                    trial={**cfg,axis:v};seq.append(self.raw(route,trial,coords))
                sequences[axis]=[z['config'] for z in seq]
                errors[axis]=[{f:max(abs(D(seq[1]['results'][i]['values'][f])-D(seq[0]['results'][i]['values'][f])),
                                      abs(D(seq[2]['results'][i]['values'][f])-D(seq[1]['results'][i]['values'][f]))) for f in targets}
                              for i in range(len(coords))]
                if any(e[f]>D(targets[f]) for e in errors[axis] for f in targets): failed.append(axis)
            if not failed:
                final=self.raw(route,cfg,coords);unc=[]
                for i,z in enumerate(final['results']):
                    unc.append({f:sum(errors[a][i][f] for a in ladders)+D(z['roundoff'][f]) for f in targets})
                return {'values':[z['values'] for z in final['results']],'uncertainties':unc,
                        'axis_errors':errors,'axis_sequences':sequences,'final_config':cfg,
                        'actual_bit_precision':final['actual_bit_precision']}
            for axis in failed:
                if indices[axis]+1>=len(ladders[axis]): raise RefinementFailure(f'{route} {axis} ceiling, coordinates={coords}')
                indices[axis]+=1;cfg[axis]=ladders[axis][indices[axis]]

    def physical(self,route,base,budgets):
        row=self.row;S=D(row['x']).exp();tau=D(row['tau']);history=[]
        for q in P['refinement']['physical_relative_steps']:
            h=S*D(q);hv=D('.01')*D(q)
            coords=[((S+j*h).ln(),0,tau) for j in [-2,-1,0,1,2]]+[(D(row['x']),j*hv,tau) for j in [0,1,2,3,4]]
            target=min(budgets['T_C']/4,budgets['T_Delta']*h/1000,budgets['T_nu']*hv/1000)
            z=self.converge(route,coords,{'c':target})
            prices=[D(v['c']) for v in z['values']];u=[v['c'] for v in z['uncertainties']]
            delta=policy.time_fd5(prices[:5],h)
            nu=sum(w*p for w,p in zip([-25,48,-36,16,-3],prices[5:]))/(12*hv)
            propagated_delta=policy.propagated_time_uncertainty(u[:5],h)
            propagated_nu=sum(abs(w)*v for w,v in zip([-25,48,-36,16,-3],u[5:]))/(12*hv)
            gamma=round_gamma(z['actual_bit_precision'],64)
            propagated_delta+=gamma*sum(abs(w*p) for w,p in zip([1,-8,0,8,-1],prices[:5]))/(12*h)
            propagated_nu+=gamma*sum(abs(w*p) for w,p in zip([-25,48,-36,16,-3],prices[5:]))/(12*hv)
            item={'q':q,'Delta5':delta,'nu5':nu,'propagated_Delta':propagated_delta,'propagated_nu':propagated_nu,'reference':z}
            history.append(item);write(self.output/f'physical_{route}.json',history)
            if len(history)<3: continue
            extras={}
            for f,fd,prop in [('Delta','Delta5','propagated_Delta'),('nu','nu5','propagated_nu')]:
                increments=[abs(history[k][fd]-history[k-1][fd]) for k in [-1,-2]]
                extras[f]=max(increments)+abs(item[fd]-D(base['values'][0][f]))+item[prop]
            if all(extras[f]<=budgets['T_'+f]/4 for f in extras):
                return extras
        raise RefinementFailure(f'{route} physical FD ceiling')

    def run(self):
        row=self.row; coords=[(row['x'],0,row['tau'])]
        # Initial estimates establish conservative component precision goals.
        a=self.raw('E1',{'dps':80,'degree':40,'cutoff':256,'span':self.span},coords)['results'][0]['values']
        b=self.raw('E2',{'dps':80,'N':16384,'L':32},coords)['results'][0]['values']
        provisional=policy.component_budgets(a,b,row)
        bases={route:self.converge(route,coords,{f:provisional['T_'+({'c':'C'}.get(f,f))]/8 for f in FIELDS}) for route in ['E1','E2']}
        budgets=policy.component_budgets(bases['E1']['values'][0],bases['E2']['values'][0],row)
        # Lock budgets before any time derivative/residual is calculated.
        write(self.output/'COMPONENT_BUDGET_LOCK.json',{'budgets':budgets,'bases':bases,'before_residual':True})
        for f in FIELDS:
            tf=budgets['T_'+({'c':'C'}.get(f,f))]
            if abs(D(bases['E1']['values'][0][f])-D(bases['E2']['values'][0][f]))>tf:
                raise RefinementFailure('cross-estimator component disagreement: '+f)
            if any(any(e[f]>tf/4 for e in z['axis_errors'][axis]) for z in bases.values() for axis in z['axis_errors']):
                raise RefinementFailure('final component axis budget: '+f)
        extras={route:self.physical(route,bases[route],budgets) for route in bases}
        history={route:[] for route in bases}; candidate=None
        for j in P['time_stencil']['j']:
            h=D(row['tau'])/(D(2)**j)
            cs=[(row['x'],0,D(row['tau'])+k*h) for k in [-2,-1,0,1,2]]
            for route in bases:
                z=self.converge(route,cs,{'c':min(budgets['T_C']/4,budgets['B_R']*h/1000)})
                prices=[D(v['c']) for v in z['values']]; u=[v['c'] for v in z['uncertainties']]
                ctau=policy.time_fd5(prices,h);up=policy.propagated_time_uncertainty(u,h)
                ar=round_gamma(z['actual_bit_precision'],64)*sum(abs(w*p) for w,p in zip([1,-8,0,8,-1],prices))/(12*h)
                prev=history[route];ut=None
                if len(prev)>=2: ut=max(abs(ctau-prev[-1]['D5']),abs(prev[-1]['D5']-prev[-2]['D5']))
                base=bases[route];vals=base['values'][0]; bu=base['uncertainties'][0]
                rhat=policy.normalized_residual(vals['c'],vals['Delta'],vals['nu'],ctau,row)
                ur=(policy.residual_uncertainty(up+ut+ar,bu['Delta']+extras[route]['Delta'],bu['nu']+extras[route]['nu'],bu['c'],row) if ut is not None else None)
                prev.append({'j':j,'h_tau':h,'D5':ctau,'R_hat':rhat,'u_tau_price':up,'u_time_round':ar,
                             'u_trunc':ut,'u_R_hat':ur,'price_reference':z})
            write(self.output/'TIME_REFINEMENT.json',history)
            if j<10: continue  # at least five D5 levels for first common window
            qualifies=all(policy.estimator_window_accepts(history[route][-3:],budgets['B_R']) for route in bases)
            if candidate is not None and qualifies and j==candidate+1:
                one,two=[history[r][-1] for r in ['E1','E2']]
                if abs(one['R_hat']-two['R_hat'])>one['u_R_hat']+two['u_R_hat']:
                    raise RefinementFailure('independent residual disagreement')
                return {'status':'PASS','input':row,'budgets':budgets,'confirming_j':j,
                        'final':{r:history[r][-1] for r in bases},'stats':self.stats}
            candidate=j if qualifies else None
        # Do not turn stable-looking discrepancies into a model-truth claim.
        return {'status':'NUMERICAL_UNRESOLVED','input':row,'reason':'no confirmed common window through j=16',
                'budgets':budgets,'stats':self.stats,'time_history':history}


def round_gamma(bits,m):
    eps=D(2)**(1-bits);return m*eps/(1-m*eps)


def worker(row,output,deadline):
    runner=CaseRunner(row,output,deadline);path=runner.output/'RESULT.json'
    if path.exists():
        previous=json.loads(path.read_text())
        if previous.get('status')=='PASS': return previous
    try: result=runner.run()
    except ResourceStop as e: result={'status':'PENDING_RESOURCE_LIMIT','input':row,'reason':str(e),'stats':runner.stats}
    except RefinementFailure as e: result={'status':'NUMERICAL_UNRESOLVED','input':row,'reason':str(e),'stats':runner.stats}
    except Exception:
        result={'status':'EXECUTOR_ERROR_RUN_INVALID','input':row,'traceback':traceback.format_exc(),'stats':runner.stats}
    result['case_CPU_seconds_this_attempt']=time.process_time()-runner.start
    write(path,result);return result


def report(output,rows):
    output=Path(output);results=[]
    for row in rows:
        path=output/'cases'/row['case_id']/'RESULT.json'
        results.append(json.loads(path.read_text()) if path.exists() else {'input':row,'status':'NOT_RUN'})
    counts={status:sum(z['status']==status for z in results) for status in sorted({z['status'] for z in results})}
    passed=counts.get('PASS',0)==128 and len(results)==128 and not (output/'RUN_INVALID.json').exists()
    decision={'new_v0_inputs':128,'counts':counts,'NEW_V0_GATE':'PASS' if passed else 'FAIL',
              'CORE':'PASS_REUSED_1734','CORE_recomputed':0,'old_boundary_recomputed':0,
              'boundary_pointwise':'600_RESOLVED_BASELINE_REUSED',
              'finite_trace_points_reused':390,
              'RUN_VALID':not (output/'RUN_INVALID.json').exists(),
              'PHASE_1C_ELIGIBLE_FOR_REVIEW':'YES' if passed else 'NO',
              'PHASE_1C_AUTHORIZED':'NO','training_started':False,
              'reason':'Training authorization requires separate final review of all original blockers, even if this targeted gate passes.'}
    write(output/'FINAL_GATE_DECISION.json',decision)
    with (output/'FAILURE_RESOLUTION_TABLE.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(['case_id','stratum','parameter_stratum','status','reason'])
        for z in results:w.writerow([z['input']['case_id'],z['input']['stratum'],z['input']['parameter_stratum'],z['status'],z.get('reason','')])
    text='# Phase 1B.6 targeted validation\n\n'+json.dumps(decision,indent=2)+'\n\n'
    text+='Only the new 128 inputs are evaluated. Historical CORE and boundary files are untouched. Missing, resource-limited and erroneous cases cannot pass. No confidence interval or uniform-domain certification is claimed.\n'
    (output/'FINAL_VALIDATION_REPORT.md').write_text(text,encoding='utf-8')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(9,4));ax.bar(counts.keys(),counts.values());ax.set_ylabel('Cases');ax.tick_params(axis='x',rotation=20);fig.tight_layout()
    fig.savefig(output/'STATUS_COUNTS.png',dpi=160);plt.close(fig)
    fig,ax=plt.subplots(figsize=(9,4))
    for route in ['E1','E2']:
        ys=[]
        for z in results:
            v=z.get('final',{}).get(route)
            if not v:
                hp=output/'cases'/z['input']['case_id']/'TIME_REFINEMENT.json'
                if hp.exists():
                    saved=json.loads(hp.read_text()).get(route,[])
                    v=next((q for q in reversed(saved) if q.get('u_R_hat') is not None),None)
            if v and D(v['u_R_hat'])>0:ys.append(float(abs(D(v['R_hat']))/D(v['u_R_hat'])))
        if ys:ax.plot(range(len(ys)),ys,'.',label=route)
    ax.axhline(1,color='red',linestyle='--');ax.set_ylabel('|R hat| / uncertainty (latest saved levels)');ax.set_xlabel('Case with saved residual index')
    if ax.get_legend_handles_labels()[0]:ax.legend()
    fig.tight_layout();fig.savefig(output/'RESIDUAL_CONSISTENCY.png',dpi=160);plt.close(fig)
    write(output/'ARTIFACT_MANIFEST.json',{str(p.relative_to(output)):digest(p) for p in sorted(output.rglob('*')) if p.is_file() and p.name!='ARTIFACT_MANIFEST.json'})
    print(json.dumps(decision,indent=2),flush=True)
    return decision


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',default='reference_v6_colab')
    parser.add_argument('--workers',type=int,default=min(4,os.cpu_count() or 1))
    parser.add_argument('--preflight-only',action='store_true')
    parser.add_argument('--report-only',action='store_true')
    parser.add_argument('--execute-frozen-v6',action='store_true')
    args=parser.parse_args()
    if not 1<=args.workers<=4:parser.error('workers must be between 1 and 4')
    rows,output=preflight(args.output)
    if args.preflight_only: print('Freeze, baseline and dependency checks passed; no pricing started.');return
    if args.report_only:report(output,rows);return
    if not args.execute_frozen_v6:parser.error('Execution requires --execute-frozen-v6')
    # A committed, unmodified executor must precede all blinded pricing.
    for name in fingerprint():
        blob=subprocess.check_output(['git','show','HEAD:reference_v6/'+name],cwd=ROOT.parent)
        if hashlib.sha256(blob).hexdigest()!=digest(ROOT/name):raise RuntimeError('Executor is not source-committed: '+name)
    write(output/'EXECUTION_RECEIPT.json',{'UTC':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
          'explicit_command_opt_in':True,'historical_freeze_receipt_preserved':True,'workers':args.workers,
          'scope':'new128 only','executor_SHA256':fingerprint()})
    deadline=time.monotonic()+P['stopping']['batch_wall_seconds']
    pending=[r for r in rows if not (output/'cases'/r['case_id']/'RESULT.json').exists() or
             json.loads((output/'cases'/r['case_id']/'RESULT.json').read_text()).get('status')=='PENDING_RESOURCE_LIMIT']
    print(f'128 frozen inputs; {len(pending)} pending; {args.workers} CPU workers; CORE pricing calls=0.',flush=True)
    invalid=output/'RUN_INVALID.json'
    if invalid.exists():raise RuntimeError('Run invalidated by an earlier executor error; new protocol/version required')
    try:
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            futures={pool.submit(worker,r,str(output),deadline):r for r in pending}
            for future in as_completed(futures):
                result=future.result();print(result['input']['case_id'],result['status'],flush=True)
                if result['status']=='EXECUTOR_ERROR_RUN_INVALID':
                    write(invalid,{'case_id':result['input']['case_id'],'reason':'Executor coding error; run is invalid'})
                    for task in futures:task.cancel()
                    raise RuntimeError('Executor error: entire run invalid; inspect raw traceback before any further pricing')
    finally:report(output,rows)


if __name__=='__main__': main()
