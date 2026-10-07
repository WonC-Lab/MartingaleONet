"""Phase 0 CPU diagnostics; never trains or overwrites original artifacts."""
import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
import sys, json, platform, hashlib, subprocess, csv
from pathlib import Path
import numpy as np
import pandas as pd
import torch
from scipy.integrate import quad
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from timegan_model import TimeGANRiskNeutralGenerator
from heston_solver import HestonReferenceSolver
from ablation_study import PINNPricer
from deeponet_model import DeepONetOptionPricer
OUT = ROOT / 'audit'
torch.set_num_threads(1)
torch.manual_seed(2026)
np.random.seed(2026)
result = {'compute_class':'LOCAL-LIGHT','device':'cpu','seed':2026,'python':sys.version,'torch':torch.__version__,'numpy':np.__version__,'platform':platform.platform(),'git_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'openmp_workaround':'KMP_DUPLICATE_LIB_OK=TRUE (original scripts also set this); original runtime unknown'}
g = TimeGANRiskNeutralGenerator(feature_dim=2,hidden_dim=32,seq_len=252)
paths = g.generate_price_trajectories(S0=100,batch_size=200,r=.03,dt=1/252)
np.savez_compressed(OUT/'timegan_local_paths.npz',paths=paths)
terminal = paths[:,-1]
result['timegan'] = {'trained':False,'theoretical_mean':float(100*np.exp(.03)),'mean':float(terminal.mean()),'median':float(np.median(terminal)),'std_ddof0':float(terminal.std()),'min':float(terminal.min()),'max':float(terminal.max()),'quantiles':dict(zip(['0','1','5','25','50','75','95','99','100'],np.quantile(terminal,[0,.01,.05,.25,.5,.75,.95,.99,1]).tolist())),'all_path_peak':float(paths.max()),'first30_peak':float(paths[:30].max()),'terminal_growth_absolute_error':float(abs(terminal.mean()/100-np.exp(.03)))}
# Constant-in-time but different-across-path returns expose the normalization axis.
raw = torch.tensor([[[.2],[.2]],[[-.2],[-.2]]])
corr = g.apply_martingale_drift_correction(raw)
result['correction_axis_probe']={'raw':raw.tolist(),'corrected':corr.tolist(),'explanation':'Each path is divided by its own time mean, erasing persistent path drift.'}
np.random.seed(2026)
stress={}
for name,vol,drift in [('Standard Market',.15,.03),('COVID-19 Crash (OOD)',.55,-.4),('3x Leveraged ETF (TQQQ)',.65,.09)]:
    raw = np.random.normal(drift/252,vol/np.sqrt(252),(500,30,1))
    corrected=g.apply_martingale_drift_correction(torch.tensor(raw,dtype=torch.float32))[:,:,0].detach().numpy()
    p=100*np.exp(np.hstack([np.zeros((500,1)),np.cumsum(corrected,axis=1)]))
    errors=np.abs((p[:,1:]/p[:,:-1]).mean(0)-np.exp(.03/252))
    stress[name]={'corrected_martingale_error':float(errors.mean()),'max_error':float(errors.max()),'raw_martingale_error':float(np.abs(np.exp(raw[:,:,0]).mean(0)-np.exp(.03/252)).mean()),'terminal_mean':float(p[:,-1].mean())}
    np.savez_compressed(OUT/('stress_'+name.split()[0]+'.npz'),raw=raw,corrected=corrected,paths=p)
result['stress']=stress
# Recreate synthetic CSV in memory, without calling the writer.
np.random.seed(2026)
dates=pd.date_range('2015-01-02','2024-12-31',freq='B'); n=len(dates)
returns=np.random.normal((.11-.5*.16**2)/252,.16/np.sqrt(252),n); j=int(n*.51); returns[j:j+20]-=.025
spy=200*np.exp(np.cumsum(returns)); qqq=105*np.exp(np.cumsum(1.25*returns+np.random.normal(0,.005,n)))
vix=15+500*np.abs(returns); vix[j:j+30]+=45; vix=np.clip(vix,10,85)
stored=pd.read_csv(ROOT/'src/us_market_spy_qqq_vix_2015_2025.csv')
result['market_csv']={'rows':n,'start':str(dates[0].date()),'end':str(dates[-1].date()),'columns':stored.columns.tolist(),'date_match':bool((stored.Date==dates.strftime('%Y-%m-%d')).all()),'max_absolute_difference':{key:float(np.max(np.abs(stored[key].to_numpy()-value))) for key,value in [('SPY',spy),('QQQ',qqq),('VIX',vix)]},'synthetic_formula_matches':bool(np.allclose(stored[['SPY','QQQ','VIX']],np.column_stack([spy,qqq,vix]),rtol=1e-12,atol=1e-12))}
# Exact original hedging paths; no pricing-model training.
np.random.seed(2026); s=np.full((200,31),100.); v=np.full((200,31),.04)
for t in range(30):
    z1=np.random.randn(200); z2=-.7*z1+np.sqrt(1-.7**2)*np.random.randn(200); vc=np.maximum(v[:,t],1e-6)
    v[:,t+1]=np.maximum(vc+2*(.04-vc)/252+.3*np.sqrt(vc/252)*z2,1e-6)
    s[:,t+1]=s[:,t]*np.exp((.03-.5*vc)/252+np.sqrt(vc/252)*z1)
payoff=np.maximum(s[:,-1]-100,0)
result['unhedged_std'] = float(payoff.std())
np.savez_compressed(OUT/'hedging_local_paths.npz',spot=s,variance=v,payoff=payoff)
hedge=json.loads((ROOT/'hedging_results.json').read_text())
result['hedging_reduction']={key:{'std_reduction_vs_fdm_pct':100*(1-val['auto_std']/val['fdm_std']),'variance_reduction_vs_fdm_pct':100*(1-(val['auto_std']/val['fdm_std'])**2),'std_reduction_vs_unhedged_pct':100*(1-val['auto_std']/val['unhedged_std']),'variance_reduction_vs_unhedged_pct':100*(1-(val['auto_std']/val['unhedged_std'])**2)} for key,val in hedge.items()}
# Dead ReLU probe is a deliberately constructed diagnostic, not historical reproduction.
torch.manual_seed(2026); pinn=PINNPricer()
with torch.no_grad():
    pinn.net[-1].weight.zero_(); pinn.net[-1].bias.fill_(-1)
x=torch.tensor([[2,.04,.3,-.7,.04,100,100,1],[2,.04,.3,-.7,.04,120,100,.1]],dtype=torch.float32)
y=torch.tensor([[10.],[20.]])
loss=((pinn(x)-y)**2).mean(); loss.backward()
result['pinn_dead_relu_probe']={'prediction':pinn(x).detach().tolist(),'mse':float(loss),'max_parameter_gradient':max(float(p.grad.abs().max()) for p in pinn.parameters()),'global_minimum':False,'interpretation':'positive loss with zero gradient: stationary dead-output trap, not objective minimum'}
model=DeepONetOptionPricer()
with torch.no_grad():
    model.branch_net[-1].weight.zero_(); model.branch_net[-1].bias.zero_(); model.bias.fill_(-1)
result['zero_surface_pde_loss']=float(model.compute_physics_informed_heston_loss(x[:,:5],x[:,5:]))
# Independent inversion using probabilities; shares CF but uses a separate pricing identity.
solver=HestonReferenceSolver()
def probability_price(S,K,T):
    f=lambda u: solver._characteristic_function(u,S,K,T)
    p2=.5+quad(lambda u:(f(u)/(1j*u)).real,1e-8,200,limit=300)[0]/np.pi
    p1=.5+quad(lambda u:(f(u-1j)/(f(-1j)*1j*u)).real,1e-8,200,limit=300)[0]/np.pi
    return S*p1-K*np.exp(-solver.r*T)*p2
rows=[]
for S in [80,90,100,110,120]:
    for T in [.01,.1,.5,1.,2.]:
        original=solver.price_call(S,100,T); independent=probability_price(S,100,T)
        rows.append({'S':S,'K':100,'T':T,'original_price':original,'independent_probability_price':independent,'difference':original-independent,'original_gamma':solver.compute_greeks(S,100,T)['gamma']})
pd.DataFrame(rows).to_csv(OUT/'reference_solver_crosscheck.csv',index=False)
result['solver_crosscheck']={'max_absolute_difference':max(abs(row['difference']) for row in rows),'rows':rows,'identity':'S*P1-K*exp(-r*T)*P2; same characteristic function, independent inversion, not fully independent solver'}
# Sample original pricing configuration without integrating 500 prices.
np.random.seed(2026); params=[]
for _ in range(500):
    params.append([np.random.uniform(1,3),np.random.uniform(.02,.08),np.random.uniform(.1,.5),np.random.uniform(-.8,-.3),np.random.uniform(.02,.08),np.random.uniform(80,120),np.random.uniform(.1,2)])
a=np.array(params); result['feller']={'violations':int(np.sum(2*a[:,0]*a[:,1]<a[:,2]**2)),'count':500,'fixed_hedging_margin':2*2*.04-.3**2,'meaning':'Feller failure permits accessible zero variance; not itself invalid Heston parameters.'}
# Historical checkpoint is absent: never report untrained model violations as learned results.
pd.DataFrame([{'constraint':c,'status':'NEEDS_COLAB_HEAVY_RUN','sample_count':0,'violation_frequency':None,'mean_violation_magnitude':None,'worst_violation':None,'worst_region':None,'notes':'No historical learned checkpoint; untrained model is not a substitute.'} for c in ['dV/dS>=0','d2V/dS2>=0','dV/dK<=0','d2V/dK2>=0','Delta<=1','V>=max(S-K*exp(-r*T),0)','V<=S']]).to_csv(OUT/'greek_constraint_violations.csv',index=False)
(OUT/'local_diagnostics.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({key:value for key,value in result.items() if key not in ['solver_crosscheck','correction_axis_probe']},indent=2))
