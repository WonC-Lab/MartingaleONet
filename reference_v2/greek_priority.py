"""MP escalation of every observed CORE FD truncation/amplification flag."""
import json
from pathlib import Path
from reference.certify import dump
from .workflow import from_row,span
from .high_precision import evaluate,finite_differences,MPConfig

def run(output="reference_v2"):
    root=Path(output);grid=json.loads((root/"CERTIFICATION_RESULTS.json").read_text())["grid_rows"]
    targets=[r for r in grid if r.get("domain")=="CORE" and "FD_derivative_amplification_or_truncation" in r.get("failure_flags",[])]
    rows=[]
    for i,r in enumerate(targets):
        c=from_row(r);h=dict(input=c.row(),domain="CORE",precision=[],degree=[],cutoff=[])
        h["input"]["label"]=f"GREEK_PRIORITY_{i}_{c.label}"
        for d in [50,80,120]:h["precision"].append(evaluate(c,MPConfig(d,4096,40,span(c))))
        for n in [24,40,64]:h["degree"].append(evaluate(c,MPConfig(80,4096,n,span(c))))
        for u in [1024,2048,4096,8192]:h["cutoff"].append(evaluate(c,MPConfig(80,u,40,span(c))))
        h["MP_FD"]=finite_differences(c,MPConfig(80,8192,40,span(c)))
        h["A"]={f:r[f"route_A_{f}"] for f in ["price","Delta","Gamma","Vv"]}
        h["B"]={f:r[f"route_B_{f}"] for f in ["price","Delta","Gamma","Vv"]}
        rows.append(h);dump(root/"HP_GREEK_PRIORITY.json",dict(rows=rows,planned=len(targets),evaluated=len(rows),complete=len(rows)==len(targets),
            selection="all CORE FD_derivative_amplification_or_truncation flags; no deletions"))
        print("Greek priority",i+1,len(targets),flush=True)

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser();p.add_argument("--output",default="reference_v2");run(p.parse_args().output)
