"""Plots exclusively from raw output, no filled-in failed/missing values."""
import argparse
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def plot(output="reference"):
    root=Path(output);data=json.loads((root/"CERTIFICATION_RESULTS.json").read_text());rows=data["rows"]
    dest=root/"figures";dest.mkdir(exist_ok=True)
    plt.rcParams.update({"font.size":10,"figure.dpi":140,"savefig.dpi":250,"axes.spines.top":False,"axes.spines.right":False})
    fig,axs=plt.subplots(2,2,figsize=(10,7),constrained_layout=True)
    for ax,field in zip(axs.flat,["price","Delta","Gamma","Vv"]):
        rr=[r for r in rows if r.get(f"abs_{field}_gap") is not None]
        z=np.array([r[f"abs_{field}_gap"] for r in rr]);log=np.log10(np.maximum(z,1e-16))
        sc=ax.scatter([r["x"] for r in rr],[r["tau"] for r in rr],c=log,vmin=-16,vmax=2,cmap="viridis",s=45,edgecolors="black",linewidths=.3)
        ax.set(xlabel="log(S/K)",ylabel="maturity (years)",yscale="log",title=f"{field}: log10 absolute A/B gap")
    fig.colorbar(sc,ax=axs.ravel().tolist(),label="log10 gap (display floor 1e-16)")
    fig.suptitle(f"{data['metadata']['scope']} diagnostic slice; mixed regimes, failed rows retained")
    fig.savefig(dest/"disagreement_scatter.png");fig.savefig(dest/"disagreement_scatter.pdf");plt.close(fig)
    # Contours only if a full rectangular constant-parameter slice exists.
    subset=[r for r in rows if r["label"]=="offATM"]
    if not subset:subset=[r for r in rows if r["label"]=="R0" and r["v"]==.04]
    if subset:
        xs=sorted(set(r["x"] for r in subset));ts=sorted(set(r["tau"] for r in subset))
        fig,axs=plt.subplots(2,2,figsize=(10,7),constrained_layout=True)
        for ax,f in zip(axs.flat,["price","Delta","Gamma","Vv"]):
            z=np.full((len(ts),len(xs)),np.nan)
            for r in subset:
                if r.get(f"abs_{f}_gap") is not None:z[ts.index(r["tau"]),xs.index(r["x"])]=r[f"abs_{f}_gap"]
            # Logarithmic cell edges keep the short-maturity row visible.
            xmid=(np.array(xs[:-1])+np.array(xs[1:]))/2
            xedges=np.r_[2*xs[0]-xmid[0],xmid,2*xs[-1]-xmid[-1]]
            tmid=np.sqrt(np.array(ts[:-1])*np.array(ts[1:]))
            tedges=np.r_[ts[0]**2/tmid[0],tmid,ts[-1]**2/tmid[-1]]
            im=ax.pcolormesh(xedges,tedges,np.log10(np.maximum(z,1e-16)),shading="flat",vmin=-16,vmax=-6,cmap="viridis")
            ax.set(xlabel="log(S/K)",ylabel="maturity (years)",yscale="log",title=f"{f}: typical-regime gap")
        fig.colorbar(im,ax=axs.ravel().tolist(),label="log10 gap; raw sampled cells")
        fig.savefig(dest/"typical_uncertainty_heatmap.png");fig.savefig(dest/"typical_uncertainty_heatmap.pdf");plt.close(fig)
    for label in ["offATM","local_R4"]:
        r=next((r for r in rows if r["label"]==label and "FD" in r),None)
        if r is None:continue
        fig,axs=plt.subplots(1,3,figsize=(13,3.5),constrained_layout=True)
        cos=[z["estimate"] for z in r["convergence"] if z["route"]=="B" and "estimate" in z and z["estimate"]["diagnostics"]["config"]["L"]==32]
        a=[z["estimate"] for z in r["convergence"] if z["route"]=="A" and "estimate" in z][:6]
        finalA=r.get("route_A_price",np.nan);finalB=r.get("route_B_price",np.nan)
        axs[0].loglog([e["diagnostics"]["config"]["N"] for e in cos],[max(abs(e["price"]-finalB),1e-16) for e in cos],"o-")
        axs[0].set(xlabel="COS N (L=32)",ylabel="price change from N=4096")
        axs[1].loglog([e["diagnostics"]["config"]["cutoff"] for e in a],[max(abs(e["price"]-finalA),1e-16) for e in a],"o-")
        axs[1].set(xlabel="A cutoff",ylabel="price change from final A")
        for f in ["Delta","Gamma","Vv"]:
            axs[2].loglog([z["relative_step"] for z in r["FD"]],[max(abs(z[f]-r[f"route_B_{f}"]),1e-16) for z in r["FD"]],"o-",label=f)
        axs[2].set(xlabel="relative FD step",ylabel="absolute error vs analytic B");axs[2].legend()
        fig.suptitle(f"{label}: x={r['x']:.3g}, v={r['v']}, tau={r['tau']} — {r['status']}")
        fig.savefig(dest/f"convergence_{label}.png");fig.savefig(dest/f"convergence_{label}.pdf");plt.close(fig)

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--output",default="reference");plot(p.parse_args().output)
