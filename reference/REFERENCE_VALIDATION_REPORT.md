# Phase 1B reference validation report

**Gate: FAIL. Phase 1C is not authorized.**

Executed scope: local, 25 actual points out of 5840 planned Domain v1 points. Row results: 3 PASS / 22 FAIL. Runtime 89.84 seconds. A row PASS in this diagnostic slice is not a domain certificate. No neural training or final training labels were generated.

## 1. Implemented routes

A: stable little-trap P1/P2 inversion, analytic spot/variance derivatives and explicit cutoff/tolerance/panel refinements. B: independently written scaled hyperbolic Riccati solution, Taylor-ODE cumulants, analytic COS put coefficients, parity call and direct-call diagnostic, fixed-interval Greeks. Direct numerical Riccati ODE is a third CF validation, not an external price engine. Optional pinned QuantLib analytic/PDE adapter is supplied.

## 2. Independence and conventions

Only input/output dataclasses are shared. Neither route imports the other or legacy pricing code. Both model the same risk-neutral Heston process (q=0), hence common model/derivation risk remains. CF is for log(ST/S), with strike only in inversion phase. A chooses Re(d)>=0 and log1p little-trap factors; B uses a scaled hyperbolic denominator. Branch continuity is tested on sampled frequencies/perturbations, not proven over all complex frequencies. Exact moment identities are imposed in production and independently evaluated by unforced ODE.

## 3. CF validation

32 direct complex ODE comparisons: maximum A error 3.10861e-14; B error 3.10861e-14. Moment ODE maximum error 0; conjugation maxima A/B 0/0. Dense-frequency A/B maximum error 2.17244e-15. `CF_CHECKS.json` preserves all cases and perturbation results. Unit tests cover normalization, moment, continuity, sigma=0 Black–Scholes limits and off-ATM regressions.

## 4–5. Price and Greek agreement

Physical K=1 in this executed slice. Statistics include failed points; no failures are dropped. Relative price error is omitted below normalized magnitude 1e-5.

| Absolute gap | Mean | Median | p95 | p99 | Maximum | Valid/missing |
|---|---:|---:|---:|---:|---:|---:|
| price | 3.19591e-06 | 1.25074e-16 | 1.87448e-05 | 4.61779e-05 | 5.36569e-05 | 25/0 |
| Delta | 0.0213751 | 2.22045e-16 | 0.0884575 | 0.346464 | 0.421228 | 25/0 |
| Gamma | 130.949 | 1.11022e-15 | 1007.79 | 1832.79 | 2013.78 | 25/0 |
| Vv | 0.0278109 | 1.4558e-16 | 0.274528 | 0.349488 | 0.351546 | 25/0 |

Relative mean/median/p95/p99/max and every worst input are in `validation_summary.json`; each raw row records absolute/relative gaps, normalized budgets, component statuses and all refinement/stencil values.

## 6. Worst cases and failure map

- price: max 5.36569e-05, input `{"S": 1.0, "K": 1, "x": 0, "v": 0, "tau": 0.001, "kappa": 2.0, "theta": 0.04, "sigma": 0.3, "rho": -0.7, "r": 0.03, "label": "local_R0"}`.
- Delta: max 0.421228, input `{"S": 1.0, "K": 1, "x": 0, "v": 0, "tau": 0.001, "kappa": 0.5, "theta": 0.04, "sigma": 1.2, "rho": -0.99, "r": 0.03, "label": "local_R4"}`.
- Gamma: max 2013.78, input `{"S": 1.0, "K": 1, "x": 0, "v": 0, "tau": 0.001, "kappa": 0.5, "theta": 0.04, "sigma": 1.2, "rho": -0.99, "r": 0.03, "label": "local_R4"}`.
- Vv: max 0.351546, input `{"S": 1.0, "K": 1, "x": 0, "v": 0, "tau": 0.001, "kappa": 0.5, "theta": 0.04, "sigma": 1.2, "rho": -0.99, "r": 0.03, "label": "local_R4"}`.

Failure flags (overlapping counts): `{'solver_error': 20, 'FD_uncertainty_budget_unresolved': 6, 'A_domain': 4, 'B_N': 2, 'B_interval': 2, 'cross_route_unknown': 3, 'A_financial_sanity': 1, 'B_financial_sanity': 2, 'FD_derivative_amplification_or_truncation': 2, 'strike_FD_derivative_unresolved': 3}`.

A strict 1e-13 request can report float64 roundoff even when the observed A/B price gap is tiny. These raw solver failures remain failures under this protocol. v=0/short-maturity cases have slow Fourier decay and unresolved domain/N convergence; severe R4 cases also fail interval stability. These are observed numerical-axis diagnoses; they do not prove that every discrepancy has a single identified cause. No branch failure is inferred without evidence. Cross-route discrepancies unexplained by recorded refinements remain unknown.

## 7. Financial sanity and homogeneity

A financial-sanity failing rows: 1; B failing rows: 2. Bounds, Delta, Gamma, V_K and V_KK use predeclared numerical budgets. Strike homogeneity identities and physical-K FD values are stored separately.

Maximum homogeneity relative discrepancy across K=50/100/200: 1.52095e-16. Prices normalize as V=K*c(x,v,tau,p); this scaling check alone cannot detect errors in normalized pricing.

## 8. Convergence and derivative reliability

Raw A tables vary U=64..2048, tolerance 1e-9..1e-13 and panel count 4/8/16. B independently varies N=64..4096 at every L=8/12/16/24/32. Five-point physical-S and variance stencils use all six predeclared steps; v=0 uses right differences. Each row contains within-route plateau changes, FD/analytic gaps and amplification diagnostics. Small-h agreement is not assumed sufficient. `BOUNDARY_ESCALATION.json` separately extends two short/v=0 cases through U=65536 and N=65536 at L=16/32, without replacing any failed row. Typical R0 prices approach agreement under these extensions, while R4 Gamma remains strongly unstable. The hard cases require further cutoff/term extension and/or independently verified high precision before labels can be certified. Analytic-v=0 values are retained as diagnostics; zero Vega_s does not establish a trustworthy Vv.

## 9. Reference uncertainty

`REFERENCE_UNCERTAINTY.npz/json` stores max pairwise A/B price/Greek differences (two routes here). This is a numerical discrepancy diagnostic, not a theorem, confidence interval or proven bound. Agreement can underestimate common bias. Failed rows are explicitly tagged and cannot be used as certified labels. FD propagation additionally uses the quadrature estimate, but remains a diagnostic envelope with no rigorous tail bound.

## 10. Coverage, dependencies and remaining risks

Grid version `domain-v1-grid-v1.1-sobol4101`: 1680 deterministic + 4096 Sobol +64 challenge points. The local 25-point slice does not satisfy the 256 smoke/FD requirement or full coverage. Full and external runs must occur in a separate output directory using the Colab notebook. External QuantLib available: False; executed: False. Local external results explicitly record the missing dependency, rather than treating ODE CF agreement as independent PDE validation. External integer-day cases align Actual365Fixed time exactly; FD axes refine independently and require a measured-error review. Route A currently supports float64 only; the exposed precision option rejects unsupported choices. High precision escalation is a remaining implementation task. No scientifically defensible revised subdomain can be certified from this slice; training support itself lacks full mandatory coverage.

Executed environment: `{'python': '3.13.9', 'numpy': '2.3.5', 'scipy': '1.16.3', 'matplotlib': '3.10.6', 'pytest': '8.4.2'}`. Exact module SHA256 values are recorded in metadata. `requirements-local.txt` records actual numerical dependencies; `requirements-colab.txt` is a proposed pinned environment that still needs execution validation. Figures are generated from raw outputs only. Sparse local heatmaps show sampled cells, without interpolated contours or invented dense coverage.

## 11–12. Gate and next authorization

**FAIL — Phase 1C dataset generation is not authorized; neural training remains prohibited.** Required next work is numerical escalation of retained failures, complete mandatory/FD coverage, and external analytic/PDE review under unchanged budgets. Do not use the full sweep to conceal the already observed failures, or loosen tolerance to restore earlier claims. This report concludes Phase1B with a failed reference gate; it is not a certificate.
