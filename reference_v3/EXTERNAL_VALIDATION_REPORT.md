# Pinned QuantLib 1.41 validation
Exact 8 predeclared aligned inputs attempted; 6 analytic/PDE cases executed. Original and exact-time-change calendar inputs, dates, curves, day count, all engine settings and individual failures are in EXTERNAL_RESULTS.json and external_checkpoints/.

[
  {
    "label": "easy_ATM",
    "status": "REVIEW_REQUIRED",
    "analytic_levels": 3,
    "PDE_levels": 10,
    "analytic_last_two_max_change": 5.551115123125783e-17,
    "analytic_A_gap": 1.249000902703301e-16,
    "analytic_within_budget": true,
    "PDE_analytic_price_gap": 6.40913324967407e-07
  },
  {
    "label": "deep_OTM",
    "status": "REVIEW_REQUIRED",
    "analytic_levels": 3,
    "PDE_levels": 10,
    "analytic_last_two_max_change": 4.200910194488946e-17,
    "analytic_A_gap": 5.035866304799972e-17,
    "analytic_within_budget": true,
    "PDE_analytic_price_gap": 4.3246001265284703e-10
  },
  {
    "label": "deep_ITM",
    "status": "REVIEW_REQUIRED",
    "analytic_levels": 3,
    "PDE_levels": 10,
    "analytic_last_two_max_change": 2.220446049250313e-16,
    "analytic_A_gap": 0.0,
    "analytic_within_budget": true,
    "PDE_analytic_price_gap": 1.3910860665822256e-05
  },
  {
    "label": "short_core",
    "status": "REVIEW_REQUIRED",
    "analytic_levels": 6,
    "PDE_levels": 10,
    "analytic_last_two_max_change": 6.201636426617085e-17,
    "analytic_A_gap": 1.0842021724855044e-16,
    "analytic_within_budget": true,
    "PDE_analytic_price_gap": 1.8906443509294352e-08
  },
  {
    "label": "high_vol_of_vol",
    "status": "REVIEW_REQUIRED",
    "analytic_levels": 3,
    "PDE_levels": 10,
    "analytic_last_two_max_change": 9.71445146547012e-17,
    "analytic_A_gap": 6.938893903907228e-17,
    "analytic_within_budget": true,
    "PDE_analytic_price_gap": 9.290195369104914e-07
  },
  {
    "label": "near_Feller",
    "status": "REVIEW_REQUIRED",
    "analytic_levels": 3,
    "PDE_levels": 10,
    "analytic_last_two_max_change": 8.326672684688674e-17,
    "analytic_A_gap": 1.5265566588595902e-16,
    "analytic_within_budget": true,
    "PDE_analytic_price_gap": 4.6550758062147146e-07
  },
  {
    "label": "severe_failed",
    "status": "UNSUPPORTED_EXACT_V0",
    "analytic_levels": 0,
    "PDE_levels": 0
  },
  {
    "label": "zero_short_R0",
    "status": "UNSUPPORTED_EXACT_V0",
    "analytic_levels": 0,
    "PDE_levels": 0
  }
]

Exact v0=0: HestonProcess construction succeeds, but HestonModel rejects zero through its PositiveConstraint ([upstream 1.41 source](https://github.com/lballabio/QuantLib/blob/v1.41/ql/models/equity/hestonmodel.cpp)). This is UNSUPPORTED_EXACT_V0, not evidence of a mathematical singularity. No epsilon substitution was made. These two failed external attempts remain visible, while the six positive-variance cases independently triangulate CORE.

PDE axes are refined separately at the original settings, followed by larger combined grids. Current finite-grid values can exceed the unchanged reference budgets; all remain in the uncertainty matrices. Additional expensive refinements are prepared for Colab. Execution alone does not certify convergence; the complete cross-route MP comparison is pending where MP has not run. Local computations are not represented as Google Colab runs.
