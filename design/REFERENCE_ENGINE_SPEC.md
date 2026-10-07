# Reference engine specification and validation gate

Status: proposed protocol, NOT CERTIFIED YET. No Phase1A engine computation or neural training. Certification here means reproducible numerical acceptance within a declared domain and tolerance, not interval-arithmetic proof for all real-valued inputs. Reject old labels and imports from `src/heston_solver.py`; the Phase0 alternate inversion shares its CF and is diagnostic only.

## Routes and independence

A: fresh float64 Heston probability pricing with stable logarithm/branch treatment, adaptive finite-interval quadrature and explicit tail extension. B: independent COS payoff expansion with separate CF implementation derived via the affine Riccati system and distinct truncation/summation. C: pinned QuantLib AnalyticHestonEngine for third-party implementation cross-check; a small pinned FdHestonVanillaEngine refinement set provides a non-Fourier external check. A/B are independent numerical inversions but share the Heston affine model; they are not statistically independent or immune to common derivation error. Separate code modules must not call a common copied CF function. Compare both CFs against a direct complex ODE Riccati solve on at least32 cases; do not treat agreement of two inversions sharing a buggy CF as certification.

Primary method sources: [Fang–Oosterlee COS paper](https://ir.cwi.nl/pub/13283/13283D.pdf), [Little Heston Trap](https://www.maths.univ-evry.fr/pages_perso/crepey/Equities/HestonTrap.pdf), [QuantLib analytic source](https://github.com/lballabio/QuantLib/blob/master/ql/pricingengines/vanilla/analytichestonengine.cpp), [QuantLib COS source](https://github.com/lballabio/QuantLib/blob/master/ql/pricingengines/vanilla/coshestonengine.cpp). These identify methods/cross-check candidates; Phase1B must pin actual dependency versions and commit hashes before accepting outputs. No claim that an external library is infallible.

## A: probability representation with explicit CF convention

Let Y=log(S_tau/S), psi(u)=E[exp(iuY)], and Phi(u)=exp(iu log S)*psi(u). No K or log(S/K) is hidden inside psi. Write b(u)=kappa-rho*sigma*iu, d(u)=sqrt(b²+sigma²(u²+iu)) with nonnegative real part, g=(b-d)/(b+d),

\[
\psi(u)=\exp\{iur\tau+C(u,\tau)+D(u,\tau)v\},
\]

\[
C=\frac{\kappa\theta}{\sigma^2}[(b-d)\tau-2\log\frac{1-ge^{-d\tau}}{1-g}],\qquad
D=\frac{b-d}{\sigma^2}\frac{1-e^{-d\tau}}{1-ge^{-d\tau}}.
\]

Use stable expm1/log1p forms near singular cancellation, branch-continuity diagnostics, and a separately implemented sigma->0 limit; never merely rely on a principal log without checks. Exact special values psi(0)=1,psi(-i)=exp(rtau) are tested/handled analytically instead of evaluating a removable 0/0 case. Large/small sigma and long maturity branch issues get explicit flags. Evaluate

\[
P_2=\tfrac12+\pi^{-1}\int_0^\infty\Re\frac{e^{-iu\log K}\Phi(u)}{iu}du,
\quad P_1=\tfrac12+\pi^{-1}\int_0^\infty\Re\frac{e^{-iu\log K}\Phi(u-i)}{iu\Phi(-i)}du,
\quad C_A=SP_1-Ke^{-r\tau}P_2.
\]

Derive/verify u=0 integrand limits from log-CF derivatives; no epsilon-tuned denominator. Cancellation in OTM price formation is an acceptance issue: independent OTM put/call representations or higher precision escalation may be needed. Log all raw unclipped values. Never apply max(price,intrinsic) as a numerical repair. Bounds are tests, not output transformations. A returned small negative value is a failed/roundoff-qualified raw result with uncertainty, not silently zeroed.

## B: COS pricing

Implement the affine ODE independently: D'=-(u²+iu)/2+(rho*sigma*iu-kappa)D+(sigma²/2)D², C'=kappa*theta*D, D(0)=C(0)=0, plus iur*tau. Production B may use its independently derived closed form after ODE validation; do not use one expensive ODE per frequency for the final throughput baseline. For X=log(S_tau/K), phi_X(u)=exp(iu*x)psi_B(u). Define uk=k*pi/(b-a), Ak=2/(b-a) Re[phi_X(uk) exp(-iuk*a)]. Payoff coefficients Vk=integral_a^b payoff(y) cos(uk(y-a))dy. Price is exp(-rtau)sum_k' AkVk; prime halves k=0. Payoff includes K explicitly. Use analytic integration of put payoff K(1-exp(y)) on[a,min(b,0)], empty support handled explicitly; put-call parity supplies call when stable. Deep OTM call cancellation is cross-checked with direct-call/alternative interval/high-precision computation, not inferred accurate from parity alone.

Start [a,b] from separately validated log-return cumulants c1,c2,c4, e.g. c1±L sqrt(c2+sqrt(abs(c4))) shifted by x, but this is a heuristic starting interval, not a tail-error proof. If cumulant estimates fail or c2<0 beyond tolerance, fail and investigate; do not sanitize by abs(c2). Extend intervals independently of N. Also compare a conservative interval based on CF/ODE cumulant differentiation. Separate truncation, coefficient and summation error, with compensated summation where required.

## Validation case catalog

Domain for normalizedK=1: x[-1.2,1.2],v[0,.25],tau{0,1/1000,1/252,.01,.1,.5,1,2,5}; training support is narrower. Primary exhaustive smoke catalog:6 parameter regimes x7 x-values x5 v-values x8 positive tau-values=1680 cases. x={-1.2,-.7,-.1,0,.1,.7,1.2};v={0,.005,.01,.04,.25};tau={1/1000,1/252,.01,.1,.5,1,2,5}. Regimes:

| ID | kappa,theta,sigma,rho,r | Purpose |
|---|---|---|
| R0 |2,.04,.3,-.7,.03| typical |
| R1 |1,.04,sqrt(.08),-.7,.03| Feller equality |
| R2 |1,.04,.27,-.7,.03| near-Feller above |
| R3 |1,.04,.30,-.7,.03| near-Feller below |
| R4 |.5,.04,1.2,-.99,.03| severe vol-of-vol / correlation / Feller failure |
| R5 |4,.12,.8,-.1,0| high variance / zero rate |

Add256 independently drawn parameter blocks x16state queries=4096 random certification points,64 hand-selected cancellation/branch cases and32 ODE-CF checks. Frozen certification design uses seed4101; no manuscript number targets. The full grid is future computation, not run in Phase1A. A256-case subset including every named regime,short/long,ATM/OTM/ITM is LOCAL-LIGHT; full iterative certifications are COLAB-HEAVY if resource profiling exceeds15minutes, CPU is acceptable. Store all fail cases. K50/100/200 homogeneity and direct-variable sensitivity checks on32cases ensure normalized representation is consistent.

## Convergence and acceptance

Normalize prices by K. Base price tolerance T_C=1e-8+1e-6*max(|c_A|,|c_B|); nearzero relative error is secondary and only reported when |c_ref|>=1e-5. Physical currency tolerance is K*T_C. These are design tolerances, not achieved precision. Numerical error should be <=10% of the smallest intended model improvement/effect; if not, tighten reference tolerances before training or refrain from ranking the models.

- A upper integration cutoffs U=64,128,256,512,1024,2048; adaptive absolute tolerances1e-9,1e-11,1e-13 with an independently varied subinterval mesh. Require last two extensions and last two accuracy refinements each change price by<=T_C/4. Tail oscillation and nonmonotonic convergence must trigger further extension/high precision, not early acceptance based on one small difference.
- B N=128,256,512,1024,2048,4096 and L=8,12,16,24,32, then further if needed. For each interval refine N to stability; for each N-stable solution independently extend interval. Require final two increments in each dimension<=T_C/4. Coupled N/L refinement alone is insufficient.
- Require |c_A-c_B|<=T_C; A/B error estimates from refinements each<=T_C/4. Agreement plus refinement is evidence, not a rigorous mathematical error interval.
- External analytic crosscheck on256cases to the same price tolerance where the external method demonstrably converges; calendar-time/day-count conventions must agree. External FD256cases use spatial/variance/time independent refinement; discrepancies assessed against its own looser measured error band, not used to lower A/B standards. If too expensive, start32FDcases and declare narrower non-Fourier coverage.
- Check CF normalization, conjugate symmetry on realu, first moment, payoff at tau0, put-call parity, homogeneity, price bounds and derivative inequalities with their own numerical uncertainty. Do not impose bounds by clipping. Verify martingale/variance simulation only when E08 is authorized; this is distinct from CF checks.
- Sigma0 deterministic-variance limit has integrated variance I=theta*tau+(v-theta)(1-exp(-kappa*tau))/kappa; compare Black–Scholes with volatility sqrt(I/tau), not blindly sqrt(v). Include kappa->0 analytical limit I=v*tau. T=0 exact payoff bypasses numerical inversion and is not a Greek certification point at ATM.

A row is PASS only if required convergence, cross-route, invariance and sanity checks pass; FAIL otherwise, INDETERMINATE for unresolved external/numerical precision. Distinguish pricePASS from each GreekPASS. All mandatory core smoke cases must pass before certified core labels are produced; extended-domain failures require a narrower versioned domain and re-review, never silent selection. At least99.9% random core price/Greek points must pass initial automated checks; all remaining cases are escalated and training remains blocked until each retained core region is resolved or explicitly removed through a preregistered domain change. Maintain a failure map including the rejected region and original counts. Any model-test coverage change occurs before training, not after model performance is seen.

## Reference Greeks and numerical independence

Define Delta=V_S, Gamma=V_SS, nu=V_v; also Vega_s=2sqrt(v)*nu for v>0. For normalized pricing validate Delta, KGamma,nu/K. At v=0 use right variance derivatives only if converged, separately tagged; Vega_s=0 there may conceal large nu, so do not substitute it for variance sensitivity.

A differentiate the integral with respect to S and v after verifying dominated differentiability on the interior; psi_v=D*psi. Since price is linear-homogeneous in S,K and CF phase contains logS, derive derivatives in physicalS or analytically apply chain rules. Analytic Delta agrees withP1 for this model; check this identity against independent finite differences. Gamma may be obtained from differentiated P1 integrals, with explicit integrability/refinement. B differentiate finite COS terms with a/b held fixed for a local Greek stencil; adapting intervals with the queried input can contaminate a finite-series derivative. Re-run convergence for Greek coefficients. Either analytical route requires implementation derivation notes and unit tests; AD of a fixed-node quadrature is a crosscheck only after node/interval stability.

Independent check: five-point central FD in physicalS, not accidentally x. For h, Delta≈(V(S-2h)-8V(S-h)+8V(S+h)-V(S+2h))/(12h); Gamma≈(-V(S+2h)+16V(S+h)-30V(S)+16V(S-h)-V(S-2h))/(12h²). Variance uses analogous five-point first derivative for v±2hv>0, high-order one-sided near0. Initial hS/S={.02,.01,.005,.0025,.00125,.000625}; hv/max(v,.01) same ladder. Use Richardson comparisons and the roundoff/truncation plateau, not smallesth by default. Price tolerance for each stencil must satisfy propagated numerical error<T_G/4 (sum absolute stencil coefficients times price uncertainty); gamma's1/h² amplification may require80digit pricing. Save everyh/stencil price and error bound. No generic complex-step on real-price Re/abs/branch/adaptive quadrature: those maps are nonholomorphic. Complex-step is allowed only on a demonstrated analytic integrand parameterization with full derivation, not a default shortcut.

Greek design tolerances: T_Delta=2e-6+1e-5|Delta_ref|; T_KGamma=2e-5+1e-4|KGamma_ref|; T_nu/K=2e-5+1e-4|nu_ref/K|. Require within-route plateau<=T_G/4 and cross-route agreement<=T_G, including the verified FD check on256cases. Near-expiry Gamma divergent behavior is physical and not compared with finite terminalATM Greek. Any region lacking trustworthy Greeks remains uncertified, no target placeholders.

## Phase1B deliverables and training gate

Implement only new `reference/` and `tests/reference/`, plus small `colab_phase1b/` validation runner if needed; do not create training scripts. APIs expose raw price/Greek, numeric error estimate, refinement parameters, convergence status, domain/version and route ID. Store `reference_validation/cases.parquet`, per-route raw refinements,Greek stencils,ODE-CF checks,external-engine outputs,`validation_report.json`,`REFERENCE_CERTIFICATE.md`,source/config hashes and environment lock. Depend on NumPy/SciPy/mpmath, optional pinned QuantLib, all float64 unless flagged high precision. Libraries must be frozen before execution; API availability is checked rather than assumed.

Approval gate: independent methods implemented, mandatory case results reviewed, price/Greek error metadata below their declared budgets, coverage explicit, external conventions aligned, deterministic rerun and numerical-error sensitivity passing. Gate remains NOT PASSED until actual artifacts exist. Dataset generation/model training needs a separate authorization after this review. Reference computation is not “model training”; legacy labels remain quarantined from all new joins.
