# Phase 0: user-run Colab experiments

These rerun the existing scientific implementation without fixing it. Nothing has been run by the audit agent. Reproducing an output does not validate its financial interpretation. Run on a Colab runtime; the original code uses CPU tensors and `.numpy()` and is intentionally kept on CPU even if a GPU is attached. No new speedup claim should use these instrumented timings.

## Setup and exact execution

Upload a ZIP of this repository (including `src/`, `audit/`, and `colab_phase0/`) to Colab, then use:

```python
from google.colab import files
uploaded = files.upload()  # select the repository ZIP
```

```python
import zipfile, pathlib
archive = next(name for name in uploaded if name.endswith('.zip'))
with zipfile.ZipFile(archive) as z:
    z.extractall('/content/phase0_repo')
repo = next(p.parent.parent for p in pathlib.Path('/content/phase0_repo').rglob('colab_phase0/run_original_experiments.py'))
print(repo)
```

```python
%pip install numpy scipy pandas matplotlib torch
```

```python
import subprocess, sys
for experiment in ['pricing', 'hedging', 'ablation', 'multi_asset']:
    subprocess.run([sys.executable, str(repo/'colab_phase0/run_original_experiments.py'),
                    '--experiment', experiment, '--output', '/content/phase0_results'],
                   cwd=repo, check=True)
```

To resume after interruption, rerun the same command with `--resume`. Training resumes at the last atomic checkpoint (every 10 optimizer steps), restoring module, optimizer, Torch and NumPy RNG state. Data preparation is regenerated from seed before state restoration. Completed experiments are skipped. Evaluation restarts after an interrupted evaluation; no evaluation-level progress is saved. Keep `/content/phase0_results` on Drive or download it before a runtime is destroyed, then restore it before resuming. Input script hashes must remain unchanged. Use a fresh output directory after any code/config/dependency change. Environment versions and CPU thread count are logged; historical dependency versions are unavailable.

## Experiments and exact original configurations

| Experiment | Purpose | Data and configuration | Expected outputs |
|---|---|---|---|
| pricing | C3/C9 learned-surface diagnostics and historical pricing rerun | 500 Fourier labels; seed 2026; original sampled ranges; K=100, r=.03; DeepONet 64/32; Adam .003; 200 full-batch steps; data + .01 PDE | original summary/fig1–4; `run_experiment_1_deeponet_pricing_and_speed.npz`; model state; Greek grid and CSV |
| hedging | C1 exact hedging generation with per-cost raw PnL | 5,000 S/T labels; fixed branch (2,.04,.3,-.7,.04); 150 full-batch steps; 200 paths,30 days; TC 0/.001/.002 | original hedging JSON/fig5; `pnl_0bps.npz`, `pnl_10bps.npz`, `pnl_20bps.npz`; paths and checkpoint |
| ablation | C7 collapse reproduction and C8 actual baseline generation | 400 labels; seed 2026; three independently initialized models; 150 steps each; PINN actually supervised MSE only | original JSON/fig8; raw predictions/targets; all three model states |
| multi_asset | Verify existing basket results | 600 constant-volatility GBM MC labels, 10,000 draws each; seed 2026; 128/64 operator; Adam .002; 400 full-batch steps | original JSON/fig6; raw predictions/targets, MC correlation curves and state |

All runs use CPU, float32 model tensors, full-batch training and the unmodified original reference-label formula. Instrumentation adds AST loop checkpointing and return-local capture; no losses, architecture, seeds or labels are repaired. `environment.json` records dependencies and SHA256; `execution.log` captures stdout/stderr; `training.jsonl` contains real training scalars; `training_line_*.pt` stores resumable states; `COMPLETE.json` is written only after success. Training checkpoints and saved states are trusted local files; do not load third-party pickle checkpoints.

## Return results

```python
import shutil
shutil.make_archive('/content/phase0_results', 'zip', '/content/phase0_results')
files.download('/content/phase0_results.zip')
```

Extract into `audit/colab_returns/<run-id>/`, without overwriting root JSON/figures or the current audit. Return the entire bundle, especially environment metadata, raw NPZ, checkpoints, logs and COMPLETE files. The audit manifest is intentionally pending until those results are actually reviewed. These scripts cannot recover the missing historical checkpoint or prove absent manuscript Table 3/7 values.

Then compute metrics from the returned arrays only:

```bash
python colab_phase0/analyze_returns.py audit/colab_returns/<run-id>
```

This writes `recomputed_accuracy.json` and `stratified_accuracy.csv`, explicitly marked as original in-sample evaluation against original labels. No missing result is fabricated. Greek CSV distinguishes all-grid mean magnitude from mean among violating points.

## Compute policy

LOCAL-LIGHT: inventory, hashes, arithmetic, CPU path generation, synthetic CSV reconstruction, dead-ReLU and reference-solver checks (already executed). COLAB-HEAVY: the four full original training reruns above (not executed). NOT-NEEDED-YET: redesign, corrected reference-label training, new FNO implementation, real-market calibration, new large benchmark and new theory; all require Phase 1 authorization.
