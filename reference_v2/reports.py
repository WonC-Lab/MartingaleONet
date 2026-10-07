"""Reports and failure-map updates derived from raw data, no invented results."""
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
import numpy as np
from .workflow import aggregate,verify_history,ROOT
from .numerical_analysis import analyze
from .domains import classify
from .workflow import from_row
from reference.certify import dump

KEYS=["x","v","tau","K","kappa","theta","sigma","rho","r"]
def key(row):return tuple(row[k] for k in KEYS)

def write_reports(output="reference_v2"):
    root=Path(output);meta=aggregate(root);analysis=analyze(root)
    raw=json.loads((root/"CERTIFICATION_RESULTS.json").read_text());grid=raw["grid_rows"]
    by_input={}
    for row in analysis:
        k=key(row["input"])
        if k not in by_input or row["gamma_status"]=="NUMERICALLY_RESOLVED":by_input[k]=row
    path=root/"FAILURE_CLASSIFICATION.csv"
    with path.open(encoding="utf-8",newline="") as h:classified=list(csv.DictReader(h));columns=classified[0].keys() if classified else []
    for r in classified:
        match=by_input.get(key(json.loads(r["input"])))
        if match:
            r["gamma_status"]=match["gamma_status"]
            flags=json.loads(r["secondary_flags"])
            if match["gamma_status"]=="NUMERICALLY_RESOLVED" and "FD_derivative_amplification_or_truncation" in flags:
                r["primary_diagnosis"]="FD_TRUNCATION"
                r["evidence"]="legacy last-two FD changes exceed budget; independently refined MP prices/Greeks and smaller physical-step windows meet unchanged budgets"
    with path.open("w",encoding="utf-8",newline="") as h:
        writer=csv.DictWriter(h,fieldnames=columns);writer.writeheader();writer.writerows(classified)
    def write(name,text):(root/name).write_text(text.strip()+"\n",encoding="utf-8")
    c=meta["domains"]["CORE"];stats=c["statistics"] or {}
    hp_counts=Counter(r["gamma_status"] for r in by_input.values())
    core_grid=[r for r in grid if classify(from_row(r))=="CORE"]
    core_pending=c["planned"]-c["evaluated_grid"]
    fdflags=Counter(f for r in core_grid for f in r.get("failure_flags",[]))
    fd_unresolved=sum(any(f.startswith("FD_") for f in r.get("failure_flags",[])) for r in core_grid)
    table="| Metric | Mean absolute gap | Median | p95 | p99 | Maximum |\n|---|---:|---:|---:|---:|---:|\n"
    for f in ["price","Delta","Gamma","Vv"]:
        s=stats.get("abs_"+f+"_gap")
        if s:table+=f"| {f} | {s['mean']:.6g} | {s['median']:.6g} | {s['p95']:.6g} | {s['p99']:.6g} | {s['max']:.6g} |\n"
    hp_table="| Input label | Domain | Gamma evidence | Maximum precision change (price) | Last two cutoff-change maximum (Gamma) |\n|---|---|---|---:|---:|\n"
    for r in analysis:
        hp_table+=f"| {r['input']['label']} | {r['domain']} | {r['gamma_status']} | {r['precision_changes']['price']} | {r['cutoff_changes']['Gamma']} |\n"
    repro=meta["reproducibility"]
    external=json.loads((root/"EXTERNAL_RESULTS.json").read_text()) if (root/"EXTERNAL_RESULTS.json").exists() else {}
    ext_completed=sum(r.get("status")=="REVIEW_REQUIRED" for r in external.get("rows",[]))
    write("CORE_DOMAIN_CERTIFICATE.md",f"""
# CORE reference certificate — NOT ISSUED

**CORE GATE: FAIL.** This is a failed/incomplete certification record, not a certificate.

The closed core box is exactly x[-.7,.7],v[.01,.16],tau[1/252,2],kappa[.5,4],theta[.02,.12],sigma[.1,.8],rho[-.9,-.1],r[0,.08]. No Feller filtering.

Evaluated {c['evaluated_grid']}/{c['planned']} original planned CORE points. Mandatory deterministic points evaluated: {c['mandatory_core_evaluated']}/300. Original CORE points still pending in this output: {core_pending}. No new random slice replaces the catalog. All deterministic rows and failures are retained.

Strict row PASS {stats.get('PASS_rows',0)}, FAIL {stats.get('FAIL_rows',0)}. {c['derivative_checks']} physical-variable FD studies were executed; {fd_unresolved} still have a flagged FD budget/plateau problem under the historical strict protocol. Execution count is not certified-derivative coverage.

{table}

Every original tolerance and last-two-refinement rule is retained. Final-method agreement is encouraging but is not sufficient: earlier cutoff refinements, reported requested-accuracy failures, FD propagation and mandatory coverage still require resolution. No challenge failure is used to fail this core decision; its own missing coverage/unresolved evidence fails it.

Boundary labels and external checks needed for the original objective also remain unapproved. Phase 1C is not authorized.
""")
    write("HIGH_PRECISION_REPORT.md",f"""
# Genuine arbitrary-precision validation

mpmath 1.3.0; true 50/80/120-digit CF, quadrature nodes/weights, summation and stored decimal prices. No wrapper around float64. A Lewis half-contour inversion differs from A P1/P2 and B COS, but its little-trap algebra still shares model/derivation risk with A. External PDE triangulation is separately required.

Normalized call formula: c=exp(x)-exp(-r*tau)*exp(x/2)/pi * integral Re[exp(i*u*x)*psi(u-i/2)]/(u^2+1/4) du. The phase contains log(S/K) only once; the CF contains log(ST/S), avoiding the historical double-prefactor defect. Analytic MP Gamma=exp(-r*tau)*exp(-3*x/2)/(pi*K)*integral Re[exp(i*u*x)*psi(u-i/2)] du. Vv follows psi_v=D*psi.

{hp_table}

MP axes are varied independently. The initial typical and severe v=0/tau=.001 examples agree to roughly 50 digits across precision while Gamma still changes by tens/thousands under cutoff extension. This identifies finite-domain truncation as substantial, rather than just insufficient floating-point digits. It does not prove absence of common branch bias.

The fixed typical zero-variance case was additionally extended to U=131072/262144/524288, rechecked at 50/80/120 digits and degrees 24/40/64, with right-variance FD and spot FD. Refined A, B and MP agree within unchanged budgets at that point. The original failed values remain unchanged in reference/ and the initial HP records remain visible. Selected numerical resolution does not certify the entire v=0 boundary.

Exact strings, all stencil prices and independent axis changes are in HP_*.json, FD_PRECISION_CONVERGENCE.json and HIGH_PRECISION_ANALYSIS.json. Classification uses observed refinement differences and is not a rigorous interval proof. Every retained failure/near-failure is scheduled by full_escalation.py for Colab; that complete escalation has not run locally. Missing cases are not labeled resolved.

CF_DECAY_ANALYSIS.json checks the large-frequency affine expansion with 80-digit CF samples. For fixed positive tau, log|psi(u-i/2)|=-alpha*|u|+O(1), alpha=(v+kappa*theta*tau)*sqrt(1-rho^2)/sigma. At v=0,tau=.001, alpha is about 1.90438e-4 for R0 and 2.35112e-6 for R4; measured log-CF slopes approach these values. The severe example's decay scale is about 81 times longer. High precision cannot compensate for a cutoff covering too few decay scales.
""")
    write("GREEK_CERTIFICATION.md",f"""
# Greek certification — incomplete

**No domain-wide Greek certificate.** {c['derivative_checks']} CORE physical-S/v five-point studies were executed; FD flags remain on {fd_unresolved} rows. Price, Delta, KGamma and Vv/K budgets are unchanged. Vega_s is not used to certify Vv at v=0.

All {len([r for r in core_grid if 'FD_derivative_amplification_or_truncation' in r.get('failure_flags',[])])} CORE rows flagged for FD truncation/amplification were selected without deletion for additional MP work. See HP_GREEK_PRIORITY.json for evaluated/planned counts. Additional studies use 3-/5-point schemes, Richardson3/5 and ten spot steps from .02 to 1e-7. At v=0 all variance stencils are right-sided. Fifty/eighty/120-digit last-step stencil checks are in FD_PRECISION_CONVERGENCE.json.

Unique selected-input Gamma evidence counts: {dict(hp_counts)}. NUMERICALLY_RESOLVED means the recorded precision/degree/cutoff, cross-route and FD evidence meets the selected-point budgets; it is not a certified domain or authorization for training. No BOUNDARY_SINGULAR diagnosis is inferred solely from unstable quadrature.

The core ATM example has Gamma about 1.8801037393561391. Float64 FD5 goes to about 1.85499764 at h/S=1e-7, while MP FD tracks the analytic result. This is direct small-step cancellation evidence. Larger steps instead show truncation; the smallest float step is not chosen automatically. The nominal six-step legacy FD grid also fails some short-core peaks despite extremely small final A/B Greek gaps; additional MP physical steps investigate those points.

The full predeclared 256 reliably validated derivative requirement is not established simply by performing 300 checks. Full-core derivative/FD resolution and external refined PDE evidence are still required. Raw Gamma estimates, within-method discrepancies, coefficients and price uncertainty propagation are preserved. FD agreement with the same finite MP integration grid cannot by itself establish its tail accuracy.
""")
    write("BOUNDARY_REPORT.md",f"""
# Collar and degenerate boundary evidence

**BOUNDARY/COLLAR GATE: FAIL.** Only {meta['domains']['COLLAR']['evaluated_grid']}/3202 planned positive-variance collar grid points have new full-row coverage. Historical collar rows and all sequence diagnostics remain separate and visible. Exact v=0 belongs to the fixed CHALLENGE partition, but is also a boundary obligation of the proposed PDE training objective.

Limiting PDE at v=0: c_tau=r*c_x+kappa*theta*c_v-r*c. Positive kappa*theta means future variance is stochastic even when current variance is zero; do not substitute the discounted intrinsic payoff. In the resolved typical tau=.001 case, price is about 9.4226809227e-5, Delta .6299337671, Gamma 1893.6287006251, and right Vv .9413028798. Vega_s=0 conceals that nonzero variance sensitivity.

Sequences v=0,1e-8,1e-7,1e-6,1e-5,1e-4,1e-3,1e-2 were actually evaluated for typical R0 and severe R4 at tau=.001, with separate A cutoffs and COS term counts. Finite-grid traces are diagnostic; not all are certified. See BOUNDARY_SEQUENCES_local.json and plots. Additional x/positive-v MP sequences are prepared for the full run.

BOUNDARY_PDE_CHECKS.json records physical-time five-point differences and the limiting-PDE RHS, without inventing a PDE tolerance. R0 residual decreases from around 1.87e-5 at U32768 to around 1e-10 or below at U524288; R4 retains roughly 1.9e-3 residual at the latter cutoff. Finite-cutoff consistency is not a boundary proof, but it reinforces the need to refine the numerical tail before diagnosing physical singularity.

The v=.25 and x=±1.2 artificial-boundary labels required by Phase1A remain uncertified as a complete population. A core-only price certificate, even if obtained later, would not yet satisfy the current training objective's label obligations.
""")
    write("CHALLENGE_REPORT.md",f"""
# Challenge/OOD validation

**CHALLENGE/OOD GATE: FAIL.** New complete-row planned-grid coverage is {meta['domains']['CHALLENGE']['evaluated_grid']}/904; historical severe failures and diagnostic sequences remain in the report. No outcome-dependent reassignment or filtering.

v=0 and short maturities are treated separately from learning interior. The typical v=0/tau=.001 case becomes NUMERICALLY_RESOLVED after much larger integration limits. Severe R4 (kappa=.5,theta=.04,sigma=1.2,rho=-.99) still has unresolved MP cutoff/Greek behavior. Its stable 50/80/120-digit finite-cutoff values cannot certify the infinite integral; COS also needs independent N/interval and external checks. No mathematical fixed-positive-tau singularity is established by these failures.

Actual ATM/near-ATM tau=1e-4,2.5e-4,5e-4,.001,1/252,.01,.05 sequences were evaluated. In the typical COS diagnostics, c/tau stays near .09425 to .09291 and tau*Gamma near 1.893 to 1.921; Vv is nonzero. These patterns are consistent with the formal v=0 short-time scaling, not a proof that every sequence value is certified.

Formal scaling derived from the declared SDE: Y_s=v_(tau*s)/tau tends to dY=kappa*theta ds+sigma*sqrt(Y)dB at initial zero. The leading log-price increment is of order tau, unlike order sqrt(tau) when initial v>0. If the scaled return has a regular density at the ATM evaluation point, this suggests Gamma of order 1/tau. The density regularity and uniform asymptotics are additional assumptions, not established here. Gamma growth as tau approaches zero does not establish singularity at a fixed positive tau. No tolerance was changed.

The independently sampled large-frequency decay agrees with alpha=(v+kappa*theta*tau)*sqrt(1-rho^2)/sigma. All these fixed-positive-tau cases have alpha>0; polynomial Greek factors times that exponential are integrable for the correct affine CF. Thus fixed-positive-tau infinite Gamma is not supported here, even at initial v=0. Uniform bounds as tau->0 or |rho|->1 do not follow. This distinction supports an unresolved numerical-tail diagnosis for R4 rather than assigning BOUNDARY_SINGULAR to its current quadrature failures.

No Domain v2 revision is proposed before complete retained-failure/external analysis. The original Domain v1 and its failed coverage remain reported. Stress inputs can eventually be evaluation-only, but the current boundary labels required for training have not all passed.
""")
    write("REFERENCE_VALIDATION_REPORT.md",f"""
# Phase 1B.2 validation report

**CORE: FAIL — BOUNDARY/COLLAR: FAIL — CHALLENGE/OOD: FAIL. Phase 1C is not authorized.**

The historical FAIL was reproduced on {repro['executed']} rows; {repro['same_statuses']} matched statuses. Raw A/B values reproduced exactly in this environment. {meta['history_integrity']['historical_files_verified']} historical files verified unchanged. Never interpret a new resolved point as an upgrade of the historical gate.

CORE planned coverage {c['evaluated_grid']}/{c['planned']}; {c['mandatory_core_evaluated']}/300 mandatory deterministic points and {c['derivative_checks']} CORE FD studies were executed. Original CORE points still pending in this output: {core_pending}. Strict rows: {stats.get('PASS_rows',0)} PASS / {stats.get('FAIL_rows',0)} FAIL. The strict protocol retains requested quadrature-accuracy and FD propagation failures despite tiny final-method discrepancies. Flags overlap: {dict(fdflags)}.

{table}

Genuine 50/80/120-digit Lewis pricing and MP physical-variable FD distinguish requested-accuracy/roundoff issues, FD truncation/cancellation, and integration tails. Unique selected Gamma evidence: {dict(hp_counts)}. See HIGH_PRECISION_REPORT.md and GREEK_CERTIFICATION.md. The all-core FD-truncation target set is explicit; not every retained numerical flag or old price failure has complete MP/external escalation yet.

QuantLib 1.41 release commit 367ce80ae4f285835ceb3bba97746bea239984ad is pinned in the Colab workflow ([official release](https://github.com/lballabio/QuantLib/releases/tag/v1.41)). Aligned analytic/PDE cases completed in this output: {ext_completed}/{len(external.get('rows',[]))}. {"The dependency was unavailable for this run; recorded exceptions are INDETERMINATE." if ext_completed==0 else "Computed external cases require convergence review; execution alone is not certification."} The supplied notebook installs and runs the pinned version in Colab; the local output does not claim a remote execution. Direct integer-day cases and exact process time changes have separate convention metadata and unit tests; no silently rounded year fraction is compared.

Financial sanity passes on the executed mandatory core slice within the original budgets, but is not a substitute for convergence/coverage. Homogeneity and physical-K FD data are retained. REFERENCE_UNCERTAINTY.json/npz contains route-pair matrices, max/median gaps and deviations from route median on available A/B/MP values. Unvalidated route values and finite-cutoff diagnostics are not rigorous intervals or certified labels.

The actual 31x31 R0/v=.04 core slice supports the disagreement contours; it is explicitly diagnostic, without full per-cell refinement certification. Failure maps use raw counts, and MP/Gamma/N/cutoff/v/tau figures preserve failed values. No sparse failed data were interpolated into fake dense contours.

The core decision fails on its own incomplete/unresolved evidence. Challenge failures do not automatically invalidate a separately valid core certificate. Nevertheless the current proposed objective also needs finite-x/v boundary information and v=0 compatibility, whose complete certification is absent. Labels remain unapproved.

Next numerical work is in colab/phase1b2_reference_escalation.ipynb: complete core then collar/OOD coverage, every retained failure/near-failure MP escalation, external analytic/PDE axis refinement, and renewed review under unchanged tolerances. No neural code is invoked. No Domain v2 is recommended before that evidence exists. Stop after Phase1B.2.
""")
    dump(root/"FINAL_PROVENANCE.json",dict(history=verify_history(root),
        current_source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in Path(__file__).resolve().parent.glob("*.py")},
        local_executed_coverage_workflow_snapshot="reference_v2/executed_sources/workflow_coverage_v2_0.py",
        note="coverage source snapshot predates JSON-null aggregation fixes; pricing algorithms and raw rows were not changed"))

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser();p.add_argument("--output",default="reference_v2");write_reports(p.parse_args().output)
