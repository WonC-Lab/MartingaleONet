# Figure architecture

No new result or manuscript figure is generated in Phase 1A. Future figures read immutable standardized arrays and metric IDs. Use vector PDF/SVG, consistent readable fonts, colorblind-safe palettes, explicit units and uncertainty. Mark failed reference points; never interpolate them into favorable zero-error regions.

| ID | Scientific question | Panels / form | Data dependencies | Interpretation limit |
|---|---|---|---|---|
| F01 | Is the reference resolved? | Cross-route/refinement curves; COS N–interval heatmap; Greek step-size plateaus; failure map | E01 raw refinements and stencils | Agreement alone is not a formal error bound |
| F02 | Can price-accurate models have unreliable Greeks? | Price nRMSE vs Gamma-error scatter; shape markers; seed bands and Pareto frontier | E03/E11 fixed-budget and development-selected price-matched checkpoints | Show failures and all seeds; do not select a favorable seed |
| F03 | Where do pricing errors concentrate? | Signed residual scatter; filled moneyness–maturity contours; price buckets | E03/E07 predictions, references and masks | Relative tail errors require explicit price floor |
| F04 | Which Greeks fail? | Separate Delta, KGamma and variance-sensitivity error contours; ATM-short zoom; reference uncertainty | E04 fixed grids and physical derivatives | Exclude terminal ATM Greeks; distinguish variance and volatility sensitivities |
| F05 | Which necessary shape constraints fail? | Curvature/strike-slope heatmaps; threshold curves; valid probability bounds or cell coverage | E05 quantities, thresholds and verification records | Sampled zero does not imply global admissibility; homogeneous curvature is one condition |
| F06 | What are the regime limits? | rho–sigma and Feller-ratio–variance heatmaps; counts/coverage strip | E07 parameter-block records | Separate interpolation/OOD; empty bins are not zero error |
| F07 | Are more labels or physics worth the cost? | Size vs value/Greek/shape learning curves; compute–reliability frontier | E02 nested sizes, seeds and costs | Show only executed sizes, including failures |
| F08 | Which treatment causes the effect? | Paired factorial effects and interactions; price noninferiority; information/compute budgets | E06/E11 paired aggregates | Retraining and evaluation checks are different ablations |
| F09 | Do Greek errors affect hedge deviation and tails? | PnL ECDFs; loss-tail quantiles; weighted Delta-risk scatter; volatility-risk control | E08 shared paths, ledgers and PnL | Reference Delta does not perfectly replicate Heston calls |
| F10 | Does the result survive costs? | Cost vs variance/ES/mean; turnover vs frequency; paired intervals | E09 per-cost ledgers | Cost labels come from the same dataset key as the plotted arrays |
| F11 | When does computation amortize? | Batch latency, per-contract latency and throughput curves; CPU/GPU panels; crossover range | E10 raw timing repetitions and total costs | Same-device comparisons only; prices and Greeks are separate workloads |

A main paper can combine F03/F04 and F09/F10 into approximately six to eight figures. Reference resolution and the joint reliability frontier are mandatory. Include unfavorable primary outcomes; supplementary plots retain the same metric parents. Prefer filled contours/heatmaps to 3D surfaces. A 3D truth surface is optional only if geometry itself answers a question. Synthetic training curves are forbidden; real optimization logs belong in a diagnostic supplement.

Predeclared slices: R0/R1/R4; v=.01/.04/.16; positive maturity. Use common color scales per quantity across models, mark any clipping, and report extrema. Seed aggregation uses medians and bands without smoothing away oscillatory Greeks. Captions include population, units, seed count and reference version.
