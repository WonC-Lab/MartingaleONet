# Collar and degenerate boundary evidence

**BOUNDARY/COLLAR GATE: FAIL.** Only 0/3202 planned positive-variance collar grid points have new full-row coverage. Historical collar rows and all sequence diagnostics remain separate and visible. Exact v=0 belongs to the fixed CHALLENGE partition, but is also a boundary obligation of the proposed PDE training objective.

Limiting PDE at v=0: c_tau=r*c_x+kappa*theta*c_v-r*c. Positive kappa*theta means future variance is stochastic even when current variance is zero; do not substitute the discounted intrinsic payoff. In the resolved typical tau=.001 case, price is about 9.4226809227e-5, Delta .6299337671, Gamma 1893.6287006251, and right Vv .9413028798. Vega_s=0 conceals that nonzero variance sensitivity.

Sequences v=0,1e-8,1e-7,1e-6,1e-5,1e-4,1e-3,1e-2 were actually evaluated for typical R0 and severe R4 at tau=.001, with separate A cutoffs and COS term counts. Finite-grid traces are diagnostic; not all are certified. See BOUNDARY_SEQUENCES_local.json and plots. Additional x/positive-v MP sequences are prepared for the full run.

BOUNDARY_PDE_CHECKS.json records physical-time five-point differences and the limiting-PDE RHS, without inventing a PDE tolerance. R0 residual decreases from around 1.87e-5 at U32768 to around 1e-10 or below at U524288; R4 retains roughly 1.9e-3 residual at the latter cutoff. Finite-cutoff consistency is not a boundary proof, but it reinforces the need to refine the numerical tail before diagnosing physical singularity.

The v=.25 and x=±1.2 artificial-boundary labels required by Phase1A remain uncertified as a complete population. A core-only price certificate, even if obtained later, would not yet satisfy the current training objective's label obligations.
