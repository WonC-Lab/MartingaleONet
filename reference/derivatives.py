"""Independent physical-variable finite-difference diagnostics."""
from dataclasses import replace
import math
import numpy as np
from . import route_b

STEPS=(.02,.01,.005,.0025,.00125,.000625)
def studies(case, base):
    fixed=route_b.COS(4096,32,tuple(base.diagnostics["interval"]))
    rows=[]
    for rel in STEPS:
        h=case.S*rel; hs=[-2,-1,0,1,2]
        vals=[route_b.price(replace(case,x=math.log((case.S+j*h)/case.K)),fixed).price for j in hs]
        d=(vals[0]-8*vals[1]+8*vals[3]-vals[4])/(12*h)
        g=(-vals[4]+16*vals[3]-30*vals[2]+16*vals[1]-vals[0])/(12*h*h)
        hv=max(case.v,.01)*rel
        js=[-2,-1,0,1,2] if case.v>=2*hv else [0,1,2,3,4]
        vv=[route_b.price(replace(case,v=case.v+j*hv),fixed).price for j in js]
        cv=(vv[0]-8*vv[1]+8*vv[3]-vv[4])/(12*hv) if js[0]==-2 else np.dot([-25,48,-36,16,-3],vv)/(12*hv)
        rows.append(dict(relative_step=rel,hS=h,hv=hv,Delta=float(d),Gamma=float(g),Vv=float(cv),
            spot_stencil=vals,variance_stencil=vv,variance_offsets=js,
            amplification_Delta=18/(12*h),amplification_Gamma=64/(12*h*h),
            amplification_Vv=(18 if js[0]==-2 else 128)/(12*hv)))
    return rows

def strike_check(case,base,relative_step=.00125):
    h=case.K*relative_step
    cfg=route_b.COS(4096,32,tuple(base.diagnostics["interval"]))
    # X changes with K; fixed physical log(ST) means shift interval with log(K).
    vals=[]
    for j in [-2,-1,0,1,2]:
        k=case.K+j*h; shift=math.log(case.K/k)
        z=replace(case,K=k,x=math.log(case.S/k))
        shifted=replace(cfg,interval=tuple(a+shift for a in cfg.interval))
        vals.append(route_b.price(z,shifted).price)
    return dict(h=h,values=vals,V_K=(vals[0]-8*vals[1]+8*vals[3]-vals[4])/(12*h),
                V_KK=(-vals[4]+16*vals[3]-30*vals[2]+16*vals[1]-vals[0])/(12*h*h))
