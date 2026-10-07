"""Explicit Greek stencil precision convergence on selected cases."""
import json
from pathlib import Path
from reference.certify import dump
from .workflow import from_row,span
from .high_precision import MPConfig,finite_differences

def run(output="reference_v2"):
    root=Path(output);hps=json.loads((root/"HP_local.json").read_text())["rows"];rows=[]
    for h in hps:
        c=from_row(h["input"]);cutoff=h["MP_FD"]["config"]["cutoff"]
        checks=[finite_differences(c,MPConfig(d,cutoff,40,span(c)),steps=['.00001','.000001','.0000001']) for d in [50,80,120]]
        rows.append(dict(input=c.row(),checks=checks));print("FD precision",c.label,flush=True)
    dump(root/"FD_PRECISION_CONVERGENCE.json",dict(rows=rows,
         warning="matched finite integration grid; stable digits cannot resolve an unbounded tail"))

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser();p.add_argument("--output",default="reference_v2");run(p.parse_args().output)
