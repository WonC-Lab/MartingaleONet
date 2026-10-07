"""Actual v=0 limiting-PDE compatibility, checkpointed per required input."""
import argparse,hashlib,json
from concurrent.futures import ProcessPoolExecutor,as_completed
from dataclasses import replace
from pathlib import Path
from reference.certify import dump
from reference_v2.high_precision import evaluate,MPConfig,context
from reference_v2.workflow import span
from .boundary import plan
from .coverage import key

def worker(item):
    c,evidence=item;ctx=context(100);u=evidence.get('cutoff',[{'config':{'cutoff':32768}}])[-1]['config']['cutoff']
    cfg=MPConfig(80,u,40,span(c));base=evaluate(c,cfg);v=base['values'];K=ctx.mpf(str(c.K));S=ctx.mpf(str(c.S));p=c.p
    rhs=(ctx.mpf(str(p.r))*S*ctx.mpf(v['Delta'])+ctx.mpf(str(p.kappa))*ctx.mpf(str(p.theta))*ctx.mpf(v['Vv'])-ctx.mpf(str(p.r))*ctx.mpf(v['price']))/K
    levels=[]
    for relative in ['.001','.0005','.00025']:
        h=ctx.mpf(str(c.tau))*ctx.mpf(relative);prices=[]
        for j in [-2,-1,0,1,2]:
            # tau is supplied as an exact decimal string to the MP CF.
            cc=replace(c,tau=ctx.nstr(ctx.mpf(str(c.tau))+j*h,90))
            prices.append(ctx.mpf(evaluate(cc,cfg)['values']['price'])/K)
        derivative=(prices[0]-8*prices[1]+8*prices[3]-prices[4])/(12*h)
        levels.append(dict(relative_time_step=relative,c_tau=ctx.nstr(derivative,80),RHS=ctx.nstr(rhs,80),residual=ctx.nstr(derivative-rhs,80),stencil_prices=[ctx.nstr(z,80) for z in prices],coefficient_amplification=ctx.nstr(ctx.mpf(18)/(12*h),50)))
    return dict(input=c.row(),config=cfg.__dict__,base=base,levels=levels,status='REVIEW_REQUIRED',reason='No new limiting-PDE residual tolerance is invented; complete value/Greek and time-stencil convergence must be reviewed under the original protocol.')

def run(output='reference_v3',workers=2):
    root=Path(output);folder=root/'boundary_pde_checkpoints';folder.mkdir(exist_ok=True)
    by={}
    for p in (root/'mp_cases').rglob('*.json'):
        z=json.loads(p.read_text());by[key(z['input'])]=z
    tasks=[]
    for c in plan():
        if c.v!=0:continue
        identity=hashlib.sha256(json.dumps(key(c.row())).encode()).hexdigest()[:20];target=folder/(identity+'.json')
        if not target.exists():tasks.append((c,by.get(key(c.row()),{}),target))
    with ProcessPoolExecutor(max_workers=workers) as pool:
        fs={pool.submit(worker,(c,e)):target for c,e,target in tasks}
        for f in as_completed(fs):dump(fs[f],f.result());print('v0 limiting PDE',fs[f].name,flush=True)
    dump(root/'BOUNDARY_PDE_CHECKS.json',dict(rows=[json.loads(p.read_text()) for p in folder.glob('*.json')],planned=210))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',default='reference_v3');p.add_argument('--workers',type=int,default=2);a=p.parse_args();run(a.output,a.workers)
