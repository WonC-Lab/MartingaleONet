# Phase 1A research design: reliable parametric Heston surrogates

Design date: 2026-10-07, Asia/Seoul. Status: specification only; no new engine has passed validation, no new labels exist, and no neural training is authorized before the reference gate. Phase 0 remains binding evidence: [audit report](../audit/PHASE0_FORENSIC_AUDIT.md), [issue matrix](../audit/reviewer_issue_matrix.md), [CSV manifest](../audit/artifact_manifest.csv), [JSON manifest](../audit/artifact_manifest.json).

## Decision and research question

Proceed to reference implementation and validation only. Do not proceed to model training or claim a novel architecture. Ask: under a specified risk-neutral Heston family, can a parametric surrogate jointly meet predeclared budgets for values, Delta/Gamma/variance sensitivity, measured static admissibility and stock-hedging deviation, at useful amortized throughput? The output is a measured reliability frontier with explicit failure regions, not a single accuracy or speed number.

Price accuracy, derivative fidelity and admissibility require distinct evidence. This distinction motivates the study but is not itself new; [NOVELTY_MOAT.md](NOVELTY_MOAT.md) records close competitors and a conditional novelty gate. The useful proposed contribution is a reference-uncertainty-aware, controlled comparison of these objectives, with an independent evidence/certification layer and a path-weighted link to hedge deviation. Successful training is an empirical hypothesis.

## Legacy disposition

Exclude TimeGAN, temporal martingale normalization, P-to-Q claims, synthetic crisis/TQQQ validation, real-market calibration, old percentages/speedups/FNO/PINN results, constructed baseline TV, synthetic convergence Figure 9 and every pricing metric obtained with defective labels from the new paper. Keep all old files intact as historical audit material. `src/heston_solver.py` and Phase 0's shared-CF probability crosscheck must not be imported into the new reference stack or promoted into ground truth. Phase 0 Colab reruns are optional historical diagnosis, not prerequisites for a new certified dataset. Do not rewrite README/manuscript or physically move legacy files in Phase 1A.

## Mathematical object and units

Assume a chosen pricing measure Q from the outset; it is an input model assumption, not an estimated change of measure. With no dividends:

\[
dS_t=rS_tdt+S_t\sqrt{v_t}dW_t^S,\quad
dv_t=\kappa(\theta-v_t)dt+\sigma\sqrt{v_t}dW_t^v,\quad
d\langle W^S,W^v\rangle_t=\rho dt.
\]

State variables: S>0,v>=0,current time t. Contract variables: K>0,expiry T,European call payoff; tau=T-t. Model parameters p=(kappa,theta,sigma,rho,r); v is the current state, not a static fifth model coefficient. Define

\[
G_H(p)(S,v,K,\tau)=E^Q[e^{-r\tau}(S_{t+\tau}-K)^+\mid S_t=S,v_t=v].
\]

This is a finite-dimensional parameter-to-function map, evaluated by a branch/trunk network. It is not a demonstrated advantage over ordinary finite-dimensional regression; the MLP comparison is mandatory. Constant rates, time-homogeneous parameters and zero dividends are deliberate scope restrictions. K rescales currency; all maturity units are years, variance annualized, sigma is vol-of-variance, and r annual continuously compounded rate.

Let x=log(S/K), c_p(x,v,tau)=G_H(p)/K. Exact homogeneity is built into evaluation as V=Kc. The PDE is

\[
\partial_\tau c=\tfrac12v c_{xx}+\rho\sigma v c_{xv}
+\tfrac12\sigma^2v c_{vv}+(r-\tfrac12v)c_x
+\kappa(\theta-v)c_v-rc.
\]

Equivalently V_tau=.5vS²V_SS+rho*sigma*v*S*V_Sv+.5sigma²vV_vv+rSV_S+kappa(theta-v)V_v-rV. Payoff c(x,v,0)=(e^x-1)^+, V(0,v,K,tau)=0, V~S-Ke^{-rtau} as S->infinity for fixed v,tau,p. These asymptotic statements are not exact finite-S boundary labels. Use certified values at artificial finite x/v boundaries. At v=0, diffusion vanishes and the compatible limiting equation is c_tau=r c_x+kappa*theta c_v-r c; zero variance now does not imply a deterministic future variance. Do not impose V=max(S-Ke^{-rtau},0) for positive kappa*theta. Finite v_max is an artificial boundary and uses certified reference values, not a claimed physical boundary law.

Theory uses interior compact sets v>=v_min>0,tau>=tau_min>0,|rho|<=rho_max<1 and smooth coefficients; the diffusion matrix in (x,v) has positive determinant sigma²v²(1-rho²)/4. Exact maturity payoff is kinked, so C² claims cannot include tau=0,ATM. v=0/Feller-violating regimes require separate boundary analysis and are not covered by a uniform elliptic theorem. Feller 2kappa*theta>=sigma² is reported, not used to discard hard experiments. Require positive kappa,theta,sigma and the true-martingale/moment integrability assumptions needed for payoff expectation and differentiation; verify first CF moment and numerical integrability across the declared domain.

## Domain v1

| Quantity | Training support | Boundary / challenge population |
|---|---|---|
| x | [-.7,.7] | guard-domain[-1.2,1.2]; OOD outside training |
| v | [.01,.16] | reference collar[0,.25]; exact0 separate |
| tau | [1/252,2] | payoff0; short1/1000; long3–5 |
| kappa | [.5,4] | OOD .2–.5 and4–6 |
| theta | [.02,.12] | OOD .005–.02 and .12–.2 |
| sigma | [.1,.8] | OOD .8–1.2 |
| rho | [-.9,-.1] | OOD[-.99,-.9] and[0,.5] |
| r | [0,.08] | negative-rate experiment deferred |
| K | normalized1 | physical evaluation50/100/200, homogeneity check |

This support is provisional engineering scope, not a guarantee of numerical certification. Domain changes require a versioned preregistration before final test access. Theory collars and learning support must be distinguished; guard-domain reference queries enable out-of-support diagnostics, not unannounced training. Parameters may violate Feller. Data are certified jointly on the retained region; failed certification is recorded and cannot be silently deleted from test statistics.

## Admissibility: what is and is not guaranteed

For q=0 European calls under a true-martingale Heston stock: max(S-Ke^{-rtau},0)<=V<=S; 0<=V_S<=1; V_SS>=0; -e^{-rtau}<=V_K<=0; V_KK>=0. Strike conditions are necessary for vertical-spread/butterfly static admissibility at a fixed maturity. Spot conditions are comparative statics across hypothetical states in this model; they are not the same traded strike-arbitrage condition. In x variables:

\[
\Delta=e^{-x}c_x,\quad K\Gamma=e^{-2x}(c_{xx}-c_x),\quad
V_K=c-c_x,\quad K V_{KK}=c_{xx}-c_x,\quad V_v=Kc_v.
\]

Thus spot and strike convexity share one curvature inequality when homogeneity is exact. Do not train duplicate independent convexity losses. Report both in physical units as a coordinate-consistency test. State-variance Greek nu=V_v and initial instantaneous-volatility sensitivity Vega_s=2sqrt(v)V_v at fixed p are distinct; none is the Heston parameter sigma sensitivity.

Necessary local inequalities on sampled points are not sufficient for a coherent global surface or dynamic no-arbitrage. For a full strike slice on K in(0,infinity), convexity, slope bounds, C(0)=S,C(infinity)=0 give a nonnegative implied terminal measure; with C'(0+)=-e^{-rtau} and proper limiting conditions it has mass1 and meanSe^{rtau}. Across maturities require compatibility/convex order of the appropriate normalized distributions; measured slice constraints alone do not establish it. Because r>=0,q=0, calendar call monotonicity follows from conditional Jensen and the martingale stock, and is a secondary diagnostic. Do not generalize that assertion to negative rates/dividends without reformulation. Global homogeneity is the only structural identity enforced in this design. No global convexity or arbitrage-free-network guarantee is claimed.

## Architecture and objective candidate

All continuous surrogates use smooth Tanh or smooth Softplus hidden activations; no final ReLU/clipping and no kinked intrinsic-plus-positive-correction ansatz. Use scaled x,v,tau and p with invertible transforms and correct AD chain rules. Branch p, trunk(x,v,tau), normalized scalar c; hidden widths/rank selected through development-only capacity controls. Use the same normalized function class for vanilla, physics and proposed operator arms. Exact payoff is supervised at tau=0; the network need not be C² there. No Black–Scholes carrier is presumed novel or mandatory; that mechanism already has close literature competitors.

\[
L=\lambda_dL_d+\lambda_pL_p+\lambda_bL_b
+\lambda_gL_g+\lambda_sL_s.
\]

| Term | Information and sampling | Purpose / pathology / cost |
|---|---|---|
| L_d | certified c labels; training mixture defined below | value anchor; nearzero relative division unstable, use K-normalized MSE; one forward |
| L_p | dimensionless full Heston residual on nonterminal interior | coupling of v,x,tau; small empirical loss is not continuum control; second state AD plus parameter backprop costs |
| L_b | exact terminal, exact S=0 external check, certified finite-x/v traces, limiting v=0 equation | uniqueness/boundary consistency; payoff kink never differentiated in PDE; reference trace error audited |
| L_g | certified Delta, KGamma and nu/K on a 20% training subset; stable fixed scales from training RMS with floor | justified by known differential learning and absent derivative guarantee from values; noisy second derivatives can dominate; extra second-state derivatives and labels |
| L_s | squared negative part of KGamma plus strike slope below -discount/above0 on shape collocation | penalize common curvature and traded strike constraints; soft penalty is no architecture proof; compute c_x,c_xx |

Default shape includes these three shortfall functions only; price bounds/spot slope/calendar remain diagnostics first. Add a bound penalty only if development failures justify it, then record an explicit extra arm. Greek scales are trained-data statistics frozen in config; no per-test-label scaling. PDE scaling uses fixed characteristic units tau*=1year,v*=.04 and derivatives through the coordinate map, never arbitrary residual clipping. Begin with normalized lambda_d=lambda_b=1 and a bounded development grid lambda_p in{.1,1},lambda_g in{.1,1},lambda_s in{.1,1}; select under price noninferiority and development Greek/violation objectives, not test accuracy. Use a declared subset of at most12 candidates per arm, identical tuning wall-time budget; exact schedule must be frozen before Phase1C. Do not auto-enable differentiated PDE residuals (third/fourth order): include at most one budget-matched conceptual-competitor control if needed.

The main proposal is physics+certified derivative supervision+minimal shape treatment with an independent reliability evaluation. It is allowed to fail or to be matched by differential learning. Its scientific value depends on a new controlled result, not on branding this sum as novel.

## Collocation and datasets

Training parameter designs use independently Owen-scrambled Sobol sequences. Initially use 256 parameter blocks: 192 broad-support blocks and 64 near-Feller blocks obtained by recorded rejection sampling, where near Feller means |2kappa*theta/sigma²-1|<=.1. Within each block, state queries use a 50% broad component (x uniform, tau log-uniform), 25% ATM-short component (|x|<=.1, tau<=.1), and 25% low-variance component (v in [.01,.02]). All other coordinates follow their stated support transforms. Record mixture choices, rejected draws and achieved counts. Include Feller violations rather than filtering them away. This training distribution differs explicitly from the broad IID evaluation population. Avoid adaptive sampling in the main factorial experiment; a development-only adaptive arm can be separately budgeted with full sample-history logging.

Per prospective optimization step: data batch512; interior1024; terminal256; finite-x boundaries256 total (128 each); finite-v boundaries256 total (128 each); shape512; derivative-labelled subset128 of data. These are initial config proposals for Phase1C profiling, not executed schedules. v=0 boundary draws use the limiting PDE; guard-domain v_max=.25 and x=±1.2 traces use certified values. Training states stay in the stated support plus separately tagged BC points. Use Sobol rescrambling per epoch for physics with logged seeds/counters, immutable supervised labels, and no final-test reuse. Do not differentiate exact ATM terminal payoff; shape/PDE tau>=1/252 and v>0 only. All arms share supervised labels and sampling budgets when a term is active; inactive terms have no hidden extra labels.

Scaling initially5k/10k/50k/100k unique(p,state) labelled rows, nested training subsets,3 paired seeds. Hold500k/1M in reserve only if100k has unsaturated learning curves and a measured reference-cost budget permits. Main comparison50k labels,5 paired initialization seeds. Labels can be grouped into256 parameter blocks with state queries; training sizes count price observations, not unique operator inputs. Enforce zero overlap of full parameter blocks between train/development/final tests. Scaling may append training blocks; tests never change.

Immutable development:64 parameter blocks x128 queries=8192; separate tuning stress set64x64. Final interpolation:256 held-out parameter blocks x256 queries=65536; boundary:64 blocks x128 queries=8192; OOD:128 blocks x128=16384 across predeclared one-axis and joint shifts. Sample x,v,tau independently within each test block using IID draws for interpretable sampling inference; fixed deterministic diagnostic slices are additional descriptive grids. Test block seed keys3001/3002/3003, development2001/2002,train1001,collocation1101. These published seeds are for reproducibility, not license to inspect final labels during tuning. A separate sealed final evaluator releases aggregate results after checkpoint/config hashes freeze. Split manifests include block membership, coordinates, seeds and all hashes. Any certification failure stays in coverage denominators; metrics only on certified rows plus an explicit failed-coverage table. Failure rates trigger domain redesign before training, not favorable test exclusion.

## Workflow and gates

Phase1B is reference-only: new separate CF routes, convergence/Greek/cross-implementation checks, validation report and numerical-error metadata. Phase1C (future authorization) is data freeze and small pilot; Phase1D is user-run COLAB-HEAVY training and statistical evaluation. The framework is only specified here. [REFERENCE_ENGINE_SPEC.md](REFERENCE_ENGINE_SPEC.md) defines the training gate, [EXPERIMENT_MATRIX.md](EXPERIMENT_MATRIX.md) defines E01–E11 and hedging/timing, and [HYPOTHESES.md](HYPOTHESES.md) declares possible refutations.

Single source of truth: immutable raw arrays -> schema-validated standardized records -> versioned metric aggregation -> tables/figures. Numerical values in prose must resolve to a metric ID. No hand-entered result labels. Each record contains experiment/run/model/checkpoint/split/reference IDs and hashes, full config, device/precision, coordinate/Greek units, sampler/RNG state and failure masks. No new manuscript figures are drawn until new experiments have results. [FIGURE_PLAN.md](FIGURE_PLAN.md), [TABLE_PLAN.md](TABLE_PLAN.md) specify prospective visual questions.

Main paper excludes real market data. A controlled synthetic-Heston benchmark is stronger for isolating fidelity than synthetic histories mislabeled as markets; external validity remains limited. A future market study would require European contracts or American pricing, dividends/corporate actions, bid/ask-aware losses, stale/crossed/zero quotes filtering, timestamps, curve conventions, verified IV inversion, calibration train/test separation and independent licensed data provenance. None is bundled into this study for appearance.

## Three candidate framings

| Candidate title | Central question / novelty candidate | Theory / experiment | Likely criticism |
|---|---|---|---|
| **When Accurate Prices Fail: Value, Greek and Admissibility Frontiers for Heston Surrogates** (recommended) | What evidence makes a price surrogate fit for derivative/hedge use? Controlled reliability frontiers, not a new loss claim | negative counterexamples and bounded-risk links; certified labels, strong differential competitors and paired hedges | evaluation study may be incremental; must identify a reproducible non-obvious tradeoff or useful certification rule |
| Physics-Informed Heston Operators with Derivative-Aware Reliability Assessment | Can combined objectives pass declared budgets? | restricted residual stability and norm/penalty links; factorial training comparison | reads as penalty engineering; reject this framing unless combined treatment beats strong differential/shape controls |
| From Price Error to Hedge Deviation: Auditing Parametric Heston Operators | Which diagnostics predict downstream stock-strategy error? | Ito-isometry hedge deviation with incompleteness caveat; common-path evidence | hedge metric depends on Q/path design; must report turnover and volatility-risk floor |

Recommend the first with model-development results subordinate to the evaluation question. Avoid “certified model” in the title: Phase1B numerical certification is tolerance-based, while continuous-network certificates remain conditional/restricted. The go/no-go decision is reference work GO; novelty and training readiness NOT YET ESTABLISHED. [RISK_REGISTER.md](RISK_REGISTER.md) includes hostile-review objections and design modifications.
