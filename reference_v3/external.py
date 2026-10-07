"""Checkpoint every pinned external setting, including unsupported inputs."""
import argparse
import hashlib
import json
import platform,sys
from pathlib import Path
from reference.certify import dump
from reference_v2.external import cases,evaluate,QL_VERSION,QL_COMMIT,mapping
from reference import route_a as A,route_b as B

GRIDS=[(100,300,150),(200,300,150),(400,300,150),(400,100,150),(400,200,150),(400,400,150),(400,400,50),(400,400,100),(400,400,200)]
def adaptive(case,tolerance):
    import QuantLib as ql
    if ql.__version__!=QL_VERSION:raise RuntimeError('wrong QuantLib version')
    c,alignment=mapping(case);today=ql.Date(7,10,2026);expiry=today+alignment['days'];ql.Settings.instance().evaluationDate=today;dc=ql.Actual365Fixed()
    if abs(dc.yearFraction(today,expiry)-c.tau)>1e-14:raise ArithmeticError('day count mismatch')
    curve=ql.YieldTermStructureHandle(ql.FlatForward(today,c.p.r,dc,ql.Continuous));div=ql.YieldTermStructureHandle(ql.FlatForward(today,0.,dc,ql.Continuous))
    process=ql.HestonProcess(curve,div,ql.QuoteHandle(ql.SimpleQuote(c.S)),c.v,c.p.kappa,c.p.theta,c.p.sigma,c.p.rho);model=ql.HestonModel(process)
    option=ql.VanillaOption(ql.PlainVanillaPayoff(ql.Option.Call,c.K),ql.EuropeanExercise(expiry));engine=ql.AnalyticHestonEngine(model,tolerance,1000000);option.setPricingEngine(engine)
    return dict(values=dict(price=option.NPV()),engine='analytic',version=QL_VERSION,source_commit=QL_COMMIT,alignment=alignment,evaluation_date=today.ISO(),exercise_date=expiry.ISO(),day_count=dc.name(),calendar=ql.NullCalendar().name(),q=0.,original_input=case.row(),mapped_input=c.row(),integration_order=None,adaptive_relative_tolerance=tolerance,max_evaluations=1000000,integration='adaptive Gauss-Lobatto',grids=None)

def run(output='reference_v3',refine=False,local_refine=False,cross_environment=False,adaptive_refine=False):
    root=Path(output);check=root/'external_checkpoints'
    if cross_environment:
        environment=dict(python=sys.version,platform=platform.platform(),version=QL_VERSION)
        tag=hashlib.sha256(json.dumps(environment,sort_keys=True).encode()).hexdigest()[:12];check=check/tag
        dump(root/'CROSS_ENVIRONMENT_VALIDATION_PLAN.json',dict(deliberate_subset=True,CORE_points=6,exact_zero_challenge_points=2,entire_CORE_sweep_repeated=False,inputs=[c.row() for c in cases()],environment=environment,purpose='Independent aligned 8-case external analytic/PDE validation and A/B environment cross-check; not a new CORE full sweep'))
    check.mkdir(parents=True,exist_ok=True)
    initial={}
    prior=root/'EXTERNAL_RESULTS.json'
    if prior.exists() and not cross_environment:initial={r['input']['label']:r for r in json.loads(prior.read_text()).get('rows',[])}
    rows=[]
    for c in cases():
        inherited=initial.get(c.label,{})
        r=dict(input=c.row(),alignment=mapping(c)[1],status='REVIEW_REQUIRED',analytic=[],PDE=[],errors=[],A=inherited.get('A') or A.price(c,A.Quadrature(cutoff=8192)).row(),B=inherited.get('B') or B.price(c,B.COS(16384,32)).row())
        extra=([(800,800,400),(1600,800,400),(1600,1600,400),(1600,1600,800),(1600,3200,800),(1600,6400,800)] if refine else [(800,800,400)] if local_refine else []) if c.v>0 else []
        analytic_settings=[64,128,192]+([{'eps':eps} for eps in [1e-9,1e-11,1e-13]] if (refine or adaptive_refine) and c.label=='short_core' else [])
        for engine,settings in [('analytic',analytic_settings),('PDE',GRIDS+extra)]:
            for setting in settings:
                if engine=='PDE' and setting[1]>1600 and r['PDE']:
                    last=r['PDE'][-1]['values'];reference=r['A'];K=c.K
                    fields=['price','Delta','Gamma'];scales=[1/K,1,K];absolute=[1e-8,2e-6,2e-5];relative=[1e-6,1e-5,1e-4]
                    if all(abs(last[f]-reference[f])*s<=a+b*max(abs(last[f]*s),abs(reference[f]*s)) for f,s,a,b in zip(fields,scales,absolute,relative)):
                        r.setdefault('adaptive_grid_skips',[]).append(dict(grids=setting,reason='prior larger combined grid already meets unchanged price/Delta/KGamma disagreement budgets; no extra grid is needed for triangulation'))
                        continue
                identity=hashlib.sha256(json.dumps([c.row(),engine,setting,QL_VERSION]).encode()).hexdigest()[:20];path=check/(identity+'.json')
                if path.exists():record=json.loads(path.read_text())
                else:
                    reuse=next((z for z in inherited.get(engine,[]) if ((z.get('adaptive_relative_tolerance')==setting['eps'] if isinstance(setting,dict) else z['integration_order']==setting) if engine=='analytic' else tuple(z['grids'])==setting)),None)
                    try:record=dict(status='EXECUTED',result=reuse or (adaptive(c,setting['eps']) if isinstance(setting,dict) else evaluate(c,order=setting) if engine=='analytic' else evaluate(c,'PDE',grids=setting)))
                    except Exception as exc:record=dict(status='UNSUPPORTED_EXACT_V0' if c.v==0 else 'UNRESOLVED',exception=repr(exc),input=c.row(),engine=engine,setting=setting,alignment=r['alignment'],version=QL_VERSION,source_commit=QL_COMMIT)
                    dump(path,record)
                if record['status']=='EXECUTED':r[engine].append(record['result'])
                else:r['errors'].append(record);r['status']='UNSUPPORTED_EXACT_V0' if c.v==0 else 'UNRESOLVED'
        rows.append(r);dump(root/'EXTERNAL_RESULTS.json',dict(rows=rows,requested_version=QL_VERSION,source_commit=QL_COMMIT,attempted=len(rows),planned=8,complete=len(rows)==8,execution_location='runtime host; Colab only when run in Colab',exact_v0_constraint_source='https://github.com/lballabio/QuantLib/blob/v1.41/ql/models/equity/hestonmodel.cpp'))
        print('external',c.label,r['status'],len(r['analytic']),len(r['PDE']),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',default='reference_v3');p.add_argument('--refine',action='store_true');p.add_argument('--local-refine',action='store_true');p.add_argument('--cross-environment',action='store_true');p.add_argument('--adaptive',action='store_true');a=p.parse_args();run(a.output,a.refine,a.local_refine,a.cross_environment,a.adaptive)
