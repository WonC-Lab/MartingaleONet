# Claim–evidence contract

All new empirical claims are PENDING. No old metric carries forward. Published claims must resolve to immutable raw arrays, metric IDs, split IDs, model/reference hashes and the listed experiment.

| ID | Candidate claim | Required evidence | Current status and limit | Experiment |
|---|---|---|---|---|
| C01 | Reference prices meet declared tolerances | Separate A/B CF implementations and inversions, convergence, ODE/external checks, failure coverage | Specified, not certified; old shared CF is insufficient | E01 training gate |
| C02 | Reference Delta/Gamma/variance sensitivity are resolved | Independent derivatives, FD plateaus, stencil error propagation and units | Pending; a smooth plot is not certification | E01 |
| C03 | Price convergence need not imply Greek convergence | Interior counterexample preserving price bounds and boundary traces | Design proof provided; classical mathematics, not new empirical evidence | Proposition B / E04 |
| C04 | Finite collocation does not certify continuum Greeks | Localized smooth perturbation and explicit capacity/coverage caveat | Function-space counterexample; no denial of valid continuum PDE stability | Proposition B2 / E04–E05 |
| C05 | Proposed treatment improves joint reliability | H2/H3/H4 against strong differential controls; matched information/compute | Pending; objective notation does not establish novelty | E03–E07/E11 |
| C06 | Necessary shape violations decrease | Physical shortfalls, thresholds, independent populations and uncertainty | Pending; zero observed violations is not global no-arbitrage | E05/E11 |
| C07 | Limited population or cell certificate applies | Valid IID bounds or verified Lipschitz bounds and coverage radius | Conditional; no full-domain certificate exists | Proposition D / E05 |
| C08 | Better Greeks improve stock hedging | Shared paths/current variance/premium; complete accounting and H5 tests | Pending; AD exactness is not replication or financial accuracy | E08–E09/E11 |
| C09 | Weighted Delta error predicts reference-hedge deviation | Path-weighted errors and paired gain differences under stated Q assumptions | Classical identity established; empirical predictive relationship pending | Proposition E / E08 |
| C10 | Useful amortized throughput | Same device, batches and accuracy; strong vectorization; repeated timings and costs | Pending; no legacy speedup or cross-device ratio | E10 |
| C11 | Scaling/generalization within Heston support | Parameter-block held-out splits, sizes/seeds, regime metrics and coverage | Pending; in-sample fit is insufficient | E02/E07/E11 |
| C12 | Homogeneity gives common spot/strike curvature | Definition V=Kc(log(S/K)) plus correct chain-rule checks | Mathematical identity; no global financial guarantee | E01/E05 |
| C13 | Real-market calibration or crisis robustness | Genuine data and exercise/dividend/quote/calibration protocol | Excluded from main study | NOT-NEEDED-YET |
| C14 | Trained TimeGAN or genuine measure transformation | Entirely new evidence/theory would be needed | Excluded; no legacy reuse | NOT-NEEDED-YET |

## Mandatory provenance

Raw pricing rows contain row ID, parameters, S/v/K/tau, both route prices/Greeks, uncertainty and status. Raw model rows add run/model/checkpoint hashes, prediction, derivative implementation, physical Greeks and constraint quantities. Path rows contain path/contract IDs, seed, simulator version, dates and S/v. Hedge ledgers contain strategy ID, Delta, cash, interest, trades, costs, payoff and terminal PnL. Timing rows contain session/device/thread/dtype/batch, workload, repetitions, elapsed time and transfer flags.

Schema validation checks types, units, IDs and numerical failures before aggregation. Aggregates contain metric-definition version, exact masks, row/block counts, failed coverage, uncertainty and parent hashes. Figures and tables request the same aggregate IDs; their annotations cannot use independently typed values. Prose improvement claims resolve to the hypothesis decision and the same metric parents.

Pipeline: RAW OUTPUT -> STANDARDIZED RESULT -> METRIC AGGREGATION -> TABLE AND FIGURE. Rendering applies rounding only at the last step. A mismatched checkpoint, split, cost rate, reference version or population blocks export.

New joins require the newly certified reference version. Root legacy JSON/CSV/PNG are never new benchmark inputs. A historical appendix may cite Phase 0 as an audit of defective results, not as new performance evidence. The framework is specified here and remains unimplemented.
