# Phase 1B.3 reference validation
CORE **FAIL**, BOUNDARY **FAIL**, CHALLENGE **FAIL**. Phase1C is not authorized.

Executed the exact original CORE catalog: 1734/1734, with 300 inherited SHA-verified deterministic rows and 1434 new Sobol rows. No Feller filtering, no altered Domain v1, no changed tolerance. Historical evidence: {'BYTE_IDENTICAL': 213}.

Original strict PASS 187; FAIL 1547. Separate resolution review: 173 failed rows numerically resolved, 1374 unresolved. Old strict statuses remain immutable. Flags (overlap): {'A_domain': 51, 'solver_error': 1531, 'FD_uncertainty_budget_unresolved': 240, 'FD_derivative_amplification_or_truncation': 15, 'strike_FD_derivative_unresolved': 4, 'B_N': 25}.

| Metric | Mean | Median | p95 | p99 | Maximum |
|---|---:|---:|---:|---:|---:|
| price | 1.41961e-15 | 2.22045e-16 | 8.21825e-16 | 1.78434e-15 | 1.86758e-12 |
| Delta | 1.93844e-13 | 3.33067e-16 | 1.46272e-15 | 3.27377e-14 | 1.98847e-10 |
| Gamma | 6.15091e-10 | 1.33227e-15 | 1.78219e-14 | 3.43156e-12 | 1.05203e-06 |
| Vv | 5.28186e-13 | 2.01228e-16 | 1.22125e-15 | 7.63399e-15 | 7.46993e-10 |


Every retained CORE failure/near-failure is explicitly planned: 1557 required MP inputs, 179 with available executed MP evidence, 179 numerically resolved. The local external-light batch is predeclared by aligned external inputs and cost (positive v, tau>=.1), not by achieved accuracy. Complete MP work is COLAB_HEAVY; it has not been claimed complete locally.

Supported QuantLib analytic cases within unchanged price budgets: 6/6; all 8 original inputs were attempted, with two exact v0=0 inputs rejected by the upstream model constraint. Independent PDE computations are retained even when their current gaps exceed budget. No PDE result is treated as absolute truth.

Training-required boundary strict coverage 600/600; {'FAIL': 566, 'PASS': 34}. Complete boundary MP and limiting-PDE compatibility remain unapproved. Evaluation-only OOD failures are preserved separately and do not decide CORE.

Tests, exact commands, resume behavior and the fresh-clone Colab workflow are documented in README.md. The Colab notebook writes reference_v3_colab/ and packages reference_v3_colab_results.zip. No remote result is claimed until actual execution. No neural training labels are generated.
