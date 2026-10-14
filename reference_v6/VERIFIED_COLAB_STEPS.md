# Continue the existing production folder safely

Open `colab/phase1b6_verified_resume.ipynb` in Colab. Stop the older production
runtime first; closing its browser tab does not stop its subprocesses. Use CPU.

1. Run bootstrap: a new `/content/MartingaleONet_verified_940937a76aaa`
   checkout is pinned to `940937a76aaaaf73495939ae9b9ff772b509df6c`. A new Python
   subprocess checks HEAD, source bytes and imported runner directory every time.
2. Run Drive/plan cell. It refuses a missing original
   `/content/drive/MyDrive/MartingaleONet/reference_v6_colab` folder. It saves
   `RESUME_PLAN.json` and `PLAN.log` in a newly timestamped sibling
   `reference_v6_resume_verification_<UTC>`. This invokes
   `--resume-plan-only --plan-report <PLAN>` and performs zero kernel calls.
3. Inspect the printed proof for E1 key
   `2363ac445ab63eddd1fdfcab278b1930bf305d93e6c159872a7739ee94f6691a`.
   Each pending case has reusable E1/E2 and partial counts and its first missing
   causal key. Unknown later adaptive counts are not estimates of zero.
4. Run hydration cell. It invokes `reference_v6.hydrate_legacy --output <OUT>
   --audit-dir <EVIDENCE>/hydration`. It creates journals, saves exact imported
   E1/E2 counts and journal paths, and prints actual journal contents. All old
   raw/partial, scientific traces, identities and RESULT files remain intact.
   The plan is regenerated after hydration so journal hashes agree.
5. Only after the reuse proof, set `RUN_ONE_SMOKE=True` in the optional cell.
   It invokes `--smoke-case v6_00_1 --plan-report <PLAN> --smoke-output
   <EVIDENCE>/smoke`. It emits checked REUSED events before at most one missing
   numerical evaluation. Its hard kernel cap is one; only that single case is
   selected. Results/partials are confined to the new smoke evidence overlay.
6. Keep full production paused until the live smoke report confirms at most one
   kernel call and unchanged production files. After review, regenerate the plan
   and use the notebook's `command` function with
   `["--execute-frozen-v6", "--workers", "2", "--plan-report", str(PLAN)]`.
   `command` always appends the exact commit/repository/output guards and saves
   stdout. The full runner rejects absent hydration or changed checkpoint trees.

Do not change the original output folder, protocol, blinded inputs, thresholds,
or acceptance rules. Do not delete Drive files. The smoke overlay is external
validation evidence, not a case PASS or an amendment to certification results.
