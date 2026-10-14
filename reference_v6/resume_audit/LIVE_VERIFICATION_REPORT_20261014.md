# Live production resume verification — 2026-10-14

Verified in the authenticated Colab runtime against the original mounted Drive
directory, not an old audit ZIP. Full 128-case production remains stopped.
No CORE sweep or neural training was executed. The frozen protocol, blinded
inputs, tolerances and acceptance rules were not changed.

Executor commit: `07283f898aedcffeb1f15bc82df9bd307f4ffeb5`.
Original output: `/content/drive/MyDrive/MartingaleONet/reference_v6_colab`.
Evidence: `/content/drive/MyDrive/MartingaleONet/reference_v6_resume_verification_20261014T011655Z`.
Archive: the same evidence path followed by `_results.zip`.

## Actual findings

The previous production environment identifies commit `ab9f4fb7...` and runner
hash `3a37abbe...`; the updated preflight identified `0d8d7eb...` and
`05cef6ed...`. Before this live audit, v6_00_1 had no resume journals and the
audit folder had no hydration report. The previous updated preflight had not
established a matching updated execution/hydration. The new notebook launches
fresh subprocesses from an explicitly pinned, independently named checkout;
the CLI verifies the commit, import directory and source bytes before work.

The E1 and E2 old/new serialized keys are byte-identical in
`LIVE_KEY_COMPARISON_20261014.json`. Source hash, protocol identity and git commit
are not raw-key components. For these examples no mismatch exists in span,
Decimal representation, estimator configuration or legacy key schema. Worker
state restoration is also covered by a fresh-process synthetic test.

The four user-reported timings match four newly created five-time-coordinate
raw files. Their coordinate set differs from the old base-coordinate files;
all four old base-coordinate files retain their prior byte hashes. Full keys
and exact matching timings are in `LIVE_REPORTED_TIMING_KEYS_20261014.json`.
This example supports new time-stencil work, not duplicate base-key pricing.
It does not establish zero waste across every older keyless production log.

The live audit additionally exposed a DriveFS heartbeat replacement race. That
race was fixed with bounded lease-read retries and a resource stop if ownership
cannot be verified. Workers receive their completed-key catalog directly from
the verified parent plan, so temporary file invisibility cannot authorize
recomputation. A separate raw-file I/O stall used 1 CPU second in more than
7 minutes; stopping that read-only process and using the official flush/remount
resolved it. Existing checkpoints were not deleted or rewritten.

## Actual journals and imported keys

| Pending case | Imported E1 | Imported E2 | Journals | Next saved position |
|---|---:|---:|---:|---|
| v6_00_1 | 236 | 92 | 15 | E2 N=32768, L=24, dps=120; node 12288 |
| v6_00_3 | 114 | 7 | 5 | E1 cutoff=262144, degree=64, dps=80; node 45056 |
| v6_01_3 | 180 | 7 | 8 | E1 cutoff=8192, degree=24, dps=120; node 12160 |

The exact v6_00_1 catalog path is:

```
/content/drive/MyDrive/MartingaleONet/reference_v6_colab/cases/v6_00_1/resume/raw_catalog_b1362a4c8e3714114ba0c05da69ef84df30525e9507e3d9460393ae33bc931c8.json
```

Its state contains 328 completed key-to-file-SHA256 entries. Exact paths and
complete journal contents for these three cases are saved in
`LIVE_ACTUAL_JOURNALS_20261014.json`; the hydration report records exact imported
counts and next missing configurations. Hydration pricing calls: **0**.
`LIVE_THREE_CASE_REUSE_20261014.csv` lists all 636 completed keys, original-byte
comparisons and current REUSED classifications. This verification recomputed
no completed numerical key for these three cases: duplicate kernel time **0**.
That scoped result is distinct from the incomplete historical timing audit.

## Actual zero-pricing plan and bounded smoke

The final real-directory plan covers **105 pending cases**, with 4,083 reusable
E1 and 481 reusable E2 evaluations after the one-result addition. The E1 total
was already 4,083 before the smoke in the accepted hydration report. A prior
earlier inventory had 4,082; the difference is not a second smoke kernel call.
The plan and hydration call no pricer. Future adaptive missing counts remain
explicitly UNKNOWN until preceding numerical values exist; each current causal
frontier and its first missing key is reported exactly.

The required v6_00_1 cutoff=65536/degree=24/dps=120 key
`2363ac445ab63eddd1fdfcab278b1930bf305d93e6c159872a7739ee94f6691a`
is classified **REUSED**. No pricing kernel was invoked for it.

Only after that proof, a controlled smoke selected **v6_09_2 only**, whose
frontier was genuinely new rather than partial. Actual stdout contains:

```
83 REUSED E1/E2 events
v6_09_2 NEW E2 key=d44749c5c0dfd33c896a248a9ae4a86871632d4904f99d437002957b73106500 start_node=0
v6_09_2 E2 raw checkpoint saved: {'N': 16384, 'L': 24, 'dps': 120}, 16384 nodes, 59.9s
kernel_calls: 1
status: Smoke maximum ONE missing sub-evaluation
```

All 187 pre-existing files in that production case, including raw, partial,
journal, trace, event and RESULT files, retain identical hashes. The completed
single new raw result was then added using exclusive creation to its previously
absent production filename. No old file was overwritten or deleted. The final
zero-pricing plan confirms that this new key is now reusable, so continuation
does not repeat the smoke. Its next missing key is
`20321230b9c7ecbe2272ac701f6573bdbd7b7825148ef3ed9b2b855ac49bb00d`
(E2 N=16384, L=32, dps=50, the same five time coordinates).

Proof files: `LIVE_SMOKE_20261014.log`, `LIVE_SMOKE_REPORT_20261014.json`,
`LIVE_CASE_PRESERVATION_20261014.json`, `LIVE_APPEND_ONLY_PROMOTION_20261014.json`
and `LIVE_FINAL_VERIFICATION_20261014.json`.

## Continuing

Use `colab/phase1b6_verified_resume.ipynb` and `reference_v6/VERIFIED_COLAB_STEPS.md`.
The old launcher is retired. Run bootstrap, mount and zero-pricing plan. Existing
journals are already prepared; leave `RUN_ONE_SMOKE=False` because the live
smoke is complete. To continue manually after checking the current plan, use:

```python
command(["--execute-frozen-v6", "--workers", "2", "--plan-report", str(PLAN)],
        EVIDENCE / "PRODUCTION_CONTINUATION.log")
```

The wrapper always includes the original output directory, pinned commit and
expected source directory. Full production was **not** started by this audit.
All 18 synthetic infrastructure/executor tests passed, including interrupt/
resume, completed-key exclusion, exact partial-sum restoration for both
estimators, fresh-worker restoration, file invisibility and lease races.
