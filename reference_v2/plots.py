"""Publication-quality plots of actual raw numerical diagnostics only."""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def save(fig,dest,name):
    fig.savefig(dest/(name+".png"),dpi=250,bbox_inches="tight")
    fig.savefig(dest/(name+".pdf"),bbox_inches="tight");plt.close(fig)

def run(output="reference_v2"):
    root=Path(output);dest=root/"figures";dest.mkdir(exist_ok=True)
    plt.rcParams.update({"font.size":10,"axes.spines.top":False,"axes.spines.right":False})
    path=root/"DENSE_VISUAL_GRID.json"
    if path.exists():
        data=json.loads(path.read_text());rr=data["rows"];xs=sorted(set(r["x"] for r in rr));ts=sorted(set(r["tau"] for r in rr))
        if len(rr)==len(xs)*len(ts) and len(xs)>=21 and len(ts)>=21:
            for f in ["price","Delta","Gamma","Vv"]:
                z=np.full((len(ts),len(xs)),np.nan)
                for r in rr:z[ts.index(r["tau"]),xs.index(r["x"])]=r[f"abs_{f}_gap"]
                fig,ax=plt.subplots(figsize=(6.2,4.4),constrained_layout=True)
                im=ax.contourf(xs,ts,np.log10(np.maximum(z,1e-16)),levels=np.linspace(-16,-6,21),extend="max",cmap="viridis")
                ax.set(xlabel="log(S/K)",ylabel="maturity (years)",yscale="log",title=f"{f} A/B gap: actual {len(xs)} x {len(ts)} core slice")
                fig.colorbar(im,ax=ax,label="log10 absolute gap; display floor 1e-16")
                fig.text(.5,-.01,"Fixed R0, v=0.04. Diagnostic values; no convergence certificate.",ha="center",fontsize=8)
                save(fig,dest,f"core_{f}_disagreement")
    rows=[]
    for p in root.glob("coverage_*.jsonl"):rows += [json.loads(s) for s in p.read_text().splitlines()]
    rr=[r for r in rows if r.get("label","").startswith("R")]
    if rr:
        xs=sorted(set(r["x"] for r in rr));ts=sorted(set(r["tau"] for r in rr))
        failed=np.zeros((len(ts),len(xs)));total=np.zeros_like(failed)
        for r in rr:
            j=ts.index(r["tau"]);i=xs.index(r["x"]);total[j,i]+=1;failed[j,i]+=r["status"]!="PASS"
        z=np.divide(failed,total,out=np.full_like(failed,np.nan),where=total>0)
        fig,ax=plt.subplots(figsize=(7,4),constrained_layout=True)
        im=ax.imshow(z,origin="lower",aspect="auto",vmin=0,vmax=1,cmap="magma",
            extent=[-.5,len(xs)-.5,-.5,len(ts)-.5])
        ax.set_xticks(range(len(xs)),[f"{x:g}" for x in xs]);ax.set_yticks(range(len(ts)),[f"{t:.4g}" for t in ts])
        ax.set(xlabel="log(S/K)",ylabel="maturity (years)",title="Strict row failure fraction across regimes and variances")
        fig.colorbar(im,ax=ax,label="failed/evaluated at each sampled cell")
        save(fig,dest,"failure_locations")
    hps=[]
    for p in root.glob("HP_*.json"):hps += json.loads(p.read_text()).get("rows",[])
    floats=json.loads((root/"FLOAT_GAMMA_local.json").read_text())["rows"] if (root/"FLOAT_GAMMA_local.json").exists() else []
    for i,h in enumerate(hps):
        label=h["input"]["label"];fig,axs=plt.subplots(1,2,figsize=(10,3.7),constrained_layout=True)
        for f in ["price","Gamma"]:
            ref=float(h["precision"][-1]["values"][f]);values=[float(e["values"][f]) for e in h["precision"]]
            # Precision differences use decimal subtraction before plot conversion.
            import mpmath
            ctx=mpmath.mp.clone();ctx.dps=140
            refmp=ctx.mpf(h["precision"][-1]["values"][f])
            errors=[float(abs(ctx.mpf(e["values"][f])-refmp)) for e in h["precision"]]
            axs[0].semilogy([e["config"]["dps"] for e in h["precision"]],np.maximum(errors,1e-125),"o-",label=f)
            axs[1].plot([e["config"]["cutoff"] for e in h["cutoff"]],[float(e["values"][f]) for e in h["cutoff"]],"o-",label=f)
        axs[0].set(xlabel="decimal digits",ylabel="gap vs 120 digits at identical cutoff");axs[0].legend()
        axs[1].set(xlabel="quadrature cutoff",xscale="log",yscale="symlog",ylabel="raw finite-cutoff estimate");axs[1].legend()
        fig.suptitle(f"{label}: digit agreement does not certify the integration tail")
        save(fig,dest,f"high_precision_{label}")
        fd=h["MP_FD"];steps=[float(r["relative_step"]) for r in fd["rows"]]
        fig,axs=plt.subplots(1,2,figsize=(12,4),constrained_layout=True)
        for f in ["Gamma3","Gamma5","Gamma_Richardson3","Gamma_Richardson5"]:
            ys=[float(r["values"].get(f,"nan")) for r in fd["rows"]]
            axs[0].semilogx(steps,ys,".-",label="MP "+f)
        aU=h["A"].get("diagnostics",{}).get("config",{}).get("cutoff",2048)
        bN=h["B"].get("diagnostics",{}).get("config",{}).get("N",4096)
        axs[0].axhline(h["A"]["Gamma"],linestyle="--",color="grey",label=f"analytic A (U={aU})")
        axs[0].axhline(h["B"]["Gamma"],linestyle=":",color="black",label=f"COS B (N={bN},L=32)")
        axs[1].loglog(steps,[max(float(r["values"]["Gamma5_analytic_gap"]),1e-80) for r in fd["rows"]],"o-",label="MP FD vs same-grid MP analytic")
        match=next((r for r in floats if r["input"]["label"]==label),None)
        if match:
            qs=[float(r["relative_step"]) for r in match["rows"]]
            axs[0].semilogx(qs,[r["Gamma5"] for r in match["rows"]],"x-",label="float64 FD5")
            axs[1].loglog(qs,[max(r["Gamma5_analytic_gap"],1e-16) for r in match["rows"]],"x-",label="float FD vs analytic B")
        axs[0].set(xlabel="physical spot h/S",ylabel="Gamma estimate");axs[0].legend(fontsize=7)
        axs[1].set(xlabel="physical spot h/S",ylabel="within-method discrepancy (not true error)");axs[1].legend(fontsize=7)
        fig.suptitle(f"{label}; MP U={fd['config']['cutoff']}, dps={fd['config']['dps']}")
        save(fig,dest,f"gamma_steps_{label}")
    rep=root/"REPRODUCTION.json"
    if rep.exists():
        rr=json.loads(rep.read_text())["rows"]
        r=next((r for r in rr if r["label"]=="local_R4" and r["v"]==0),None)
        if r:
            e=[z["estimate"] for z in r["convergence"] if z["route"]=="B" and "estimate" in z and z["estimate"]["diagnostics"]["config"]["L"]==32]
            fig,ax=plt.subplots(figsize=(6,4),constrained_layout=True)
            ax.semilogx([z["diagnostics"]["config"]["N"] for z in e],[z["Gamma"] for z in e],"o-")
            ax.set(xlabel="COS N, fixed L=32",ylabel="raw Gamma",title="Severe previously failed case: term convergence")
            save(fig,dest,"COS_N_convergence")
    boundary=root/"BOUNDARY_SEQUENCES_local.json"
    if boundary.exists():
        rr=json.loads(boundary.read_text())["rows"]
        for j in [0,4]:
            vs=[r for r in rr if r["label"]==f"vseq_R{j}"];ts=[r for r in rr if r["label"]==f"tseq_R{j}" and r["x"]==0]
            for kind,seq,coordinate in [("variance",vs,"v"),("maturity",ts,"tau")]:
                fig,axs=plt.subplots(1,3,figsize=(12,3.5),constrained_layout=True)
                for ax,f in zip(axs,["price","Gamma","Vv"]):
                    for route in ["A","B"]:
                        ax.plot([r[coordinate] for r in seq],[r[route][-1][f] for r in seq],"o-",label=route)
                    ax.set(xlabel=coordinate,ylabel=f,xscale="symlog" if kind=="variance" else "log",yscale="symlog")
                    if kind=="variance":ax.set_xscale("symlog",linthresh=1e-8)
                    ax.legend()
                fig.suptitle(f"R{j}: {kind} sequence — finite cutoffs, unresolved rows retained")
                save(fig,dest,f"{kind}_continuity_R{j}")

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser();p.add_argument("--output",default="reference_v2");run(p.parse_args().output)
