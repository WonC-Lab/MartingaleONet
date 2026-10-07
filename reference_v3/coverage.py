"""Resume the exact predeclared CORE grid, preserving every strict row."""
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import json
import os
from pathlib import Path
import time
from reference.certify import assess, clean, dump
from reference_v2.domains import all_core, classify
from reference_v2.workflow import ROOT
from .provenance import verified

KEYS=('x','v','tau','K','kappa','theta','sigma','rho','r')
def key(r):return tuple(r[k] for k in KEYS)
def worker(c):
    try:r,_,_=assess(c)
    except Exception as e:r={**c.row(),'status':'FAIL','failure_flags':['exception'],'exception':repr(e)}
    return clean(r)

def run(output='reference_v3',workers=10):
    out=Path(output);out.mkdir(exist_ok=True,parents=True)
    old=ROOT/'reference_v2';meta=json.loads((old/'COVERAGE_mandatory.json').read_text())
    for name,h in meta['source_sha256'].items():
        p=ROOT/name
        if name=='reference_v2/workflow.py':p=old/'executed_sources/workflow_coverage_v2_0.py'
        verified(p,h)
    cases=all_core();catalog={key(c.row()):i for i,c in enumerate(cases)}
    path=out/'coverage_core.jsonl'
    if not path.exists():
        with path.open('w',encoding='utf-8') as h:
            for r in meta['rows']:
                row=dict(r,domain='CORE',grid_index=catalog[key(r)],inherited_source='reference_v2/COVERAGE_mandatory.json')
                h.write(json.dumps(row,allow_nan=False)+'\n')
    done={key(r):r for r in [json.loads(z) for z in path.read_text().splitlines()]}
    pending=[c for c in cases if key(c.row()) not in done]
    dump(out/'CORE_PLAN.json',dict(planned=len(cases),inherited=300,remaining_at_start=len(pending),inputs=[c.row() for c in cases]))
    start=time.time()
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures={pool.submit(worker,c):c for c in pending}
        for f in as_completed(futures):
            c=futures[f];r=f.result();r.update(domain=classify(c),grid_index=catalog[key(r)],execution_source='reference_v3.coverage')
            with path.open('a',encoding='utf-8') as h:h.write(json.dumps(r,allow_nan=False)+'\n')
            done[key(r)]=r
            if len(done)%25==0 or len(done)==len(cases):print('CORE',len(done),len(cases),'elapsed',round(time.time()-start,1),flush=True)
    rows=[done[key(c.row())] for c in cases]
    dump(out/'COVERAGE_core.json',dict(planned=len(cases),evaluated=len(rows),complete=len(rows)==len(cases),rows=rows,elapsed_this_session=time.time()-start))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',default='reference_v3');p.add_argument('--workers',type=int,default=10)
    a=p.parse_args();run(a.output,a.workers)
