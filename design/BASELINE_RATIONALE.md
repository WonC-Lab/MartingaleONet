# Baseline rationale and fairness rules

No baseline is implemented or trained in Phase 1A. Retire all old reported baseline metrics. New surrogates share normalized coordinates, units and smooth activations. No final ReLU, price clipping or hidden reference correction is permitted.

| ID | Baseline | Scientific purpose | Information / objective | Fairness and limitations |
|---|---|---|---|---|
| B00 | Validated semi-analytic A / COS B | Numerical value and Greek standard; strong timing competitor | No training; independently converged routes | Report cross-route discrepancy, uncertainty and cost; no self-scored zero-error row |
| B01 | Smooth normalized MLP | Test whether branch/trunk factorization helps this finite-parametric task | Value and boundary labels | Parameter-count and compute controls; equal tuning budget |
| B02 | Vanilla DeepONet | Operator architecture control | Value and boundary labels | Same class and initial weights as physics/proposed arms |
| B03 | Physics-informed DeepONet | Isolate Heston residual information | Value + PDE + boundary | Full payoff, finite boundary and variance handling |
| B04 | Differential MLP | Strong established derivative-learning competitor | Value + boundary + certified Greek labels | Equal derivative-label count and generation cost |
| B05 | Differential DeepONet | Differential-only operator control | Value + boundary + Greeks | Same price/Greek information as proposed; no PDE or shape |
| B06 | Differential physics DeepONet | Isolate shape benefit beyond PDE and Greeks | Value + PDE + boundary + Greeks | Main strong comparator for H2/H4 |
| B07 | Shape physics DeepONet | Isolate shape without certified derivative supervision | Value + PDE + boundary + minimal shape | Shares class, initialization and active sampling streams with B03/B06/B08 |
| B08 | Proposed treatment | Test joint value–Greek–admissibility reliability | B06 plus minimal shape | Must beat or clarify useful tradeoffs against B06/B05; no assumed superiority |
| B09 | Generic smoothness control | Test whether benefits are ordinary regularization | B03 plus a development-selected smoothness regularizer | Match compute; no invented Greek-TV quantities |
| B10 | Sensitivity-PDE control | Compare a close conceptual extension suggested in prior work | B03 plus explicitly derived sensitivity residuals | Optional development-budget arm; expensive third/fourth derivatives; do not call it an exact published reproduction |

The main 2×2 factorial B03/B06/B07/B08 uses identical initial weights, price data, active collocation streams and step counts. Greek-labelled observations are identical where the Greek term is active. Changing an objective requires retraining. Changing AD to finite differences on the same frozen operator is an evaluation check with identical price predictions; it is not a new pricing model.

Capacity controls: parameter counts within 10% where feasible; equal validation trials and wall-time caps; at least one higher-capacity MLP sensitivity check. Report both equal-step and equal-wall-time comparisons because PDE/Greek terms change step costs. Tabulate label information and generation time, including derivative labels. Preserve unstable and failed runs with reasons rather than replacing seeds.

Exclude FNO from the main study: finite model parameters plus point queries do not provide a natural shared spatial-function-grid comparison. An FNO study would need a separate grid task, resolution protocol and matched outputs. Include a PINN only if it actually uses PDE, payoff and boundary conditions. A fixed-parameter PINN may be a small solver control, but its per-parameter training cost precludes an unqualified operator amortization comparison.

Document all literature adaptations. A DeepSVM-inspired protocol is not a full paper reproduction unless its architecture, loss, sampling and budget are reproduced; source availability and failures must be recorded. FI-DeepONet studies another local-volatility family, so conceptual comparison is mandatory but a Heston port is not a direct replication. A Black–Scholes carrier may be a control if justified, but it is prior art and not required new scope. See [novelty review](NOVELTY_MOAT.md).

Hedging controls: unhedged; analytic reference Delta A; independent COS/FD reference Delta B; learned B02/B03/B08 Delta, with B05/B06 where available. Include the instantaneous locally variance-minimizing reference stock position as a secondary incomplete-market control. AD and FD of the same learned function are derivative implementation checks, not proof that AD produces financially better Greeks.
