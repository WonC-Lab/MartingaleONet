# Genuine arbitrary-precision validation

mpmath 1.3.0; true 50/80/120-digit CF, quadrature nodes/weights, summation and stored decimal prices. No wrapper around float64. A Lewis half-contour inversion differs from A P1/P2 and B COS, but its little-trap algebra still shares model/derivation risk with A. External PDE triangulation is separately required.

Normalized call formula: c=exp(x)-exp(-r*tau)*exp(x/2)/pi * integral Re[exp(i*u*x)*psi(u-i/2)]/(u^2+1/4) du. The phase contains log(S/K) only once; the CF contains log(ST/S), avoiding the historical double-prefactor defect. Analytic MP Gamma=exp(-r*tau)*exp(-3*x/2)/(pi*K)*integral Re[exp(i*u*x)*psi(u-i/2)] du. Vv follows psi_v=D*psi.

| Input label | Domain | Gamma evidence | Maximum precision change (price) | Last two cutoff-change maximum (Gamma) |
|---|---|---|---:|---:|
| HP_ZERO_R0_EXTENDED | CHALLENGE | NUMERICALLY_RESOLVED | 1.26860377160692281452501413271e-50 | 0.0000000276358592535277248929686169737 |
| GREEK_PRIORITY_0_R0 | CORE | NUMERICALLY_RESOLVED | 1.08024406349583015591300550666e-50 | 1.67921716683408003045329798911e-20 |
| GREEK_PRIORITY_1_R0 | CORE | NUMERICALLY_RESOLVED | 1.22683734181844904607289361051e-50 | 2.82214762667142580519477211706e-22 |
| GREEK_PRIORITY_2_R0 | CORE | NUMERICALLY_RESOLVED | 1.17191546813222342959660693417e-50 | 0.0 |
| GREEK_PRIORITY_3_R1 | CORE | NUMERICALLY_RESOLVED | 1.14057955290631494533445271263e-50 | 2.76331292717823637899084521208e-21 |
| GREEK_PRIORITY_4_R1 | CORE | NUMERICALLY_RESOLVED | 1.19891772614422469642303223486e-50 | 1.38054501659077233757015050302e-23 |
| GREEK_PRIORITY_5_R1 | CORE | NUMERICALLY_RESOLVED | 1.05552073612679082886571126874e-50 | 0.0 |
| GREEK_PRIORITY_6_R2 | CORE | NUMERICALLY_RESOLVED | 1.0684713100278403786567975305e-50 | 3.89011525846743760415827136954e-22 |
| GREEK_PRIORITY_7_R2 | CORE | NUMERICALLY_RESOLVED | 1.05673381136407828201505564518e-50 | 4.78844635307125221046395712316e-24 |
| GREEK_PRIORITY_8_R2 | CORE | NUMERICALLY_RESOLVED | 1.05800137343617552853372136572e-50 | 0.0 |
| GREEK_PRIORITY_9_R3 | CORE | NUMERICALLY_RESOLVED | 1.02120124453578567250111956105e-50 | 3.92803884110521303405451091997e-20 |
| GREEK_PRIORITY_10_R3 | CORE | NUMERICALLY_RESOLVED | 1.12930152622312462323371215588e-50 | 5.59927136428755826553361926087e-22 |
| GREEK_PRIORITY_11_R3 | CORE | NUMERICALLY_RESOLVED | 1.01933922924963754108216672588e-50 | 0.0 |
| GREEK_PRIORITY_12_R5 | CORE | NUMERICALLY_RESOLVED | 9.42827366986153371108210848745e-51 | 4.58905183622374296037089755405e-12 |
| GREEK_PRIORITY_13_R5 | CORE | NUMERICALLY_RESOLVED | 1.01816080593346846190236964839e-50 | 1.86617616732766789097551829912e-15 |
| GREEK_PRIORITY_14_R5 | CORE | NUMERICALLY_RESOLVED | 9.8703986961130182803112062146e-51 | 5.13857754410259116872567297672e-46 |
| HP_CORE_ATM | CORE | NUMERICALLY_RESOLVED | 1.02774811750284477966021985591e-50 | 2.54196822321289447837393039735e-31 |
| HP_ZERO_R0 | CHALLENGE | UNRESOLVED | 1.2299684189064064024828824575e-50 | 60.8146046630276046153617594697 |
| HP_ZERO_R4 | CHALLENGE | UNRESOLVED | 1.18180708938130027508789462621e-50 | 5015.77431182395102861461268172 |


MP axes are varied independently. The initial typical and severe v=0/tau=.001 examples agree to roughly 50 digits across precision while Gamma still changes by tens/thousands under cutoff extension. This identifies finite-domain truncation as substantial, rather than just insufficient floating-point digits. It does not prove absence of common branch bias.

The fixed typical zero-variance case was additionally extended to U=131072/262144/524288, rechecked at 50/80/120 digits and degrees 24/40/64, with right-variance FD and spot FD. Refined A, B and MP agree within unchanged budgets at that point. The original failed values remain unchanged in reference/ and the initial HP records remain visible. Selected numerical resolution does not certify the entire v=0 boundary.

Exact strings, all stencil prices and independent axis changes are in HP_*.json, FD_PRECISION_CONVERGENCE.json and HIGH_PRECISION_ANALYSIS.json. Classification uses observed refinement differences and is not a rigorous interval proof. Every retained failure/near-failure is scheduled by full_escalation.py for Colab; that complete escalation has not run locally. Missing cases are not labeled resolved.

CF_DECAY_ANALYSIS.json checks the large-frequency affine expansion with 80-digit CF samples. For fixed positive tau, log|psi(u-i/2)|=-alpha*|u|+O(1), alpha=(v+kappa*theta*tau)*sqrt(1-rho^2)/sigma. At v=0,tau=.001, alpha is about 1.90438e-4 for R0 and 2.35112e-6 for R4; measured log-CF slopes approach these values. The severe example's decay scale is about 81 times longer. High precision cannot compensate for a cutoff covering too few decay scales.
