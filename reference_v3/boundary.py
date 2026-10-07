"""Only the original objective's deterministic finite traces, not all OOD."""
import argparse
from concurrent.futures import ProcessPoolExecutor,as_completed
import json
from pathlib import Path
from reference.certification_grid import deterministic
from reference_v2.domains import parameter_core
from reference.certify import dump
from .coverage import worker,key

def plan():
    return [c for c in deterministic() if parameter_core(c.p) and 1/252<=c.tau<=2 and (c.v==0 or c.v==.25 or (abs(c.x)==1.2 and c.v>0))]

def run(output='reference_v3',workers=10,plan_only=False):
    root=Path(output);cases=plan()
    dump(root/'BOUNDARY_REQUIRED_PLAN.json',dict(planned=len(cases),selection='original deterministic finite x=+/-1.2, v_max=.25 traces and v=0 compatibility inputs; positive-tau CORE parameter support; not a random or outcome-selected subset',inputs=[c.row() for c in cases],v0_note='v=0 requires limiting PDE consistency; a price/Greek row alone cannot certify it'))
    if plan_only:return
    path=root/'boundary_required.jsonl';rows=[json.loads(z) for z in path.read_text().splitlines()] if path.exists() else [];known={key(r) for r in rows}
    with ProcessPoolExecutor(max_workers=workers) as pool:
        fs={pool.submit(worker,c):c for c in cases if key(c.row()) not in known}
        for f in as_completed(fs):
            r=f.result();r['training_required_boundary']=True
            with path.open('a',encoding='utf-8') as h:h.write(json.dumps(r,allow_nan=False)+'\n')
            rows.append(r)
            if len(rows)%25==0:print('required boundary',len(rows),len(cases),flush=True)
    dump(root/'BOUNDARY_REQUIRED_RESULTS.json',dict(rows=rows,planned=len(cases),evaluated=len(rows),complete=len(rows)==len(cases)))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',default='reference_v3');p.add_argument('--workers',type=int,default=10);p.add_argument('--plan-only',action='store_true');a=p.parse_args();run(a.output,a.workers,a.plan_only)
