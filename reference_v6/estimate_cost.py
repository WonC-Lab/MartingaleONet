"""Input geometry + historical timing metadata only. No pricing/residuals."""
import json,math,statistics
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'reference_v6'

def nodes(U,degree,phase):
    widthmax=math.pi*degree/(4*max(phase,.01));left=0.;width=1.;panels=0
    while left<U:
        left=min(U,left+min(width,widthmax));width*=2;panels+=1
    return degree*panels

def run():
    rows=[json.loads(z) for z in (OUT/'BOUNDARY_BLINDED_INPUTS.jsonl').read_text().splitlines()]
    rates=[]
    for p in (ROOT/'reference_v4/returned_evidence/reference_v3_colab/boundary_pde_checkpoints').glob('*.json'):
        # Access ONLY performance fields; never use residual/price/Greek outcomes.
        record=json.loads(p.read_text());base=record['base'];seconds=base['elapsed_seconds']
        if seconds>0:rates.append(base['nodes']/seconds)
    if not rates:raise RuntimeError('Missing historical cost metadata')
    rates.sort();lo=rates[len(rates)//10];med=statistics.median(rates);hi=rates[len(rates)*9//10]
    plans=[]
    for r in rows:
        alpha=r['kappa']*r['theta']*r['tau']*math.sqrt(1-r['rho']**2)/r['sigma']
        h=r['tau']/65536
        floor_br=1e-8+abs(r['r'])*math.exp(r['x'])*2e-6+r['kappa']*r['theta']*2e-5+abs(r['r'])*1e-8
        price_planning_goal=floor_br*h/(4*1.5)
        estimated_U=-math.log(price_planning_goal)/alpha
        U=2**max(8,math.ceil(math.log2(estimated_U)));ceiling=2**20;U=min(U,ceiling)
        phase=abs(r['x'])+.04+abs(r['r'])*r['tau']+abs(r['rho'])*r['kappa']*r['theta']*r['tau']/max(r['sigma'],.1)
        ladder=[2**j for j in range(6,int(math.log2(U))+1)]
        nfinal=nodes(U,40,phase)
        naive_grid_nodes=sum(nodes(u,40,phase) for u in ladder)+4*nfinal
        prefix_grid_nodes=nfinal+40*len(ladder)+4*nfinal
        plans.append(dict(case_id=r['case_id'],block_id=r['block_id'],tau=r['tau'],phase_span=phase,
                          planning_alpha=alpha,planning_U=estimated_U,capped_ladder_endpoint=U,
                          planning_exceeds_schedule=estimated_U>ceiling,final_nodes=nfinal,
                          cold_CF_nodes_min=naive_grid_nodes*15,cold_CF_nodes_max=naive_grid_nodes*25,
                          prefix_cached_CF_nodes_min=prefix_grid_nodes*15,prefix_cached_CF_nodes_max=prefix_grid_nodes*25))
    # Same p/base tau for ATM_SHORT and RIGHT_COLLAR_SHORT can share spectra.
    grouped={}
    for p in plans:
        k=(p['block_id'],p['tau'])
        if k not in grouped or p['prefix_cached_CF_nodes_max']>grouped[k]['prefix_cached_CF_nodes_max']:grouped[k]=p
    workmin=sum(p['prefix_cached_CF_nodes_min'] for p in grouped.values())
    workmax=sum(p['prefix_cached_CF_nodes_max'] for p in grouped.values())
    estimate=dict(status='PLANNING_ONLY_NOT_A_BENCHMARK',new_points=128,parameter_blocks=32,
                  time_levels_min=6,time_levels_max=11,time_prices_min=15,time_prices_max=25,
                  apparent_time_price_calls_min=128*15,apparent_time_price_calls_max=128*25,
                  E1_reference_axis_configs_min=7,E1_reference_axis_configs_max=19,
                  E2_reference_axis_configs_min=11,E2_reference_axis_configs_max=27,
                  E1_time_price_outputs_over_axis_configs_min=128*15*7,E1_time_price_outputs_over_axis_configs_max=128*25*19,
                  E2_time_price_outputs_over_axis_configs_min=128*15*11,E2_time_price_outputs_over_axis_configs_max=128*25*27,
                  physical_FD_price_outputs_per_case_max=80,
                  E2='MP COS new port has no measured timing; total may exceed this E1 estimate',
                  historical_metadata_samples=len(rates),historical_MP80_nodes_per_second=dict(p10=lo,median=med,p90=hi),
                  paired_p_tau_CF_families=len(grouped),E1_prefix_cached_CF_nodes_min=workmin,E1_prefix_cached_CF_nodes_max=workmax,
                  E1_CPU_hours_at_median_min=workmin/med/3600,E1_CPU_hours_at_median_max=workmax/med/3600,
                  E1_four_CPU_wall_hours_envelope=[workmin/hi/3600/4,workmax/lo/3600/4],
                  final_node_peak=max(p['final_nodes'] for p in plans),
                  planned_block_peak_nodes=4096,estimated_memory='streamed chunk4096; cap512MiB per worker, four workers plus parent within4GiB; avoid25 full spectral arrays',
                  limited_precision_cost_note='Historical metadata is80dps;120dps, physical-FD, cosine and streaming sums add unknown overhead. Runtime range is not a completion promise.',
                  CUDA='no benefit for scalar mpmath/gmpy2; no A100 dependency',
                  equivalent_implementation=['stream quadrature in4096-node chunks','cache Gauss rules and complete-prefix panel contributions',
                                             'reuse frequency beta/root/ratio at fixed p; evaluate true CF at each time',
                                             'share identical p/base-tau spectra acrossx without reusing prices',
                                             'reuse affine-variance spectra for right FD; keep independent axes and same decision rule',
                                             'cache nested COS-frequency prefixes at fixed L and fixed intervals',
                                             'earliest fixed window plus one confirming level, no threshold or case changes'],
                  never_discount_by_old_residual_success=True,plans=plans)
    (OUT/'COMPUTE_COST_ESTIMATE.json').write_text(json.dumps(estimate,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({k:estimate[k] for k in ['historical_MP80_nodes_per_second','apparent_time_price_calls_min','apparent_time_price_calls_max','E1_four_CPU_wall_hours_envelope','final_node_peak']},indent=2))

if __name__=='__main__':run()
