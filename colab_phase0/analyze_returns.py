"""Compute accuracy and stratified diagnostics from actual returned raw arrays only."""
import argparse,json
from pathlib import Path
import numpy as np
import pandas as pd
def metrics(y,p):
    e=p-y; denominator=np.sum((y-y.mean())**2)
    return {'count':len(y),'RMSE':float(np.sqrt(np.mean(e**2))),'MAE':float(np.abs(e).mean()),'MAPE_original_epsilon_pct':float((np.abs(e/(y+1e-5))).mean()*100),'MAPE_positive_prices_pct':float((np.abs(e[y>1e-8]/y[y>1e-8])).mean()*100) if (y>1e-8).any() else None,'median_absolute_error':float(np.median(np.abs(e))),'R2':float(1-np.sum(e**2)/denominator) if denominator>0 else None}
def main():
    a=argparse.ArgumentParser();a.add_argument('result_dir');args=a.parse_args();root=Path(args.result_dir)
    sources=[('pricing','run_experiment_1_deeponet_pricing_and_speed.npz',[('proposed','v_test_pred','target_t','branch_t','trunk_t')]),('ablation','run_experiment_ablation.npz',[(name,p,'y_true','branch_t','trunk_t') for name,p in [('proposed','p_onet'),('MLP','p_mlp'),('PINN','p_pinn')]]),('multi_asset','run_experiment_multi_asset.npz',[('basket','preds','targets','branch_t','trunk_t')])]
    summaries={};strata=[]
    for exp,file,models in sources:
        path=root/exp/file
        if not path.exists():continue
        with np.load(path,allow_pickle=False) as data:
            for name,pkey,ykey,bkey,tkey in models:
                y=data[ykey].ravel();p=data[pkey].ravel();b=data[bkey];t=data[tkey]
                key=exp+'/'+name;summaries[key]={'evaluation':'original training set; no held-out generalization claim','minimum_prediction':float(p.min()),'maximum_prediction':float(p.max()),**metrics(y,p)}
                axes={'option_price':pd.cut(y,[-np.inf,1,5,10,20,np.inf]),'maturity':pd.cut(t[:,-1],[0,.1,.25,.5,1,2,np.inf])}
                if exp!='multi_asset':
                    axes.update({'moneyness_S_over_K':pd.cut(t[:,0]/t[:,1],[0,.9,.98,1.02,1.1,np.inf]),'volatility_sqrt_v0':pd.cut(np.sqrt(b[:,4]),[0,.15,.2,.25,.3,np.inf]),'rho':pd.cut(b[:,3],[-1,-.7,-.5,0,1]),'kappa':pd.cut(b[:,0],[0,1.5,2,2.5,np.inf]),'theta':pd.cut(b[:,1],[0,.04,.06,np.inf]),'vol_of_vol':pd.cut(b[:,2],[0,.2,.3,.4,np.inf]),'Feller':np.where(2*b[:,0]*b[:,1]>=b[:,2]**2,'satisfied','violated')})
                for axis,buckets in axes.items():
                    labels=np.asarray(buckets.astype(str) if hasattr(buckets,'astype') else buckets)
                    for label in np.unique(labels):
                        mask=labels==label;strata.append({'model':key,'stratification':axis,'bucket':label,**metrics(y[mask],p[mask])})
    if not summaries:raise SystemExit('No real returned prediction arrays found; no metrics generated.')
    (root/'recomputed_accuracy.json').write_text(json.dumps(summaries,indent=2))
    pd.DataFrame(strata).to_csv(root/'stratified_accuracy.csv',index=False)
    print(json.dumps(summaries,indent=2))
if __name__=='__main__':main()
