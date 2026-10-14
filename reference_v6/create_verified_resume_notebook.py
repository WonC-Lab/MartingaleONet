"""Create a separately named, pinned notebook; default is zero pricing."""
import json
from pathlib import Path

REF='07283f898aedcffeb1f15bc82df9bd307f4ffeb5'
cells=[]
def md(z):cells.append({'cell_type':'markdown','metadata':{},'source':z.splitlines(True)})
def code(z):cells.append({'cell_type':'code','metadata':{},'source':z.splitlines(True),'execution_count':None,'outputs':[]})
md('''# Verify the REAL production resume before continuing
Stop the other production runtime first. CPU runtime. Run cells in order.
Default execution performs **zero pricing**. No CORE sweep or neural training.
The existing Drive folder must exist. No checkpoints are deleted.
The optional smoke test permits at most one missing sub-evaluation, in a NEW
sibling evidence folder. Full production remains disabled during the audit.
''')
code(f'''from pathlib import Path
import subprocess, sys, os, json, datetime
REF = "{REF}"
REPO = Path("/content/MartingaleONet_verified_" + REF[:12])
if not REPO.exists():
    subprocess.run(["git", "clone", "https://github.com/WonC-Lab/MartingaleONet.git", str(REPO)], check=True)
subprocess.run(["git", "checkout", "--detach", REF], cwd=REPO, check=True)
assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip() == REF
subprocess.run([sys.executable, "-m", "pip", "install", "-r", "reference_v6/requirements-colab.txt"], cwd=REPO, check=True)
ENV = dict(os.environ, PYTHONPATH=str(REPO), PYTHONUNBUFFERED="1")
def command(args, log):
    with log.open("w") as f:
        p = subprocess.Popen([sys.executable, "-m", "reference_v6.run_boundary_certification", "--output", str(OUT), "--expected-commit", REF, "--expected-repo-root", str(REPO)] + args, cwd=REPO, env=ENV, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        try:
            for line in p.stdout: print(line, end=""); f.write(line); f.flush()
            if p.wait(): raise RuntimeError("See " + str(log))
        except BaseException:
            p.terminate(); p.wait(); raise
''')
code('''from google.colab import drive
drive.mount("/content/drive")
OUT = Path("/content/drive/MyDrive/MartingaleONet/reference_v6_colab")
assert (OUT / "RUN_IDENTITY.json").exists(), "Wrong original folder/account"
assert (OUT / "cases").is_dir()
EVIDENCE = OUT.parent / ("reference_v6_resume_verification_" + datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
EVIDENCE.mkdir(exist_ok=False)
PLAN = EVIDENCE / "RESUME_PLAN.json"
command(["--resume-plan-only", "--plan-report", str(PLAN)], EVIDENCE / "PLAN.log")
target = "2363ac445ab63eddd1fdfcab278b1930bf305d93e6c159872a7739ee94f6691a"
entry = next(z for z in json.loads(PLAN.read_text())["cases"] if z["case_id"] == "v6_00_1")
assert target in {z["key"] for z in entry["completed"]}, "Required exact E1 key NOT reusable"
print("PROVEN REUSED E1", target)
print("Existing journals:", entry["journal_paths"])
''')
md('''## Hydrate unfinished cursors: zero pricing, preserve scientific files
This explicitly creates infrastructure journals in the ORIGINAL production tree.
Stop all old runtimes first. Never override an active lease. Inspect the saved
hydration report, imported catalog keys and actual journal contents below.
''')
code('''subprocess.run([sys.executable, "-m", "reference_v6.hydrate_legacy", "--output", str(OUT), "--audit-dir", str(EVIDENCE / "hydration")], cwd=REPO, env=ENV, check=True)
print((EVIDENCE / "hydration/HYDRATION_REPORT.json").read_text())
for case_id in ["v6_00_1", "v6_01_0", "v6_01_1"]:
    journals = OUT / "cases" / case_id / "resume"
    for path in sorted(journals.glob("*.json")):
        print("ACTUAL JOURNAL", path)
        print(path.read_text())
command(["--resume-plan-only", "--plan-report", str(PLAN)], EVIDENCE / "PLAN_AFTER_HYDRATION.log")
''')
md('''## Optional ONE-case smoke, at most ONE missing kernel call
Enable only after the exact reuse proof above. All existing production files
are read-only during smoke. Results stay in this new evidence overlay.
''')
code('''RUN_ONE_SMOKE = False
SMOKE_CASE = "v6_09_2"  # one pending case with a genuinely new frontier, no partial restart
if RUN_ONE_SMOKE:
    command(["--smoke-case", SMOKE_CASE, "--plan-report", str(PLAN), "--smoke-output", str(EVIDENCE / "smoke")], EVIDENCE / "SMOKE.log")
    print((EVIDENCE / "smoke/SMOKE_REPORT.json").read_text())
else:
    print("PAUSED. No pricing. Evidence:", EVIDENCE)
''')
md('''## Full continuation is paused
After a successful live smoke review, continuing requires a fresh plan and:
`--execute-frozen-v6 --workers 2 --expected-commit REF --expected-repo-root REPO
--plan-report PLAN --output ORIGINAL_OUT`. Use `command` above so logs are saved.
The smoke overlay is separate validation evidence, not production certification.
Do not use the old notebook's cached executor/runtime.
''')
notebook={'nbformat':4,'nbformat_minor':5,'metadata':{'kernelspec':{'name':'python3','display_name':'Python 3'},'language_info':{'name':'python'}},'cells':cells}
for i,c in enumerate(cells):c['id']=f'verified-resume-{i}'
Path('colab/phase1b6_verified_resume.ipynb').write_text(json.dumps(notebook,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
