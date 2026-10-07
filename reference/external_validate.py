"""Small external-only grid with exact date/time agreement; independent refinements."""
import argparse
from dataclasses import replace
from pathlib import Path
import numpy as np
from .types import Case
from . import external, route_a as A, route_b as B, certification_grid as grid
from .certify import dump

def run(output="reference",count=32):
    rows=[]
    for i in range(count):
        c=Case([-.3,0,.3,.7][i%4],[.01,.04,.16,.25][(i//4)%4],
               [30/365,180/365,1,2][(i//8)%4],1,grid.REGIMES[i%6],f"external_{i}")
        row={"input":c.row(),"status":"INDETERMINATE"}
        try:
            a=A.price(c,A.Quadrature(cutoff=2048));b=B.price(c,B.COS(4096,32))
            row.update(A=a.row(),B=b.row(),analytic=external.evaluate(c))
            fd=[]
            # Vary one PDE dimension at a time, not a coupled refinement.
            for config in [(100,300,150),(200,300,150),(400,300,150),
                           (400,100,150),(400,200,150),(400,400,150),
                           (400,400,50),(400,400,100),(400,400,200)]:
                fd.append(external.evaluate(c,True,*config))
            row["FD_refinements"]=fd
            row["analytic_AB_max_gap"]=max(abs(row["analytic"]["price"]-a.price),abs(row["analytic"]["price"]-b.price))
            row["price_budget"]=1e-8+1e-6*max(abs(a.price),abs(b.price))
            row["FD_changes"]=[abs(fd[j]["price"]-fd[j-1]["price"]) for j in [1,2,4,5,7,8]]
            row["FD_final_AB_max_gap"]=max(abs(fd[-1]["price"]-a.price),abs(fd[-1]["price"]-b.price))
            row["status"]="REVIEW_REQUIRED" if row["analytic_AB_max_gap"]<=row["price_budget"] else "FAIL"
        except Exception as exc:row["exception"]=repr(exc)
        rows.append(row)
        print(i+1,count,row["status"],flush=True)
    out=Path(output);out.mkdir(parents=True,exist_ok=True)
    dump(out/"EXTERNAL_RESULTS.json",dict(rows=rows,gate_impact="No automatic gate upgrade; PDE error-band review required"))
    return rows

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--output",default="reference");p.add_argument("--count",type=int,default=32)
    args=p.parse_args();run(args.output,args.count)
