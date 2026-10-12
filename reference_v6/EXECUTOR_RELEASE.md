# v6.0 Colab executor release

This release implements the executor deferred by the immutable protocol freeze.
The freeze, blinded inputs, tolerance formulas and receipt are unchanged. Source
committing and five synthetic numerical tests precede all blinded evaluations.
No blinded input was priced while preparing this release.

Verified locally: independent characteristic-function algebra; Lewis versus
hyperbolic COS prices/Delta/nu; fourth-order time-stencil signs and amplification;
synthetic sigma=0 positive-variance PDE signs; interrupted mid-sum checkpoint
resume giving exactly the same results as an uninterrupted evaluation. Preflight
verifies frozen Git blobs, current source hashes, pinned packages and historical
gate snapshots. Report-only testing shows 128 NOT_RUN, CORE calls zero, gate FAIL.

The executor streams scalar arbitrary-precision sums and evaluates same-time
coordinates together. It does not yet implement cross-case parameter-block
spectral prefix caching. Cost is consequently uncertain and can exceed the
original optimized four-CPU estimate. Use CPU, persistent Drive checkpoints and
explicit manual resumption after each capped invocation. No GPU speedup is
claimed. The actual new-128 numerical outcome is not yet known.

Outputs must go to the separate versioned `reference_v6_colab` directory. A
resource stop is pending, a refinement ceiling is unresolved, and a coding error
invalidates the run. A missing confirmed zero-consistency window is conservatively
unresolved rather than automatically labeled as a physical-model failure. No
thresholds are relaxed, no completed historical result is overwritten, and no
neural training or Phase 1C run is launched.
