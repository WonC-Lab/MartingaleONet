# Table plan and single numerical source

These are prospective schemas. No table is filled with legacy results. Every numerical cell is rendered from the same metric ID used by the corresponding figure. Not-run, failed and uncertified results have explicit reasons and counts.

| ID | Question and columns | Source | Figures |
|---|---|---|---|
| T01 | Reference domain, price/Greek tolerances, convergence settings, gaps, uncertainty, coverage and external-check scope | E01 validation records | F01 |
| T02 | Split/hash, parameter blocks, rows, ranges, price/Greek labels, failures, generation/training/tuning costs | Dataset manifests and E02/E03 configs | F07 |
| T03 | Model/checkpoint/seeds; price nRMSE/nMAE/p95; Delta/KGamma/nu errors; shape metrics; failures and cost | E03–E05/E11 shared aggregates | F02–F05 |
| T04 | PDE/Greek/shape toggles, shared initialization, information/compute budgets, price noninferiority and paired effects | E06 paired aggregates | F08 |
| T05 | Interpolation/boundary/OOD tags, Feller class, errors, shape metrics, reference coverage and seed uncertainty | E07/E11 | F06 |
| T06 | Strategy/state inputs, regime, cost/frequency, common premium, PnL mean/std/variance/RMSE, loss VaR/ES, turnover/cost and gain deviation | E08/E09 common-path ledgers | F09/F10 |
| T07 | Workload, hardware/threads/dtype, batch, price/Greek scope, resident/end-to-end latency, median/IQR/p95, throughput and crossover | E10 repetitions | F11 |
| T08 | H1–H6 effect, interval, practical threshold, adjusted test where applicable, decision and metric parents | E11 decision records | F02/F08 |

Definitions and units come from HYPOTHESES. Round only during rendering; compute ratios and intervals from unrounded metrics. Seed dispersion differs from contract PnL standard deviation. Spot and strike convexity cannot count as two independent wins under exact homogeneity. Numerical reference discrepancies are resolution evidence, not self-scored zero error.

Prose claims must agree with T08 and the underlying metric IDs. Manual edits invalidate export hashes and require regeneration. A publication export records every table/figure parent. Differences in population, cost, checkpoint, reference version or seed list block export. This mandatory contract is only specified in Phase 1A; its framework implementation is deferred.
