"""Explicit all-failure CORE escalation, multiprocess with per-case checkpoints."""
import argparse
from concurrent.futures import ProcessPoolExecutor,as_completed
import hashlib
import json
from pathlib import Path
import time
from reference.certify import dump
from reference_v2.workflow import ROOT
from .mp import worker

KEYS=('x','v','tau','K','kappa','theta','sigma','rho','r')
def key(r):return tuple(r[k] for k in KEYS)
def selected(r):
    return r['status']!='PASS' or any((r.get('normalized_'+f+'_gap') or 0)>=.1*r.get('tolerance_'+f,float('inf')) for f in ['price','Delta','Gamma','Vv'])

def run(output='reference_v3',workers=12,scope='all',plan_only=False):
    out=Path(output);done=out/'mp_cases';done.mkdir(exist_ok=True)
    rows=[json.loads(z) for z in (out/'coverage_core.jsonl').read_text().splitlines()]
    selected_rows=[r for r in rows if selected(r)]
    history=json.loads((ROOT/'reference/CERTIFICATION_RESULTS.json').read_text())['rows']
    from reference_v2.domains import classify
    from reference_v2.workflow import from_row
    unique={key(r):r for r in selected_rows}
    for r in history:
        if classify(from_row(r))=='CORE' and selected(r) and key(r) not in unique:unique[key(r)]={**r,'domain':'CORE'}
    plan=list(unique.values())
    sources={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'reference_v3/mp.py',ROOT/'reference_v2/high_precision.py',ROOT/'reference/route_a.py',ROOT/'reference/route_b.py']}
    fingerprint=hashlib.sha256(json.dumps(sources,sort_keys=True).encode()).hexdigest()
    dump(out/'HP_ESCALATION_PLAN.json',dict(planned=len(plan),selection='every strict CORE failure and >=10% budget near-failure; historical CORE failures included',inputs=[{k:r[k] for k in KEYS} for r in plan],source_sha256=sources))
    if plan_only:return
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
    for r in plan:
        if local_keys is not None and key(r) not in local_keys:continue
        identity=hashlib.sha256(json.dumps(key(r)).encode()).hexdigest()[:20]
        path=done/(identity+'.json')
        if path.exists():
            if json.loads(path.read_text()).get('execution_fingerprint')!=fingerprint:raise RuntimeError('MP source mismatch')
        else:tasks.append((r,path))
    start=time.time();count=len(list(done.glob('*.json')))
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures={pool.submit(worker,r):path for r,path in tasks}
        for f in as_completed(futures):
            z=f.result();z['execution_fingerprint']=fingerprint;dump(futures[f],z);count+=1
            print('MP',count,len(plan),z['input']['label'],z['status'],'elapsed',round(time.time()-start,1),flush=True)
    result=[json.loads(p.read_text()) for p in done.glob('*.json')]
    dump(out/'HP_core.json',dict(rows=result,planned=len(unique),evaluated=len(result),complete=all((done/(hashlib.sha256(json.dumps(key(r)).encode()).hexdigest()[:20]+'.json')).exists() for r in unique.values()),execution_scope=scope,source_sha256=sources))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',default='reference_v3');p.add_argument('--workers',type=int,default=12);p.add_argument('--scope',choices=['all','external-light'],default='all');p.add_argument('--plan-only',action='store_true')
    a=p.parse_args();run(a.output,a.workers,a.scope,a.plan_only)
