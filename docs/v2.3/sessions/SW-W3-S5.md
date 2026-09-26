# SW-W3-S5 handoff
- Branch: `cursor/sw-w3-s5-460c`   Base SHA: `fd92d239909b71a72685a7ff3cab2af51d9bc838`   Head SHA (code): `faf215b587dbe6c1ad3afeafd9f9f4979fac46c6`
- PR: draft PR to `cursor/sw-v23-integration-460c` (see PR body `pr_bodies/SW-W3-S5.md` in the coordinator audit dir; opened by the environment/coordinator)
- Integration branch stands in for `dev` (coordinator override); session branch name uses the `-460c` suffix.
## Done
- `scripts/v20_compose_smoke.sh` (executable; `bash -n` SYNTAX_OK) and `docs/evidence/v20/compose-smoke/README.md` created verbatim.
- Docker installed once on this VM (`docker.io` 29.1.3, compose v2.40.3); the script's Docker path was executed for real (first execution anywhere).
- `docs/evidence/v20/compose-smoke/latest.json` committed with the honest result: **`fail` — "compose up did not become healthy"** (step `compose_up` not ok). V20-E10 is NOT done.
## Verification
Checks run by `/agent/wt/check.sh` on commit `faf215b587dbe6c1ad3afeafd9f9f4979fac46c6` (Postgres 127.0.0.1:5432 available):
```
ruff: All checks passed!
mypy: Success: no issues found in 256 source files
alembic heads: a23opsplatform0001 (head) 
offline CI: 672 passed, 1 skipped in 35.24s
integration (Postgres): 88 passed in 22.43s
tree: 6c50a3f368ebd9f89cf6f78c42e9b1dbac4d8fae dirty=0
```
- Run 1 (01:40Z): `exit=1`; api stuck at `alembic upgrade head`. Diagnosis: container→container TCP to `db:5432` timed out because this VM's leftover `iptables-legacy` tables have `FORWARD DROP` (environment, not repo). Fixed VM-locally with `sysctl net.bridge.bridge-nf-call-iptables=0` (no repo or `deploy/` change).
- Run 2 (01:46Z, evidence committed): `exit=1`; `api`, `console`, `db` healthy; `worker` **unhealthy**. Cause: `deploy/compose/product.yml` `worker` defines no healthcheck and inherits the root `Dockerfile` `HEALTHCHECK curl -fsS http://127.0.0.1:8765/health/live`, but the connector process serves no HTTP, so `compose up --wait` can never succeed. Pre-existing (compose file from `e2b64ecb`).
- `git status --short deploy/` empty after each run (temporary `product.env` symlink removed); leak check on `latest.json`: CLEAN. Token/password generated per run and never printed.
- V20-E10 compose smoke: fail on Ubuntu 24.04 VM, docker 29.1.3 — failing step: `compose_up` (worker healthcheck).
- The verbatim script failed `tests/release/test_release_verify.py::test_security_harden_ok` once tracked (secret-pattern false positive on the generated `PG_PASSWORD` line; first check run: `1 failed, 671 passed, 1 skipped`). Fixed in a separate commit by appending the scanner's allowlist marker comment (`# value hidden: generated per run, never echoed`) to that line; behaviour unchanged, `bash -n` OK. Result above is after the fix.
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
- Did not change the script to skip the worker's health: the smoke is meant to catch exactly this kind of packaging defect.
## Needs other owner
- `deploy/compose/product.yml`, service `worker`: add `healthcheck: {disable: true}` (or a connector-specific liveness check) so it does not inherit the API image's HTTP HEALTHCHECK; then re-run `scripts/v20_compose_smoke.sh` (operator/Docker host).
## Status
implemented / offline-tested only (NOT accepted; needs independent Codex review)
