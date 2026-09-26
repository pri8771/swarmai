**Goal.** V20-E10: one script, `scripts/v20_compose_smoke.sh`, that proves the installable product stack (`deploy/compose/product.yml`) works end to end. It writes **sanitized** evidence to `docs/evidence/v20/compose-smoke/latest.json`. If this machine has no Docker, the same script records an honest `blocked_env_no_docker` (exit code 3); that is a valid outcome for this session.

It depends on SW-W3-S1 because the probes hit `/v1/scheduler/queues` and `/v1/scheduler/projects/{pid}`.

**Hard rules:**
- **Never** commit `deploy/env/product.env`. The script creates it as a temporary symlink to a `mktemp` file and deletes it on exit. It refuses to run (`blocked_existing_env`) if a real `deploy/env/product.env` already exists.
- The token and password are generated per run with Python `secrets`. They are never echoed, logged or written into the repository.
- Do not edit any file under `deploy/`. Do not publish any port beyond `127.0.0.1`. Do not enable paid inference or the provider network.
- The script tears down with `down -v`, so nothing persists between runs.

The script was syntax-checked (`bash -n`) and its blocked path was run on the audit VM, which has no Docker: exit code 3 and valid JSON with `"status": "blocked_env_no_docker"`. **The Docker path has not been executed by the auditor.** Treat your own run as the first real execution and report exactly what happened.

### Step 1 — `scripts/v20_compose_smoke.sh` (create exactly, then make it executable)
```bash
{{FILE:scripts/v20_compose_smoke.sh}}
```
```bash
chmod +x scripts/v20_compose_smoke.sh
bash -n scripts/v20_compose_smoke.sh && echo SYNTAX_OK
```

### Step 2 — `docs/evidence/v20/compose-smoke/README.md` (create, exactly)
```markdown
{{FILE:docs/evidence/v20/compose-smoke/README.md}}
```

### Step 3 — run it and keep whatever it produces
If the api container stays `health: starting` and its log stops at `running alembic upgrade head`, test `docker compose … exec -T api python -c "import socket;socket.create_connection(('db',5432),3)"`. A timeout means host bridge filtering: check `sudo iptables-legacy -S FORWARD`; on a disposable VM you may run `sudo sysctl -w net.bridge.bridge-nf-call-iptables=0` and re-run. Record this environment change in the handoff and restore the value afterwards. Never change `deploy/` to work around it.

```bash
./scripts/v20_compose_smoke.sh; echo "exit=$?"
cat docs/evidence/v20/compose-smoke/latest.json
git status --short deploy/      # MUST print nothing (no product.env left behind)
```
- **Exit 0 (`pass`):** commit `latest.json`. In the PR body write "V20-E10 compose smoke: pass on <OS>, docker <version>".
- **Exit 1 (`fail`):** commit `latest.json` anyway, since it is honest evidence. List the failing `steps[].name` in the PR body. Do **not** change application code in this session; write the follow-up under "Needs other owner" in the handoff. Known historical cause (fixed by SW-FIX-COMPOSE, `e5fd04c0`): the `worker` service inherited the API image HTTP HEALTHCHECK and was always unhealthy. If `compose ps` shows `worker` unhealthy again, check that `deploy/compose/product.yml` still gives `worker:` its own process healthcheck; `healthcheck: {disable: true}` does **not** work with `compose up --wait` ("has no healthcheck configured"). Do not edit `deploy/` in this session.
- **Exit 3 (`blocked_*`):** commit `latest.json`. In the PR body write "V20-E10 blocked_env_no_docker — needs an operator run". This does **not** mark E10 done.

Before committing, confirm that `latest.json` contains no token or password value:
```bash
grep -E "atk_smoke_|[0-9a-f]{48}" docs/evidence/v20/compose-smoke/latest.json && echo "LEAK — do not commit" || echo CLEAN
```

Run the section 6 offline list **after** `git add` of your new files: `tests/release/test_release_verify.py::test_security_harden_ok` scans only tracked files, so a pre-`git add` run looks green even when the script trips a secret pattern.
