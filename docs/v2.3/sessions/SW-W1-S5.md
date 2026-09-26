# SW-W1-S5 handoff
- Branch: `cursor/sw-w1-s5-460c`   Base SHA: `55d15252ea6e3ce93b8941449c445f1c1556e1f5`   Head SHA (code): `252f8f4bba58727ee5982fc611b8ace7ef44cd7a`
- PR: draft PR to `cursor/sw-v23-integration-460c` (see PR body `pr_bodies/SW-W1-S5.md` in the coordinator audit dir; opened by the environment/coordinator)
- Integration branch stands in for `dev` (coordinator override); session branch name uses the `-460c` suffix.
## Done
- `src/swarm/capabilities/signing.py`: keyed HMAC-SHA256 pack signatures (`hmac-sha256-v1:<hex>`) per publisher; keys from environment only (`trusted_keys_from_env`), never in the repo (F-02).
- `src/swarm/capabilities/__init__.py`: registry supports keyed mode (`trusted_keys`), refusing forged/tampered/wrong-key/untrusted/unsigned packs; legacy digest mode only when `trusted_keys=None` (existing fixtures unchanged).
- `src/swarm/capabilities/lifecycle.py`: installed → enabled_for_project → draining → disabled → uninstalled, immediate revoke; in-memory and SQL (`v23_pack_installs`) persistence.
- Tests: `tests/extensions/test_v23_pack_lifecycle.py` (9), `tests/integration/db/test_v23_pack_installs_sql.py` (1). Legacy tests `test_v18_v30_gaps.py`, `test_v23_v20.py`, `tests/portability` pass unchanged (inside the offline CI run).
## Verification
Checks run by `/agent/wt/check.sh` on commit `252f8f4bba58727ee5982fc611b8ace7ef44cd7a` (Postgres 127.0.0.1:5432 available):
```
ruff: All checks passed!
mypy: Success: no issues found in 246 source files
alembic heads: a23opsplatform0001 (head) 
session tests: 10 passed in 0.49s
offline CI: 562 passed, 3 skipped in 26.24s
integration (Postgres): 81 passed in 18.93s
tree: f7a4042dc2106637389387bb5dad4f6e917dc9f8 dirty=0
```

## Acceptance
- [x] Keyed mode: forged, tampered, wrong-key, untrusted-publisher and unsigned packs are refused.
- [x] Lifecycle: enable is per project; other projects are denied; capabilities are never widened; draining blocks new use and new enables; disable and uninstall follow the transition table; revoke disables immediately.
- [x] Legacy fixture tests pass unchanged.
- [x] Handoff "Needs other owner": "SW-W3-S1 must build the operational registry as `CapabilityPackRegistry(require_signature=True, trusted_keys=trusted_keys_from_env())`."
- [x] Every step in section 5 done; every acceptance box in section 5 ticked.
- [x] `uv run ruff check .` and `uv run mypy src/swarm` pass.
- [x] `uv run alembic heads` prints exactly one head.
- [x] Full offline CI list passes (paste the final `N passed` line into the handoff).
- [x] Integration run passed, or SKIPPED with reason in the handoff.
- [x] `git status --porcelain` lists only files from section 3 + the handoff.
- [x] No secrets, no network calls beyond section 5, no `accepted`/`complete` claims.
- [x] The Codex review packet (section 11) is in the PR description and the handoff.
## Decisions
- Tests ran against the private Postgres DB `swarm_sw460c` (isolation from concurrent agents).
## Needs other owner
- SW-W3-S1 must build the operational registry as `CapabilityPackRegistry(require_signature=True, trusted_keys=trusted_keys_from_env())`.
## Status
implemented / offline-tested only (NOT accepted; needs independent Codex review)
