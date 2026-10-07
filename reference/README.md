# Reference-only Phase 1B

Run from repository root:

```powershell
python -m pytest reference/tests -q
python -m reference.certify --scope local
python -m reference.plot_validation
```

Full user-run computation (CPU; can take hours):

```text
python -m reference.certify --scope full --output reference/full_run
python -m reference.plot_validation --output reference/full_run
python -m reference.external_validate --output reference/full_run
```

`colab/phase1b_reference_certification.ipynb` calls these same modules, with no duplicated scientific algebra. Actual local outputs remain separate from full Colab outputs. Pin dependencies before execution; runtime and source hashes accompany every run. Do not infer PASS from unit tests or a few accurate points.

Route A uses little-trap probability integration. Route B uses a separately derived scaled hyperbolic Riccati solution, Taylor-ODE cumulants and COS put coefficients; no shared pricing code. Direct Riccati ODE checks validate both CFs. The optional pinned QuantLib adapter checks analytic and independent PDE prices with aligned integer-day maturity conventions.

Known limits: float64 only for Route A; demanding 1e-13 quadrature can explicitly report roundoff; finite cutoff may fail at short maturity/v=0; broad COS intervals at fixed N can fail for extreme parameters. Precision requests outside float64 raise rather than pretend to execute. Failures are scientific outputs and block labels. `u_ref` is diagnostic, not a rigorous enclosure.

Greek derivation: A Delta=P1, KGamma=(pi*exp(x))^-1 integral Re[e^(iux) psi(u-i)/psi(-i)]du; Vv follows psi_v=D psi. B differentiates fixed-interval phase with factors iu,-u²,D; spot chain rule yields Delta=1+put_x/exp(x), KGamma=(put_xx-put_x)/exp(2x), Vv/K=put_v. Vega_s=2sqrt(v)Vv; v=0 is a right-sensitivity challenge, not validated by zero Vega_s. Strike identities are supplemented by physical-K finite differences.
