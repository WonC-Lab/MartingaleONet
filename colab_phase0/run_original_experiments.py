"""Instrument original experiments in an isolated copy. No methodological fixes.
Run from repository root: python colab_phase0/run_original_experiments.py --experiment pricing
"""
import argparse, ast, contextlib, hashlib, json, os, platform, shutil, sys, time
os.environ['KMP_DUPLICATE_LIB_OK']='TRUE'
from pathlib import Path
import numpy as np
import torch

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--experiment',choices=['pricing','hedging','ablation','multi_asset'],required=True)
    parser.add_argument('--output',default='/content/phase0_results')
    parser.add_argument('--resume',action='store_true')
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    out=Path(args.output).resolve()/args.experiment
    if out.exists() and not args.resume:
        raise SystemExit('Output exists; choose a new output or use --resume.')
    out.mkdir(parents=True,exist_ok=True)
    if args.resume and (out/'COMPLETE.json').exists():
        print('Completed experiment retained:',out); return
    sandbox=out/'original_copy'; sandbox.mkdir(exist_ok=True)
    if not (sandbox/'src').exists(): shutil.copytree(root/'src',sandbox/'src',ignore=shutil.ignore_patterns('__pycache__'))
    source_hashes={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'src').glob('*.py')}
    if args.resume and (out/'environment.json').exists():
        previous=json.loads((out/'environment.json').read_text())
        if previous['source_sha256']!=source_hashes:
            raise SystemExit('Source hashes changed. Use a fresh output directory; cannot resume this run.')
    torch.manual_seed(2026); np.random.seed(2026)
    # Original code is CPU-only (.numpy(), CPU noise/tensors). Preserve that device.
    torch.set_num_threads(2)
    meta={'purpose':'Forensic rerun of unchanged scientific implementation with raw-output capture','experiment':args.experiment,'seed':2026,'device':'cpu','gpu_available':torch.cuda.is_available(),'python':sys.version,'torch':torch.__version__,'numpy':np.__version__,'platform':platform.platform(),'source_sha256':source_hashes,'compute_class':'COLAB-HEAVY','resume':args.resume,'threads':2,'note':'No GPU conversion: it would change the original execution. CPU execution on a Colab runtime is intentional.'}
    if not (out/'environment.json').exists():
        (out/'environment.json').write_text(json.dumps(meta,indent=2))
    else:
        with (out/'resume_events.jsonl').open('a') as f: f.write(json.dumps(meta)+'\n')
    counters={}; handles={}
    def checkpoint_path(key): return out/(key+'.pt')
    def audit_iter(key, iterable, scope):
        items=list(iterable); start=0
        cp=checkpoint_path(key)
        if args.resume and cp.exists():
            saved=torch.load(cp,map_location='cpu',weights_only=False)
            for name,obj in scope.items():
                if isinstance(obj,(torch.nn.Module,torch.optim.Optimizer)) and name in saved['states']:
                    obj.load_state_dict(saved['states'][name])
            torch.set_rng_state(saved['torch_rng']); np.random.set_state(saved['numpy_rng']); start=saved['completed']
        counters[key]=start
        return items[start:]
    def audit_checkpoint(key,scope):
        counters[key]+=1
        metrics={name:float(obj.detach()) for name,obj in scope.items() if name.startswith(('loss','l_data','l_pde')) and isinstance(obj,torch.Tensor) and obj.numel()==1}
        with (out/'training.jsonl').open('a') as f: f.write(json.dumps({'stage':key,'iteration':counters[key],**metrics})+'\n')
        if counters[key]%10==0:
            states={name:obj.state_dict() for name,obj in scope.items() if isinstance(obj,(torch.nn.Module,torch.optim.Optimizer))}
            temp=out/(key+'.tmp'); torch.save({'states':states,'completed':counters[key],'torch_rng':torch.get_rng_state(),'numpy_rng':np.random.get_state()},temp); temp.replace(checkpoint_path(key))
    class Instrument(ast.NodeTransformer):
        def visit_Assign(self,node):
            self.generic_visit(node)
            if any(isinstance(t,ast.Subscript) and isinstance(t.value,ast.Name) and t.value.id=='hedging_results' for t in node.targets):
                return [node,*ast.parse('audit_capture_pnl(tc_key, locals())').body]
            return node
        def visit_For(self,node):
            self.generic_visit(node)
            training=any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='step' for b in node.body for n in ast.walk(b))
            if training:
                key='training_line_'+str(node.lineno)
                node.iter=ast.Call(func=ast.Name(id='audit_iter',ctx=ast.Load()),args=[ast.Constant(key),node.iter,ast.Call(func=ast.Name(id='locals',ctx=ast.Load()),args=[],keywords=[])],keywords=[])
                node.body.extend(ast.parse(f'audit_checkpoint({key!r}, locals())').body)
            return node
    mapping={'pricing':('run_paper1_experiments.py','main'),'hedging':('hedging_engine.py','run_experiment_hedging_transaction_costs'),'ablation':('ablation_study.py','run_experiment_ablation'),'multi_asset':('multi_asset_extension.py','run_experiment_multi_asset')}
    filename,function=mapping[args.experiment]; source=sandbox/'src'/filename
    tree=Instrument().visit(ast.parse(source.read_text(encoding='utf-8'))); ast.fix_missing_locations(tree)
    # Capture original function locals on return: no approximation from figure pixels.
    def trace(frame,event,arg):
        if event=='return' and frame.f_code.co_filename==str(source) and frame.f_code.co_name.startswith('run_experiment'):
            scope=frame.f_locals; prefix=frame.f_code.co_name
            arrays={name:obj.detach().cpu().numpy() if isinstance(obj,torch.Tensor) else obj for name,obj in scope.items() if isinstance(obj,(np.ndarray,torch.Tensor))}
            if arrays: np.savez_compressed(out/(prefix+'.npz'),**arrays)
            for name,obj in scope.items():
                if isinstance(obj,torch.nn.Module): torch.save(obj.state_dict(),out/(prefix+'_'+name+'_state.pt'))
                elif isinstance(obj,dict):
                    try: (out/(prefix+'_'+name+'.json')).write_text(json.dumps(obj,indent=2))
                    except (TypeError,ValueError): pass
            if args.experiment=='pricing' and 'model' in scope and 'branch_t' in scope:
                greek_grid(scope['model'],scope['branch_t'][0:1],out)
        return trace
    os.environ['KMP_DUPLICATE_LIB_OK']='TRUE'; os.environ['MPLBACKEND']='Agg'
    sys.path.insert(0,str(sandbox/'src')); os.chdir(sandbox)
    def audit_capture_pnl(key,scope):
        np.savez_compressed(out/('pnl_'+key+'.npz'),**{name:scope[name] for name in ['pnl_autograd','pnl_fdm','pnl_unhedged']})
    namespace={'__name__':'phase0_original','__file__':str(source),'audit_iter':audit_iter,'audit_checkpoint':audit_checkpoint,'audit_capture_pnl':audit_capture_pnl}
    with (out/'execution.log').open('a') as log,contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
        exec(compile(tree,str(source),'exec'),namespace)
        sys.settrace(trace)
        try: namespace[function]()
        except BaseException:
            import traceback
            traceback.print_exc()
            raise
        finally: sys.settrace(None)
    for p in sandbox.glob('*.json'): shutil.copy2(p,out/p.name)
    for p in sandbox.glob('*.png'): shutil.copy2(p,out/p.name)
    (out/'COMPLETE.json').write_text(json.dumps({'completed':True,'experiment':args.experiment,'unix_time':time.time()}))
    print('Completed:',out)

def greek_grid(model,branch,out):
    import pandas as pd
    import itertools
    x=torch.tensor(list(itertools.product(np.linspace(70,130,31),[80.,100.,120.],[.05,.1,.5,1.,2.])),dtype=torch.float32,requires_grad=True)
    b=branch.detach().repeat(len(x),1)
    price=model(b,x); first=torch.autograd.grad(price.sum(),x,create_graph=True)[0]
    gamma=torch.autograd.grad(first[:,0].sum(),x,retain_graph=True)[0][:,0]
    strike2=torch.autograd.grad(first[:,1].sum(),x)[0][:,1]
    values={'dV/dS>=0':torch.relu(-first[:,0]),'d2V/dS2>=0':torch.relu(-gamma),'dV/dK<=0':torch.relu(first[:,1]),'d2V/dK2>=0':torch.relu(-strike2),'Delta<=1':torch.relu(first[:,0]-1),'V>=lower_bound':torch.relu(torch.relu(x[:,0]-x[:,1]*torch.exp(-.03*x[:,2]))-price[:,0]),'V<=S':torch.relu(price[:,0]-x[:,0])}
    rows=[]
    for name,v in values.items():
        a=v.detach().numpy(); i=int(a.argmax()); mask=a>1e-7
        rows.append({'constraint':name,'status':'RERUN_DIAGNOSTIC_NOT_HISTORICAL_CHECKPOINT','sample_count':len(a),'violation_frequency':float(mask.mean()),'mean_violation_magnitude':float(a.mean()),'mean_magnitude_among_violations':float(a[mask].mean()) if mask.any() else 0.,'worst_violation':float(a.max()),'worst_region':json.dumps({'S':float(x[i,0].detach()),'K':float(x[i,1].detach()),'T':float(x[i,2].detach()),'branch':branch.tolist()}),'notes':'K !=100 and T=.05 are outside training support; tolerance 1e-7; ReLU derivatives exclude distributional kink contribution.'})
    pd.DataFrame(rows).to_csv(out/'greek_constraint_violations.csv',index=False)
    np.savez_compressed(out/'greek_grid.npz',trunk=x.detach().numpy(),branch=b.numpy(),price=price.detach().numpy(),first=first.detach().numpy(),gamma=gamma.detach().numpy(),strike_second=strike2.detach().numpy())

if __name__=='__main__': main()
