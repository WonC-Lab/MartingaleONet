"""Evidence-only failure review under the unchanged Phase 1A budgets."""
import argparse,csv,hashlib,json,platform,subprocess,sys
from collections import Counter
from pathlib import Path
import numpy as np
from reference.certify import dump,save_npz,summarize
from reference_v2.workflow import ROOT,uncertainty
from reference_v2.domains import classify
from reference_v2.workflow import from_row
from .coverage import key
from .escalation import selected
from .provenance import verify

FIELDS=['price','Delta','Gamma','Vv']
def read(path,default):return json.loads(path.read_text()) if path.exists() else default
def budget(values,K):
    scaled=np.array([values['price']/K,values['Delta'],K*values['Gamma'],values['Vv']/K])
    return np.array([1e-8,2e-6,2e-5,2e-5])+np.array([1e-6,1e-5,1e-4,1e-4])*abs(scaled)

def prior_evidence():
    by={}
    analysis=read(ROOT/'reference_v2/HIGH_PRECISION_ANALYSIS.json',{}).get('rows',[])
    for z in analysis:
        if z['domain']=='CORE' and z['gamma_status']=='NUMERICALLY_RESOLVED':
            values={f:float(z['candidate_values'][f]) for f in FIELDS};tol=budget(values,z['input']['K']);scales=[1/z['input']['K'],1,z['input']['K'],1/z['input']['K']]
            if all(float(z['cross_route_max_gap'][f])*scales[i]<=tol[i] for i,f in enumerate(FIELDS)):
                by[key(z['input'])]=dict(input=z['input'],status='NUMERICALLY_RESOLVED',component_status={f:'NUMERICALLY_RESOLVED' for f in FIELDS},candidate=values,source='reference_v2/'+z['source'],inherited=True,strike_resolved=False,analysis=z)
    return by

def run(output='reference_v3'):
    root=Path(output);history=verify(ROOT/'reference_v3/HISTORICAL_SNAPSHOT.json')
    rows=[json.loads(z) for z in (root/'coverage_core.jsonl').read_text().splitlines()]
    rows.sort(key=lambda r:r['grid_index']);by=prior_evidence()
    for p in sorted((root/'mp_cases').rglob('*.json'),key=lambda p:p.stat().st_mtime):
        z=read(p,{})
        if z.get('precision'):
            z['candidate']={f:float(z['precision'][-1]['values'][f]) for f in FIELDS};z['source']=str(p.relative_to(root));by[key(z['input'])]=z
    ext=read(root/'EXTERNAL_RESULTS.json',{});extby={key(r['input']):r for r in ext.get('rows',[])}
    table=[];unc=[];resolved=0;unresolved=0
    for r in rows:
        h=by.get(key(r));flags=r['failure_flags'];status='NUMERICALLY_RESOLVED' if r['status']=='PASS' else 'UNRESOLVED'
        diagnosis='NOT_APPLICABLE_STRICT_PASS' if r['status']=='PASS' else 'UNRESOLVED';evidence=['coverage_core.jsonl#grid_index='+str(r['grid_index'])]
        if h:
            evidence.append(h['source'])
            if h['status']=='NUMERICALLY_RESOLVED' and ('strike_FD_derivative_unresolved' not in flags or h.get('strike_resolved')):
                status='NUMERICALLY_RESOLVED'
                if any(f.startswith('FD_') or f.startswith('strike_FD') for f in flags):diagnosis='FD_RESOLVED'
                elif 'A_domain' in flags:diagnosis='QUADRATURE_RESOLVED'
                elif any(f.startswith('B_') for f in flags):diagnosis='COS_RESOLVED' if h.get('B_convergence_resolved') else 'UNRESOLVED';status='UNRESOLVED' if diagnosis=='UNRESOLVED' else status
                elif 'solver_error' in flags:
                    messages=[z.get('estimate',{}).get('diagnostics',{}).get('message','').lower() for z in r.get('convergence',[]) if z.get('route')=='A']
                    diagnosis='FLOAT64_TOLERANCE_FLOOR' if any('round' in m for m in messages) else 'HIGH_PRECISION_CONFIRMED'
                else:diagnosis='HIGH_PRECISION_CONFIRMED'
                if any(f.startswith('B_') for f in flags) and not h.get('B_convergence_resolved'):
                    status='UNRESOLVED';diagnosis='UNRESOLVED'
        routes={route:{f:r['route_'+route+'_'+f] for f in FIELDS} for route in ['A','B']}
        if h:routes['MP']=h['candidate']
        e=extby.get(key(r))
        if e:
            evidence.append('EXTERNAL_RESULTS.json#'+e['input']['label'])
            if e['analytic']:routes['QuantLib_analytic']=e['analytic'][-1]['values']
            if e['PDE']:routes['QuantLib_PDE']=e['PDE'][-1]['values']
        u=dict(input={k:r[k] for k in ['x','v','tau','K','kappa','theta','sigma','rho','r','label']},domain='CORE',**uncertainty(routes));tol=budget(routes['A'],r['K']);scales=[1/r['K'],1,r['K'],1/r['K']]
        u['within_budget']=all(u[f]['max_disagreement']*scales[i]<=tol[i] for i,f in enumerate(FIELDS));u['three_routes']=all(len(u[f]['routes'])>=3 for f in FIELDS);unc.append(u)
        if not u['within_budget']:status='UNRESOLVED';diagnosis='UNRESOLVED'
        if r['status']=='FAIL':
            if status=='NUMERICALLY_RESOLVED':resolved+=1
            else:unresolved+=1
        table.append(dict(scope='CORE_GRID',grid_index=r['grid_index'],label=r['label'],original_status=r['status'],original_failure_flags=json.dumps(flags),final_diagnosis=diagnosis,final_status=status,evidence=json.dumps(evidence),input=json.dumps(u['input'])))
    catalog={key(r) for r in rows}
    old=read(ROOT/'reference/CERTIFICATION_RESULTS.json',{}).get('rows',[])
    for i,r in enumerate(old):
        if r['status']!='FAIL' or key(r) in catalog:continue
        h=by.get(key(r));domain=classify(from_row(r));status='NUMERICALLY_RESOLVED' if h and h['status']=='NUMERICALLY_RESOLVED' else 'UNRESOLVED'
        table.append(dict(scope='HISTORICAL_'+domain,grid_index='historical_'+str(i),label=r['label'],original_status=r['status'],original_failure_flags=json.dumps(r['failure_flags']),final_diagnosis='HIGH_PRECISION_CONFIRMED' if status=='NUMERICALLY_RESOLVED' else 'UNRESOLVED',final_status=status,evidence=json.dumps(['reference/CERTIFICATION_RESULTS.json#'+str(i)]+([h['source']] if h else [])),input=json.dumps({k:r[k] for k in ['x','v','tau','K','kappa','theta','sigma','rho','r','label']})))
    with (root/'FAILURE_RESOLUTION_TABLE.csv').open('w',encoding='utf-8',newline='') as h:
        w=csv.DictWriter(h,fieldnames=table[0].keys());w.writeheader();w.writerows(table)
    strict=summarize([{k:np.nan if v is None else v for k,v in r.items()} for r in rows]);flags=Counter(f for r in rows for f in r['failure_flags'])
    gaps_table='| Metric | Mean | Median | p95 | p99 | Maximum |\n|---|---:|---:|---:|---:|---:|\n'
    for f in FIELDS:
        s=strict['abs_'+f+'_gap'];gaps_table+='| '+f+' | '+' | '.join(f"{s[k]:.6g}" for k in ['mean','median','p95','p99','max'])+' |\n'
    mpplan=read(root/'HP_ESCALATION_PLAN.json',{});needed={key(z) for z in mpplan.get('inputs',[])}
    mp_done=sum(k in by for k in needed);mp_resolved=sum(k in by and by[k]['status']=='NUMERICALLY_RESOLVED' for k in needed)
    ext_ok=0;extdetails=[]
    for e in ext.get('rows',[]):
        detail=dict(label=e['input']['label'],status=e['status'],analytic_levels=len(e['analytic']),PDE_levels=len(e['PDE']))
        if e['analytic']:
            prices=[z['values']['price'] for z in e['analytic']];tol=1e-8+1e-6*max(abs(p) for p in prices[-3:]);change=max(abs(prices[i+1]-prices[i]) for i in range(max(0,len(prices)-3),len(prices)-1))
            gap=abs(prices[-1]-e['A']['price'])/e['input']['K'];detail.update(analytic_last_two_max_change=change,analytic_A_gap=gap,analytic_within_budget=change/e['input']['K']<=tol/4 and gap<=tol)
            ext_ok+=detail['analytic_within_budget']
        if e['PDE'] and e['analytic']:
            detail['PDE_analytic_price_gap']=abs(e['PDE'][-1]['values']['price']-e['analytic'][-1]['values']['price'])
        extdetails.append(detail)
    boundary=read(root/'BOUNDARY_REQUIRED_RESULTS.json',dict(rows=[],evaluated=0,planned=600));boundary_strict=Counter(z['status'] for z in boundary['rows'])
    # Unsupported exact-zero cases do not become false positive external checks.
    # Complete-coverage PASS additionally needs all retained difficult inputs,
    # available aligned external cases, three-route uncertainty and derivatives.
    core_pass=(len(rows)==1734 and len({key(r) for r in rows})==1734 and unresolved==0 and mp_done==len(needed) and mp_resolved==len(needed) and ext_ok==6 and all(u['within_budget'] for u in unc) and not any('exception' in r.get('failure_flags',[]) or any('financial_sanity' in f or f=='homogeneity' for f in r.get('failure_flags',[])) for r in rows))
    # PDE unresolved discrepancies remain in the actual uncertainty matrix;
    # they cannot be removed merely to pass the gate.
    core_gate='PASS' if core_pass else 'FAIL'
    metadata=dict(phase='1B.3',CORE=core_gate,BOUNDARY='FAIL',CHALLENGE='FAIL',Phase1C_authorized=False,core_evaluated=len(rows),core_planned=1734,strict_statistics=strict,original_flags=dict(flags),strict_failures_numerically_resolved=resolved,strict_failures_unresolved=unresolved,MP_required=len(needed),MP_evaluated=mp_done,MP_numerically_resolved=mp_resolved,external_analytic_supported=6,external_analytic_within_budget=ext_ok,external_details=extdetails,boundary_evaluated=boundary['evaluated'],boundary_planned=boundary['planned'],boundary_strict=dict(boundary_strict),history_integrity=dict(Counter(history.values())),tolerances_unchanged=True,domain_version='domain-v1-grid-v1.1-sobol4101')
    dump(root/'CERTIFICATION_RESULTS.json',dict(metadata=metadata,rows=rows,resolution_rows=table));save_npz(root/'CERTIFICATION_RESULTS.npz',rows)
    dump(root/'REFERENCE_UNCERTAINTY.json',dict(rows=unc,interpretation='observed numerical route disagreements, not rigorous confidence intervals'))
    arrays={f+'_max':np.array([u[f]['max_disagreement'] for u in unc]) for f in FIELDS}
    for f in FIELDS:
        width=max(len(u[f]['routes']) for u in unc);matrix=np.full((len(unc),width,width),np.nan);values=np.full((len(unc),width),np.nan);names=np.full((len(unc),width),'',dtype='U32');deviation=np.full((len(unc),width),np.nan)
        for i,u in enumerate(unc):
            n=len(u[f]['routes']);matrix[i,:n,:n]=u[f]['pairwise_matrix'];values[i,:n]=u[f]['values'];names[i,:n]=u[f]['routes'];deviation[i,:n]=[u[f]['deviation_from_route_median'][k] for k in u[f]['routes']]
        arrays.update({f+'_pairwise':matrix,f+'_values':values,f+'_routes':names,f+'_median':np.array([u[f]['median_disagreement'] for u in unc]),f+'_deviation':deviation})
    arrays.update({k:np.array([r[k] for r in rows]) for k in ['x','v','tau','K','kappa','theta','sigma','rho','r']});np.savez_compressed(root/'REFERENCE_UNCERTAINTY.npz',**arrays)
    def md(name,s):(root/name).write_text(s.strip()+'\n',encoding='utf-8')
    md('REFERENCE_VALIDATION_REPORT.md',f'''# Phase 1B.3 reference validation
CORE **{core_gate}**, BOUNDARY **FAIL**, CHALLENGE **FAIL**. Phase1C is not authorized.

Executed the exact original CORE catalog: {len(rows)}/1734, with 300 inherited SHA-verified deterministic rows and 1434 new Sobol rows. No Feller filtering, no altered Domain v1, no changed tolerance. Historical evidence: {dict(Counter(history.values()))}.

Original strict PASS {strict['PASS_rows']}; FAIL {strict['FAIL_rows']}. Separate resolution review: {resolved} failed rows numerically resolved, {unresolved} unresolved. Old strict statuses remain immutable. Flags (overlap): {dict(flags)}.

{gaps_table}

Every retained CORE failure/near-failure is explicitly planned: {len(needed)} required MP inputs, {mp_done} with available executed MP evidence, {mp_resolved} numerically resolved. The local external-light batch is predeclared by aligned external inputs and cost (positive v, tau>=.1), not by achieved accuracy. Complete MP work is COLAB_HEAVY; it has not been claimed complete locally.

Supported QuantLib analytic cases within unchanged price budgets: {ext_ok}/6; all 8 original inputs were attempted, with two exact v0=0 inputs rejected by the upstream model constraint. Independent PDE computations are retained even when their current gaps exceed budget. No PDE result is treated as absolute truth.

Training-required boundary strict coverage {boundary['evaluated']}/{boundary['planned']}; {dict(boundary_strict)}. Complete boundary MP and limiting-PDE compatibility remain unapproved. Evaluation-only OOD failures are preserved separately and do not decide CORE.

Tests, exact commands, resume behavior and the fresh-clone Colab workflow are documented in README.md. The Colab notebook writes reference_v3_colab/ and packages reference_v3_colab_results.zip. No remote result is claimed until actual execution. No neural training labels are generated.
''')
    md('CORE_DOMAIN_CERTIFICATE.md',f'''# CORE domain certificate
**{core_gate}. {'Certificate issued' if core_pass else 'Certificate NOT ISSUED'}.**

Exact catalog coverage {len(rows)}/1734. Strict {strict['PASS_rows']} PASS / {strict['FAIL_rows']} FAIL; unresolved after available evidence {unresolved}. All 1734 derivative studies are executed; execution does not establish reliable derivative certification. Remaining MP evidence {len(needed)-mp_done} planned inputs. External analytic within budget {ext_ok}/6 supported cases; unresolved external PDE gaps remain included in uncertainty.

The original pointwise price/Delta/KGamma/Vv/K budgets and two stable-refinement rules remain unchanged. An original strict PASS is only internal numerical resolution, not independent certification. No retrospective subdomain or CONDITIONAL PASS is declared.

Maximum final A/B gaps: { {f:strict['abs_'+f+'_gap']['max'] for f in FIELDS} }.
''')
    md('EXTERNAL_VALIDATION_REPORT.md',f'''# Pinned QuantLib 1.41 validation
Exact 8 predeclared aligned inputs attempted; {sum(bool(e['analytic']) for e in ext.get('rows',[]))} analytic/PDE cases executed. Original and exact-time-change calendar inputs, dates, curves, day count, all engine settings and individual failures are in EXTERNAL_RESULTS.json and external_checkpoints/.

{json.dumps(extdetails,indent=2)}

Exact v0=0: HestonProcess construction succeeds, but HestonModel rejects zero through its PositiveConstraint ([upstream 1.41 source](https://github.com/lballabio/QuantLib/blob/v1.41/ql/models/equity/hestonmodel.cpp)). This is UNSUPPORTED_EXACT_V0, not evidence of a mathematical singularity. No epsilon substitution was made. These two failed external attempts remain visible, while the six positive-variance cases independently triangulate CORE.

PDE axes are refined separately at the original settings, followed by larger combined grids. Current finite-grid values can exceed the unchanged reference budgets; all remain in the uncertainty matrices. Additional expensive refinements are prepared for Colab. Execution alone does not certify convergence; the complete cross-route MP comparison is pending where MP has not run. Local computations are not represented as Google Colab runs.
''')
    md('HIGH_PRECISION_REPORT.md',f'''# Complete-set MP escalation status
Required retained CORE failures/near-failures {len(needed)}; executed evidence {mp_done}; numerically resolved {mp_resolved}. Incomplete: {len(needed)-mp_done} inputs pending. HP_ESCALATION_PLAN.json enumerates every required input. mp_cases/ stores every actual 50/80/120-digit price/Delta/Gamma/Vv result, independent cutoff/degree sweeps, physical spot/variance/strike stencil prices, component statuses and exceptions. Inherited MP evidence remains linked to immutable reference_v2 files.

The new affine-variance cache reuses psi(v+dv)=psi(v)*exp(D*dv) in genuine MP arithmetic; it changes no model or quadrature formula. Separate tests compare it with the uncached implementation. No float64 prices enter the MP stencils. Precision agreement at a finite cutoff is not tail certification. All three axis changes contribute to FD price-uncertainty propagation.

Classification: NUMERICALLY_RESOLVED for matched point evidence; UNRESOLVED otherwise. CERTIFIED requires the full independent gate and is not assigned to incomplete evidence. Complete-set escalation is prepared in Colab, without selecting inputs by favorable outputs.
''')
    md('GREEK_CERTIFICATION.md',f'''# Greek certification
**Domain-wide certification incomplete.** All {len(rows)} CORE points have the original Delta/Gamma/Vv and physical-FD study. Flagged counts: {dict(flags)}. FD, strike, quadrature and COS failures cannot be cleared without matched evidence. MP derivative stencils include 3/5-point and Richardson Gamma, ten physical spot steps, central or right-sided variance steps, and explicit price-uncertainty propagation. Strike failures additionally require actual MP strike differences.

Retained failed-row resolution {resolved}; remaining unresolved {unresolved}. See FAILURE_RESOLUTION_TABLE.csv for every original flag, final diagnosis/status and evidence pointer. No domain Greek certificate follows from 1734 studies or the inherited selected Gamma resolutions alone.
''')
    md('BOUNDARY_REQUIRED_CERTIFICATION.md',f'''# Training-required boundary certification
**BOUNDARY GATE FAIL.** Predeclared deterministic finite x=+/-1.2, v_max=.25 and exact v=0 inputs at original CORE parameter regimes/maturities: {boundary['evaluated']}/{boundary['planned']} executed; strict {dict(boundary_strict)}.

These support the original Phase1A boundary objective. Evaluation-only short/OOD R4 points are not substitutes. Exact v=0 still requires c_tau=r*c_x+kappa*theta*c_v-r*c compatibility, right variance derivatives and v->0+ continuity. Exact terminal payoff is not differentiated at the kink. Complete MP boundary and limiting-PDE validation are pending; BOUNDARY_REQUIRED_PLAN.json and the notebook enumerate the work. No residual tolerance is invented where the original protocol did not declare one. No boundary labels are approved for training.
''')
    dump(root/'FINAL_PROVENANCE.json',dict(history=history,python=sys.version,platform=platform.platform(),module_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'reference_v3').glob('*.py')},git_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),note='No certified engine lock unless CORE passes; uncommitted source hashes are explicit.'))
    if core_pass:
        # Freeze only the independently certified implementation, never labels.
        lock=dict(read(root/'FINAL_PROVENANCE.json',{}),QuantLib='1.41',tolerances='unchanged Phase1A',grid='domain-v1-grid-v1.1-sobol4101',settings_files=['HP_ESCALATION_PLAN.json','EXTERNAL_RESULTS.json','CERTIFICATION_RESULTS.json'],neural_labels_generated=False)
        dump(root/'REFERENCE_ENGINE_LOCK.json',lock)
    print(json.dumps({k:metadata[k] for k in ['CORE','core_evaluated','strict_failures_unresolved','MP_required','MP_evaluated','external_analytic_within_budget','boundary_evaluated']}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',default='reference_v3');run(p.parse_args().output)
