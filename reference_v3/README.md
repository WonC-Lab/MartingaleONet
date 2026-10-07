# Phase 1B.3 completion-only workflow

Domain v1, all Phase1A budgets and historical strict rows are unchanged. No neural training or neural-label generation occurs.

## CORE is reused, never automatically reswept

The local run completed **1734/1734** original CORE inputs: 300 inherited, SHA-verified deterministic rows and 1434 new Sobol rows. `coverage_core.jsonl` contains every raw convergence/stencil record and original final strict status. The original strict result is 187 PASS /1547 FAIL, not a domain certificate.

`immutable/local_core_1734.jsonl.gz` transports the exact completed raw bytes (about 7 MB compressed). `immutable/LOCAL_CORE_MANIFEST.json` records archive/raw SHA256 and canonical pricing-module hashes. `reuse import` verifies these plus the exact original input catalog, then copies raw bytes to the new output. A mismatch or missing snapshot aborts. It never triggers a full sweep and never overwrites a different output file. The local source is read only.

The notebook contains **no coverage command**. It calls `reference_v3.reuse import`, and asserts `reused=1734`, `recomputed=0`. This was integration-tested twice with all A/B pricing entry points disabled. `CORE_REUSE_RECEIPT.json` is the audit receipt.

## Fresh-clone Colab

Use `colab/phase1b3_reference_completion.ipynb`. The existing `colab/phase1b2_reference_escalation.ipynb` now contains the same completion workflow; its previous contents are preserved in `colab/archive/phase1b2_reference_escalation_original.ipynb`.

Before launching from GitHub, publish the new workflow, immutable CORE archive/manifest, necessary `reference`, `reference_v2`, `audit`, `design` historical inputs, and this version's historical snapshot. The notebook verifies these instead of silently replacing missing artifacts. This workspace preparation does not claim a GitHub push or remote Colab execution.

Completed local MP/external/boundary evidence is also transported in `immutable/LOCAL_EVIDENCE_MANIFEST_0001.zip`, with its original manifest and `LOCAL_EVIDENCE_MANIFEST_0001_BUNDLE.json` SHA256 metadata. Publish all three together with the updated `reuse.py`. The importer prefers this verified bundle, so a fresh clone does not require hundreds of loose checkpoint files. It verifies all entries before copying, refuses changed existing checkpoints, and preserves resumed boundary output. Missing evidence never triggers a CORE sweep. After updating the Colab clone to the published fix, rerun the failed reuse cell; the existing CORE receipt/output is retained.

The setup cell clones `https://github.com/WonC-Lab/MartingaleONet.git` with the chosen ref (default current branch `main`), installs `requirements-colab.txt`, records environment and commit, creates `reference_v3_colab/`, and optionally stores it on Drive for runtime-reset resume. The Colab runtime performs the deliberate external environment subset, not another complete CORE sweep.

Exact remaining commands, with OUT set to the versioned output directory:

```text
python -m pytest reference_v3/tests reference_v2/tests -q
python -m reference_v3.reuse import --output OUT
python -m reference_v3.escalation --scope all --workers 4 --output OUT
python -m reference_v3.external --cross-environment --refine --output OUT
python -m reference_v3.boundary --workers 4 --output OUT
python -m reference_v3.escalation --scope boundary --workers 4 --output OUT
python -m reference_v3.continuity --output OUT
python -m reference_v3.boundary_pde --workers 4 --output OUT
python -m reference_v3.review --output OUT
python -m reference_v3.plots --output OUT
```

The final cell creates `reference_v3_colab_results.zip`, including failures, raw stencils, every engine setting/result, checkpoints, CSV resolution table, NPZ/JSON uncertainty, figures and reports. The runner also archives available outputs when a step fails. No unexecuted output is counted as passed.

## Explicit deliberate cross-environment subset

QuantLib 1.41 analytic/PDE checks use exactly the original **six CORE inputs** (ATM, deep OTM, deep ITM, short CORE, high sigma, near-Feller) and **two exact v0=0 challenge inputs**. This is recorded in `CROSS_ENVIRONMENT_VALIDATION_PLAN.json`. A/B repricing on these eight inputs supports convention/environment validation; it does not replace or overwrite their original CORE strict rows.

QuantLib `HestonModel` rejects exact v0=0 through its positive parameter constraint. Failed attempts are saved as `UNSUPPORTED_EXACT_V0`; no epsilon substitution is permitted. Noninteger-day maturities use the already-tested exact deterministic process time change, with all original/mapped inputs and calendar conventions stored. Independent PDE values remain in uncertainty even when their grid error exceeds budget.

## Resume and execution costs

MP: one checkpoint per physical input, source-revision namespace, all true 50/80/120-digit values, independent cutoff/degree refinements and physical stencils. Fulfilled compatible point obligations are reused, including immutable Phase1B.2 evidence; strike/COS flags need their additional matching checks. Pending cases are never removed from the complete plan.

External: one checkpoint per input/engine/setting/environment. Boundary: input-key resume. Completed local boundary rows and compatible MP checkpoints are imported. Increasing PDE grids appends settings; it does not erase the earlier sequence. The CORE archive/manifest is separate from all mutable new-output checkpoints.

Local-light cost planning is input-only (`LOCAL_COST_PLAN.json`), never selected by favorable numerical answers. Use `--max-seconds 600` for a bounded local MP session: stop submitting new cases when the budget expires, finish active cases, save every result and leave the rest pending. Full MP/PDE/boundary completion is COLAB_HEAVY and may require hours or longer. Hardware/environment execution alone cannot certify the reference engine.

Current reports are fail-closed while mandatory numerical evidence remains unresolved. No retrospective subdomain, relaxed tolerance or automatic Phase1C start is allowed. The reference-engine lock is only produced if every existing CORE criterion passes.
