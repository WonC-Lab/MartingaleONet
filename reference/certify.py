"""Reproducible reference-only validation CLI. Full coverage is user-run."""
import argparse
from dataclasses import replace
import hashlib
import importlib.metadata
import importlib.util
import json
from pathlib import Path
import platform
import time
import traceback
import numpy as np
from . import route_a as A, route_b as B, certification_grid as grid, ode_check
from .derivatives import studies, strike_check
from .types import Case

FIELDS=("price","Delta","Gamma","Vv")

def normalized(e,c): return np.array([e.price/c.K,e.Delta,e.Gamma*c.K,e.Vv/c.K])
def budgets(a,b):
    scale=np.maximum(abs(a),abs(b))
    return np.array([1e-8,2e-6,2e-5,2e-5])+np.array([1e-6,1e-5,1e-4,1e-4])*scale

def clean(x):
    # NaN is represented by JSON null; numeric NPZ retains IEEE NaNs.
    if isinstance(x,dict): return {k:clean(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)): return [clean(v) for v in x]
    if isinstance(x,np.ndarray): return clean(x.tolist())
    if isinstance(x,(float,np.floating)): return float(x) if np.isfinite(x) else None
    if isinstance(x,np.integer): return int(x)
    if isinstance(x,np.bool_): return bool(x)
    return x

def dump(path,value):
    path.write_text(json.dumps(clean(value),indent=2,ensure_ascii=False,allow_nan=False),encoding="utf-8")

def save_npz(path,rows):
    numeric=sorted({k for r in rows for k,v in r.items() if isinstance(v,(int,float,np.number)) and not isinstance(v,bool)})
    arrays={k:np.array([r.get(k,np.nan) for r in rows],float) for k in numeric}
    arrays["label"]=np.array([r["label"] for r in rows]); arrays["status"]=np.array([r["status"] for r in rows])
    for key in ["feller_satisfied","failure_flags",* [f"{s}_status" for s in FIELDS]]:
        if any(key in r for r in rows):
            arrays[key]=np.array([json.dumps(r.get(key),ensure_ascii=False) for r in rows])
    np.savez_compressed(path,**arrays)

def assess(case):
    raw=[]; errors=[]
    def call(route,cfg):
        try:
            e=(A.price if route=="A" else B.price)(case,cfg)
            if not np.all(np.isfinite(normalized(e,case))): raise ArithmeticError("nonfinite estimate")
            raw.append(dict(route=route,estimate=e.row()))
            if route=="A" and not e.diagnostics.get("success",True):
                errors.append(dict(route=route,failure="quadrature",diagnostics=e.diagnostics))
            return e
        except Exception as exc:
            errors.append(dict(route=route,failure="unknown",exception=repr(exc),traceback=traceback.format_exc()))
            raw.append(dict(route=route,config=cfg.__dict__,exception=repr(exc)))
            return None
    aa=[call("A",A.Quadrature(cutoff=u,atol=1e-11,rtol=1e-11)) for u in [64,128,256,512,1024,2048]]
    at=[call("A",A.Quadrature(cutoff=2048,atol=t,rtol=t)) for t in [1e-9,1e-11,1e-13]]
    am=[call("A",A.Quadrature(cutoff=2048,atol=1e-13,rtol=1e-13,panels=n)) for n in [4,8,16]]
    bb={L:[call("B",B.COS(N,L)) for N in [64,128,256,512,1024,2048,4096]] for L in [8,12,16,24,32]}
    a=am[-1]; b=bb[32][-1]; row=case.row()
    row.update(feller_ratio=2*case.p.kappa*case.p.theta/case.p.sigma**2,
               feller_satisfied=bool(2*case.p.kappa*case.p.theta>=case.p.sigma**2))
    if a is None or b is None:
        row.update(status="FAIL",failure_flags=["exception"],convergence=raw)
        return row,errors,raw
    na=normalized(a,case); nb=normalized(b,case); tol=budgets(na,nb); gap=abs(na-nb)
    maxchanges={}
    def differences(seq):
        if any(e is None for e in seq): return np.full(4,np.inf)
        ns=np.array([normalized(e,case) for e in seq])
        return np.max(abs(np.diff(ns[-3:],axis=0)),axis=0)
    maxchanges["A_domain"]=differences(aa)
    maxchanges["A_tolerance"]=differences(at)
    maxchanges["A_panels"]=differences(am)
    maxchanges["B_N"]=np.max([differences(bb[L]) for L in bb],axis=0)
    maxchanges["B_interval"]=differences([bb[L][-1] for L in bb])
    flags=[]
    for name,values in maxchanges.items():
        if np.any(values>tol/4): flags.append(name)
    if np.any(gap>tol): flags.append("cross_route_unknown")
    if errors: flags.append("solver_error")
    for route,e,n in [("A",a,na),("B",b,nb)]:
        disc=np.exp(-case.p.r*case.tau); m=np.exp(case.x)
        vk=n[0]-m*n[1]; kvkk=m*m*n[2]
        sane=[max(m-disc,0)-tol[0]<=n[0]<=m+tol[0],
              -tol[1]<=n[1]<=1+tol[1],n[2]>=-tol[2],
              -disc-(tol[0]+m*tol[1])<=vk<=tol[0]+m*tol[1],kvkk>=-m*m*tol[2]]
        row[f"{route}_sanity"]=sane
        if not all(sane): flags.append(f"{route}_financial_sanity")
        row[f"{route}_V_K"]=vk; row[f"{route}_V_KK"]=kvkk/case.K
    fd=studies(case,b); row["FD"]=fd
    fn=np.array([[r["Delta"],case.K*r["Gamma"],r["Vv"]/case.K] for r in fd])
    fdplateau=np.max(abs(np.diff(fn[-3:],axis=0)),axis=0)
    fderror=abs(fn[-1]-nb[1:])
    # Deliberately diagnostic envelope, not a rigorous error bound.
    price_envelope=gap[0]*case.K+a.diagnostics.get("quadrature_error_vector_norm",0)*case.K/np.pi
    ampl=price_envelope*np.array([fd[-1][f"amplification_{s}"] for s in ["Delta","Gamma","Vv"]])*np.array([1,case.K,1/case.K])
    if np.any(fdplateau>tol[1:]/4) or np.any(fderror>tol[1:]/4): flags.append("FD_derivative_amplification_or_truncation")
    if np.any(ampl>tol[1:]/4): flags.append("FD_uncertainty_budget_unresolved")
    row["FD_plateau"]=fdplateau.tolist();row["FD_analytic_gap"]=fderror.tolist();row["FD_propagated_diagnostic"]=ampl.tolist()
    hom=[]
    for K in [50,100,200]:
        z=replace(case,K=K)
        # Actual calls exercise both physical-unit interfaces.
        ea=A.price(z,A.Quadrature(cutoff=2048,atol=1e-13,rtol=1e-13,panels=16))
        eb=B.price(z,B.COS(4096,32))
        hom.append(max(abs(ea.price/K-a.price/case.K),abs(eb.price/K-b.price/case.K)))
    row["homogeneity_max_abs_normalized"]=max(hom)
    row["homogeneity_max_relative"]=max(hom)/max(abs(na[0]),abs(nb[0])) if max(abs(na[0]),abs(nb[0]))>0 else np.nan
    if max(hom)>tol[0]/4: flags.append("homogeneity")
    row["strike_FD"]=strike_check(case,b)
    sk=row["strike_FD"];m=np.exp(case.x)
    row["strike_FD_identity_gaps"]=[abs(sk["V_K"]-row["B_V_K"]),abs(sk["V_KK"]-row["B_V_KK"])]
    if row["strike_FD_identity_gaps"][0]>tol[0]+m*tol[1] or row["strike_FD_identity_gaps"][1]>m*m*tol[2]/case.K:
        flags.append("strike_FD_derivative_unresolved")
    for i,s in enumerate(FIELDS):
        row[f"route_A_{s}"]=float(getattr(a,s));row[f"route_B_{s}"]=float(getattr(b,s))
        physical_gap=abs(getattr(a,s)-getattr(b,s)); magnitude=max(abs(getattr(a,s)),abs(getattr(b,s)))
        row[f"abs_{s}_gap"]=physical_gap
        row[f"relative_{s}_gap"]=physical_gap/magnitude if magnitude>0 and (s!="price" or magnitude/case.K>=1e-5) else np.nan
        row[f"u_ref_{s}"]=physical_gap; row[f"normalized_{s}_gap"]=float(gap[i]);row[f"tolerance_{s}"]=float(tol[i])
        row[f"{s}_agreement_refinement_status"]="PASS" if gap[i]<=tol[i] and all(vals[i]<=tol[i]/4 for vals in maxchanges.values()) else "FAIL"
        row[f"{s}_status"]="PASS" if row[f"{s}_agreement_refinement_status"]=="PASS" and not errors and not any("financial_sanity" in f for f in flags) and (i==0 or not any("FD_" in f for f in flags)) else "FAIL"
    row["route_A_Vega_s"]=a.Vega_s;row["route_B_Vega_s"]=b.Vega_s
    row["convergence_max_changes"]={k:v.tolist() for k,v in maxchanges.items()}
    row["failure_flags"]=flags; row["status"]="FAIL" if flags else "PASS"
    row["convergence"]=raw
    return row,errors,raw

def cf_checks():
    rows=[]
    cases=grid.local()
    for i in range(32):
        c=cases[i%len(cases)];u=[.1,1.,5.,20.][i%4]
        if i%3==0:u-=1j
        expected=ode_check.cf(u,c.v,c.tau,c.p)
        av=A.cf(u,c.v,c.tau,c.p);bv=B.cf(u,c.v,c.tau,c.p)
        # Normalization/moment and symmetry independently checked via ODE too.
        moment=ode_check.cf(-1j,c.v,c.tau,c.p)
        freqs=np.linspace(0,100,1001)
        valsA=A.cf(freqs,c.v,c.tau,c.p);valsB=B.cf(freqs,c.v,c.tau,c.p)
        perturb=replace(c.p,rho=c.p.rho+1e-7)
        rows.append(dict(case=c.row(),u=[u.real,u.imag],A_ODE_gap=float(abs(av-expected)),
            B_ODE_gap=float(abs(bv-expected)),zero_A=float(abs(A.cf(0,c.v,c.tau,c.p)-1)),
            zero_B=float(abs(B.cf(0,c.v,c.tau,c.p)-1)),moment_ODE_gap=float(abs(moment-np.exp(c.p.r*c.tau))),
            moment_A=float(abs(A.cf(-1j,c.v,c.tau,c.p)-np.exp(c.p.r*c.tau))),
            moment_B=float(abs(B.cf(-1j,c.v,c.tau,c.p)-np.exp(c.p.r*c.tau))),
            conjugacy_A=float(np.max(abs(A.cf(-freqs,c.v,c.tau,c.p)-np.conj(valsA)))),
            conjugacy_B=float(np.max(abs(B.cf(-freqs,c.v,c.tau,c.p)-np.conj(valsB)))),
            dense_CF_cross_gap=float(np.max(abs(valsA-valsB))),
            parameter_continuity_A=float(abs(A.cf(u,c.v,c.tau,perturb)-av)),
            parameter_continuity_B=float(abs(B.cf(u,c.v,c.tau,perturb)-bv))))
    return rows

def summarize(rows):
    out={"rows":len(rows),"PASS_rows":sum(r["status"]=="PASS" for r in rows),"FAIL_rows":sum(r["status"]=="FAIL" for r in rows)}
    for field in FIELDS:
        for kind in ["abs","relative"]:
            key=f"{kind}_{field}_gap";vals=np.array([r.get(key,np.nan) for r in rows]);valid=np.isfinite(vals)
            if valid.any():
                ix=int(np.nanargmax(vals));v=vals[valid]
                out[key]=dict(valid=int(valid.sum()),missing=int((~valid).sum()),mean=float(v.mean()),
                    median=float(np.median(v)),p95=float(np.quantile(v,.95)),p99=float(np.quantile(v,.99)),
                    max=float(v.max()),worst_input={k:rows[ix][k] for k in Case().row()})
    return out

def run(scope="local",output="reference",limit=None):
    out=Path(output);out.mkdir(parents=True,exist_ok=True)
    cases=grid.full() if scope=="full" else grid.local()
    if limit is not None:cases=cases[:limit]
    start=time.time();rows=[];failures=[]
    checkpoint=out/"partial_checkpoint.jsonl"
    checkpoint.write_text("",encoding="utf-8")
    for i,c in enumerate(cases):
        try:r,errors,_=assess(c)
        except Exception as exc:
            r={**c.row(),"status":"FAIL","failure_flags":["exception"],"exception":repr(exc)}
            errors=[dict(failure="unknown",exception=repr(exc),traceback=traceback.format_exc())]
        rows.append(r)
        if r["status"]!="PASS" or errors:failures.append(dict(index=i,input=c.row(),flags=r["failure_flags"],errors=errors))
        print(f"{i+1}/{len(cases)} {c.label}: {r['status']} {r['failure_flags']}",flush=True)
        # Recovery checkpoint retains partial work and never claims completion.
        with checkpoint.open("a",encoding="utf-8") as handle:
            handle.write(json.dumps(clean(r),ensure_ascii=False,allow_nan=False)+"\n")
    checks=cf_checks();summary=summarize(rows)
    summary.update(scope=scope,grid_version=grid.VERSION,full_grid_size=len(grid.full()),elapsed_seconds=time.time()-start,
        gate="FAIL",phase1c_authorized=False,gate_reason="Unresolved numerical failures and/or missing full/external reviewed certification coverage",
        external={"available":bool(importlib.util.find_spec("QuantLib")),"executed":False},
        CF_checks=32,CF_max_A_ODE=max(r["A_ODE_gap"] for r in checks),CF_max_B_ODE=max(r["B_ODE_gap"] for r in checks),
        environment={"python":platform.python_version(),**{k:importlib.metadata.version(k) for k in ["numpy","scipy","matplotlib","pytest"]}},
        source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in Path(__file__).parent.glob("*.py")})
    dump(out/"CERTIFICATION_RESULTS.json",dict(metadata=summary,rows=rows));save_npz(out/"CERTIFICATION_RESULTS.npz",rows)
    dump(out/"CF_CHECKS.json",checks);dump(out/"failures.json",failures)
    uncertainty=[{k:v for k,v in r.items() if k in c.row() or k.startswith("u_ref_") or k=="status"} for r in rows]
    dump(out/"REFERENCE_UNCERTAINTY.json",dict(interpretation="cross-route diagnostic, not a rigorous bound",rows=uncertainty))
    save_npz(out/"REFERENCE_UNCERTAINTY.npz",uncertainty)
    dump(out/"validation_summary.json",summary)
    return summary

if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--scope",choices=["local","full"],default="local")
    parser.add_argument("--output",default="reference");parser.add_argument("--limit",type=int)
    args=parser.parse_args();run(args.scope,args.output,args.limit)
