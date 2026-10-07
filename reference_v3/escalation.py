"""Explicit all-failure CORE escalation, multiprocess with per-case checkpoints."""
import argparse
from concurrent.futures import ProcessPoolExecutor,wait,FIRST_COMPLETED
import hashlib
import json
from pathlib import Path
import time
import math
from reference.certify import dump
from reference_v2.workflow import ROOT
from .mp import worker

KEYS=('x','v','tau','K','kappa','theta','sigma','rho','r')
def key(r):return tuple(r[k] for k in KEYS)
def selected(r):
    return r['status']!='PASS' or any((r.get('normalized_'+f+'_gap') or 0)>=.1*r.get('tolerance_'+f,float('inf')) for f in ['price','Delta','Gamma','Vv'])

def run(output='reference_v3',workers=12,scope='all',plan_only=False,max_seconds=None):
    out=Path(output)
    boundary_scope=scope=='boundary'
    source=out/('boundary_required.jsonl' if boundary_scope else 'coverage_core.jsonl')
    rows=[json.loads(z) for z in source.read_text().splitlines()]
    from reference_v2.domains import classify
    from reference_v2.workflow import from_row
    rows=[dict(r,domain=classify(from_row(r))) for r in rows]
    selected_rows=[r for r in rows if selected(r)]
    history=json.loads((ROOT/'reference/CERTIFICATION_RESULTS.json').read_text())['rows']
    unique={key(r):r for r in selected_rows}
    for r in ([] if boundary_scope else history):
        if classify(from_row(r))=='CORE' and selected(r) and key(r) not in unique:unique[key(r)]={**r,'domain':'CORE'}
    plan=list(unique.values())
    sources={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'reference_v3/mp.py',ROOT/'reference_v2/high_precision.py',ROOT/'reference/route_a.py',ROOT/'reference/route_b.py']}
    fingerprint=hashlib.sha256(json.dumps(sources,sort_keys=True).encode()).hexdigest()
    done=out/'mp_cases'/fingerprint[:12];done.mkdir(exist_ok=True,parents=True)
    dump(out/('HP_BOUNDARY_ESCALATION_PLAN.json' if boundary_scope else 'HP_ESCALATION_PLAN.json'),dict(planned=len(plan),selection='every strict failure and >=10% budget near-failure in the selected predeclared set',inputs=[{k:r[k] for k in KEYS} for r in plan],source_sha256=sources))
    if plan_only:return
    # Reuse fulfilled point obligations across compatible executed revisions;
    # original raw records and archived source hashes remain attached.
    from .review import prior_evidence
    fulfilled=prior_evidence()
    for checkpoint in sorted((out/'mp_cases').rglob('*.json'),key=lambda p:p.stat().st_mtime):
        z=json.loads(checkpoint.read_text())
        if z.get('status')=='NUMERICALLY_RESOLVED' and z.get('MP_axes_within_budget') and z.get('valid_FD_windows') and all(v=='NUMERICALLY_RESOLVED' for v in z.get('component_status',{}).values()):fulfilled[key(z['input'])]=z
    tasks=[]
    local_keys=None
    if scope=='external-light':
        from reference_v2.external import cases
        local_keys={key(c.row()) for c in cases() if c.v>0 and c.tau>=.1}
        # Aligned external cases are predeclared, including deep ITM/OTM and
        # high sigma. This is a cost-limited local batch, never full coverage.
        for c in cases():
            if key(c.row()) in local_keys and key(c.row()) not in unique:
                from reference.certify import assess
                r,_,_=assess(c);plan.append(dict(r,domain='CORE'))
    if scope=='local-light':
        from reference_v2.workflow import span
        def cost(r):
            c=from_row(r);p=c.p
            alpha=(c.v+p.kappa*p.theta*c.tau)*math.sqrt(1-p.rho*p.rho)/p.sigma
            # Input-only planning estimate, NEVER an error bound or criterion.
            estimated_cutoff=92.1034/max(alpha,1e-12)
            width=math.pi*40/(4*max(span(c),.01))
            return 40*(12+math.ceil(estimated_cutoff/width))
        local_keys={key(r) for r in plan if cost(r)<=2000}
        dump(out/'LOCAL_COST_PLAN.json',dict(threshold_estimated_nodes=2000,local_planned=len(local_keys),heavy_planned=len(plan)-len(local_keys),definition='alpha=(v+kappa*theta*tau)*sqrt(1-rho^2)/sigma; Uestimate=92.1034/alpha, panels estimate=12+ceil(Uestimate/(pi*40/(4*span))); cost plan only, not tail certification',all_mandatory_inputs_remain_in_HP_ESCALATION_PLAN=True))
    if scope=='cos':
        local_keys={key(r) for r in plan if any(f.startswith('B_') for f in r.get('failure_flags',[]))}
    for r in plan:
        if local_keys is not None and key(r) not in local_keys:continue
        h=fulfilled.get(key(r))
        if h and ('strike_FD_derivative_unresolved' not in r.get('failure_flags',[]) or h.get('strike_resolved')) and (not any(f.startswith('B_') for f in r.get('failure_flags',[])) or h.get('B_convergence_resolved')):continue
        identity=hashlib.sha256(json.dumps(key(r)).encode()).hexdigest()[:20]
        path=done/(identity+'.json')
        if path.exists():
            if json.loads(path.read_text()).get('execution_fingerprint')!=fingerprint:raise RuntimeError('MP source mismatch')
        else:tasks.append((r,path))
    start=time.time();count=len(list(done.glob('*.json')))
    with ProcessPoolExecutor(max_workers=workers) as pool:
        iterator=iter(tasks);futures={}
        def submit_next():
            try:r,path=next(iterator)
            except StopIteration:return
            futures[pool.submit(worker,r)]=(r,path)
        for _ in range(workers):submit_next()
        while futures:
            ready,_=wait(futures,timeout=30,return_when=FIRST_COMPLETED)
            for f in ready:
                r,path=futures.pop(f)
                try:z=f.result()
                except Exception as exc:z=dict(input=from_row(r).row(),domain=r['domain'],status='UNRESOLVED',exception=repr(exc))
                z['execution_fingerprint']=fingerprint;dump(path,z);count+=1
                print('MP',count,len(plan),z['input']['label'],z['status'],'elapsed',round(time.time()-start,1),flush=True)
                if max_seconds is None or time.time()-start<max_seconds:submit_next()
    result=[json.loads(p.read_text()) for p in (out/'mp_cases').rglob('*.json')]
    present={key(z['input']) for z in result}|set(fulfilled)
    dump(out/('HP_boundary.json' if boundary_scope else 'HP_core.json'),dict(rows=result,planned=len(unique),evaluated=sum(k in present for k in unique),complete=all(k in present for k in unique),execution_scope=scope,source_sha256=sources))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',default='reference_v3');p.add_argument('--workers',type=int,default=12);p.add_argument('--scope',choices=['all','external-light','local-light','cos','boundary'],default='all');p.add_argument('--plan-only',action='store_true');p.add_argument('--max-seconds',type=int)
    a=p.parse_args();run(a.output,a.workers,a.scope,a.plan_only,a.max_seconds)
