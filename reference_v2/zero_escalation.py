"""Additional fixed typical-boundary case; never overwrites the initial MP study."""
import json
from pathlib import Path
from reference import route_a as A,route_b as B
from reference.certify import dump
from .workflow import from_row
from .high_precision import evaluate,finite_differences,MPConfig

def run(output="reference_v2"):
    root=Path(output);original=json.loads((root/"HP_local.json").read_text())["rows"][1]
    c=from_row(original["input"]);row=json.loads(json.dumps(original));row["input"]["label"]="HP_ZERO_R0_EXTENDED"
    row["A_original"]=row["A"];row["B_original"]=row["B"]
    # For h/S<=1e-5 the analytic phase envelope is far below .01.
    # Retain a conservative .01 bound; this changes node layout, not tolerances.
    for u in [131072,262144,524288]:
        row["cutoff"].append(evaluate(c,MPConfig(80,u,40,.01)))
        print("zero cutoff",u,flush=True)
    row["precision"]=[evaluate(c,MPConfig(d,524288,40,.01)) for d in [50,80,120]]
    row["degree"]=[evaluate(c,MPConfig(80,524288,n,.01)) for n in [24,40,64]]
    row["MP_FD"]=finite_differences(c,MPConfig(80,524288,40,.01),steps=['.00001','.000001','.0000001'])
    row["A"]=A.price(c,A.Quadrature(cutoff=524288,atol=1e-11,rtol=1e-11)).row()
    row["B"]=B.price(c,B.COS(65536,32)).row()
    dump(root/"HP_extended.json",dict(rows=[row],planned=1,evaluated=1,complete=True,
         warning="additional fixed boundary case; no domain gate upgrade"))

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser();p.add_argument("--output",default="reference_v2");run(p.parse_args().output)
