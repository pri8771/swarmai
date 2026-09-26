# SW-FIX-COMPOSE handoff
- Branch: `cursor/sw-fix-compose-healthcheck-460c`   Base SHA: `b31627121d9d56836374f5dbfad32e579821937c`   Head SHA (code): `6f85edc7c540a8748f1559ec9715777de28ecc39`
- PR: to `cursor/sw-v23-integration-460c` (PR body `pr_bodies/SW-FIX-COMPOSE.md` in the coordinator audit dir).
## Problem
`deploy/compose/product.yml` `worker` reuses `swarm-ai:local` without a `healthcheck`, so it inherits the Dockerfile `HEALTHCHECK curl -fsS http://127.0.0.1:8765/health/live`. The connector (`python -m swarm.workers.connector`) serves no HTTP, so the worker is always `unhealthy` and `docker compose up --wait` (V20-E10 smoke) fails.
## Done
- Reproduced on base `b3162712`: `scripts/v20_compose_smoke.sh` exit 1, api/console/db healthy, worker `unhealthy`.
- First attempt `healthcheck: {disable: true}` (`ee731faf`): compose v2.40.3 `up --wait` fails with `container … has no healthcheck configured`. Not usable.
- Final: worker process healthcheck (`/app/.venv/bin/python -c …`): PID 1 cmdline contains `swarm.workers.connector` and its `/proc/1/stat` state is not `Z`/`X`; interval 15 s, timeout 5 s, retries 3, start_period 10 s. The connector keeps no local heartbeat (it heartbeats to the API, where lease TTLs track progress), so a process check is the strongest check available without new product code. The reason is commented in the compose file.
- `tests/deployment/test_product_compose.py`: worker has its own `test:` healthcheck using `/proc/1/cmdline`, no inherited `8765/health`, not disabled; the embedded Python is valid and exits 1 (not a traceback) when PID 1 is not the connector. Both new tests fail on the base compose file (`2 failed, 3 passed`).
- Evidence/docs: `docs/evidence/v20/compose-smoke/latest.json` (`pass`, `git_sha` `6f85edc7`), README note, `docs/v2.3/EXIT_CHECKLIST.md` V20-E10 row, `docs/agents/V20_TODO.md`, `docs/agents/context.json`.
## Verification
- Compose smoke on `6f85edc7` (Docker 29.1.3, compose v2.40.3, Ubuntu VM): exit 0, `pass`, 17/17 steps (compose_up + 8 probes on first boot + 8 after api restart).
- VM-local environment change for the run only: `sysctl net.bridge.bridge-nf-call-iptables=0` (leftover `iptables-legacy` `FORWARD DROP`, see SW-W3-S5). Afterwards dockerd was stopped, the sysctl restored to `1`, and `iptables-save`/`iptables-legacy-save` rules compared equal to the pre-run snapshot.
- `/agent/wt/check.sh` (private DB `swarm_fix460c`): ruff pass; mypy `Success: no issues found in 256 source files`; one head `a23opsplatform0001`; session `24 passed`; offline CI `689 passed, 1 skipped`; integration (Postgres) `88 passed`.
## Status
implemented / offline-tested; compose smoke pass on a dev VM (NOT accepted; needs independent Codex review)
