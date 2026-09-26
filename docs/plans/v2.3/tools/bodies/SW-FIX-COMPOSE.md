> **EXECUTED** 2026-09-26 by the integrator: branch `cursor/sw-fix-compose-healthcheck-460c` head `7c34da5e4d887211094ee27b77ed143c9e1790c7` (compose change `6f85edc7`), merged into `cursor/sw-v23-integration-460c` at `e5fd04c00028b7e89ae749da7d2966ef742bea74`. V20-E10 smoke: `pass` 17/17 on the dev VM.

**Goal.** `deploy/compose/product.yml` service `worker` reuses `swarm-ai:local` and inherited the Dockerfile `HEALTHCHECK curl -fsS http://127.0.0.1:8765/health/live`. The connector serves no HTTP, so the worker was always `unhealthy` and `docker compose up --wait` (V20-E10) failed.

### Step 0 — Docker and host state
Start Docker (`sudo dockerd` in tmux when systemd is absent). Save `sudo iptables-save`, `sudo iptables-legacy-save` and `sysctl -n net.bridge.bridge-nf-call-iptables` to a temp dir. If containers cannot reach each other (api log stops at `alembic upgrade head`), on a disposable VM run `sudo sysctl -w net.bridge.bridge-nf-call-iptables=0` and record it. Run `./scripts/v20_compose_smoke.sh` once on the unfixed tree (observed: exit 1, worker `unhealthy`).

### Step 1 — `deploy/compose/product.yml`, service `worker`
Add a `healthcheck` with a process check (the connector keeps no local heartbeat; it heartbeats to the API): `/app/.venv/bin/python -c` code that exits 0 when `/proc/1/cmdline` contains `swarm.workers.connector` and the state field of `/proc/1/stat` (after the last `)`) is not `Z` or `X`; `interval: 15s`, `timeout: 5s`, `retries: 3`, `start_period: 10s`, with a comment giving the reason. Do **not** use `healthcheck: {disable: true}`: compose v2.40 `up --wait` fails with `container … has no healthcheck configured`.

### Step 2 — `tests/deployment/test_product_compose.py`
Add: the worker block has its own `test:` healthcheck using `/proc/1/cmdline`, no `8765/health`, no `disable: true` key; the api keeps its HTTP check; the embedded Python exits 1 without a traceback on a host whose PID 1 is not the connector. Both tests must fail on the old compose file (observed `2 failed, 3 passed`).

### Step 3 — smoke, evidence, cleanup
Commit the code, run the smoke (observed: exit 0, `pass`, 17/17), commit `latest.json`, and update the V20-E10 rows (checklist, `V20_TODO.md`, `context.json`) honestly: dev-VM run, VM-local sysctl change. Then stop dockerd, restore the sysctl, and compare the iptables dumps with the saved ones (must be equal).

### Acceptance (this session)
- [ ] Worker healthy under `compose up --wait`; smoke result recorded as it happened.
- [ ] Host firewall and sysctl restored; Docker stopped.
