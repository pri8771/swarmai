# Failure diagnosis and settled-source review

## Source progression

- Accepted base: `ba458eb1a9a1af5f7e022159f36e6ce296d472cc`.
- Provisional candidate: `0c2589b9e62d501f2ca177b035355508107f1d6b`, tree `a6154f3da9038fd44b2c2afe12d296e87e048bf0`.
- Settled candidate: `1ea1ca55a2470d94fe704d64c029a991c3c0dea5`, tree `1b8577c91b2984b804ea6df259e6a47a697ccc31`.
- Settled worktree status was clean (`status_porcelain_bytes=0`).

## Preserved adverse evidence and closure

`provisional-full-failed.log` is retained unchanged: 41 failed / 571 passed, pytest exit 1, disposable PostgreSQL cleanup 0. It contains 40 direct `ApiMcpAdapter.__init__() missing ... 'manifest'` exceptions; the remaining failure is downstream from the same child/helper incompatibility.

`provisional-to-settled.diff` shows the exact four-file, test-only compatibility correction:

1. `_effect_crash_child.py` supplies the canonical `mcp.echo@1` manifest to its adapter subclass.
2. `_effect_tx_child.py` does the same for its pausing adapter.
3. `test_effect_transactions.py` adds the same constructor to `RaisingAdapter`, covering its parameterized callers.
4. `test_effect_crash_window.py` supplies the now-required canonical manifest digest to its two direct private `_finalize` test calls.

No production file changed between the provisional and settled candidates. The focused compatibility rerun passed 35 tests on disposable PostgreSQL, and the full settled run passed 612 tests with cleanup 0. This closes the observed compatibility failure without weakening the new production contract.

The zero-byte `baseline-root-initial-import-failure.log` is also intentionally retained. The initial baseline invocation omitted explicit `PYTHONPATH`; stderr was not captured into that file. `baseline-root-corrected.log` is the successful corrected repeat.

## Independent production review

A bounded read-only review found no concrete released-scope defect in manifest strictness, recursive key/value secret scanning, foreign-class checks, per-operation classification, canonical digest calculation, execute/reconcile receipt propagation, immutable replay, or nonmutating historical read compatibility. This review was source inspection plus the retained focused evidence; it is not formal acceptance.

Recursive `load_all` duplicate rejection across subdirectories matches directory-level uniqueness. The dynamic legacy manifest uses `network_scopes=["*"]` as the coarse replacement for the former unrestricted boolean and retains literal `network` operation authority.

The local file-backed manifest declares `/tmp/swarm-sandbox`, while tests may inject another bounded `root=`. Its receipt digest binds the declared default scope, not the injected instance root. Existing traversal and actual-root confinement remain. R29a did not release filesystem-scope enforcement, so this is recorded as a limitation rather than expanded into another repair.
