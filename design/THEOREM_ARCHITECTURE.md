# Smallest defensible mathematical architecture

Status: exact elementary statements and proof sketches below are part of the design, not novel theorem claims. No convergence theorem for neural optimization, global Heston boundary regularity, or full financial no-arbitrage guarantee is established. Minimum paper core is the counterexample plus a carefully scoped hedge-deviation identity; stability/norm/penalty results are supporting lemmas only if used in an actual empirical analysis.

Notation follows [research design](PHASE1A_RESEARCH_DESIGN.md). c is the normalized price; p is fixed for PDE theory, e=chat-c; L_p is the Heston spatial generator excluding -r. Network and reference share units and domains. Each parameter-to-function statement needs constants uniform on a compact parameter subset; integration over parameters is not automatically a PDE regularity theorem.

## A — restricted residual-to-value stability

Statement: on Q_T=Omega_xv x(0,T] with bounded Omega, v>=v_min>0,sigma>=sigma_min>0,|rho|<=rho_max<1,r>=0,smooth bounded coefficients, let c,chat be continuous on the parabolic closure and C^{2,1} inside. If exact c solves (partial_tau-L_p+r)c=0, error on initial/spatial parabolic boundary is bounded by b, and continuum residual R=(partial_tau-L_p+r)chat is bounded by delta, then

\[
\|e(\cdot,\tau)\|_\infty\le b+\tau\delta.
\]

Proof: ±(b+tau*delta) are super/sub-barriers for the linear operator since r>=0. Apply parabolic maximum principle; equivalently use a stopped Feynman–Kac expectation with boundary error and residual source. For a negative bounded r, an exponential factor is required; that case is not the main domain. Artificial-boundary label uncertainty contributes to b and cannot be omitted.

Tools: maximum principle/stopped diffusion; [PINN stability literature](https://arxiv.org/abs/2006.16144) provides broader context. Failure points: empirical L² residual is not continuum L-infinity; v=0/rho=±1 destroy stated ellipticity; payoff is nonsmooth at tau0; missing BC excludes uniqueness; unbounded domain needs different growth control. Empirical consequence: report separately residual distribution, terminal/boundary error and reference boundary uncertainty. Do not derive this bound from a minibatch loss. Status: standard lemma with proof above under stated hypotheses, not new general Heston theory.

## B — value convergence does not entail Greek or convexity convergence

Fix a certified interior option point z0 with tau0>0,v0>0,S0>0,K>0 where V is C², and a compact neighborhood U strictly inside price bounds. Assume a uniform positive margin m from upper/lower call bounds on U. Pick a smooth cutoff chi with support in U,0<=chi<=1,chi=1 near z0. Keep p fixed and K fixed initially. In a dimensionless spot coordinate s=S/K, define

\[
V_n=V+K n^{-3/2}\chi(z)\cos(n(s-s_0)).
\]

Uniform price error <=K n^{-3/2}->0. On a compact region with bounded cutoff derivatives, Delta error=O(n^{-1/2}) and converges uniformly, but at z0 Gamma error=-n^{1/2}/K, so Gamma diverges and becomes negative for large n. All perturbed prices remain within call bounds for K n^{-3/2}<m. Because cutoff vanishes near time/space boundaries, the exact payoff/boundary traces are unchanged. This gives a price-bounds-preserving interior counterexample, not just an abstract sinusoid.

For Delta failure replace perturbation by K n^{-1/2}chi sin(n(s-s0)). At z0 the Delta error=n^{1/2}, violating the upper Delta bound while price error still vanishes. To preserve homogeneity across K use V_n=K[c(x,v,tau)+n^{-3/2}chi(x,v,tau)cos(n(x-x0))]; at x0 the KGamma error is -e^{-2x0}sqrt(n), and Delta tends to zero error. The sin/n^{-1/2} analogue diverges in Delta. Chain-rule cutoff terms are bounded lower-order terms. Price bounds persist on a positive-margin compact normalized domain. These perturbations are candidate approximating functions, not admissible solutions of the exact Heston PDE.

Proof is explicit differentiation and margin control. Tools: smooth compact cutoffs and the classical discontinuity of differentiation in the C0 norm; no deep theorem needed. Failure points: a payoff kink or zero price-bound margin cannot be included; increasingly oscillatory functions may need increasing model capacity. It does not prove any particular trained network behaves this way. Empirical consequence: price and Delta convergence cannot replace Gamma evaluation; report all three independently. This is known functional analysis applied carefully to pricing, not claimed original theory.

### B2 — finite collocation cannot certify continuum derivative accuracy

For any fixed finite collection of value, PDE and boundary samples, choose an interior neighborhood disjoint from these points, and a smooth compact perturbation supported there. The perturbation and all derivatives vanish at every sampled point. Scale its oscillatory amplitude to zero while increasing frequency as above; sampled value/PDE/boundary losses are identical to the unperturbed function but an unsampled Greek diverges. The same construction preserves price bounds if the support has a positive margin.

This proves lack of a deterministic guarantee from finite sampling **without capacity/smoothness/coverage bounds**. It does not invalidate well-resolved population PDE estimates. With uniform ellipticity, suitable continuum graph norms and regular BC, residual estimates may indeed control derivatives: no claim “small true PDE error never controls Greeks.” A neural representability or stochastic generalization claim would require separate approximation/capacity hypotheses. Empirical consequence: independent dense/IID grids, validation of worst regions, and sampling/capacity controls are necessary.

## C — stronger norms give the derivative control they actually contain

On an interior compact (x,v) domain with bounded e^{-x}, if

\[
\|e\|_{L^2(p,\tau;H^2(x,v))}\to0,
\]

then L² errors in Delta=e^{-x}c_x,KGamma=e^{-2x}(c_xx-c_x),nu/K=c_v converge to0 by bounded multiplier inequalities. Write their constants explicitly from x_min and the K scale if physical Greeks are used. No derivative in p is controlled unless it is included in the norm. To conclude uniform pointwise second-derivative convergence on spatial slices, require sup_{p,tau}||e||_{H^s(Omega)}->0 with s>3 in spatial dimension2 and an extension-domain hypothesis; Sobolev embedding gives C² control. Treating time and all parameters as spatial variables changes the dimension threshold and is not allowed silently.

If a true shape quantity has margin eta>0 on a specified compact region and the relevant uniform derivative error is<eta, that shape constraint survives. Without a positive margin, vanishing L² error does not imply zero violations everywhere. Tools: derivative norm definitions, bounded multipliers, Sobolev embedding. Failure: degeneration/payoff singularity; an empirical Greek loss is not full H² norm; a supervised finite set does not establish that norm. Consequence: report sampled Greek errors and margin-dependent statements, not guaranteed convergence from training. Status: standard implication, not a new training theorem.

## D — population shape loss, violation magnitude and limited certificates

For any fixed learned model and a declared evaluation probability distribution mu, let g(z)>=0 be a constraint shortfall, e.g. (-KGamma)^+ or (V_K)^+. If L=E_mu[g²]<infinity, then

\[
E_mu[g]\le\sqrt L,\quad \mu(g>eta)\le L/eta^2\quad(eta>0).
\]

Proof: Cauchy–Schwarz and Markov. This controls population measure/magnitude at a threshold, not global worst violation, and depends on the evaluation distribution and physical scaling. It is an elementary lemma, not publishable standalone novelty.

For n fresh IID evaluation points independent of model selection and a verified g<=M, Hoeffding yields with probability>=1-delta:

\[
L\le\hat L+M^2\sqrt{\log(1/delta)/(2n)}.
\]

Use union bound delta/m across m predeclared constraints/models. If M is only an empirical maximum, this bound is invalid. Instead report exact binomial confidence bounds for threshold-exceedance indicators from truly IID independent point draws (conditional frozen model); no bound on uncapped magnitude follows. For0 exceedances, one-sided95% upper probability is1-.05^{1/n}. Clustered parameter-surface samples need cluster-aware uncertainty, not n-point binomial intervals. Sobol samples are not IID; report them descriptively or use a valid randomized-QMC argument, not Hoeffding as if independent.

Optional restricted continuous certificate: for a finite h-net in a compact slice, if each shortfall g is globally L_g-Lipschitz on the slice with a **verified** derivative/operator bound, then supg<=max_gridg+L_g*h. Proof: nearest-net-point triangle inequality. Requires verified network third derivatives for Gamma shortfalls, coverage radius and physical scaling. A sampled Lipschitz estimate is not certification. Interval/verified bounds may be too loose; report failed certificate coverage, never “global arbitrage-free.” High-dimensional full-parameter certification is optional, not presumed affordable. Tools: elementary probability and covering lemma; [continuous PINN verification](https://arxiv.org/abs/2305.10157) is relevant prior art.

Consequence: E05 should separate empirical violation rates, statistical population upper bounds where valid, and any restricted verified-cell coverage. The word certificate names a precise object, never just a heatmap.

## E — delta-approximation hedge deviation, not guaranteed PnL superiority

Under the specified Q dynamics, with identical initial premium, discounted stock X_t=e^{-rt}S_t, identical information/state, a finite horizon, stopped/otherwise square-integrable integrands and no transaction costs, let D_t=Delta_hat_t-Delta_ref_t. The **difference** between two discounted continuous stock-hedge gains is

\[
Z=\int_0^T D_t\,dX_t,\qquad
E[Z^2]=E\int_0^T e^{-2rt}S_t^2v_tD_t^2dt.
\]

Proof: X is a Q martingale with diffusion e^{-rt}Ssqrt(v); apply Ito isometry. This provides a natural evaluation weight, not a claim that pointwise Delta accuracy or shape penalties alone minimize terminal short-call PnL.

Discrete hedge at t_j: decompose D_j=Delta_hat(t_j)-Delta_ref(t_j); the continuous deviation from reference Delta equals (Delta_hat step-Delta_ref step)+(Delta_ref step-Delta_ref continuous). Ito-isometry/triangle inequality bounds L² gain deviation by the sum of the corresponding weighted stochastic-integral norms. A rate O(sqrt(h)) in L² requires suitable time/state regularity and integrability; near expiry/ATM or v=0 the constants may diverge. Do not assert a universal convergence rate without verifying those assumptions.

With proportional transaction cost alpha and matched settlement conventions, discounted paid costs A_alpha(h)=sum_j alpha e^{-rt_j}S_j|h_j-h_{j-1}| (including opening and chosen closing), so the discounted terminal PnL difference is

\[
Z_{grid}-[A_\alpha(\hat\Delta)-A_\alpha(\Delta_{ref})]
\]

plus any separately declared initial-premium difference. Triangle inequality gives an L² bound using the discrete gain deviation and cost-difference norm; it has no guaranteed favorable sign. Smooth Delta errors can still alter turnover.

Incomplete-market caveat: discounted option diffusion has both Ssqrt(v)V_S dW^S and sigma sqrt(v)V_v dW^v. A stock-only V_S hedge leaves volatility risk. Instantaneous local variance-minimizing stock position is V_S+(rho*sigma/S)V_v when the integrability/observable-state conditions hold. For Delta-only strategies, covariance of remaining volatility risk and Delta-approximation error means a more accurate V_S hedge need not yield smaller total PnL variance. Include the locally minimizing reference position as a secondary control; do not call reference Delta a replicating/variance-optimal hedge. Under Q this is a local risk diagnostic, not full real-world variance-optimal strategy.

Tools: self-financing discounted portfolios, Ito isometry, L² triangle inequality, Brownian projection. Failure: physical-measure drift changes identity; differing paths/current variance/premium invalidate comparison; unobserved v limits practical applicability; transaction costs break frictionless expectation arguments. Consequence: E08 tests hedge **deviation** against matched reference Delta; E09/H5 separately test PnL variance/ES/turnover and may fail. Status: standard identities with explicit scope; no model-training theorem.

## Theorem inclusion rule

Include only results that explain a measured experiment or a precise validation gate. A/B/C/D/E should not all be promoted to numbered “new theorems.” Core counterexample and hedge-deviation proposition can be accompanied by standard supporting lemmas in an appendix with clear attribution. A genuinely new theorem would need additional, nontrivial parameter-uniform bounds or a useful constructive certificate; none has been established in Phase1A.
