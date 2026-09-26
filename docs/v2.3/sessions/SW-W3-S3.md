# SW-W3-S3 handoff
- Branch: `cursor/sw-w3-s3-460c`   Base SHA: `74b885d61d2fef36fe680ddf0ad0260fa2cbd085`   Head SHA (code): `d1992578413002908bf70646b3d4d9bcb2ef3389`
- PR: draft PR to `cursor/sw-v23-integration-460c` (see PR body `pr_bodies/SW-W3-S3.md` in the coordinator audit dir; opened by the environment/coordinator)
- Integration branch stands in for `dev` (coordinator override); session branch name uses the `-460c` suffix.
## Done
- `src/swarm/cli_v23.py`: offline `swarm v23` commands — `scheduler-policy`, `scheduler-simulate` (N in 1..100000), `pack-sign` (key from `SWARM_PACK_KEY_<PUBLISHER>`, never printed), `pack-verify`, `export`, `import` (tampering → `bundle_integrity_mismatch`). One JSON document per command; failures print `{"ok": false, "error": …}` and exit 2. No network/provider/HTTP; simulation broker is module-local (no imports from `tests/` or `swarm.acceptance`).
- `src/swarm/cli.py`: exactly three hook edits (import, `cli_v23.register(sub)`, `cli_v23.dispatch(args)`), applied with `git apply --check` clean.
- `tests/product/test_v23_cli.py` (9; test-only key literal via `monkeypatch`).
## Verification
Checks run by `/agent/wt/check.sh` on commit `d1992578413002908bf70646b3d4d9bcb2ef3389` (Postgres 127.0.0.1:5432 available):
```
ruff: All checks passed!
mypy: Success: no issues found in 255 source files
alembic heads: a23opsplatform0001 (head) 
session tests: 22 passed in 1.32s
offline CI: 657 passed, 1 skipped in 35.33s
integration (Postgres): 88 passed in 21.75s
tree: d8ae9f8740e853cdd62035213b784f11bddd31b0 dirty=0
```
- `uv run swarm v23 scheduler-simulate --projects a:1,b:3 --decisions 400` → `admitted {"a": 100, "b": 300}`, share 0.25/0.75 = target.
- `uv run swarm --help` lists `v23`.
## Acceptance
- [x] Every step in section 5 done; every acceptance box in section 5 ticked.
- [x] `uv run ruff check .` and `uv run mypy src/swarm` pass.
- [x] `uv run alembic heads` prints exactly one head.
- [x] Full offline CI list passes (paste the final `N passed` line into the handoff).
- [x] Integration run passed, or SKIPPED with reason in the handoff.
- [x] `git status --porcelain` lists only files from section 3 + the handoff.
- [x] No secrets, no network calls beyond section 5, no `accepted`/`complete` claims.
- [x] The Codex review packet (section 11) is in the PR description and the handoff.
## Decisions
- Tests ran against the private Postgres DB `swarm_sw460c`.
## Needs other owner
none
## Status
implemented / offline-tested only (NOT accepted; needs independent Codex review)
