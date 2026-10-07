# Skeptical novelty analysis

Literature checked 2026-10-07. Search scope: primary papers/author repositories for Heston operators, derivative learning, shape-constrained pricing, residual-error certification and hedge approximation. This is a targeted review, not proof that no competing work exists. All empirical findings of the new project remain untested. The distinction between value and derivatives is longstanding; the oscillatory example is motivation, not a new mathematical discovery.

## Closest competitors and required controls

| Work | Relevant existing contribution | What our project must add or test |
|---|---|---|
| [DeepSVM, v1, December2025](https://arxiv.org/html/2512.07162v1) | Heston PI-DeepONet; ATM Greeks remain unstable; authors report an unsuccessful Gamma penalty and suggest sensitivity-aware training | This is the closest comparator. A new loss plus Greek plots is insufficient. Compare a documented normalized PI operator, certified derivative control and a budget-matched sensitivity-residual arm; assess out-of-sample tradeoffs and actual hedge deviation |
| [FI-DeepONet, v2, October2026](https://arxiv.org/html/2609.33213v2) | Local-volatility carrier/correction construction, price bounds and qualified sensitivity analysis; its bound layer does not ensure spot convexity | Do not claim carrier, bounds or value-to-Greek diagnostics as new. Distinguish full stochastic-variance state, independent reference uncertainty, strike/spot identities and matched payoff/hedging populations. Heston alone is not a novelty claim |
| [Sobolev Training,2017](https://arxiv.org/abs/1706.04859) | Function-plus-derivative supervision | Include derivative-supervised control; this term is prior art |
| [Differential Machine Learning,2020](https://arxiv.org/abs/2005.02347) | Differential labels for financial surrogates | Include differential MLP and differential DeepONet; count label-generation costs and information budgets |
| [Heston deep differential networks,v4,September2026](https://arxiv.org/abs/2407.15536) | Heston prices and parameter derivatives for calibration | Our state Delta/Gamma/variance sensitivity and independent financial-use diagnostics differ; price+derivative learning on Heston is already established |
| [Dugas et al.,NIPS2000](https://proceedings.neurips.cc/paper_files/paper/2000/hash/44968aece94f667e4095002d140b5896-Abstract.html) | Shape-informed option-pricing network architecture | No first convex/monotone-network claim. Include smooth shape control or strong soft-penalty baseline; hard guarantee needs an actual proof |
| [Deep Local Volatility,2020](https://arxiv.org/abs/2007.10462) | Hard/soft financial constraints and local-volatility inference | Penalty engineering is incremental; test whether Greek supervision and shape constraints have independently measurable effects |
| [Operator Deep Smoothing,v3,2025](https://arxiv.org/abs/2406.11520) | Market-observation-to-surface neural operator | This study has no observation/operator calibration claim; clarify finite-parametric operator scope and synthetic-only validity |
| [Mishra–Molinaro PINN error estimates](https://arxiv.org/abs/2006.16144), [De Ryck–Mishra Kolmogorov analysis](https://arxiv.org/abs/2106.14473) | Stability/generalization theory for residual methods | Our restricted stability lemma is an application, not a new general theorem; finite sampling and degenerate boundaries must remain qualified |
| [Efficient Error Certification for PINNs](https://arxiv.org/abs/2305.10157) | Continuous-domain verification of residual conditions | Empirical validation cannot be relabeled formal certification. Any cell certificate must have verified bounds, or remain a conditional design |

Additional [neural Heston validation case study,Zenodo2026](https://zenodo.org/records/21726313) is a caution against taking stable losses/calibration behavior as fidelity evidence; it is not used as established proof about our model. Quantitative results from competing papers are not copied into our design as target outcomes. Reproductions must name version, source availability, changes and failed attempts.

## Proposed moat, stated without overclaim

1. **A falsifiable reliability frontier:** ask which combinations meet simultaneous, predeclared budgets for values, state Greeks, strike/spot shape and path-weighted hedge deviation. Evaluate the same frozen inputs/checkpoints, accounting for reference uncertainty. Report failed budgets and Pareto tradeoffs rather than claim universal superiority.
2. **A controlled separation of mechanisms:** common smooth function class and common labels for a2x2 Greek-supervision/shape-treatment factorial around a physics operator; standalone differential-learning and smoothness controls separate extra supervision from physics/shape benefit. Price noninferiority and matched labeling/compute costs are mandatory.
3. **A limited evidence-to-risk bridge:** use exact homogeneity identities to remove redundant convexity diagnostics, independently bounded/empirically estimated shape excursions and a Q-weighted Delta hedge-deviation identity. These ingredients are mostly classical; a useful new result would be their quantitatively validated predictive relation and clearly measured limits, including the incomplete-market counterpressure on PnL improvement.

Do not call these three ingredients an established novel algorithm. They define an experimentally testable contribution candidate. A full-domain formal financial certificate is optional and presently unproved; no marketing term may imply it. A simple known-Markov inequality does not constitute a novelty moat by itself.

## Redesign against the incremental version

Reject framing “DeepONet + Gamma penalty improves option pricing.” It directly overlaps existing studies and cannot isolate mechanisms. Recommend a critical computational-finance methods paper around **when a price-accurate surrogate is reliable for derivative use**, with model development subordinate to the evidence protocol. Introduce the dual-axis comparisons: value-matched checkpoints and compute-matched checkpoints, with derivative-target information-matched baselines. Predeclare a test of whether path-weighted Delta error predicts common-path deviation better than price RMSE. Add a shape-free differential baseline and verify whether shape metrics provide any additional predictive value. If shape adds no effect, report it and remove it from the recommended objective.

The comparison must include near-expiry and low-variance cases where reference Greeks are resolved, and identify where residual, price and Greek diagnostics disagree. A research contribution can be an honest negative result if it overturns a plausible training heuristic with controlled evidence; it cannot rely on adverse legacy baselines.

## Novelty gate before full training

Gate N1: independent reference and Greek uncertainty pass E01. N2: close-competitor protocols are reconstructed from primary sources, including version-specific assumptions and adaptation costs; no paper method is replaced by a weak straw baseline. N3: a development pilot yields either a substantial reliability/label-cost advantage over differential MLP/DeepONet and smoothness controls, or a clear non-obvious failure boundary robust across seeds. N4: any certificate has a verified domain/norm interpretation and usefulness beyond trivial bounds. N5: literature review is refreshed before submission, with exact prior-overlap matrix.

If N3/N4 fail, do not escalate to1M labels or invent more penalties. Narrow to a reproducible evaluation/negative-result study, or stop. The project is strong enough for reference construction; publication-level novelty is not established by this design alone.

## Candidate title decision

Recommended: **When Accurate Prices Fail: Value, Greek and Admissibility Frontiers for Heston Surrogates**. Alternatives and criticism are recorded in [PHASE1A_RESEARCH_DESIGN.md](PHASE1A_RESEARCH_DESIGN.md). Avoid “Martingale” branding in the new main claim because no measure construction is proposed. Retaining the repository name for history does not imply a martingale result.
