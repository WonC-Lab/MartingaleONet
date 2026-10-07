# Challenge/OOD validation

**CHALLENGE/OOD GATE: FAIL.** New complete-row planned-grid coverage is 0/904; historical severe failures and diagnostic sequences remain in the report. No outcome-dependent reassignment or filtering.

v=0 and short maturities are treated separately from learning interior. The typical v=0/tau=.001 case becomes NUMERICALLY_RESOLVED after much larger integration limits. Severe R4 (kappa=.5,theta=.04,sigma=1.2,rho=-.99) still has unresolved MP cutoff/Greek behavior. Its stable 50/80/120-digit finite-cutoff values cannot certify the infinite integral; COS also needs independent N/interval and external checks. No mathematical fixed-positive-tau singularity is established by these failures.

Actual ATM/near-ATM tau=1e-4,2.5e-4,5e-4,.001,1/252,.01,.05 sequences were evaluated. In the typical COS diagnostics, c/tau stays near .09425 to .09291 and tau*Gamma near 1.893 to 1.921; Vv is nonzero. These patterns are consistent with the formal v=0 short-time scaling, not a proof that every sequence value is certified.

Formal scaling derived from the declared SDE: Y_s=v_(tau*s)/tau tends to dY=kappa*theta ds+sigma*sqrt(Y)dB at initial zero. The leading log-price increment is of order tau, unlike order sqrt(tau) when initial v>0. If the scaled return has a regular density at the ATM evaluation point, this suggests Gamma of order 1/tau. The density regularity and uniform asymptotics are additional assumptions, not established here. Gamma growth as tau approaches zero does not establish singularity at a fixed positive tau. No tolerance was changed.

The independently sampled large-frequency decay agrees with alpha=(v+kappa*theta*tau)*sqrt(1-rho^2)/sigma. All these fixed-positive-tau cases have alpha>0; polynomial Greek factors times that exponential are integrable for the correct affine CF. Thus fixed-positive-tau infinite Gamma is not supported here, even at initial v=0. Uniform bounds as tau->0 or |rho|->1 do not follow. This distinction supports an unresolved numerical-tail diagnosis for R4 rather than assigning BOUNDARY_SINGULAR to its current quadrature failures.

No Domain v2 revision is proposed before complete retained-failure/external analysis. The original Domain v1 and its failed coverage remain reported. Stress inputs can eventually be evaluation-only, but the current boundary labels required for training have not all passed.
