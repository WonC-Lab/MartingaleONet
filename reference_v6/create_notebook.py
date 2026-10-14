"""Build the portable CPU notebook, with no execution outputs embedded."""
import json
import argparse
from pathlib import Path

if __name__=='__main__':
    raise SystemExit('Retired resume template. Use reference_v6/create_verified_resume_notebook.py and colab/phase1b6_verified_resume.ipynb.')

cells=[]
def md(text):cells.append({'cell_type':'markdown','metadata':{},'source':text.splitlines(keepends=True)})
def code(text):cells.append({'cell_type':'code','metadata':{},'source':text.splitlines(keepends=True),'execution_count':None,'outputs':[]})

md('''# Phase 1B.6 — frozen v6.0 limiting-v0 validation (CPU)

**Run this notebook, not the earlier Phase 1B.3 completion notebook.**
Only the new 128 frozen v0 inputs are evaluated. The 1,734-point CORE and old
600-point boundary sweeps are never launched. No training. The frozen protocol
and inputs remain byte-identical. Both estimators use 50/80/120-digit mpmath.

Choose a **CPU runtime**. GPU allocation does not accelerate these MP kernels.
The earlier 12–22-hour estimate was already a four-CPU estimate for the Lewis
part; the independent COS/FD overhead is additional and unmeasured. This first
executor prioritizes correctness and bounded memory; it may take longer.
Each invocation stops after 8 wall hours / 30 CPU minutes per case and saves
partial sums. Re-run the execution cell to continue resource-limited cases.
Ceiling failures and numerical failures never become PASS automatically.
''')
code('''from pathlib import Path
import os, subprocess, sys, shutil, json, signal
REPO_URL = "https://github.com/WonC-Lab/MartingaleONet.git"
REPO_REF = "__EXECUTOR_COMMIT__"  # replaced by the publication receipt commit
REPO = Path("/content/MartingaleONet_v6")
if not REPO.exists():
    subprocess.run(["git", "clone", REPO_URL, str(REPO)], check=True)
subprocess.run(["git", "fetch", "origin"], cwd=REPO, check=True)
subprocess.run(["git", "checkout", "--detach", REPO_REF], cwd=REPO, check=True)
os.chdir(REPO)
subprocess.run([sys.executable, "-m", "pip", "install", "-r", "reference_v6/requirements-colab.txt"], check=True)
''')
md('''## Persistent output (recommended)
Mount Drive to preserve checkpoints when Colab disconnects. Resume requires the
identical frozen protocol/input hashes and either the current tested executor
or the specifically verified ab9f4fb legacy source hashes. The original identity
is preserved. This notebook refuses a missing original output directory.
If Drive is disabled, download the ZIP before the runtime disappears.
''')
code('''USE_DRIVE = True
if USE_DRIVE:
    from google.colab import drive
    drive.mount("/content/drive")
    OUT = Path("/content/drive/MyDrive/MartingaleONet/reference_v6_colab")
else:
    OUT = Path("/content/reference_v6_colab")
OUT.mkdir(parents=True, exist_ok=True)
assert (OUT / "RUN_IDENTITY.json").exists(), "Wrong output directory or Drive account: original RUN_IDENTITY missing. Do not start a new run."
assert (OUT / "cases").is_dir(), "Original cases directory missing. Do not continue."
WORKERS = min(4, os.cpu_count() or 1)
ENV = dict(os.environ, PYTHONUNBUFFERED="1")
def run_logged(arguments, name):
    with (OUT / name).open("a", encoding="utf-8") as log:
        command = [sys.executable, "-m", "reference_v6.run_boundary_certification", "--output", str(OUT), *arguments]
        log.write("\\nCOMMAND: " + repr(command) + "\\n"); log.flush()
        process = subprocess.Popen(command, cwd=REPO, env=ENV, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, start_new_session=True)
        try:
            for line in process.stdout:
                print(line, end=""); log.write(line); log.flush()
            returncode = process.wait()
        except BaseException:
            # Colab Stop must not leave the executor/pool writing in background.
            try: os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError: pass
            try: process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                try: os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError: pass
                process.wait()
            raise
        if returncode:
            raise RuntimeError(f"Executor exited {returncode}; inspect {OUT / name}")
print("CPU workers:", WORKERS, "Outputs:", OUT)
run_logged(["--preflight-only"], "PREFLIGHT.log")
''')
md('''## Read-only resume audit — run before any production continuation
The original checkpoints and RUN_IDENTITY are preserved. The specific original
ab9f4fb executor is accepted through tested infrastructure compatibility; arbitrary
hash changes still fail. Audit every raw checksum/key and all partial accumulator
layouts without pricing. Tables include exact coordinates and checkpoint keys.
Keep production stopped while inspecting this report. Different runtimes must
not execute this same output directory simultaneously.
''')
code('''AUDIT = OUT.parent / "reference_v6_resume_audit"
subprocess.run([sys.executable, "-m", "reference_v6.audit_resume", "--output", str(OUT), "--audit-dir", str(AUDIT)], cwd=REPO, env=ENV, check=True)
AUDIT_SUMMARY = json.loads((AUDIT / "AUDIT_SUMMARY.json").read_text())
print("CHECKPOINTS_ACCEPTED:", AUDIT_SUMMARY["CHECKPOINTS_ACCEPTED"])
print("Per-case inventory:", AUDIT_SUMMARY["case_inventory"])
AUDIT_ZIP = Path(shutil.make_archive(str(AUDIT), "zip", root_dir=AUDIT))
print("Audit ZIP:", AUDIT_ZIP)
ALLOW_PRODUCTION_RESUME = False  # audit only by default; set True only after reviewing the audit
TAKEOVER_STALE_LEASE = False  # only after other runtime stopped and >=180 seconds since its heartbeat
''')
md('''## Prepare legacy resume positions without pricing
After reviewing the audit, run this cell. It reads completed checked raw files
once to create new infrastructure journals, and stops at each first missing raw
sub-evaluation. It cannot call a pricer and never overwrites old scientific
traces, raw checkpoints, partial sums or case RESULT files. Future execution
then starts directly at these saved cursors. Stop all older runtimes first.
''')
code('''PREPARE_RESUME_JOURNALS = False  # change to True after inspecting the read-only audit
if PREPARE_RESUME_JOURNALS:
    assert AUDIT_SUMMARY["CHECKPOINTS_ACCEPTED"]
    prepare_args = [sys.executable, "-m", "reference_v6.hydrate_legacy", "--output", str(OUT), "--audit-dir", str(AUDIT)]
    if TAKEOVER_STALE_LEASE: prepare_args += ["--takeover-stale-lease"]
    subprocess.run(prepare_args, cwd=REPO, env=ENV, check=True)
    print((AUDIT / "HYDRATION_REPORT.json").read_text())
else:
    print("PAUSED: legacy journal preparation not requested.")
''')
md('''## Start / resume the targeted calculation
This is the only expensive cell. It invokes the committed executor explicitly.
It logs case completion and checkpoints raw quadrature/COS sums every 4,096
nodes and at resource stops. Completed PASS cases and completed raw evaluations
are reused. Resource-limited cases resume; numerical ceiling failures stay
unresolved. The full gate stays FAIL until every one of the 128 inputs passes.
An executor error invalidates the run and requires review, not repeated retries.
''')
code('''if not ALLOW_PRODUCTION_RESUME:
    print("PAUSED: audit only; no production calculation started.")
else:
    assert AUDIT_SUMMARY["CHECKPOINTS_ACCEPTED"], "Audit rejected checkpoints"
    try:
        args = ["--workers", str(WORKERS), "--execute-frozen-v6"]
        if TAKEOVER_STALE_LEASE: args += ["--takeover-stale-lease"]
        run_logged(args, "EXECUTION.log")
    finally:
        run_logged(["--report-only"], "REPORT.log")
        ZIP = Path(shutil.make_archive(str(OUT.parent / "reference_v6_colab_results"), "zip", root_dir=OUT))
        print("Saved:", ZIP)
''')
md('''## Rebuild reports / export / download
Run this cell after an interrupt, or at any time to inspect saved checkpoints.
A partial ZIP is evidence of progress, not certification. Resume the expensive
cell until no cases remain pending, or return the ZIP for failure analysis.
''')
code('''from google.colab import files
if not ALLOW_PRODUCTION_RESUME:
    files.download(str(AUDIT_ZIP))
else:
    run_logged(["--report-only"], "REPORT.log")
    ZIP = Path(shutil.make_archive(str(OUT.parent / "reference_v6_colab_results"), "zip", root_dir=OUT))
    print((OUT / "FINAL_VALIDATION_REPORT.md").read_text())
    print("Result ZIP:", ZIP)
    files.download(str(ZIP))
''')
parser=argparse.ArgumentParser();parser.add_argument('--executor-commit',default='__EXECUTOR_COMMIT__');args=parser.parse_args()
for cell in cells:
    if cell['cell_type']=='code':cell['source']=[line.replace('__EXECUTOR_COMMIT__',args.executor_commit) for line in cell['source']]
notebook={'cells':cells,'metadata':{'colab':{'name':'phase1b6_boundary_certification.ipynb'},
          'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'language_info':{'name':'python'}},'nbformat':4,'nbformat_minor':5}
path=Path(__file__).resolve().parent.parent/'colab/phase1b6_boundary_certification.ipynb'
for i,cell in enumerate(cells):cell['id']=f'v6-cell-{i:02d}'
path.write_text(json.dumps(notebook,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
