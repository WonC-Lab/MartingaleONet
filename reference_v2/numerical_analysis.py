"""Precision-aware evidence analysis, separate from immutable raw outputs."""
import json
from pathlib import Path
import mpmath
from reference.certify import dump

FIELDS=["price","Delta","Gamma","Vv"]

def analyze(output="reference_v2"):
    root=Path(output);ctx=mpmath.mp.clone();ctx.dps=140;rows=[]
    for path in root.glob("HP_*.json"):
        for h in json.loads(path.read_text()).get("rows",[]):
            def numbers(e):return [ctx.mpf(e["values"][f]) for f in FIELDS]
            def changes(seq):
                ns=[numbers(e) for e in seq]
                return [max(abs(ns[i][j]-ns[i+1][j]) for i in range(max(0,len(ns)-3),len(ns)-1)) for j in range(4)]
            precision=changes(h["precision"]);degree=changes(h["degree"]);cutoff=changes(h["cutoff"])
            candidate=numbers(h["cutoff"][-1]);K=ctx.mpf(str(h["input"]["K"]))
            scales=[1/K,ctx.mpf(1),K,1/K]
            normalized=[abs(x*s) for x,s in zip(candidate,scales)]
            tol=[ctx.mpf(a)+ctx.mpf(b)*z for a,b,z in zip(["1e-8","2e-6","2e-5","2e-5"],["1e-6","1e-5","1e-4","1e-4"],normalized)]
            within=all(change*s<=t/4 for change,s,t in zip([max(p,d,u) for p,d,u in zip(precision,degree,cutoff)],scales,tol))
            cross=[max(abs(ctx.mpf(str(h[route][f]))-candidate[j]) if h[route].get(f) is not None else ctx.inf for route in ["A","B"]) for j,f in enumerate(FIELDS)]
            price_diagnostic=max(precision[0],degree[0],cutoff[0])
            fd=h["MP_FD"];base=[ctx.mpf(fd["base"][f]) for f in FIELDS];valid_windows=[]
            for i in range(2,len(fd["rows"])):
                trio=fd["rows"][i-2:i+1]
                latest=trio[-1]["values"];ok=True
                for j,f in enumerate(["Delta","Gamma","Vv"]):
                    vals=[ctx.mpf(z["values"][f+"5"]) for z in trio]
                    plateau=max(abs(vals[k+1]-vals[k]) for k in [0,1])
                    gap=abs(vals[-1]-base[j+1]);ampl=ctx.mpf(latest[f+"_amplification"])*price_diagnostic
                    if max(plateau,gap,ampl)*scales[j+1]>tol[j+1]/4:ok=False
                if ok:valid_windows.append([z["relative_step"] for z in trio])
            # Full domain certification never follows from a single resolved point.
            gamma_status="NUMERICALLY_RESOLVED" if within and cross[2]*K<=tol[2] and valid_windows else "UNRESOLVED"
            rows.append(dict(input=h["input"],domain=h["domain"],source=path.name,
                precision_changes={f:ctx.nstr(x,30) for f,x in zip(FIELDS,precision)},
                degree_changes={f:ctx.nstr(x,30) for f,x in zip(FIELDS,degree)},
                cutoff_changes={f:ctx.nstr(x,30) for f,x in zip(FIELDS,cutoff)},
                cross_route_max_gap={f:ctx.nstr(x,30) for f,x in zip(FIELDS,cross)},
                candidate_values={f:ctx.nstr(x,80) for f,x in zip(FIELDS,candidate)},
                MP_axes_within_budget=within,valid_FD_windows=valid_windows,gamma_status=gamma_status,
                price_diagnostic_uncertainty=ctx.nstr(price_diagnostic,30),
                conclusion="finite-cutoff/degree/precision evidence; observed errors are diagnostics, not rigorous bounds"))
    dump(root/"HIGH_PRECISION_ANALYSIS.json",dict(rows=rows))
    return rows

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser();p.add_argument("--output",default="reference_v2");analyze(p.parse_args().output)
