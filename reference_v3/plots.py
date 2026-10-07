"""Raw scatter/dense-grid and independent external refinement figures."""
import argparse,json
from pathlib import Path
import numpy as np
import mpmath
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reference_v2.workflow import ROOT
from reference_v2.external import cases
from .coverage import key

def run(output='reference_v3'):
    root=Path(output);folder=root/'figures';folder.mkdir(exist_ok=True)
    rows=[json.loads(z) for z in (root/'coverage_core.jsonl').read_text().splitlines()]
    def save(fig,name):
        fig.savefig(folder/(name+'.png'),dpi=170,bbox_inches='tight');fig.savefig(folder/(name+'.pdf'),bbox_inches='tight');plt.close(fig)
    dense=ROOT/'reference_v2/DENSE_VISUAL_GRID.json'
    if dense.exists():
        rr=json.loads(dense.read_text())['rows'];xs=sorted({r['x'] for r in rr});ts=sorted({r['tau'] for r in rr})
        if len(rr)==len(xs)*len(ts) and min(len(xs),len(ts))>=21:
            for field in ['price','Delta','Gamma','Vv']:
                z=np.full((len(ts),len(xs)),np.nan)
                for r in rr:z[ts.index(r['tau']),xs.index(r['x'])]=r['abs_'+field+'_gap']
                fig,ax=plt.subplots(figsize=(8,5));im=ax.contourf(xs,ts,np.log10(np.maximum(z,1e-16)),levels=np.linspace(-16,-6,21));ax.set(yscale='log',xlabel='x',ylabel='tau',title=field+': inherited actual 31x31 diagnostic slice');fig.colorbar(im,ax=ax,label='log10 gap; floor 1e-16');save(fig,'CORE_'+field+'_dense_diagnostic')
    for field in ['price','Delta','Gamma','Vv']:
        fig,ax=plt.subplots(figsize=(8,5));color=np.log10(np.maximum([r['abs_'+field+'_gap'] for r in rows],1e-16))
        p=ax.scatter([r['x'] for r in rows],[r['tau'] for r in rows],c=color,s=12,cmap='viridis',vmin=-16)
        ax.set(yscale='log',xlabel='log(S/K)',ylabel='maturity',title=f'{field}: actual completed CORE 1734 points')
        fig.colorbar(p,ax=ax,label='log10 absolute A/B gap; display floor 1e-16');save(fig,'CORE_'+field+'_completed_coverage')
    fig,axes=plt.subplots(2,3,figsize=(14,8));types=['solver_error','A_domain','B_N','FD_uncertainty_budget_unresolved','FD_derivative_amplification_or_truncation','strike_FD_derivative_unresolved']
    for ax,flag in zip(axes.flat,types):
        found=[r for r in rows if flag in r['failure_flags']];ax.scatter([r['x'] for r in rows],[r['tau'] for r in rows],s=3,color='lightgray');ax.scatter([r['x'] for r in found],[r['tau'] for r in found],s=9,color='red');ax.set(yscale='log',title=flag+' ('+str(len(found))+')',xlabel='x',ylabel='tau')
    fig.tight_layout();save(fig,'failure_type_map_raw_points')
    external=root/'EXTERNAL_RESULTS.json'
    if external.exists():
        ext=json.loads(external.read_text())['rows'];available=[e for e in ext if e['analytic'] and e['PDE']]
        fig,ax=plt.subplots(figsize=(10,5));names=[]
        for i,e in enumerate(available):
            names.append(e['input']['label']);reference=e['analytic'][-1]['values']['price']
            for route,marker,color,value in [('A','o','blue',e['A']['price']),('B','x','orange',e['B']['price']),('PDE','^','green',e['PDE'][-1]['values']['price'])]:ax.scatter(i,value-reference,marker=marker,color=color,label=route if i==0 else None)
        ax.legend()
        ax.set(xticks=range(len(names)),xticklabels=names,yscale='symlog',title='A/B/PDE signed price gaps versus QuantLib analytic',ylabel='price difference');ax.tick_params(axis='x',rotation=25);save(fig,'QuantLib_cross_engine_price')
        for e in available:
            fig,axes=plt.subplots(1,3,figsize=(14,4))
            for j,(field,ax) in enumerate(zip(['price','Delta','Gamma'],axes)):
                seq=e['PDE'];ax.plot(range(len(seq)),[z['values'][field] for z in seq],'o-');ax.set(title=field,xlabel='recorded refinement index');ax.set_xticks(range(len(seq)),[str(tuple(z['grids'])) for z in seq],rotation=90,fontsize=6)
            fig.suptitle(e['input']['label']+' — separate-axis then combined PDE refinements');fig.tight_layout();save(fig,'PDE_refinement_'+e['input']['label'])
    # Every completed MP input retains its actual convergence and stencil curves.
    # Reuse plotting routines only; their output path is the new version folder.
    representative={key(c.row()) for c in cases()}
    for p in (root/'mp_cases').rglob('*.json'):
        h=json.loads(p.read_text())
        if h.get('B_refinement'):
            fig,ax=plt.subplots(figsize=(8,5));seq=h['B_refinement']
            for L in sorted({z['diagnostics']['config']['L'] for z in seq}):
                group=[z for z in seq if z['diagnostics']['config']['L']==L];ax.plot([z['diagnostics']['config']['N'] for z in group],[z['Gamma'] for z in group],'o-',label='L='+str(L))
            ax.set(xscale='log',xlabel='COS N',ylabel='Gamma',title=h['input']['label']+' — independent N/interval sweeps');ax.legend();save(fig,'COS_N_interval_'+p.stem)
        if h.get('precision') and h.get('MP_FD') and key(h['input']) in representative:
            label=p.stem
            fig,axes=plt.subplots(1,3,figsize=(14,4));reference=float(h['precision'][-1]['values']['Gamma'])
            ctx=mpmath.mp.clone();ctx.dps=140;mp_reference=ctx.mpf(h['precision'][-1]['values']['Gamma'])
            axes[0].semilogy([z['config']['dps'] for z in h['precision']],[max(float(abs(ctx.mpf(z['values']['Gamma'])-mp_reference)),1e-130) for z in h['precision']],'o-');axes[0].set(xlabel='digits',title='Gamma precision differences; display floor 1e-130')
            axes[1].plot([z['config']['cutoff'] for z in h['cutoff']],[float(z['values']['Gamma']) for z in h['cutoff']],'o-');axes[1].set(xlabel='cutoff',xscale='log',title='Gamma cutoff convergence')
            fd=h['MP_FD'];steps=[float(z['relative_step']) for z in fd['rows']]
            for scheme in ['Gamma3','Gamma5','Gamma_Richardson3','Gamma_Richardson5']:
                axes[2].plot(steps,[float(z['values'].get(scheme,np.nan)) for z in fd['rows']],'o-',label=scheme)
            axes[2].axhline(float(fd['base']['Gamma']),color='black',linestyle=':');axes[2].set(xscale='log',xlabel='physical spot h/S',title='Gamma stencils');axes[2].legend();fig.suptitle(h['input']['label']+f" x={h['input']['x']:.3g}, v={h['input']['v']:.3g}, tau={h['input']['tau']:.3g}");fig.tight_layout();save(fig,'MP_Gamma_'+label)
    print('Plots saved under',folder,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',default='reference_v3');run(p.parse_args().output)
