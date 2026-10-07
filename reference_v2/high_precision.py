"""Genuine arbitrary precision Lewis half-contour reference and physical FD.

No NumPy/scipy float64 computation in the pricing algebra or quadrature.
Finite cutoff/degree are explicit; precision convergence alone is insufficient.
"""
from dataclasses import dataclass, replace
from functools import lru_cache
import time
import mpmath

@dataclass(frozen=True)
class MPConfig:
    dps: int = 50
    cutoff: int = 2048
    degree: int = 24
    phase_span: float = .75

def context(dps):
    if dps<30:raise ValueError("at least 30 decimal digits required")
    ctx=mpmath.mp.clone();ctx.dps=dps
    return ctx

def num(ctx,value):return ctx.mpf(str(value))

def cf(ctx,u,v,tau,p,with_D=False):
    u=ctx.mpc(u);v=num(ctx,v);t=num(ctx,tau)
    k,theta,sigma,rho,r=[num(ctx,getattr(p,f)) for f in ["kappa","theta","sigma","rho","r"]]
    if u==0:return (ctx.mpc(1),ctx.mpc(0)) if with_D else ctx.mpc(1)
    if u==-ctx.j:return (ctx.exp(r*t),ctx.mpc(0)) if with_D else ctx.exp(r*t)
    if sigma==0:
        av=t if k==0 else -ctx.expm1(-k*t)/k
        iv=v*t if k==0 else theta*t+(v-theta)*av
        D=-(u*u+ctx.j*u)*av/2
        z=ctx.exp(ctx.j*u*r*t-(u*u+ctx.j*u)*iv/2)
    else:
        beta=k-rho*sigma*ctx.j*u
        root=ctx.sqrt(beta*beta+sigma*sigma*(u*u+ctx.j*u))
        if ctx.re(root)<0:root=-root
        ratio=(beta-root)/(beta+root)
        decay=ctx.exp(-root*t)
        D=(beta-root)/(sigma*sigma)*(-ctx.expm1(-root*t))/(1-ratio*decay)
        C=k*theta/(sigma*sigma)*((beta-root)*t-2*(ctx.log1p(-ratio*decay)-ctx.log1p(-ratio)))
        z=ctx.exp(ctx.j*u*r*t+C+v*D)
    return (z,D) if with_D else z

@lru_cache(maxsize=24)
def gaussian_rule(dps,degree):
    ctx=context(dps);nodes,weights=ctx.gauss_quadrature(degree,"legendre")
    return tuple(nodes),tuple(weights)

def integration_grid(ctx,cfg):
    base,w=gaussian_rule(cfg.dps,cfg.degree)
    cutoff=num(ctx,cfg.cutoff)
    # Phase_span is a predeclared bound on local oscillation, not observed error.
    max_width=ctx.pi*cfg.degree/(4*max(num(ctx,cfg.phase_span),ctx.mpf('.01')))
    edges=[ctx.mpf(0)];left=ctx.mpf(0);width=ctx.mpf(1)
    while left<cutoff:
        right=min(cutoff,left+min(width,max_width));edges.append(right)
        left=right;width*=2
    nodes=[];weights=[]
    for a,b in zip(edges,edges[1:]):
        mid=(a+b)/2;half=(b-a)/2
        for q,wq in zip(base,w):nodes.append(mid+half*q);weights.append(half*wq)
    return nodes,weights,len(edges)-1

class Integrator:
    def __init__(self,case,cfg=MPConfig()):
        self.case=case;self.cfg=cfg;self.ctx=context(cfg.dps)
        self.u,self.weights,self.panels=integration_grid(self.ctx,cfg)
        self.cache={}

    def spectrum(self,v):
        key=str(v)
        if key not in self.cache:
            self.cache[key]=[cf(self.ctx,u-self.ctx.j/2,v,self.case.tau,self.case.p,True) for u in self.u]
        return self.cache[key]

    def values(self,S=None,v=None,greeks=True):
        c=self.case;ctx=self.ctx
        K=num(ctx,c.K);S=num(ctx,c.S) if S is None else ctx.mpf(S)
        variance=num(ctx,c.v) if v is None else ctx.mpf(v)
        x=ctx.log(S/K);root=ctx.sqrt(S*K);disc=ctx.exp(-num(ctx,c.p.r)*num(ctx,c.tau))
        spec=self.spectrum(variance)
        z=[ctx.exp(ctx.j*u*x)*phi for u,(phi,D) in zip(self.u,spec)]
        integral=ctx.fsum(w*ctx.re(q)/(u*u+ctx.mpf('.25')) for w,u,q in zip(self.weights,self.u,z))
        price=S-disc*root/ctx.pi*integral
        out={"price":price}
        if greeks:
            dx=ctx.fsum(w*ctx.re((ctx.mpf('.5')+ctx.j*u)*q)/(u*u+ctx.mpf('.25')) for w,u,q in zip(self.weights,self.u,z))
            density=ctx.fsum(w*ctx.re(q) for w,q in zip(self.weights,z))
            dv=ctx.fsum(w*ctx.re(q*D)/(u*u+ctx.mpf('.25')) for w,u,q,(_,D) in zip(self.weights,self.u,z,spec))
            out.update(Delta=1-disc*root/(S*ctx.pi)*dx,
                Gamma=disc*root/(S*S*ctx.pi)*density,Vv=-disc*root/ctx.pi*dv)
            out["Vega_s"]=2*ctx.sqrt(variance)*out["Vv"]
        return out

def serial(ctx,values):
    return {k:ctx.nstr(v,ctx.dps) for k,v in values.items()}

def evaluate(case,cfg=MPConfig()):
    start=time.time();obj=Integrator(case,cfg);values=obj.values()
    return dict(values=serial(obj.ctx,values),config=cfg.__dict__,panels=obj.panels,
                nodes=len(obj.u),elapsed_seconds=time.time()-start,raw_unclipped=True,
                tail_certified=False,route="MP-Lewis")

STEPS=(".02",".01",".005",".0025",".00125",".000625",".0001",".00001",".000001",".0000001")
def finite_differences(case,cfg=MPConfig(),steps=STEPS):
    obj=Integrator(case,cfg);ctx=obj.ctx;S=num(ctx,case.S);v=num(ctx,case.v)
    base=obj.values();rows=[];previous=None
    for rel in steps:
        q=ctx.mpf(rel);h=S*q;hv=max(v,ctx.mpf('.01'))*q
        prices=[obj.values(S=S+j*h,greeks=False)["price"] for j in [-2,-1,0,1,2]]
        delta3=(prices[3]-prices[1])/(2*h)
        gamma3=(prices[3]-2*prices[2]+prices[1])/(h*h)
        delta5=(prices[0]-8*prices[1]+8*prices[3]-prices[4])/(12*h)
        gamma5=(-prices[4]+16*prices[3]-30*prices[2]+16*prices[1]-prices[0])/(12*h*h)
        offsets=[-2,-1,0,1,2] if v>=2*hv else [0,1,2,3,4]
        vp=[obj.values(v=v+j*hv,greeks=False)["price"] for j in offsets]
        if offsets[0]==-2:
            vv3=(vp[3]-vp[1])/(2*hv);vv5=(vp[0]-8*vp[1]+8*vp[3]-vp[4])/(12*hv)
        else:
            vv3=(-3*vp[0]+4*vp[1]-vp[2])/(2*hv)
            vv5=(-25*vp[0]+48*vp[1]-36*vp[2]+16*vp[3]-3*vp[4])/(12*hv)
        vals=dict(hS=h,hv=hv,Delta3=delta3,Delta5=delta5,Gamma3=gamma3,Gamma5=gamma5,Vv3=vv3,Vv5=vv5,
            Delta5_analytic_gap=abs(delta5-base["Delta"]),Gamma5_analytic_gap=abs(gamma5-base["Gamma"]),
            Vv5_analytic_gap=abs(vv5-base["Vv"]),Gamma_amplification=ctx.mpf(64)/(12*h*h),
            Delta_amplification=ctx.mpf(18)/(12*h),Vv_amplification=ctx.mpf(18 if offsets[0]==-2 else 128)/(12*hv))
        if previous is not None:
            ratio=previous[0]/q
            vals["Gamma_Richardson3"]=(ratio**2*gamma3-previous[1])/(ratio**2-1)
            vals["Gamma_Richardson5"]=(ratio**4*gamma5-previous[2])/(ratio**4-1)
        rows.append(dict(relative_step=rel,values=serial(ctx,vals),
            spot_prices=[ctx.nstr(z,ctx.dps) for z in prices],variance_prices=[ctx.nstr(z,ctx.dps) for z in vp],
            variance_offsets=offsets))
        previous=(q,gamma3,gamma5)
    return dict(config=cfg.__dict__,base=serial(ctx,base),rows=rows,route="MP-price-FD",
                warning="FD agreement with fixed-grid analytic integral is not independent tail certification")
