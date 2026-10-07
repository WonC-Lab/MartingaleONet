"""Optional pinned QuantLib check. Never silently round Heston maturity."""
import math

def evaluate(case,fd=False,t_grid=200,x_grid=200,v_grid=100):
    import QuantLib as ql
    if ql.__version__ != "1.41": raise RuntimeError(f"expected QuantLib 1.41, got {ql.__version__}")
    days=round(case.tau*365)
    if abs(days/365-case.tau)>1e-12: raise ValueError("external date maturity differs from requested tau")
    today=ql.Date(7,10,2026); maturity=today+days
    ql.Settings.instance().evaluationDate=today
    dc=ql.Actual365Fixed()
    rf=ql.YieldTermStructureHandle(ql.FlatForward(today,case.p.r,dc))
    div=ql.YieldTermStructureHandle(ql.FlatForward(today,0.,dc))
    process=ql.HestonProcess(rf,div,ql.QuoteHandle(ql.SimpleQuote(case.S)),case.v,
        case.p.kappa,case.p.theta,case.p.sigma,case.p.rho)
    model=ql.HestonModel(process)
    option=ql.VanillaOption(ql.PlainVanillaPayoff(ql.Option.Call,case.K),ql.EuropeanExercise(maturity))
    engine=ql.FdHestonVanillaEngine(model,t_grid,x_grid,v_grid) if fd else ql.AnalyticHestonEngine(model,192)
    option.setPricingEngine(engine)
    return dict(price=option.NPV(),engine="FD" if fd else "analytic",version=ql.__version__,
                actual_tau=days/365,t_grid=t_grid,x_grid=x_grid,v_grid=v_grid)
