"""Tiny scalar optimizer test of checkpoint/resume; no repository model training."""
import os
os.environ['KMP_DUPLICATE_LIB_OK']='TRUE'
import json,shutil,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
toy='''import torch, numpy as np
from pathlib import Path
def run_experiment_ablation():
    model=torch.nn.Linear(1,1)
    optimizer=torch.optim.Adam(model.parameters(),lr=.01)
    x=torch.ones(1,1)
    for epoch in range(20):
        if epoch==13 and not Path("interrupted.marker").exists():
            Path("interrupted.marker").write_text("yes")
            raise RuntimeError("intentional interruption")
        optimizer.zero_grad()
        loss=(model(x)-2).square().mean()
        loss.backward()
        optimizer.step()
    prediction=model(x).detach().numpy()
    return prediction
'''
with tempfile.TemporaryDirectory(prefix='phase0_instrumentation_') as directory:
    base=Path(directory);(base/'src').mkdir();(base/'colab_phase0').mkdir()
    shutil.copy2(ROOT/'colab_phase0/run_original_experiments.py',base/'colab_phase0/run_original_experiments.py')
    (base/'src/ablation_study.py').write_text(toy)
    cmd=[sys.executable,str(base/'colab_phase0/run_original_experiments.py'),'--experiment','ablation','--output',str(base/'returns')]
    first=subprocess.run(cmd,capture_output=True,text=True)
    if 'intentional interruption' not in (base/'returns/ablation/execution.log').read_text():
        print(first.stderr)
        print((base/'returns/ablation/execution.log').read_text())
    assert first.returncode!=0 and 'intentional interruption' in (base/'returns/ablation/execution.log').read_text()
    second=subprocess.run(cmd+['--resume'],capture_output=True,text=True)
    assert second.returncode==0,second.stderr
    import numpy as np
    import torch
    actual=np.load(base/'returns/ablation/run_experiment_ablation.npz')['prediction']
    torch.manual_seed(2026);reference=torch.nn.Linear(1,1);opt=torch.optim.Adam(reference.parameters(),lr=.01)
    for _ in range(20):
        opt.zero_grad();loss=(reference(torch.ones(1,1))-2).square().mean();loss.backward();opt.step()
    expected=reference(torch.ones(1,1)).detach().numpy()
    assert np.array_equal(actual,expected),(actual,expected)
    third=subprocess.run(cmd+['--resume'],capture_output=True,text=True)
    assert third.returncode==0 and 'Completed experiment retained' in third.stdout
    evidence={'scalar_resume_test':'passed','exact_prediction_match':True,'completed_run_skip':'passed','full_experiments_executed':False,'test_scope':'20 scalar Adam steps; interrupted at13, restored iteration10'}
    (ROOT/'audit/colab_instrumentation_validation.json').write_text(json.dumps(evidence,indent=2))
    print(json.dumps(evidence))
