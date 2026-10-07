# Phase 0 forensic reproducibility and scientific-integrity audit

Date: 2026-10-07 (Asia/Seoul). Audited HEAD: `c07f9102fb8ebed466227dafe6683b67b4a64285`.

## Scope and evidence standard

Phase 0 only. No original source, figure, CSV or result JSON has been changed or deleted. No repository model was trained locally and no expensive experiment was run. New files are confined to `audit/` and `colab_phase0/`. This report distinguishes observed code behavior, numerical reproduction, visual evidence, and unresolved historical provenance. Reproducing an erroneous numerical output does not validate its scientific interpretation. Findings concern evidence and implementation; author intent is not inferred.

All 28 original tracked files were inspected, all ten PNGs were viewed, all JSON scalar leaves were catalogued, and the three reachable commits were inspected. The original working tree was clean. There is no AGENTS.md in the repository or inspected parent directories. There is no manuscript, reviewer letter, table source, historical environment lockfile, checkpoint, raw prediction/PnL array, actual training log, notebook, or test suite. `.gitignore` ignores LaTeX but no ignored manuscript was present. Original provenance therefore stops at source candidates and aggregate outputs for most trained experiments. User-supplied Table 3/6/7 descriptions are claims, not independently recovered manuscript content.

Inventory with file types, PRIMARY/DERIVED/ORPHANED/UNKNOWN classifications, SHA256, sizes and duplicate detection: [repository_inventory.json](repository_inventory.json). No duplicate original files by SHA256 were found. PRIMARY means source/configuration input, not scientifically correct. MANUALLY_EDITED flags indicate explicit synthetic construction; no arbitrary file-age inference is used. STALE is not assigned without a known superseding generation. `test_fig5.png` is ORPHANED; its producer and obsolescence are unknown. `.git` was examined through tracked trees and reachable history, not treated as experimental data.

[artifact_manifest.csv](artifact_manifest.csv) and [artifact_manifest.json](artifact_manifest.json) include every existing figure, aggregate JSON, each reported JSON scalar, dataset and major README/user-supplied table claim. Eighty entries use only the requested status vocabulary. Unknown checkpoint, runtime and configuration details are explicit. The manifest status REPRODUCED refers to the listed statistic, not exact historical raster pixels or full scientific validity. Reviewer identities are not supplied; [reviewer_issue_matrix.md](reviewer_issue_matrix.md) maps C1–C12 without inventing reviewer attribution.

## Executive finding

The repository does not currently substantiate the central claims of a trained risk-neutral TimeGAN, strict martingale/change-of-measure construction, genuine US option-chain calibration, fair PINN/FNO comparison, measured convergence, or the advertised 15,225x/59.5% improvements. Pricing labels themselves have a material non-ATM Fourier-normalization defect. Existing accuracy results are training-set fit against those labels, not held-out Heston accuracy. Historical trained-model Greek frequencies and pricing stratifications cannot be recovered from PNGs and aggregate JSONs.

The following failures **are reproducible**: synthetic CSV provenance; terminal TimeGAN mean near44.89 and displayed path peaks near3000; the limited stress metric; unhedged hedging standard deviation4.19656; arithmetic inconsistency of improvement claims; zero-PDE/dead-ReLU diagnostic behavior; and discrepancies between the original reference price and a separate inversion identity. Exact learned surfaces and model-dependent PnL remain pending user-run Colab experiments.

## Provenance graph

| Artifact | Source candidate/function | Inputs and generation | Missing or contradictory links |
|---|---|---|---|
| Figure1 / master pricing JSON | `src/run_paper1_experiments.py:21`, `run_experiment_1_deeponet_pricing_and_speed` | seed2026 -> 500 random Heston parameter/coordinate rows -> original Fourier labels -> 200 full-batch Adam steps -> same500 rows evaluated | no checkpoint/raw arrays; test is training set; labels defective |
| Figure2 | same file:122, `run_experiment_2_autograd_greeks` | Figure1 in-memory model -> first randomly sampled branch -> S70–130,T.1–2,K100,50x50 grid | no derivative arrays/model; no training at K !=100; part of S domain is extrapolation |
| Figure3 / mean_S_T | same file:178, `run_experiment_3_timegan_risk_neutral_paths` | fresh seed2026 -> newly initialized GRU -> Gaussian latent noise -> time-axis correction ->200x252 paths | no training, data, optimizer or checkpoint needed; this is an untrained generator |
| Figure4 | same file:218, `run_experiment_4_us_volatility_surface_calibration` | generated CSV last VIX -> hand-built smile/maturity formula | no option chains, IV inversion, fitting objective or calibrated parameters |
| Figure5 / hedging JSON | `src/hedging_engine.py:20` | separate fixed-branch5,000-label pricer ->150steps ->200 Heston paths,30days ->delta rebalancing | no pricer/PnL arrays; Figure5 histogram mixed cost generations |
| Figure6 / multi_asset JSON | `src/multi_asset_extension.py:66` |600 labels from correlated constant-volatility GBM MC ->400steps ->same training rows evaluated | not stochastic-volatility baskets or observed SPY/QQQ options; no arrays/checkpoint |
| Figure7 / stress JSON | `src/stress_test_leverage.py:18` | synthetic Gaussian returns in three parameter regimes ->same correction ->ratio-error metric | no crisis observations; generator network is instantiated but not used |
| Figure8 / ablation JSON | `src/ablation_study.py:52` |400 labels ->independent DeepONet/MLP/Tanh-regressor initialization ->150steps each ->training-set errors | no FNO; no component ablations; PINN has no PDE loss; baseline TV values invented as multiples |
| Figure9 | `src/plot_training_loss.py:5-16` |synthetic exponential curves + random noise + clipping ->plot | not a recorded optimization trace |
| test_fig5 | no producing reference in source/history |plain two-point line plot visually | committed in initial commit; likely test image, exact producer unknown |

All full-batch source execution is CPU inferred from CPU tensor constructors and `.numpy()` calls. The original physical CPU, Torch/NumPy versions and thread settings are unavailable. No saved configuration files exist; the configurations are embedded in code. The first commit introduces Figures1–8 and test_fig5 together; the second explicitly adds the synthetic Figure9 script. No older alternative Table3 generation is exposed by reachable Git history.

## C1 — Table3 versus Figure5

Figure5 values are directly supported by `hedging_results.json`: at10bps, auto std=2.4113460657, FDM std=2.7484351496, unhedged std=4.1965578019. These are `np.std(..., ddof=0)` of dollar PnL arrays. The plot visually agrees with the right-hand bars. Reconstructing the exact seed2026/200path/30step Heston simulation gives unhedged std=4.196557801943061, matching the JSON to roundoff. Initial premium is constant across paths and does not affect that standard deviation.

The user-reported Table3 stds1.842/.37–.45/.16–.18 occur nowhere in source, aggregate results or reachable historical README. No Table3 data, script, checkpoint, parameters or manuscript is present. **The root cause of the cross-table numerical generation difference is unresolved missing provenance**, not proven manual editing, a seed change, or a changed dataset. These hypotheses cannot be ranked from the available evidence. The Figure5 branch has a recoverable configuration, while the Table3 branch has none; they cannot be certified comparable.

Recovered Figure5 settings: S0=K=100,r=.03,T=30/252,Npaths=200,Nsteps=30,seed2026,kappa2,theta.04,sigma.3,rho-.7,v0.04,TC0/.001/.002. Payoff is one short European call; initial value is original solver price at ATM. No contract100 multiplier, position normalization or vega hedge is applied. Cash starts as premium minus delta stock value and initial transaction cost; interest is accrued during29 rebalances. No final cash interest for the last step is applied before expiration, while unhedged premium accrues30 steps; liquidation transaction cost is absent. These conventions affect means/comparability and are not repaired.

Additional confirmed errors:

- `src/hedging_engine.py:180-184`: histogram arrays remain from20bps after the loop, while title and legend select10bps. The saved figure mixes20bps distribution with10bps std labels.
- `src/hedging_engine.py:135-137`: FDM uses the fixed solver variance. Autograd receives current simulated variance at:131. This compares different pricing-state inputs, not just derivative methods. The autograd branch was trained only at fixedv0.04 and is extrapolated to varying variance.
- Training maturities start.05 but late hedging maturities drop below.05; spots can leave80–120. No extrapolation diagnostic is saved.
- Comments say Delta-Vega/deep hedging; implementation is fixed-rule delta rebalancing with no learned hedging policy or vega instrument.
- Reference solver defect described in C9 compromises FDM deltas. It is a candidate explanation for poor FDM performance, not an explanation for an absent Table3 generation.

Required computation: original model/PnL rerun COLAB-HEAVY; path-only std and inspection LOCAL-LIGHT; corrected strategy comparison NOT-NEEDED-YET.

## C2 — 59.5% reduction

The only narrative reference found is `README.md:14`; it calls59.5% a variance reduction. No code computes that percentage. All variance/std/PnL keyword hits are in README or hedging metric/plot code; numeric hits inside the CSV are incidental market-table digits. Exact origin cannot be established. All reachable README generations repeat the same claim.

Using stored JSON values, without selecting parameters to fit a target:

| TC | Std reduction vsFDM | Variance reduction vsFDM | Std reduction vsunhedged | Variance reduction vsunhedged |
|---|---:|---:|---:|---:|
|0bps|9.9558%|18.9204%|43.4123%|67.9783%|
|10bps|12.2648%|23.0253%|42.5399%|66.9834%|
|20bps|14.5384%|26.9631%|41.6328%|65.9327%|

Formulas are100(1-sigma_auto/sigma_baseline) and100(1-sigma_auto²/sigma_baseline²). None matches59.5. No claim is made that59.5 was definitely a mislabeled std statistic: the generating operands are absent. Evidence and recomputed values: `audit/local_diagnostics.json:hedging_reduction`. LOCAL-LIGHT completed.

## C3 — Autograd Greeks and static arbitrage

`src/deeponet_model.py:53` enforces only V>=0 by final ReLU. Tanh branch/trunk plus unconstrained inner product does not enforce spot/strike monotonicity, convexity, call bounds or0<=Delta<=1. Automatic differentiation is exact for the represented function within floating-point precision; it does not make that function a correct arbitrage-free price surface. ReLU kinks also need care when interpreting second derivatives.

Figure2 was visibly inspected: Gamma contains negative regions, and Delta bends downward at high spots. These are image observations only; raster shading is not sufficient to measure violation frequency, mean magnitude or coordinates accurately. The figure's checkpoint is missing. Therefore `audit/greek_constraint_violations.csv` contains explicit NEEDS_COLAB_HEAVY_RUN rows with sample_count0 and blank statistics, not fabricated zeros or randomly initialized model results.

The Colab pricing rerun captures a new checkpoint and a31x3x5 S/K/T diagnostic grid using the original Figure2 branch sample. It computes spot/strike first and second derivatives, Delta upper bound and call price bounds; logs frequency at tolerance1e-7, mean magnitude over all samples and violating samples, maximum and region. K80/120 and T.05 are explicitly identified as outside training support. It cannot retroactively become the historical Figure2 checkpoint. Additional branch/regime diagnostics can follow returned checkpoints, without any local training. Source calls `dV/dv0` Vega; conventional volatility sensitivity would require the chain-rule factor2sqrt(v0), so nomenclature should be precise.

## C4 — Implemented drift correction and theorem limits

`src/timegan_model.py:40-49` takes a tensor indexed(path i,time t,feature) and computes `mean(...,dim=1)`. The denominator is **a finite temporal mean within each path**, not a conditional expectation, population expectation, moving estimate, or cross-path minibatch mean at a time point.

Let G_it=exp(R_it), n=sequence length, m_i=(1/n)sum_tG_it, g=exp(rdt), epsilon=1e-8. The actual transformation is

`G_tilde_it = G_it*g/(m_i+epsilon)`

`R_prime_it = log(G_tilde_it+epsilon)`.

The gross ratio used in reconstructed price paths is exp(R_prime)=G_tilde+epsilon. Therefore its time-average per path is approximatelyg, with epsilon and float32 errors. It does not force a cross-sectional average at each step, much less E[S_(t+1)|F_t]=S_tg. It also uses future returns in m_i, so the corrected return depends on the entire sequence rather than an adapted online conditional correction. A two-path constant-return probe confirms which axis is normalized (`audit/local_diagnostics.json:correction_axis_probe`).

Ignoring epsilon, AM-GM gives product_tG_prime_it <= g^n, hence each path's terminal price <=S0exp(rT), with strict shrinkage whenever temporal returns vary. This explains a low terminal mean despite extreme intermediate spikes. The negative Jensen gap accumulates over252 periods. Neither an unconditional terminal expectation nor the conditional martingale property is established.

No Radon–Nikodym density, likelihood reweighting, Girsanov kernels, joint Brownian measure change, volatility risk-premium specification, or density-integrability check exists. The second generated feature is unused in price reconstruction. Naming synthetic outputs P* constructs no complete P->P* measure transformation. The manuscript theorem is not present, so its precise hypotheses/proof cannot be compared; the user-specified conditional conclusion is not implied by this implementation. LOCAL-LIGHT completed; new theory is NOT-NEEDED-YET.

## C5 — Synthetic-path failure

The full original252-step path generator is lightweight enough to rerun on CPU. Seed2026, S0=100,r=.03,dt=1/252,T=1,Npaths=200,feature_dim2,hidden_dim32,two-layer GRU,default hidden_dim_lstm32. No return standardization/denormalization, real-data training or generator checkpoint exists. It is initialized and sampled immediately at `src/run_paper1_experiments.py:187-189`.

| Terminal statistic | Local result |
|---|---:|
| Theoretical mean S0exp(rT) |103.0454533954|
| Mean |44.8918150806|
| Median |44.5945224762|
| Std (ddof0) |5.9826817996|
| Min / max |24.2368602753 /59.7982635498|
| q1 /q5 /q25 |32.2143305206 /35.6675285339 /40.5906724930|
| q75 /q95 /q99 |48.9319534302 /54.9047548294 /58.1845027542|
| Peak among first30 plotted paths, at any time |2972.4116210938|
| Peak among all200 paths, at any time |11699.416015625|

Stored mean44.8918523884 differs by3.73e-5, consistent with runtime floating-point differences. Stored terminal growth error.5815360101 reruns as.5815363831. The reviewer mean44.89 and plotted extreme near3000 are reproduced. Those extremes are **intermediate**, not terminal; the distinction resolves the seemingly incompatible terminal maximum. Root cause is untrained unconstrained returns plus the temporal normalization/Jensen contraction, not a trained TimeGAN failure after calibration. Raw local paths: `audit/timegan_local_paths.npz`; full statistics and environment: `audit/local_diagnostics.json`.

## C6 — Martingale violation metrics

Master summary: `abs(mean_i(S_iT/S0)-exp(rT))`, absolute unconditional terminal growth-ratio error. It is dimensionless and not divided by exp(rT). The corresponding dollar terminal expectation error is100 times the reported quantity.

Stress script: for t=0,...,29, `e_t=abs(mean_i(S_i,t+1/S_it)-exp(rdt))`; stored `corrected_martingale_error=mean_te_t`, `max_error=max_te_t`. Raw metric has the same mean absolute definition on raw gross ratios. This is an aggregate **unconditional one-step gross-ratio** moment error; it is not a conditional error, terminal price error, relative error, or proof of discounted-price martingality.

Local reproduction of corrected means: standard.0002719427192, crash.0008890013373, leveraged.0014492753405, versus stored.0002719428008/.0008890011891/.0014492751612. Differences are below2e-10. The temporal correction approximately preserves an overall path/time gross mean, but averaging absolute cross-sectional errors remains nonzero; strong claims cannot be inferred from small numbers. Terminal means at30days are100.226882/98.636036/97.918309 instead of target100exp(.03*30/252)≈100.3578. Synthetic Gaussian vol/drift regimes are not empirical COVID/TQQQ data, and no leveraged-ETF financing/reset mechanism is modeled. Table6 itself is absent; linking its exact cells is pending, though the candidate stress metric is fully traced. LOCAL-LIGHT completed.

## C7 — PINN collapse

`src/ablation_study.py:36-50` defines a Tanh regressor with final ReLU. Its loop at:114-121 minimizes **only supervised mean-squared price error** with Adam(lr.003),150full-batch steps on400 rows. There is no PDE residual, terminal-payoff loss, spatial-boundary loss, T=0 sampling, boundary sampling, separate loss weights or input normalization. Thus this experiment is not a standard physics-informed baseline despite its name. Inputs S/K≈100 enter unnormalized Tanh layers and can saturate. The output is clipped by ReLU.

Stored MAPE99.9999106 is compatible with zero predictions when denominator uses price+1e-5, but raw historical predictions are missing. No multiple seeds/std estimate exists to substantiate “100.00±0.00”. The exact historical optimizer collapse mechanism is not proven.

A controlled lightweight dead-output probe sets the last pre-ReLU output negative: predictions0, MSE250 on targets10/20, and all parameter gradients0. This establishes a dead-ReLU stationary trap with **positive loss**, not that V=0 minimizes the implemented supervised objective. Separately the homogeneous DeepONet PDE residual at an intentionally constructed zero surface is exactly0; no terminal/boundary condition in that residual excludes the trivial solution. The proposed supervised data term does penalize zero prices. These are diagnostic constructions, explicitly not reconstructed historical models. Full baseline rerun is COLAB-HEAVY; the probes are LOCAL-LIGHT completed.

## C8 — Ablations and mixed generations

No Table7 component variants exist in source or JSON. `ablation_study.py` compares three architectures; it does not remove Greeks, correction or downstream blocks from a fixed operator. The400-sample DeepONet is initialized and trained independently from the500-sample/200step master pricer and5,000-label hedging pricer. A single nominal seed2026 does not make them identical: dataset sizes, random-number consumption, initialization order, optimization steps and parameter inputs differ.

README proposed RMSE1.1794/MAPE10.07 are master-pipeline values, but GammaTV.2064 is the independently trained ablation operator. Actual ablation RMSE1.328777/MAPE11.024347 differ. Those quantities should not be presented as one evaluation of one checkpoint.

`src/ablation_study.py:163-164` assigns PINN TV=proposedTV*1.8 and MLP TV=proposedTV*3.2. The JSON confirms exact multiplication. These are unmeasured fabricated baseline metrics in code, regardless of whether they were intended as placeholders. FDM self-RMSE/MAPE0 are literal values, not independent accuracy measurements. FNO README values1.8920/15.40/.4120 have no implementation, training script, outputs or checkpoint; source only mentions FNO in README.

If two variants retain the exact same price operator weights and inputs and change only derivative computation or downstream path/hedging processing, their pointwise prices and pricing RMSE on the same targets should be identical. Random retraining/data changes would confound such an ablation. No claim is made about absent Table7 exact provenance. Original architecture-baseline rerun is COLAB-HEAVY; implementing missing ablations/FNO is NOT-NEEDED-YET.

## C9 — Pricing floor and defective reference labels

Figure1 visually has a floor near6 for its observed low target-price points. Neither PNG nor aggregate summary contains recoverable paired price/parameter arrays. Exact floor, MAE, median absolute error, R² and bucketed errors are therefore pending. Existing RMSE/MAPE are measured on the same500 training rows (`src/run_paper1_experiments.py:80-95`), not held-out observations. Multi-asset and ablation evaluations also reuse training rows. All training strikes are100 and rates.03; generalization to arbitrary strike/rate is not experimentally established.

**New critical finding: original “ground truth” has a Fourier prefactor mismatch.** The characteristic function includes `x=log(S/K)` (`src/heston_solver.py:23,35`). Evaluating it at u-i/2 introduces a factor sqrt(S/K). Multiplying its integral by sqrt(SK) again (`:43`) double-counts that factor. Algebraically the represented shifted-CF identity would instead have prefactor K; equivalently the phase/damping could be separated before using sqrt(SK). This diagnosis does not modify the existing solver.

An audit-only probability inversion `S*P1-K*exp(-rT)*P2` uses the same Heston CF with separate integrals to provide an independent pricing identity. It agrees near ATM (where the prefactor error disappears) but disagrees materially off ATM:

| S,K,T | Original solver | Probability inversion | Difference |
|---|---:|---:|---:|
|80,100,.1|8.445827|.0000035|8.445824|
|90,100,.5|6.129155|1.592367|4.536788|
|100,100,1|9.242521|9.242521|≈1.25e-8|
|110,100,1|12.955447|16.601187|-3.645741|
|120,100,2|25.823547|29.643318|-3.819771|

Full25-point diagnostic is `audit/reference_solver_crosscheck.csv`; worst difference8.445588. At very short maturity, finite integration limits produce small residual errors, including tiny negative independently inverted OTM prices; those values are disclosed, not clipped to manufacture agreement. This is a separate inversion identity, **not a wholly independent characteristic function**, so it is not a replacement certified reference solver.

The original max(price,intrinsic,0) (`:44`) hides negative/too-low price errors and creates flat/linear pieces and derivative kinks. Its reference gamma is negative at some OTM points (e.g. S80,T.1 gives-.008378), and Figure8 reference Gamma visibly spikes. Calling its TV “FDM noise” confounds the incorrect formula and clipping with numerical derivative accuracy. Even perfect fit to these labels would not establish true Heston pricing accuracy. The learned price floor may combine malformed low-price labels and network saturation; exact contribution cannot be established without returned predictions and checkpoint. Correcting labels/retraining is Phase1 and was not performed.

`colab_phase0/analyze_returns.py` computes RMSE/MAE/original-epsilon MAPE/positive-price MAPE/median absolute error/R² and strata by true-label price, moneyness, maturity, sqrt(v0),rho,kappa,theta,vol-of-vol and Feller status from actual returned arrays only. It explicitly labels those targets as original-code labels and evaluation as in-sample.

## C10 — Speed claims

Stored JSON: DeepONet.0020070076ms/contract (=2.007us), Fourier4.4740629ms/contract, ratio2229.2207x. Total implied timing intervals: one500-contract neural batch≈1.003504ms;50 scalar Fourier calls≈223.703146ms. README15,225x and.1us do not match those values. The user-mentioned100x/1,250x have no traceable occurrence or benchmark source in the repository/history.

Recovered benchmark design (`src/run_paper1_experiments.py:80-96`): CPU tensor batch500, one forward with no_grad plus NumPy conversion, timed once with time.time; scalar loop of50 semi-analytic Fourier integrations, one timing interval. No explicit warm-up, repeated timed runs, error bars, hardware model, CPU thread settings, GPU benchmark or CUDA synchronization. No host-device transfer occurs in the coded CPU path. Prior training warms some neural kernels incidentally but is not a controlled warm-up protocol. Scalar reference timing includes per-contract solver construction. “FDM” is a misleading name for this Fourier integration implementation.

This is amortized CPU batch latency versus sequential scalar CPU latency on different counts, not batch1 real-time latency or a vectorized like-for-like speedup. Historical hardware/device logs are absent, but code does not substantiate a CPU/GPU comparison. Instrumentation in the Colab runner disturbs wall timing; returned timing fields cannot support a fresh speed claim. No large benchmark run is needed in Phase0. New fair benchmark: NOT-NEEDED-YET.

## C11 — Market data and calibration

`src/us_market_data.py:16-52` has no downloader or option-chain API: it generates2608 business-day rows with Gaussian SPY returns, correlated synthetic QQQ returns and VIX as15+500*abs(SPY return), a manually injected crash/spike, and clipping. The cache exactly matches this formula to CSV roundoff (max differences≈9.1e-13/1.36e-12/1.42e-14). Date range ends2024-12-31 despite filename2015_2025; `freq='B'` includes weekday exchange holidays. The comment claiming2516 rows is inaccurate. A10-year synthetic calendar cannot establish10-year authentic exchange data.

Figure4 formula is `last_synthetic_VIX/100 + .15*(1-K/S)^2 + .05*exp(-T)` (`src/run_paper1_experiments.py:234`). There is no option bid/ask, strike/expiry observations, American/European flag, IV inversion, fit to observed surfaces, calibration optimization or out-of-sample market pricing. Only the last synthetic VIX value enters the plotted surface; no10-year surface fitting occurs.

| Claim | Classification | Evidence |
|---|---|---|
|Authentic SPY/QQQ/VIX history|UNSUPPORTED|Cached CSV is numerically reconstructed synthetic data|
|Real option chains/observed market IV|UNSUPPORTED|No chain schema, provider, calls or chain dataset|
|US volatility-surface calibration|UNSUPPORTED|Hand-built formula; no calibration objective/parameters|
|Synthetic Heston experiments|SUPPORTED as implemented generation only|Fourier labels and Heston path simulator exist; pricing defect limits validity|
|Multi-asset synthetic pricing prototype|PARTIALLY_SUPPORTED|Two-asset constant-vol GBM model/data; in-sample trained result lacks checkpoint|
|Genuine SPY option validation / manuscript exact market table|NOT_TRACEABLE|No manuscript/table/actual contract observations|

For the real-market interpretation, standard ETF/ETP options have American exercise and physical settlement ([Cboe product specification](https://www.cboe.com/exchange-traded-stock)); this matters for standard SPY options. The repository European call solver has no dividend input or early-exercise adjustment. It does **not actually price observed American SPY contracts**, because no such observations are supplied; presenting the synthetic European calculation as empirical SPY validation would omit those contract differences. LOCAL-LIGHT evidence completed; gathering/calibrating real options is NOT-NEEDED-YET.

## C12 — Obsolete and test files

`test_fig5.png` was viewed: plain line from approximately(1,3) to(2,4), no hedge histograms, std labels or relation to Figure5. It is in the initial commit and no existing script references or produces it. It appears to be an accidentally committed plotting test, but exact producer, intent and obsolescence are not established. It cannot support or explain Table3 numerical claims. No analogous filenames, hidden model caches, notebooks, temporary experiment files, test data or duplicated originals were found. The synthetic Figure9 and mixed-generation README metrics are separate integrity issues rather than assumed stale files. Everything is preserved.

## Phase0D — additional scientific sanity checks

- Non-dividend European bounds used: max(S-Kexp(-rT),0)<=V<=S. Monotonicity/convexity in spot and strike and0<=Delta<=1 are required diagnostics; they are not enforced by the architecture. Historical learned-grid measurements are pending and clearly marked.
- Feller2kappa*theta>=sigma² fails for93/500 (18.6%) of the original master seed's sampled parameter rows. Fixed hedge parameters have margin.07>0. Feller failure does not invalidate the Heston model; it affects boundary accessibility and numerical handling. No filtering or zero-boundary accuracy analysis is present. Hedge variance Euler scheme clips at1e-6; its bias is not measured.
- Fixed-strike training, saturation-prone raw spot/strike inputs, sparse short-time support and changing-variance hedging are documented limitations. Saved outputs cannot establish where trained errors concentrate; ATM/deepOTM/deepITM/maturity/volatility/rho strata must await raw arrays. The audit does not infer stratified statistics from plotted dots.
- Homogeneous PDE admits zero solution; supervised data term remains essential. No separate terminal/boundary constraints appear in the proposed training objective. Automatic differentiation of v0 as a state variance deserves explicit interpretation, but this audit does not redesign the operator.
- Basket labels are correlated GBM with fixed sigmas, not Heston joint stochastic volatility. Correlation curves use separate noisy MC draws without confidence intervals; model and reference show a visible gap. No learned-checkpoint quantification is possible yet.

## Local execution, reproducibility and limitations

Run `python audit/run_local_diagnostics.py` from the repository root. This regenerates only audit diagnostics: CPU path NPZ, CSV checks, arithmetic, dead-ReLU/zero-PDE probes, reference crosscheck and pending Greek rows. It uses seed2026 and1Torch CPU thread. Environment: Python3.13.9, Torch2.12.1+cu126, NumPy2.3.5, Windows11. CUDA was detected but not used. Original requirements mention Python3.10+/Torch2.1 without a lockfile; bit-identical trained reruns across versions are not guaranteed.

Initial dependency import exposed duplicate OpenMP runtimes. Original scripts already set `KMP_DUPLICATE_LIB_OK=TRUE`; isolated diagnostics use the same workaround and record it. Numerical results are interpreted with tolerances, not asserted as exact historical binary reproduction. No original scientific code was patched to address this environment issue.

`audit/test_colab_instrumentation.py` tests only a scalar linear model with20Adam steps and an intentional interruption; this is a tiny checkpoint unit test, not original-model training. Results are recorded in `colab_instrumentation_validation.json`. AST parse checks cover generated Python. Full Colab experiments are **unexecuted**, and their outputs have not been fabricated.

## User-run Colab deliverables and compute classification

See [colab_phase0/README.md](../colab_phase0/README.md) for dependencies, ZIP-upload setup, exact execution, configuration, seeds, data preparation, checkpoints, resume, logging, expected files and returning results. `run_original_experiments.py` is a complete Colab-compatible script acting on an isolated source copy; it instruments only capture/checkpoint behavior. Each original experiment is selected by `--experiment`:

1. pricing: original500-label/200step generation, raw predictions, saved model, Figure2-compatible Greek diagnostic.
2. hedging: original5,000-label/150step operator, generated paths and raw PnL for each of0/10/20bps.
3. ablation: original400-label/150step architectures; historical-collapse comparison remains pending.
4. multi_asset: original600-label/400step correlated-GBM prototype with raw arrays and model.

All four are classified COLAB-HEAVY and left to the user. Original source is CPU-only; using a paid GPU Colab runtime does not make this runner a GPU rewrite. Changing `.numpy()`, noise construction or devices would change historical execution; no such adaptation is silently introduced. Resume stores full models/optimizers/RNG every10steps, regenerates deterministic data first, and restarts interrupted evaluation. Completed run markers skip finished experiments. Keep results externally when Colab runtime storage is lost.

After returning actual arrays, execute `python colab_phase0/analyze_returns.py audit/colab_returns/<run-id>` to compute pooled/stratified accuracy. No absent arrays are substituted or synthesized. Every rerun remains a new execution with a documented environment, not a recovered historical checkpoint.

LOCAL-LIGHT completed: recursive inventory/history/PNG review; all JSON extraction and arithmetic; market CSV formula replay; full untrained generator replay; synthetic stress replay; unhedged std; Fourier identity grid; dead-ReLU/zero-PDE probes; Feller sample check; runner checkpoint unit test. COLAB-HEAVY pending: four original trained experiment branches. NOT-NEEDED-YET: all design fixes, new theory, manuscript rewriting, label correction/retraining, new FNO/component ablations, market-data collection/calibration and a new large fair benchmark.

## What to remove, retain and consider after approval

Remove from a future manuscript unless replaced by traceable valid evidence:59.5% claim;15,225x/.1us and untraceable100x/1,250x; strict risk neutrality/conditional martingale/change-of-measure theorem claims tied to the current correction; trained-TimeGAN/real-crisis robustness claims; authentic market/calibration claims; synthetic Figure9 presented as training; FNO results; invented baselineTV; misleading PINN comparison; derivative-method-only interpretation of current hedge results; unsupported Table3/7 numbers. Exact manuscript edits require the manuscript and are not made here.

Retain as candidate components rather than established headline results: branch/trunk implementation, represented-function autograd machinery, parameterized synthetic-data prototype, original raw code as a reproducibility record, and the independently reproduced failure diagnostics. Existing RMSE/PnL outputs can be retained in an audit appendix as historical in-sample results against the defective reference, with explicit qualification; they currently do not establish pricing superiority.

Phase1 recommendation only: first recover missing manuscript/checkpoints and review returned original runs; then validate a reference solver before any new training; separately address measure/martingale interpretation, honest baselines and terminal/boundary conditions; finally consider held-out pricing/Greek/hedging evaluation and fair timing/real-contract data. None of these Phase1 actions has begun. Stop here pending user approval.
