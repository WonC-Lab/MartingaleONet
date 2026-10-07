"""Generate the review report directly from raw certification outputs."""
import argparse
from collections import Counter
import json
from pathlib import Path

def report(output="reference"):
    root=Path(output);d=json.loads((root/"CERTIFICATION_RESULTS.json").read_text());m=d["metadata"];rows=d["rows"]
    checks=json.loads((root/"CF_CHECKS.json").read_text())
    lines=["# Phase 1B reference validation report", "", "**Gate: FAIL. Phase 1C is not authorized.**", "",
      f"Executed scope: {m['scope']}, {len(rows)} actual points out of {m['full_grid_size']} planned Domain v1 points. "
      f"Row results: {m['PASS_rows']} PASS / {m['FAIL_rows']} FAIL. Runtime {m['elapsed_seconds']:.2f} seconds. "
      "A row PASS in this diagnostic slice is not a domain certificate. No neural training or final training labels were generated.","",
      "## 1. Implemented routes","",
      "A: stable little-trap P1/P2 inversion, analytic spot/variance derivatives and explicit cutoff/tolerance/panel refinements. "
      "B: independently written scaled hyperbolic Riccati solution, Taylor-ODE cumulants, analytic COS put coefficients, parity call and direct-call diagnostic, fixed-interval Greeks. "
      "Direct numerical Riccati ODE is a third CF validation, not an external price engine. Optional pinned QuantLib analytic/PDE adapter is supplied.","",
      "## 2. Independence and conventions","",
      "Only input/output dataclasses are shared. Neither route imports the other or legacy pricing code. Both model the same risk-neutral Heston process (q=0), hence common model/derivation risk remains. "
      "CF is for log(ST/S), with strike only in inversion phase. A chooses Re(d)>=0 and log1p little-trap factors; B uses a scaled hyperbolic denominator. "
      "Branch continuity is tested on sampled frequencies/perturbations, not proven over all complex frequencies. Exact moment identities are imposed in production and independently evaluated by unforced ODE.","",
      "## 3. CF validation","",
      f"32 direct complex ODE comparisons: maximum A error {m['CF_max_A_ODE']:.6g}; B error {m['CF_max_B_ODE']:.6g}. "
      f"Moment ODE maximum error {max(c['moment_ODE_gap'] for c in checks):.6g}; conjugation maxima A/B "
      f"{max(c['conjugacy_A'] for c in checks):.6g}/{max(c['conjugacy_B'] for c in checks):.6g}. "
      f"Dense-frequency A/B maximum error {max(c['dense_CF_cross_gap'] for c in checks):.6g}. "
      "`CF_CHECKS.json` preserves all cases and perturbation results. Unit tests cover normalization, moment, continuity, sigma=0 Black–Scholes limits and off-ATM regressions.","",
      "## 4–5. Price and Greek agreement","",
      "Physical K=1 in this executed slice. Statistics include failed points; no failures are dropped. Relative price error is omitted below normalized magnitude 1e-5.","",
      "| Absolute gap | Mean | Median | p95 | p99 | Maximum | Valid/missing |",
      "|---|---:|---:|---:|---:|---:|---:|"]
    for f in ["price","Delta","Gamma","Vv"]:
        s=m.get(f"abs_{f}_gap")
        if s:lines.append(f"| {f} | {s['mean']:.6g} | {s['median']:.6g} | {s['p95']:.6g} | {s['p99']:.6g} | {s['max']:.6g} | {s['valid']}/{s['missing']} |")
    lines += ["", "Relative mean/median/p95/p99/max and every worst input are in `validation_summary.json`; each raw row records absolute/relative gaps, normalized budgets, component statuses and all refinement/stencil values.","",
              "## 6. Worst cases and failure map",""]
    for f in ["price","Delta","Gamma","Vv"]:
        s=m.get(f"abs_{f}_gap")
        if s:lines.append(f"- {f}: max {s['max']:.6g}, input `{json.dumps(s['worst_input'])}`.")
    flags=Counter(f for r in rows for f in r.get("failure_flags",[]))
    lines += ["",f"Failure flags (overlapping counts): `{dict(flags)}`.","",
      "A strict 1e-13 request can report float64 roundoff even when the observed A/B price gap is tiny. These raw solver failures remain failures under this protocol. "
      "v=0/short-maturity cases have slow Fourier decay and unresolved domain/N convergence; severe R4 cases also fail interval stability. These are observed numerical-axis diagnoses; "
      "they do not prove that every discrepancy has a single identified cause. No branch failure is inferred without evidence. Cross-route discrepancies unexplained by recorded refinements remain unknown.","",
      "## 7. Financial sanity and homogeneity","",
      f"A financial-sanity failing rows: {sum(not all(r.get('A_sanity',[False])) for r in rows)}; "
      f"B failing rows: {sum(not all(r.get('B_sanity',[False])) for r in rows)}. "
      "Bounds, Delta, Gamma, V_K and V_KK use predeclared numerical budgets. Strike homogeneity identities and physical-K FD values are stored separately.","",
      f"Maximum homogeneity relative discrepancy across K=50/100/200: "
      f"{max((r.get('homogeneity_max_relative') or 0) for r in rows):.6g}. "
      "Prices normalize as V=K*c(x,v,tau,p); this scaling check alone cannot detect errors in normalized pricing.","",
      "## 8. Convergence and derivative reliability","",
      "Raw A tables vary U=64..2048, tolerance 1e-9..1e-13 and panel count 4/8/16. B independently varies N=64..4096 at every L=8/12/16/24/32. "
      "Five-point physical-S and variance stencils use all six predeclared steps; v=0 uses right differences. "
      "Each row contains within-route plateau changes, FD/analytic gaps and amplification diagnostics. Small-h agreement is not assumed sufficient. "
      "`BOUNDARY_ESCALATION.json` separately extends two short/v=0 cases through U=65536 and N=65536 at L=16/32, without replacing any failed row. "
      "Typical R0 prices approach agreement under these extensions, while R4 Gamma remains strongly unstable. "
      "The hard cases require further cutoff/term extension and/or independently verified high precision before labels can be certified. "
      "Analytic-v=0 values are retained as diagnostics; zero Vega_s does not establish a trustworthy Vv.","",
      "## 9. Reference uncertainty","",
      "`REFERENCE_UNCERTAINTY.npz/json` stores max pairwise A/B price/Greek differences (two routes here). This is a numerical discrepancy diagnostic, "
      "not a theorem, confidence interval or proven bound. Agreement can underestimate common bias. Failed rows are explicitly tagged and cannot be used as certified labels. "
      "FD propagation additionally uses the quadrature estimate, but remains a diagnostic envelope with no rigorous tail bound.","",
      "## 10. Coverage, dependencies and remaining risks","",
      f"Grid version `{m['grid_version']}`: 1680 deterministic + 4096 Sobol +64 challenge points. "
      "The local 25-point slice does not satisfy the 256 smoke/FD requirement or full coverage. Full and external runs must occur in a separate output directory using the Colab notebook. "
      f"External QuantLib available: {m['external']['available']}; executed: {m['external']['executed']}. "
      "Local external results explicitly record the missing dependency, rather than treating ODE CF agreement as independent PDE validation. "
      "External integer-day cases align Actual365Fixed time exactly; FD axes refine independently and require a measured-error review. "
      "Route A currently supports float64 only; the exposed precision option rejects unsupported choices. High precision escalation is a remaining implementation task. "
      "No scientifically defensible revised subdomain can be certified from this slice; training support itself lacks full mandatory coverage.","",
      f"Executed environment: `{m['environment']}`. Exact module SHA256 values are recorded in metadata. "
      "`requirements-local.txt` records actual numerical dependencies; `requirements-colab.txt` is a proposed pinned environment that still needs execution validation. "
      "Figures are generated from raw outputs only. Sparse local heatmaps show sampled cells, without interpolated contours or invented dense coverage.","",
      "## 11–12. Gate and next authorization","",
      "**FAIL — Phase 1C dataset generation is not authorized; neural training remains prohibited.** "
      "Required next work is numerical escalation of retained failures, complete mandatory/FD coverage, and external analytic/PDE review under unchanged budgets. "
      "Do not use the full sweep to conceal the already observed failures, or loosen tolerance to restore earlier claims. "
      "This report concludes Phase1B with a failed reference gate; it is not a certificate.",""]
    (root/"REFERENCE_VALIDATION_REPORT.md").write_text("\n".join(lines),encoding="utf-8")

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--output",default="reference");report(p.parse_args().output)
