"""Build evidence inventory and Phase 0 reports from existing/local artifacts."""
import csv, hashlib, json, subprocess, ast
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'audit'
D=json.loads((OUT/'local_diagnostics.json').read_text())
fields=['artifact_id','artifact_name','artifact_type','source_script','source_function','input_data','checkpoint','config','seed','device','batch_size','reported_value','recomputed_value','output_file','status','root_cause','notes']
rows=[]
def add(name,kind,script='',function='',inputs='',config='',seed='',batch='',value='',recomputed='',status='NEEDS_COLAB_HEAVY_RUN',cause='',notes=''):
    rows.append(dict(zip(fields,[f'A{len(rows)+1:04d}',name,kind,script,function,inputs,'ABSENT' if script and kind not in ['source','configuration','dataset','synthetic_figure'] else '',config,seed,'CPU inferred from source; historical hardware/runtime unknown' if script else '',batch,value,recomputed,name,status,cause,notes])))
scripts={'fig1_deeponet_pricing_error.png':('run_paper1_experiments.py','run_experiment_1_deeponet_pricing_and_speed','500 generated labels; not persisted','500/200steps; K100;r.03;lr.003;PDE.01'),
'fig2_autograd_greeks_surface.png':('run_paper1_experiments.py','run_experiment_2_autograd_greeks','exp1 model; first branch sample; 50x50 S/T grid','S70:130,T.1:2,K100'),
'fig3_timegan_synthetic_paths.png':('run_paper1_experiments.py','run_experiment_3_timegan_risk_neutral_paths','untrained GRU; fresh Gaussian noise','S0=100;r=.03;dt=1/252;252 steps;200 paths'),
'fig4_us_volatility_surface.png':('run_paper1_experiments.py','run_experiment_4_us_volatility_surface_calibration','synthetic CSV last VIX','IV=VIX[-1]/100+.15(1-K/S)^2+.05exp(-T)'),
'fig5_deep_hedging_transaction_costs.png':('hedging_engine.py','run_experiment_hedging_transaction_costs','independent trained model; generated Heston paths; hedging_results.json','5000 labels;150steps;200paths;30days;TC0/10/20bps'),
'fig6_multi_asset_basket_correlation.png':('multi_asset_extension.py','run_experiment_multi_asset','constant-volatility two-asset GBM MC labels','600 labels;10000 MC each;400steps'),
'fig7_stress_test_leverage_ood.png':('stress_test_leverage.py','run_experiment_stress_test','Gaussian log returns; no trained generator','500 paths;30steps;three synthetic regimes'),
'fig8_ablation_study_baselines.png':('ablation_study.py','run_experiment_ablation','400 Fourier labels;3 independently trained models','150steps each;supervised PINN;no FNO'),
'fig9_training_loss_convergence.png':('plot_training_loss.py','module body','synthetic exponential curves and random noise','200 artificial points;seed2026')}
for name,(script,fun,inp,cfg) in scripts.items():
    status='NEEDS_COLAB_HEAVY_RUN'; cause='No historical checkpoint/raw arrays'; notes='Source candidate identified, not proof of historical execution.'; recomputed=''
    if name.startswith('fig3'): status='REPRODUCED'; cause='Untrained generator; time-axis normalization'; recomputed=D['timegan']; notes='Path statistics reproduced within floating-point tolerance; exact historical pixels/runtime not certified. Scientific risk-neutral claim false.'
    if name.startswith('fig4'): status='INCONSISTENT';cause='Synthetic IV formula presented as real calibration'
    if name.startswith('fig5'): status='INCONSISTENT';cause='Histogram uses final20bps arrays but title/legend10bps; manuscript Table3 source absent'
    if name.startswith('fig7'): status='REPRODUCED';cause='Unconditional one-step gross-ratio metric, not conditional martingale';recomputed=D['stress'];notes='Statistics reproduced; exact figure raster not regenerated.'
    if name.startswith('fig9'): status='MANUAL_VALUE_SUSPECTED';cause='Confirmed artificial loss construction in source, not observed training';notes='Synthetic construction established; intent is not inferred.'
    add(name,'synthetic_figure' if name.startswith('fig9') else 'figure','src/'+script,fun,inp,cfg,2026,200 if name.startswith('fig3') else '',recomputed=recomputed,status=status,cause=cause,notes=notes)
add('test_fig5.png','test_figure',status='SOURCE_NOT_FOUND',cause='No producing script in working tree or reachable Git history',notes='ORPHANED; visually plain line from (1,3) to (2,4), unrelated to final hedging chart; likely committed test, obsolescence cannot be established.')
json_sources={'paper1_experiments_summary.json':('run_paper1_experiments.py','main'),'hedging_results.json':('hedging_engine.py','run_experiment_hedging_transaction_costs'),'ablation_results.json':('ablation_study.py','run_experiment_ablation'),'multi_asset_results.json':('multi_asset_extension.py','run_experiment_multi_asset'),'stress_test_results.json':('stress_test_leverage.py','run_experiment_stress_test')}
def leaves(obj,path=''):
    for key,value in obj.items():
        p=f'{path}.{key}' if path else key
        if isinstance(value,dict): yield from leaves(value,p)
        else: yield p,value
for file,(script,fun) in json_sources.items():
    data=json.loads((ROOT/file).read_text())
    add(file,'result_json','src/'+script,fun,config='See source and report',seed=2026,status='REPRODUCED' if file=='stress_test_results.json' else 'NEEDS_COLAB_HEAVY_RUN',recomputed=D['stress'] if file=='stress_test_results.json' else '',cause='Numerical stress moments replayed; not a conditional guarantee' if file=='stress_test_results.json' else 'Aggregate output without raw arrays/checkpoint')
    for path,value in leaves(data):
        status='NEEDS_COLAB_HEAVY_RUN';recomputed='';cause='No raw prediction/PnL arrays or historical checkpoint'
        if file=='stress_test_results.json':
            regime,key=path.rsplit('.',1);recomputed=D['stress'][regime][key];status='REPRODUCED';cause='LOCAL-LIGHT matching numerical metric, limited unconditional interpretation'
        elif file=='hedging_results.json' and path.endswith('unhedged_std'):
            status='REPRODUCED';recomputed=D['unhedged_std'];cause='Original seed/path law reconstructed; constant initial premium does not affect std'
        elif file=='paper1_experiments_summary.json' and path in ['mean_S_T','martingale_error']:
            status='REPRODUCED';recomputed=D['timegan']['mean' if path=='mean_S_T' else 'terminal_growth_absolute_error'];cause='Untrained GRU paths reconstructed'
        elif file=='ablation_results.json' and path in ['Standard PINN.Gamma_TV','Pointwise MLP.Gamma_TV']:
            status='MANUAL_VALUE_SUSPECTED';recomputed=data['MartingaleONet (Proposed)']['Gamma_TV']*(1.8 if path.startswith('Standard') else 3.2);cause='Confirmed hard-coded multiple of proposed TV, not measured baseline Greek'
        elif file=='ablation_results.json' and path.startswith('FDM / Fourier Ground Truth.') and not path.endswith('Gamma_TV'):
            status='MANUAL_VALUE_SUSPECTED';cause='Literal 0.0 ground-truth self-error; not independent validation'
        add(file+'::'+path,'reported_scalar','src/'+script,fun,inputs=file,seed=2026,value=value,recomputed=recomputed,status=status,cause=cause)
add('src/us_market_spy_qqq_vix_2015_2025.csv','dataset','src/us_market_data.py','fetch_or_generate_us_market_dataset',config='Synthetic business-day prices 2015-01-02 to2024-12-31',seed=2026,recomputed=D['market_csv'],status='REPRODUCED',cause='Matches synthetic generation; genuine-market claim inconsistent')
for name,value,cause in [('README hedging variance reduction','59.5%','No source calculation matches stored JSON'),('README inference speedup','15225x /0.1us','JSON speedup2229.22x and2.007us; benchmark unequal batching'),('README FNO','RMSE1.8920;MAPE15.40%;TV.4120','No FNO implementation/result/checkpoint'),('Table3 user-reported values','unhedged1.842;FDM.37-.45;auto.16-.18','Manuscript and table data absent in repository'),('Table7 component ablations','Greek/martingale/downstream variants','No component-ablation code/data in repository'),('README benchmark proposed row','RMSE1.1794;MAPE10.07;TV.2064','Mixes master500-sample pricing and independently trained400-sample ablation TV')]:
    add(name,'claim',inputs='README.md or user-provided audit request',value=value,status='SOURCE_NOT_FOUND' if name.startswith('Table') or 'FNO' in name else 'INCONSISTENT',cause=cause)
inventory=[]
tracked=subprocess.check_output(['git','ls-files'],cwd=ROOT,text=True).splitlines()
for name in tracked:
    p=ROOT/name; typ='source' if p.suffix=='.py' else 'figure' if p.suffix=='.png' else 'dataset' if p.suffix=='.csv' else 'result_json' if p.suffix=='.json' else 'configuration' if name=='.gitignore' else 'documentation'
    classification='PRIMARY' if typ in ['source','configuration'] else 'ORPHANED' if name=='test_fig5.png' else 'DERIVED' if typ in ['figure','dataset','result_json'] else 'UNKNOWN'
    flags=[]
    if name=='src/plot_training_loss.py' or name.startswith('fig9'):flags=['MANUALLY_EDITED: explicitly synthetic curve construction']
    inventory.append({'path':name,'type':typ,'classification':classification,'flags':flags,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(OUT/'repository_inventory.json').write_text(json.dumps({'git_head':D['git_head'],'scope':'Every non-.git working-tree input file; Git tree/history checked separately; audit outputs excluded','tracked_count':len(tracked),'files':inventory,'absent':['checkpoints','NPY/NPZ inputs','notebooks','config files','raw predictions','training logs','manuscript/tables','tests'],'duplicates_by_sha256':{h:[i['path'] for i in inventory if i['sha256']==h] for h in set(i['sha256'] for i in inventory) if sum(i['sha256']==h for i in inventory)>1}},indent=2),encoding='utf-8')
(OUT/'artifact_manifest.json').write_text(json.dumps(rows,indent=2,ensure_ascii=False),encoding='utf-8')
with (OUT/'artifact_manifest.csv').open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows({key:json.dumps(value,ensure_ascii=False) if isinstance(value,(dict,list)) else value for key,value in row.items()} for row in rows)
issues=[
('C1','Table3 vs Figure5','src/hedging_engine.py:76-84,135-155,180-184; hedging_results.json','INCONSISTENT; Table3 SOURCE_NOT_FOUND','CRITICAL','Figure uses stored2.41/2.75/4.20; histogram20bps mislabeled10bps; missing table provenance','Recover Table3 source; rerun original with raw per-cost PnL','COLAB-HEAVY'),
('C2','59.5% variance reduction','README.md:14; audit/local_diagnostics.json hedging_reduction','INCONSISTENT','MAJOR','Neither std nor variance reductions match59.5; exact origin unknown','Remove percentage pending traceable evidence','LOCAL-LIGHT'),
('C3','Negative Gamma/decreasing Delta','src/run_paper1_experiments.py:122-174; src/deeponet_model.py:49-77','NEEDS_COLAB_HEAVY_RUN; visual violation observed','CRITICAL','No convexity guarantee; historical model absent','Evaluate saved rerun grid, report violations and support region','COLAB-HEAVY'),
('C4','Martingale/change of measure','src/timegan_model.py:33-54','INCONSISTENT; axis probe completed','CRITICAL','Temporal per-path mean, future dependence; no Radon-Nikodym density or volatility risk premium','Withdraw strict-risk-neutral/change-of-measure interpretation','LOCAL-LIGHT'),
('C5','TimeGAN path failure','src/run_paper1_experiments.py:178-216; audit/timegan_local_paths.npz','REPRODUCED failure','CRITICAL','Untrained GRU and temporal gross normalization; AM-GM terminal contraction','Retain as failure evidence; remove trained-TimeGAN empirical claim','LOCAL-LIGHT'),
('C6','Stress martingale metric','src/stress_test_leverage.py:61-79; audit/local_diagnostics.json','REPRODUCED limited metric','MAJOR','Mean absolute unconditional gross-ratio error, not conditional martingale','Relabel metric and disclose Gaussian synthetic regimes','LOCAL-LIGHT'),
('C7','PINN collapse','src/ablation_study.py:31-44,114-121; audit/local_diagnostics.json','Objective/probe verified; full collapse pending','CRITICAL','PINN uses only MSE; dead ReLU is stationary with positive loss','Rerun original baseline; withdraw PINN-performance comparison','COLAB-HEAVY'),
('C8','Component ablations / baseline table','src/ablation_study.py:94-165; README.md:99-103','INCONSISTENT; Table7 SOURCE_NOT_FOUND','CRITICAL','Different models/data; fake baseline TV multiples; FNO absent; mixed generations in README','Recover absent component variants; exclude unmeasured entries','COLAB-HEAVY'),
('C9','Pricing floor / accuracy','src/heston_solver.py:23,43-44; src/run_paper1_experiments.py:80-96','Solver discrepancy verified; learned metrics pending','CRITICAL','Incorrect Fourier prefactor for shifted CF; intrinsic clipping; in-sample evaluation','Original rerun with arrays, then separately authorize label repair','COLAB-HEAVY'),
('C10','Speedup','README.md:13; src/run_paper1_experiments.py:80-96','INCONSISTENT','MAJOR','Single CPU batch500 amortized vs50 scalar Fourier calls; no repetitions/warm-up','Withdraw universal speedups; new fair benchmark deferred','NOT-NEEDED-YET'),
('C11','Real-market calibration','src/us_market_data.py:16-52; src/run_paper1_experiments.py:222-245','Synthetic dataset REPRODUCED; real claims UNSUPPORTED','CRITICAL','Synthetic underlying histories and hand-built IV; no chains or fitted parameters','Remove real-data and calibration claims','LOCAL-LIGHT'),
('C12','test_fig5 and stale artifacts','test_fig5.png; git initial commit; audit/repository_inventory.json','SOURCE_NOT_FOUND','MINOR','Plain test line, producer missing; committed at initial generation','Preserve/quarantine in reporting; request producer if relevant','LOCAL-LIGHT')]
matrix='# Reviewer issue matrix\n\nReviewer identities and manuscript are unavailable; C identifiers refer to the supplied request.\n\n| Reviewer | Issue | Repository evidence | Reproduction status | Severity | Root cause | Required action | Compute class |\n|---|---|---|---|---|---|---|---|\n'
matrix+='\n'.join('| '+ ' | '.join(['Not supplied / '+i[0],*i[1:]])+' |' for i in issues)+'\n'
(OUT/'reviewer_issue_matrix.md').write_text(matrix,encoding='utf-8')
print('Inventory',len(inventory),'manifest entries',len(rows),'issues',len(issues))
