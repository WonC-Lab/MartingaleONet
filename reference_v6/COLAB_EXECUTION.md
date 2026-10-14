# Resume workflow replaced on 2026-10-14

Use `colab/phase1b6_verified_resume.ipynb` and [VERIFIED_COLAB_STEPS.md](VERIFIED_COLAB_STEPS.md).
The instructions below describe the historical launcher; do not use it to resume production.

# Phase 1B.6 Colab execution

Open `colab/phase1b6_boundary_certification.ipynb` in Colab and choose CPU.
The updated notebook starts in audit-only mode. Follow RESUME_INSTRUCTIONS.md
to inspect existing checkpoints, prepare legacy cursors without pricing, and
explicitly enable continuation. The notebook pins the executor Git commit,
installs `requirements-colab.txt` including QuantLib 1.41, verifies the immutable
v6 freeze and historical gate hashes, then runs only the new 128 inputs.
The original freeze's NOT_GRANTED records the state at freezing; it is preserved
as history. Running the explicit execution cell supplies current opt-in. There
is no local blinded execution during repository preparation.

Default persistent outputs:

```
MyDrive/MartingaleONet/reference_v6_colab/
MyDrive/MartingaleONet/reference_v6_colab_results.zip
```

Raw evaluations and exact MP partial accumulator checkpoints are under
`cases/<case_id>/raw/`. Component budget locks, physical stencils, time ladders,
per-case results, logs, environment/source receipts, failure CSV, figures and
final gate/report are all saved. Historical CORE and boundary evidence are
never outputs of this workflow. QuantLib is pinned for reproducibility; this
new targeted protocol does not repeat previous analytic/PDE validations.

The same steps from a fresh clone (Python 3.11 or newer):

```
python -m pip install -r reference_v6/requirements-colab.txt
python -m unittest reference_v6.test_executor -v
python -m reference_v6.run_boundary_certification --output reference_v6_colab --preflight-only
python -m reference_v6.run_boundary_certification --output reference_v6_colab --workers 4 --execute-frozen-v6
python -m reference_v6.run_boundary_certification --output reference_v6_colab --report-only
python -c "import shutil; shutil.make_archive('reference_v6_colab_results','zip','reference_v6_colab')"
```

Use at most the available CPU count and never more than four workers. An
invocation is capped at eight wall hours and 30 CPU minutes per case. Re-run the
same command against the same output directory to resume resource-limited
cases. A partial raw evaluation resumes its exact MP sums rather than starting
the large integral again. Each resume is another explicitly requested resource
allocation; caps are not relaxed or silently replenished inside a run. The log
prints one line at case completion; a quiet interval can represent quadrature
work. Checkpoint modification timestamps show progress within a case.

The initial 12–22-hour planning envelope already assumes four CPUs and covers
only optimized Lewis work, not the full independent COS/FD executor. This first
streaming executor shares CFs across same-time stencil coordinates and affine
variance shifts, but does **not** yet share full spectral prefixes across four
cases in a parameter block. Therefore it can cost more than that estimate;
actual execution timing is recorded and no completion time is promised. GPUs
are not used by these 50/80/120-digit mpmath algorithms.

The protocol, thresholds, population and seed are unchanged. Separate numerical
unit tests use synthetic inputs outside the 128 blinded cases. Unknown/error,
missing, unconverged, resource-limited or ceiling-hit cases cannot pass. A
coding error creates RUN_INVALID.json and blocks resume; the corruption policy
requires review and, for frozen-math bugs, a new protocol and unopened inputs.
This runner conservatively labels absent confirmed windows NUMERICAL_UNRESOLVED
rather than asserting the underlying Heston PDE is wrong. Phase 1C and training
remain unauthorized until a separate final review of all original requirements.
