# Greek certification — incomplete

**No domain-wide Greek certificate.** 300 CORE physical-S/v five-point studies were executed; FD flags remain on 115 rows. Price, Delta, KGamma and Vv/K budgets are unchanged. Vega_s is not used to certify Vv at v=0.

All 15 CORE rows flagged for FD truncation/amplification were selected without deletion for additional MP work. See HP_GREEK_PRIORITY.json for evaluated/planned counts. Additional studies use 3-/5-point schemes, Richardson3/5 and ten spot steps from .02 to 1e-7. At v=0 all variance stencils are right-sided. Fifty/eighty/120-digit last-step stencil checks are in FD_PRECISION_CONVERGENCE.json.

Unique selected-input Gamma evidence counts: {'NUMERICALLY_RESOLVED': 17, 'UNRESOLVED': 1}. NUMERICALLY_RESOLVED means the recorded precision/degree/cutoff, cross-route and FD evidence meets the selected-point budgets; it is not a certified domain or authorization for training. No BOUNDARY_SINGULAR diagnosis is inferred solely from unstable quadrature.

The core ATM example has Gamma about 1.8801037393561391. Float64 FD5 goes to about 1.85499764 at h/S=1e-7, while MP FD tracks the analytic result. This is direct small-step cancellation evidence. Larger steps instead show truncation; the smallest float step is not chosen automatically. The nominal six-step legacy FD grid also fails some short-core peaks despite extremely small final A/B Greek gaps; additional MP physical steps investigate those points.

The full predeclared 256 reliably validated derivative requirement is not established simply by performing 300 checks. Full-core derivative/FD resolution and external refined PDE evidence are still required. Raw Gamma estimates, within-method discrepancies, coefficients and price uncertainty propagation are preserved. FD agreement with the same finite MP integration grid cannot by itself establish its tail accuracy.
