# Phase 1B.2 validation report

**CORE: FAIL — BOUNDARY/COLLAR: FAIL — CHALLENGE/OOD: FAIL. Phase 1C is not authorized.**

The historical FAIL was reproduced on 25 rows; 25 matched statuses. Raw A/B values reproduced exactly in this environment. 68 historical files verified unchanged. Never interpret a new resolved point as an upgrade of the historical gate.

CORE planned coverage 300/1734; 300/300 mandatory deterministic points and 300 CORE FD studies were executed. Original CORE points still pending in this output: 1434. Strict rows: 24 PASS / 276 FAIL. The strict protocol retains requested quadrature-accuracy and FD propagation failures despite tiny final-method discrepancies. Flags overlap: {'A_domain': 48, 'solver_error': 261, 'FD_uncertainty_budget_unresolved': 100, 'FD_derivative_amplification_or_truncation': 15, 'strike_FD_derivative_unresolved': 4}.

| Metric | Mean absolute gap | Median | p95 | p99 | Maximum |
|---|---:|---:|---:|---:|---:|
| price | 1.9882e-16 | 1.23525e-16 | 5.53031e-16 | 8.88178e-16 | 1.33227e-15 |
| Delta | 2.92211e-15 | 3.33067e-16 | 3.86635e-15 | 8.56071e-14 | 1.09135e-13 |
| Gamma | 1.72726e-13 | 2.88658e-15 | 2.64066e-13 | 4.39694e-12 | 1.15087e-11 |
| Vv | 1.64575e-15 | 2.77556e-16 | 2.22472e-15 | 4.89127e-14 | 9.97892e-14 |


Genuine 50/80/120-digit Lewis pricing and MP physical-variable FD distinguish requested-accuracy/roundoff issues, FD truncation/cancellation, and integration tails. Unique selected Gamma evidence: {'NUMERICALLY_RESOLVED': 17, 'UNRESOLVED': 1}. See HIGH_PRECISION_REPORT.md and GREEK_CERTIFICATION.md. The all-core FD-truncation target set is explicit; not every retained numerical flag or old price failure has complete MP/external escalation yet.

QuantLib 1.41 release commit 367ce80ae4f285835ceb3bba97746bea239984ad is pinned in the Colab workflow ([official release](https://github.com/lballabio/QuantLib/releases/tag/v1.41)). Aligned analytic/PDE cases completed in this output: 0/8. The dependency was unavailable for this run; recorded exceptions are INDETERMINATE. The supplied notebook installs and runs the pinned version in Colab; the local output does not claim a remote execution. Direct integer-day cases and exact process time changes have separate convention metadata and unit tests; no silently rounded year fraction is compared.

Financial sanity passes on the executed mandatory core slice within the original budgets, but is not a substitute for convergence/coverage. Homogeneity and physical-K FD data are retained. REFERENCE_UNCERTAINTY.json/npz contains route-pair matrices, max/median gaps and deviations from route median on available A/B/MP values. Unvalidated route values and finite-cutoff diagnostics are not rigorous intervals or certified labels.

The actual 31x31 R0/v=.04 core slice supports the disagreement contours; it is explicitly diagnostic, without full per-cell refinement certification. Failure maps use raw counts, and MP/Gamma/N/cutoff/v/tau figures preserve failed values. No sparse failed data were interpolated into fake dense contours.

The core decision fails on its own incomplete/unresolved evidence. Challenge failures do not automatically invalidate a separately valid core certificate. Nevertheless the current proposed objective also needs finite-x/v boundary information and v=0 compatibility, whose complete certification is absent. Labels remain unapproved.

Next numerical work is in colab/phase1b2_reference_escalation.ipynb: complete core then collar/OOD coverage, every retained failure/near-failure MP escalation, external analytic/PDE axis refinement, and renewed review under unchanged tolerances. No neural code is invoked. No Domain v2 is recommended before that evidence exists. Stop after Phase1B.2.
