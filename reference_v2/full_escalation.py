"""User-run heavy escalation of every failed/near-failed retained input."""
import argparse
import json
from pathlib import Path
from reference.certify import dump
from .workflow import from_row,span,ROOT
from .high_precision import evaluate,finite_differences,MPConfig
from .domains import classify

def run(output="reference_v2",limit=None):
    root=Path(output);old=json.loads((ROOT/"reference/CERTIFICATION_RESULTS.json").read_text())["rows"]
    pool=old[:]
    for p in root.glob("coverage_*.jsonl"):pool += [json.loads(z) for z in p.read_text().splitlines()]
    keyfields=["x","v","tau","K","kappa","theta","sigma","rho","r"]
    selected={}
    for r in pool:
        near=any(r.get(f"normalized_{f}_gap",0)>=.1*r.get(f"tolerance_{f}",float('inf')) for f in ["price","Delta","Gamma","Vv"])
        if r["status"]!="PASS" or near:selected[tuple(r[k] for k in keyfields)]=r
    plan=list(selected.values())
    dump(root/"HP_ESCALATION_PLAN.json",dict(planned=len(plan),selection="all retained failures or >=10% predeclared discrepancy budget",inputs=[from_row(r).row() for r in plan]))
    done=root/"hp_retained";done.mkdir(exist_ok=True)
    if limit is not None:plan=plan[:limit]
    for i,r in enumerate(plan):
        target=done/f"case_{i:05d}.json"
        if target.exists():continue
        c=from_row(r);domain=classify(c)
        cuts=[512,1024,2048,4096,8192] if domain=="CORE" else [2048,8192,32768,65536,131072,262144]
        row=dict(input=c.row(),domain=domain,precision=[],degree=[],cutoff=[])
        initial=2048 if domain=="CORE" else 8192
        for d in [50,80,120]:row["precision"].append(evaluate(c,MPConfig(d,initial,40,span(c))))
        for n in [24,40,64]:row["degree"].append(evaluate(c,MPConfig(80,initial,n,span(c))))
        import mpmath
        ctx=mpmath.mp.clone();ctx.dps=130
        factors=[1/c.K,1,c.K,1/c.K];fields=["price","Delta","Gamma","Vv"]
        budgets=[ctx.mpf(str(r.get("tolerance_"+f,1e-8 if f=="price" else 2e-6 if f=="Delta" else 2e-5))) for f in fields]
        row["tail_stable"]=False
        for u in cuts:
            row["cutoff"].append(evaluate(c,MPConfig(80,u,40,span(c))))
            if len(row["cutoff"])>=3:
                ns=[[ctx.mpf(z["values"][f]) for f in fields] for z in row["cutoff"][-3:]]
                row["tail_stable"]=all(max(abs(ns[1][j]-ns[0][j]),abs(ns[2][j]-ns[1][j]))*factors[j]<=budgets[j]/4 for j in range(4))
                if row["tail_stable"]:break
        # Full FD at the largest explicitly computed cutoff. Insufficient tails
        # stay UNRESOLVED; this can be expensive and is intentionally Colab-only.
        fdcut=row["cutoff"][-1]["config"]["cutoff"]
        row["MP_FD"]=finite_differences(c,MPConfig(80,fdcut,40,span(c)))
        row["A"]={f:r.get(f"route_A_{f}") for f in ["price","Delta","Gamma","Vv"]}
        row["B"]={f:r.get(f"route_B_{f}") for f in ["price","Delta","Gamma","Vv"]}
        dump(target,row);print("retained HP",i+1,len(plan),flush=True)
    results=[json.loads(p.read_text()) for p in sorted(done.glob("case_*.json"))]
    dump(root/"HP_retained.json",dict(rows=results,planned=len(selected),evaluated=len(results),complete=len(results)==len(selected)))

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--output",default="reference_v2");p.add_argument("--limit",type=int)
    a=p.parse_args();run(a.output,a.limit)
