# Production resume verification, 2026-10-14

Production remains paused. No 128-case pricing run is authorized during this audit.

Direct reads of the current Drive production folder found no `resume/` directory
for `cases/v6_00_1`, and the current audit folder had no `HYDRATION_REPORT.json`.
Consequently no completed keys had been imported into an actual v6_00_1 journal.
The expected catalog location is
`reference_v6_colab/cases/v6_00_1/resume/raw_catalog_<identity SHA256>.json`.
Its contents were absent, not an empty accepted journal.

The root execution receipt at 2026-10-13T23:48:26Z identifies legacy runner SHA256
`3a37abbe4166fb3176feca8f467e1b5ff4d87aa9bb066816b0364dd6e0d6ecb2`.
The 2026-10-13T04:30:44Z session compatibility receipt instead identifies commit
`0d8d7eba4a541e7ff9eba12283d83e0b5a9f61c0` and runner SHA256
`05cef6edc91fbfd0025cb508cdedbb09fd8257fbc7cfdb0224b45b37e1393d33`.
That session contains no execution receipt. A successful updated preflight does
not demonstrate that the updated production runner or hydration was executed.

For the following two current Drive raw files, old and newly generated serialized
keys are byte-identical. The key schema excludes source hash and git commit.
Protocol and frozen inputs are verified separately. No mismatch was observed in
span, Decimal serialization, estimator configuration, or legacy key schema for
these exact base-coordinate examples. Worker behavior must still be verified in
the actual mounted runtime; this document does not claim a completed live test.

E1, both old and new serialization (UTF-8, no trailing newline):

```json
["E1", {"cutoff": 65536, "degree": 24, "dps": 120, "span": "0.7828821507702551295545770651553198701772117476335202297285614208306828162876224155690620203833710701859581339157612028560234455254444409071164191092549061587090"}, [["-0.7", "0", "0.1"]]]
```

Both SHA256 keys: `2363ac445ab63eddd1fdfcab278b1930bf305d93e6c159872a7739ee94f6691a`.

E2, both old and new serialization:

```json
["E2", {"L": 32, "N": 16384, "dps": 80}, [["-0.7", "0", "0.1"]]]
```

Both SHA256 keys: `2770ab8d06a6c2a72d53626fc93236f503f194b0fc8ac5529f8c5a4f9f6567e3`.

Matching cutoff/degree/dps alone is insufficient: that E1 configuration exists
for a base coordinate and multiple distinct ten-coordinate physical stencils.
The user's reported four timings total 883.0 seconds. They establish expensive
kernel activity, but assigning this time to exact duplicate keys requires the
actual executed coordinate/key records. Existing raw files and log evidence are
preserved; duplicate time is not silently assumed to be zero.

The new plan mode reads all real raw checksums and all pending cases, and replays
metadata in a temporary overlay with the kernel patched to fail on any call.
It reports exact reusable E1/E2 totals, orphan resumable partials, the first
missing causal key, and whether that frontier needs a new or partial evaluation.
The total number of future adaptive missing evaluations is explicitly UNKNOWN:
future decisions depend on numerical values that do not yet exist.

The smoke mode validates the plan's current file hashes and the required E1 key,
prints `REUSED E1/E2` for checked completed keys, and permits at most one missing
kernel call in a new sibling evidence overlay. It never writes production raw,
partial, scientific trace, or RESULT files. A later full invocation additionally
requires the exact commit, import directory, matching plan and actual journals.
