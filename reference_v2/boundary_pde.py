"""Raw limiting-PDE consistency checks; no invented PDE acceptance tolerance."""
from dataclasses import replace
from pathlib import Path
from reference.types import Case
from reference.certification_grid import REGIMES
from reference import route_a as A
from reference.certify import dump

def run(output="reference_v2"):
    rows=[]
    for j in [0,4]:
        c=Case(0,0,.001,1,REGIMES[j],f"PDE_zero_R{j}")
        for u in [32768,524288]:
            cfg=A.Quadrature(cutoff=u,atol=1e-11,rtol=1e-11);base=A.price(c,cfg)
            rhs=c.p.r*c.S*base.Delta+c.p.kappa*c.p.theta*base.Vv-c.p.r*base.price
            for rel in [.001,.0005,.00025]:
                h=c.tau*rel;ps=[A.price(replace(c,tau=c.tau+i*h),cfg).price for i in [-2,-1,0,1,2]]
                dt=(ps[0]-8*ps[1]+8*ps[3]-ps[4])/(12*h)
                rows.append(dict(input=c.row(),cutoff=u,h_tau=h,prices=ps,
                    c_tau_FD=dt,limiting_PDE_rhs=rhs,residual=dt-rhs,base=base.row(),status="DIAGNOSTIC_ONLY"))
    dump(Path(output)/"BOUNDARY_PDE_CHECKS.json",dict(rows=rows,
        equation="c_tau=r*c_x+kappa*theta*c_v-r*c at v=0; c_x=exp(x)*Delta",
        warning="No PDE tolerance declared; finite-cutoff agreement is not a boundary certificate"))

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser();p.add_argument("--output",default="reference_v2");run(p.parse_args().output)
