# Phase 1B.2 reference-only escalation

Historical `reference/`, `audit/`, `design/` outputs are unchanged and SHA256-checked. New raw files and reports live here. No neural training or final neural dataset generation.

Actual local computation: reproduce original 25 rows, complete 300 mandatory deterministic CORE cases with physical FD, a true 31x31 diagnostic slice, 50/80/120-digit MP selected cases, all 15 CORE FD-truncation targets, extra typical v=0 cutoff escalation, 58 v/tau diagnostic cases, and limiting-PDE consistency checks. See reports for actual completion status and failed counts; this README is not a certificate.

```powershell
$env:MPMATH_NOGMPY='1'
python -m pytest reference_v2/tests -q
python -m reference_v2.workflow reproduce
python -m reference_v2.workflow coverage --scope mandatory
python -m reference_v2.workflow hp --scope local
python -m reference_v2.greek_priority
python -m reference_v2.zero_escalation
python -m reference_v2.fd_precision
python -m reference_v2.workflow boundary --scope local
python -m reference_v2.boundary_pde
python -m reference_v2.decay_analysis
python -m reference_v2.diagnostics dense
python -m reference_v2.diagnostics gamma
python -m reference_v2.reports
python -m reference_v2.plots
```

These commands write new version outputs. Coverage resumes only with matching execution-source fingerprints. The completed local coverage uses the archived source below; a new run of the current source should use a fresh --output directory rather than append to that local checkpoint. Do not regenerate or overwrite the historical `reference/` outputs. `executed_sources/workflow_coverage_v2_0.py` preserves the exact orchestration source used for the local coverage before JSON-null aggregation fixes; numerical algorithms and raw values were not changed by those fixes. Postprocessing records its own current hashes.

Heavy complete coverage and every retained/near-failed MP point are prepared in `colab/phase1b2_reference_escalation.ipynb`. It installs pinned QuantLib and calls repository modules. No remote Colab results are claimed until that notebook actually runs. CORE has 1734 predeclared points, of which 1434 Sobol points remain unexecuted locally. Complete collar/OOD, MP escalation and external checks can take hours or longer.

All status/uncertainty fields are numerical evidence, not rigorous enclosures. A resolved point cannot certify a continuous domain. v=0 is classified CHALLENGE by the frozen partition but remains a boundary obligation of the original training objective.
