"""Pinned external analytic/PDE engines with exact time-change alignment."""
import argparse
from dataclasses import replace
import importlib.util
import math
from pathlib import Path
from reference.types import Case,Parameters
from reference.certification_grid import REGIMES
from reference import route_a as A,route_b as B
from reference.certify import dump

QL_VERSION="1.41"
QL_COMMIT="367ce80ae4f285835ceb3bba97746bea239984ad"
SOURCE_URL=f"https://github.com/lballabio/QuantLib/tree/{QL_COMMIT}"

def mapping(case):
    days=max(1,round(case.tau*365));calendar_tau=days/365
    scale=case.tau/calendar_tau
    p=case.p
    mapped=replace(case,tau=calendar_tau,v=scale*case.v,
                   p=Parameters(scale*p.kappa,scale*p.theta,scale*p.sigma,p.rho,scale*p.r))
    return mapped,dict(target_tau=case.tau,calendar_tau=calendar_tau,days=days,
        exact_time_change_scale=scale,mode="direct" if abs(scale-1)<1e-14 else "exact_process_time_change",
        Vv_chain_rule_factor=scale)

def evaluate(case,engine="analytic",order=192,grids=(200,200,100)):
    import QuantLib as ql
    if ql.__version__!=QL_VERSION:raise RuntimeError(f"QuantLib {QL_VERSION} required, got {ql.__version__}")
    c,alignment=mapping(case);today=ql.Date(7,10,2026);expiry=today+alignment["days"]
    ql.Settings.instance().evaluationDate=today
    dc=ql.Actual365Fixed();calendar=ql.NullCalendar()
    if abs(dc.yearFraction(today,expiry)-c.tau)>1e-14:raise ArithmeticError("day-count alignment failed")
    curve=ql.YieldTermStructureHandle(ql.FlatForward(today,c.p.r,dc,ql.Continuous))
    div=ql.YieldTermStructureHandle(ql.FlatForward(today,0.,dc,ql.Continuous))
    process=ql.HestonProcess(curve,div,ql.QuoteHandle(ql.SimpleQuote(c.S)),c.v,c.p.kappa,c.p.theta,c.p.sigma,c.p.rho)
    model=ql.HestonModel(process)
    option=ql.VanillaOption(ql.PlainVanillaPayoff(ql.Option.Call,c.K),ql.EuropeanExercise(expiry))
    obj=ql.AnalyticHestonEngine(model,order) if engine=="analytic" else ql.FdHestonVanillaEngine(model,*grids)
    option.setPricingEngine(obj);values={"price":option.NPV()}
    if engine=="PDE":values.update(Delta=option.delta(),Gamma=option.gamma())
    return dict(values=values,engine=engine,version=ql.__version__,source_commit=QL_COMMIT,alignment=alignment,
        evaluation_date=today.ISO(),exercise_date=expiry.ISO(),day_count=dc.name(),calendar=calendar.name(),
        time_convention="years; exact process time change when calendar fraction differs",q=0.,
        original_input=case.row(),mapped_input=c.row(),integration_order=order,grids=grids)

def cases():
    return [Case(0,.04,1,1,REGIMES[0],"easy_ATM"),Case(-.7,.04,1,1,REGIMES[0],"deep_OTM"),
            Case(.7,.04,1,1,REGIMES[0],"deep_ITM"),Case(0,.01,1/252,1,REGIMES[0],"short_core"),
            Case(0,.04,1,1,REGIMES[5],"high_vol_of_vol"),Case(0,.04,1,1,REGIMES[1],"near_Feller"),
            Case(0,0,.001,1,REGIMES[4],"severe_failed"),Case(0,0,.001,1,REGIMES[0],"zero_short_R0")]

def run(output="reference_v2"):
    rows=[]
    for c in cases():
        r={"input":c.row(),"status":"INDETERMINATE","analytic":[],"PDE":[]}
        try:
            r["A"]=A.price(c,A.Quadrature(cutoff=8192)).row();r["B"]=B.price(c,B.COS(16384,32)).row()
            for order in [64,128,192]:r["analytic"].append(evaluate(c,order=order))
            for grids in [(100,300,150),(200,300,150),(400,300,150),
                          (400,100,150),(400,200,150),(400,400,150),
                          (400,400,50),(400,400,100),(400,400,200)]:r["PDE"].append(evaluate(c,"PDE",grids=grids))
            r["status"]="REVIEW_REQUIRED"
        except Exception as exc:r["exception"]=repr(exc)
        rows.append(r);print("external",c.label,r["status"],flush=True)
    dump(Path(output)/"EXTERNAL_RESULTS.json",dict(installed=bool(importlib.util.find_spec("QuantLib")),rows=rows,
        requested_version=QL_VERSION,source_commit=QL_COMMIT,source_url=SOURCE_URL,
        warning="No automatic gate upgrade; measured analytic/PDE refinement review required"))

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--output",default="reference_v2");run(p.parse_args().output)
