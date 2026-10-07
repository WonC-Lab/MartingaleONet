"""Auxiliary actual dense grid and float64 Gamma FD, not substitute certification."""
import argparse
from dataclasses import replace
import math
import json
from pathlib import Path
import time
import numpy as np
from reference import route_a as A,route_b as B
from reference.types import Case
from reference.certify import dump
from .workflow import from_row
from .high_precision import STEPS

def dense(output="reference_v2",size=31):
    rows=[];start=time.time()
    for x in np.linspace(-.7,.7,size):
        for tau in np.geomspace(1/252,2,size):
            c=Case(float(x),.04,float(tau),label="dense_R0")
            a=A.price(c,A.Quadrature(cutoff=2048));b=B.price(c,B.COS(4096,32))
            row={**c.row(),"status":"DIAGNOSTIC_ONLY","A":a.row(),"B":b.row(),"refinements_complete":False}
            for f in ["price","Delta","Gamma","Vv"]:row[f"abs_{f}_gap"]=abs(getattr(a,f)-getattr(b,f))
            rows.append(row)
        print("dense",len(rows),size*size,flush=True)
    dump(Path(output)/"DENSE_VISUAL_GRID.json",dict(size=size,rows=rows,elapsed_seconds=time.time()-start,
        warning="actual rectangular diagnostic grid; does not replace mandatory/reference convergence checks"))

def gamma_float(output="reference_v2",scope="local"):
    root=Path(output);hps=json.loads((root/f"HP_{scope}.json").read_text())["rows"];rows=[]
    for h in hps:
        c=from_row(h["input"]);base=B.price(c,B.COS(4096,32));cfg=B.COS(4096,32,tuple(base.diagnostics["interval"]))
        steps=[];previous=None
        for rel in STEPS:
            q=float(rel);dx=c.S*q
            prices=[B.price(replace(c,x=math.log((c.S+j*dx)/c.K)),cfg).price for j in [-2,-1,0,1,2]]
            g3=(prices[3]-2*prices[2]+prices[1])/dx**2
            g5=(-prices[4]+16*prices[3]-30*prices[2]+16*prices[1]-prices[0])/(12*dx**2)
            r=dict(relative_step=rel,hS=dx,prices=prices,Gamma3=g3,Gamma5=g5,
                   Gamma5_analytic_gap=abs(g5-base.Gamma))
            if previous:
                ratio=previous[0]/q;r["Richardson3"]=(ratio**2*g3-previous[1])/(ratio**2-1)
            steps.append(r);previous=(q,g3)
        rows.append(dict(input=c.row(),analytic_B=base.Gamma,rows=steps))
    dump(root/f"FLOAT_GAMMA_{scope}.json",dict(rows=rows))

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("action",choices=["dense","gamma"]);p.add_argument("--output",default="reference_v2");p.add_argument("--scope",default="local");p.add_argument("--size",type=int,default=31)
    a=p.parse_args();dense(a.output,a.size) if a.action=="dense" else gamma_float(a.output,a.scope)
