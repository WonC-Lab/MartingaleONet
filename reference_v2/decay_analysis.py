"""Numerically check the large-frequency decay implied by the affine CF."""
from pathlib import Path
from reference.types import Case
from reference.certification_grid import REGIMES
from reference.certify import dump
from .high_precision import context,cf

def run(output="reference_v2"):
    ctx=context(80);rows=[]
    for j in [0,4]:
        c=Case(0,0,.001,1,REGIMES[j],f"decay_R{j}");p=c.p
        k,t,s,rho=[ctx.mpf(str(x)) for x in [p.kappa,p.theta,p.sigma,p.rho]]
        alpha=(ctx.mpf(str(c.v))+k*t*ctx.mpf(str(c.tau)))*ctx.sqrt(1-rho*rho)/s
        points=[];previous=None
        for u in [2048,8192,32768,65536,131072,262144,524288,1048576,2097152]:
            value=cf(ctx,ctx.mpf(u)-ctx.j/2,c.v,c.tau,p)
            log_abs=ctx.log(abs(value))
            row=dict(u=u,log_abs_cf=ctx.nstr(log_abs,70),alpha_times_u=ctx.nstr(alpha*u,40))
            if previous:row['observed_decay_rate']=ctx.nstr(-(log_abs-previous[1])/(u-previous[0]),40)
            points.append(row);previous=(u,log_abs)
        rows.append(dict(input=c.row(),alpha=ctx.nstr(alpha,70),inverse_decay_scale=ctx.nstr(1/alpha,40),points=points))
    dump(Path(output)/"CF_DECAY_ANALYSIS.json",dict(rows=rows,
        derivation="For Re(d)>=0, |rho|<1, sigma>0: d~sigma*sqrt(1-rho^2)*|u|. Hence log|psi(u-i/2)|=-alpha*|u|+O(1), alpha=(v+kappa*theta*tau)*sqrt(1-rho^2)/sigma.",
        implication="Positive alpha yields integrable density/Greek Fourier tails at each fixed positive tau, including v=0 when kappa*theta>0. This is not a uniform bound as tau->0 or rho->+-1; cutoff certification is still required."))

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--output',default='reference_v2');run(p.parse_args().output)
