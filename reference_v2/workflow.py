"""Versioned run orchestration, data preservation and explicit incomplete gates."""
import argparse
from collections import Counter
from dataclasses import replace
import csv
import hashlib
import importlib.metadata
import json
from pathlib import Path
import time
import numpy as np
from reference.types import Case,Parameters
from reference import route_a as A,route_b as B
from reference.certification_grid import REGIMES,full
from reference.certify import assess,dump,clean,save_npz,summarize
from .domains import classify,mandatory_core,all_core,VERSION
from .high_precision import evaluate,finite_differences,MPConfig

ROOT=Path(__file__).resolve().parents[1]
HISTORY=ROOT/"reference"

def from_row(r):
    p=Parameters(**{f:r[f] for f in ["kappa","theta","sigma","rho","r"]})
    return Case(r["x"],r["v"],r["tau"],r["K"],p,r["label"])

def history_hashes():
    return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
            for base in ["reference","audit","design"] for p in (ROOT/base).rglob("*")
            if p.is_file() and "__pycache__" not in p.parts}

def initialize(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    path=out/"HISTORICAL_SNAPSHOT.json"
    if not path.exists():dump(path,history_hashes())
    return out

def verify_history(out):
    old=json.loads((Path(out)/"HISTORICAL_SNAPSHOT.json").read_text())
    changed=[k for k,v in old.items() if not (ROOT/k).exists() or hashlib.sha256((ROOT/k).read_bytes()).hexdigest()!=v]
    if changed:raise RuntimeError(f"historical evidence changed: {changed}")
    return {"historical_files_verified":len(old),"modified":changed}

def reproduce(out):
    out=initialize(out);old=json.loads((HISTORY/"CERTIFICATION_RESULTS.json").read_text());rows=[]
    for i,r in enumerate(old["rows"]):
        c=from_row(r);new,errors,_=assess(c);new["domain"]=classify(c);new["historical_index"]=i
        new["reproduction_same_status"]=new["status"]==r["status"]
        new["reproduction_value_max_gap"]=max(abs(new.get(f"route_{route}_{f}",np.nan)-r.get(f"route_{route}_{f}",np.nan))
            for route in ["A","B"] for f in ["price","Delta","Gamma","Vv"])
        rows.append(new);print("reproduce",i+1,len(old["rows"]),new["status"],flush=True)
    dump(out/"REPRODUCTION.json",dict(rows=rows,all_statuses_reproduced=all(r["reproduction_same_status"] for r in rows),
        historical_gate=old["metadata"]["gate"],history_integrity=verify_history(out)))

def coverage(out,scope="mandatory",limit=None):
    out=initialize(out);cases=mandatory_core() if scope=="mandatory" else all_core() if scope=="core" else full()
    planned=len(cases);cases=cases if limit is None else cases[:limit]
    path=out/f"coverage_{scope}.jsonl"
    # Resume only identical version/source fingerprint. Never truncate prior rows.
    scientific=["reference/route_a.py","reference/route_b.py","reference/types.py","reference/certify.py",
                "reference/derivatives.py","reference/certification_grid.py","reference_v2/domains.py",
                "reference_v2/high_precision.py","reference_v2/workflow.py"]
    hashes={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in scientific}
    fingerprint=hashlib.sha256(json.dumps(hashes,sort_keys=True).encode()).hexdigest()
    existing=[json.loads(z) for z in path.read_text().splitlines()] if path.exists() else []
    if any(r.get("execution_fingerprint")!=fingerprint for r in existing):raise RuntimeError("resume requires unchanged execution sources")
    start=time.time()
    for i,c in enumerate(cases):
        if i<len(existing):continue
        try:r,errors,_=assess(c)
        except Exception as exc:r={**c.row(),"status":"FAIL","failure_flags":["exception"],"exception":repr(exc)}
        r.update(domain=classify(c),grid_index=i,execution_fingerprint=fingerprint)
        with path.open("a",encoding="utf-8") as handle:handle.write(json.dumps(clean(r),allow_nan=False)+"\n")
        existing.append(clean(r))
        print(scope,i+1,planned,r["status"],flush=True)
    dump(out/f"COVERAGE_{scope}.json",dict(planned=planned,evaluated=len(existing),complete=len(existing)==planned,
        rows=existing,elapsed_this_session=time.time()-start,source_sha256=hashes,history_integrity=verify_history(out)))

def span(c):
    p=c.p
    return abs(c.x)+.04+abs(p.r)*c.tau+abs(p.rho)*(c.v+p.kappa*p.theta*c.tau)/max(p.sigma,.1)

def hp_selected(out,scope="local"):
    out=initialize(out);old=json.loads((HISTORY/"CERTIFICATION_RESULTS.json").read_text())["rows"]
    # Local selection fixed by inputs, not achieved new precision results.
    if scope=="local":
        cases=[Case(.0,.04,1,1,REGIMES[0],"HP_CORE_ATM"),
               Case(0,0,.001,1,REGIMES[0],"HP_ZERO_R0"),Case(0,0,.001,1,REGIMES[4],"HP_ZERO_R4")]
    else:cases=[from_row(r) for r in old if r["status"]=="FAIL"]
    rows=[]
    for i,c in enumerate(cases):
        cutoff=512 if classify(c)=="CORE" and c.tau>=.1 else 8192
        row=dict(input=c.row(),domain=classify(c),precision=[],degree=[],cutoff=[])
        for dps in [50,80,120]:
            e=evaluate(c,MPConfig(dps,cutoff,40,span(c)));row["precision"].append(e)
        for degree in [24,40,64]:row["degree"].append(evaluate(c,MPConfig(80,cutoff,degree,span(c))))
        cuts=[256,512,1024] if cutoff==512 else [2048,8192,32768,65536]
        for u in cuts:row["cutoff"].append(evaluate(c,MPConfig(80,u,40,span(c))))
        # Local unresolved boundaries retain finite-cutoff FD as diagnostics.
        row["MP_FD"]=finite_differences(c,MPConfig(80,cutoff,40,span(c)))
        row["A"]=A.price(c,A.Quadrature(cutoff=2048)).row();row["B"]=B.price(c,B.COS(4096,32)).row()
        rows.append(row);dump(out/f"HP_{scope}.json",dict(scope=scope,rows=rows,complete=len(rows)==len(cases),planned=len(cases)))
        print("HP",i+1,len(cases),c.label,flush=True)
    return rows

def boundary(out,scope="local"):
    out=initialize(out);rows=[]
    vs=[0,1e-8,1e-7,1e-6,1e-5,1e-4,1e-3,1e-2]
    ts=[1e-4,2.5e-4,5e-4,1e-3,1/252,.01,.05]
    cases=[Case(x,v,.001,1,REGIMES[j],f"vseq_R{j}") for j in [0,4] for x in ([0] if scope=="local" else [-.01,0,.01]) for v in vs]
    cases += [Case(x,v,t,1,REGIMES[j],f"tseq_R{j}") for j in [0,4] for x in [-.01,0,.01] for v in ([0] if scope=="local" else [0,.01,.04]) for t in ts]
    for i,c in enumerate(cases):
        row={**c.row(),"domain":classify(c),"status":"UNRESOLVED","A":[],"B":[]}
        for u in [2048,8192,32768]:row["A"].append(A.price(c,A.Quadrature(cutoff=u,atol=1e-11,rtol=1e-11)).row())
        for n in [4096,16384,65536]:row["B"].append(B.price(c,B.COS(n,32)).row())
        if scope=="full":row["MP"]=evaluate(c,MPConfig(80,32768,40,span(c)))
        rows.append(row)
        print("boundary",i+1,len(cases),flush=True)
    dump(out/f"BOUNDARY_SEQUENCES_{scope}.json",dict(scope=scope,rows=rows,finite_cutoff_warning=True))

def uncertainty(routes):
    result={}
    for f in ["price","Delta","Gamma","Vv"]:
        available={k:float(v[f]) for k,v in routes.items() if f in v and v[f] is not None and np.isfinite(float(v[f]))}
        names=list(available);vals=np.array(list(available.values()));matrix=abs(vals[:,None]-vals[None,:])
        pairs=matrix[np.triu_indices(len(vals),1)];center=float(np.median(vals)) if len(vals) else np.nan
        result[f]=dict(routes=names,values=vals.tolist(),pairwise_matrix=matrix.tolist(),
            max_disagreement=float(pairs.max()) if len(pairs) else None,
            median_disagreement=float(np.median(pairs)) if len(pairs) else None,
            deviation_from_route_median={k:abs(v-center) for k,v in available.items()},
            interpretation="numerical diagnostic, not a confidence interval")
    return result

def diagnosis(r):
    changes=r.get("convergence_max_changes",{});tol=np.array([r.get(f"tolerance_{f}",np.inf) for f in ["price","Delta","Gamma","Vv"]])
    if np.any(np.array(changes.get("A_domain",[0]*4))>tol/4):return "QUADRATURE_NOT_CONVERGED","measured last-two cutoff changes exceed budget/4"
    if any(np.any(np.array(changes.get(k,[0]*4))>tol/4) for k in ["B_N","B_interval"]):return "COS_NOT_CONVERGED","measured independent COS N/interval changes exceed budget/4"
    failed_quad=[z.get("estimate",{}).get("diagnostics",{}) for z in r.get("convergence",[]) if z.get("route")=="A"]
    if any(not z.get("success",True) for z in failed_quad):
        return "QUADRATURE_NOT_CONVERGED","stored adaptive-quadrature success=False; requested accuracy not achieved (including reported roundoff)"
    return "UNKNOWN","roundoff/FD flags alone do not isolate causality without matched MP stencil evidence"

def aggregate(out):
    def safe_summary(rows):
        # JSON null preserves undefined relative error; convert only in this
        # aggregation view. Never mutate historical or current raw rows.
        return summarize([{k:(np.nan if v is None else v) for k,v in r.items()} for r in rows])
    out=initialize(out);old=json.loads((HISTORY/"CERTIFICATION_RESULTS.json").read_text());repro=out/"REPRODUCTION.json"
    reproductions=json.loads(repro.read_text())["rows"] if repro.exists() else []
    covered=[]
    for path in out.glob("coverage_*.jsonl"):
        covered.extend(json.loads(line) for line in path.read_text().splitlines())
    # Explicitly deduplicate the same planned point across resume/scope runs.
    keys=["x","v","tau","K","kappa","theta","sigma","rho","r"]
    unique={tuple(r[k] for k in keys):r for r in covered};covered=list(unique.values())
    hps=[]
    for path in out.glob("HP_*.json"):hps.extend(json.loads(path.read_text()).get("rows",[]))
    uncertainties=[]
    for h in hps:
        routes={"A":h["A"],"B":h["B"],"MP":h["precision"][-1]["values"]}
        extpath=out/"EXTERNAL_RESULTS.json"
        if extpath.exists():
            external_rows=json.loads(extpath.read_text()).get("rows",[])
            for e in external_rows:
                if all(e.get("input",{}).get(k)==h["input"].get(k) for k in keys):
                    if e.get("analytic"):routes["QuantLib_analytic"]=e["analytic"][-1]["values"]
                    if e.get("PDE"):routes["QuantLib_PDE"]=e["PDE"][-1]["values"]
        uncertainties.append(dict(input=h["input"],domain=h["domain"],status="DIAGNOSTIC_ONLY",**uncertainty(routes)))
    dump(out/"REFERENCE_UNCERTAINTY.json",dict(rows=uncertainties,interpretation="diagnostic only"))
    arrays={k:np.array([u["input"][k] for u in uncertainties],float) for k in keys}
    arrays["label"]=np.array([u["input"]["label"] for u in uncertainties],dtype="U128")
    arrays["domain"]=np.array([u["domain"] for u in uncertainties],dtype="U16")
    for f in ["price","Delta","Gamma","Vv"]:
        width=max((len(u[f]["routes"]) for u in uncertainties),default=0);count=len(uncertainties)
        matrix=np.full((count,width,width),np.nan);values=np.full((count,width),np.nan)
        deviations=np.full((count,width),np.nan);names=np.full((count,width),"",dtype="U32")
        for i,u in enumerate(uncertainties):
            n=len(u[f]["routes"]);matrix[i,:n,:n]=u[f]["pairwise_matrix"];values[i,:n]=u[f]["values"];names[i,:n]=u[f]["routes"]
            deviations[i,:n]=[u[f]["deviation_from_route_median"][k] for k in u[f]["routes"]]
        arrays.update({f+"_pairwise":matrix,f+"_values":values,f+"_routes":names,f+"_deviation":deviations,
            f+"_max":np.array([u[f]["max_disagreement"] for u in uncertainties],float),
            f+"_median":np.array([u[f]["median_disagreement"] for u in uncertainties],float)})
    np.savez_compressed(out/"REFERENCE_UNCERTAINTY.npz",**arrays)
    summary={}
    for domain in ["CORE","COLLAR","CHALLENGE"]:
        planned=sum(classify(c)==domain for c in full());rr=[r for r in covered if r["domain"]==domain]
        historical=[r for r in old["rows"] if classify(from_row(r))==domain]
        summary[domain]=dict(planned=planned,evaluated_grid=len(rr),coverage_complete=len(rr)==planned,
            mandatory_core_planned=300 if domain=="CORE" else None,
            mandatory_core_evaluated=sum(r.get("label","").startswith("R") for r in rr) if domain=="CORE" else None,
            derivative_checks=sum("FD" in r for r in rr),statistics=safe_summary(rr) if rr else None,
            historical_slice_statistics=safe_summary(historical),gate="FAIL",reason="INCOMPLETE coverage and/or retained unresolved failures/external validation")
    metadata=dict(version=VERSION,domains=summary,historical_gate="FAIL",phase1c_authorized=False,
        reproducibility=dict(executed=len(reproductions),same_statuses=sum(r["reproduction_same_status"] for r in reproductions)),
        environment={k:importlib.metadata.version(k) for k in ["numpy","scipy","mpmath","matplotlib","pytest"]},
        history_integrity=verify_history(out))
    dump(out/"CERTIFICATION_RESULTS.json",dict(metadata=metadata,grid_rows=covered,historical_reproductions=reproductions,high_precision=hps))
    save_npz(out/"CERTIFICATION_RESULTS.npz",covered or reproductions)
    with (out/"FAILURE_CLASSIFICATION.csv").open("w",newline="",encoding="utf-8") as handle:
        writer=csv.DictWriter(handle,fieldnames=["source","index","domain","primary_diagnosis","evidence","gamma_status","input","secondary_flags"]);writer.writeheader()
        for source,rr in [("historical",old["rows"]),("v2_grid",covered)]:
            for i,r in enumerate(rr):
                if r["status"]=="PASS":continue
                primary,evidence=diagnosis(r)
                writer.writerow(dict(source=source,index=i,domain=classify(from_row(r)),primary_diagnosis=primary,evidence=evidence,
                    gamma_status="UNRESOLVED",input=json.dumps({k:r[k] for k in keys}),secondary_flags=json.dumps(r.get("failure_flags",[]))))
    dump(out/"validation_summary.json",metadata)
    return metadata

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("action",choices=["initialize","reproduce","coverage","hp","boundary","aggregate"])
    p.add_argument("--output",default="reference_v2");p.add_argument("--scope",default="local");p.add_argument("--limit",type=int)
    a=p.parse_args()
    if a.action=="initialize":initialize(a.output)
    elif a.action=="reproduce":reproduce(a.output)
    elif a.action=="coverage":coverage(a.output,a.scope,a.limit)
    elif a.action=="hp":hp_selected(a.output,a.scope)
    elif a.action=="boundary":boundary(a.output,a.scope)
    else:aggregate(a.output)
