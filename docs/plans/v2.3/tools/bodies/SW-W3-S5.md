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
```bash
./scripts/v20_compose_smoke.sh; echo "exit=$?"
cat docs/evidence/v20/compose-smoke/latest.json
git status --short deploy/      # MUST print nothing (no product.env left behind)
```
- **Exit 0 (`pass`):** commit `latest.json`. In the PR body write "V20-E10 compose smoke: pass on <OS>, docker <version>".
- **Exit 1 (`fail`):** commit `latest.json` anyway, since it is honest evidence. List the failing `steps[].name` in the PR body. Do **not** change application code in this session; write the follow-up under "Needs other owner" in the handoff.
- **Exit 3 (`blocked_*`):** commit `latest.json`. In the PR body write "V20-E10 blocked_env_no_docker — needs an operator run". This does **not** mark E10 done.

Before committing, confirm that `latest.json` contains no token or password value:
```bash
grep -E "atk_smoke_|[0-9a-f]{48}" docs/evidence/v20/compose-smoke/latest.json && echo "LEAK — do not commit" || echo CLEAN
```
