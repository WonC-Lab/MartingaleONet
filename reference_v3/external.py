"""Checkpoint every pinned external setting, including unsupported inputs."""
import argparse
import hashlib
import json
from pathlib import Path
from reference.certify import dump
from reference_v2.external import cases,evaluate,QL_VERSION,QL_COMMIT,mapping
from reference import route_a as A,route_b as B

GRIDS=[(100,300,150),(200,300,150),(400,300,150),(400,100,150),(400,200,150),(400,400,150),(400,400,50),(400,400,100),(400,400,200)]
def run(output='reference_v3',refine=False,local_refine=False):
    root=Path(output);check=root/'external_checkpoints';check.mkdir(parents=True,exist_ok=True)
    initial={}
    prior=root/'EXTERNAL_RESULTS.json'
    if prior.exists():initial={r['input']['label']:r for r in json.loads(prior.read_text()).get('rows',[])}
    rows=[]
    for c in cases():
        inherited=initial.get(c.label,{})
        r=dict(input=c.row(),alignment=mapping(c)[1],status='REVIEW_REQUIRED',analytic=[],PDE=[],errors=[],A=inherited.get('A') or A.price(c,A.Quadrature(cutoff=8192)).row(),B=inherited.get('B') or B.price(c,B.COS(16384,32)).row())
        extra=([(800,800,400),(1600,800,400),(1600,1600,400),(1600,1600,800)] if refine else [(800,800,400)] if local_refine else []) if c.v>0 else []
        for engine,settings in [('analytic',[64,128,192]),('PDE',GRIDS+extra)]:
            for setting in settings:
                identity=hashlib.sha256(json.dumps([c.row(),engine,setting,QL_VERSION]).encode()).hexdigest()[:20];path=check/(identity+'.json')
                if path.exists():record=json.loads(path.read_text())
                else:
                    reuse=next((z for z in inherited.get(engine,[]) if (z['integration_order']==setting if engine=='analytic' else tuple(z['grids'])==setting)),None)
                    try:record=dict(status='EXECUTED',result=reuse or (evaluate(c,order=setting) if engine=='analytic' else evaluate(c,'PDE',grids=setting)))
                    except Exception as exc:record=dict(status='UNSUPPORTED_EXACT_V0' if c.v==0 else 'UNRESOLVED',exception=repr(exc),input=c.row(),engine=engine,setting=setting,alignment=r['alignment'],version=QL_VERSION,source_commit=QL_COMMIT)
                    dump(path,record)
                if record['status']=='EXECUTED':r[engine].append(record['result'])
                else:r['errors'].append(record);r['status']='UNSUPPORTED_EXACT_V0' if c.v==0 else 'UNRESOLVED'
        rows.append(r);dump(root/'EXTERNAL_RESULTS.json',dict(rows=rows,requested_version=QL_VERSION,source_commit=QL_COMMIT,attempted=len(rows),planned=8,complete=len(rows)==8,execution_location='runtime host; Colab only when run in Colab',exact_v0_constraint_source='https://github.com/lballabio/QuantLib/blob/v1.41/ql/models/equity/hestonmodel.cpp'))
        print('external',c.label,r['status'],len(r['analytic']),len(r['PDE']),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',default='reference_v3');p.add_argument('--refine',action='store_true');p.add_argument('--local-refine',action='store_true');a=p.parse_args();run(a.output,a.refine,a.local_refine)
