# SW-W3-S5 — V20-E10 product compose full-path smoke (Docker) — optional (**optional** — run it only when the coordinator schedules it)

Copy this whole file into a fresh Cursor session opened on the **swarmai** repository. Follow it top to bottom. It is self-contained: do not read other plans to decide what to do.

| Field | Value |
|---|---|
| Session ID | `SW-W3-S5` |
| Repository | `pri8771/swarmai` (GitHub remote `origin`; **public** repo) |
| Base branch | `cursor/sw-v23-integration-460c` — always the **current** `origin/cursor/sw-v23-integration-460c` (plan baseline `dev` @ `8e1c0fde`) |
| Your branch | `cursor/v20-w3-s5-compose-smoke` |
| Branch-suffix rule | If your environment forces a suffix (for example `-460c`), append it **once** to *your* branch and write the exact final name in the handoff. Never add a suffix to `cursor/sw-v23-integration-460c`: it already ends in `-460c`. |
| PR target | `cursor/sw-v23-integration-460c` — **draft** PR. Never `dev`, never `main`. |
| Wave | 3 |
| Depends on | SW-W3-S1 |
| Handoff file | `docs/v2.3/sessions/SW-W3-S5.md` |
| Independent reviewer | Codex (owner decision D2). You never accept your own work. |
| Plan | `docs/plans/v2.3/PLAN.md`; owner preflight `docs/plans/v2.3/OWNER_PREFLIGHT.md`; decisions `docs/swarm-mvp/DECISIONS.md` |

## 0. Hard rules (read twice)
1. Edit **only** the files listed in “Files you own” plus your handoff file. If another file must change, do not change it: write the exact change under “Needs other owner” in the handoff.
2. Never push to, or merge into, `main`, `dev` or `cursor/sw-v23-integration-460c`. Never merge any PR, never force-push, never rewrite history, never delete branches. Only the wave MERGE prompts (`SW-MERGE-*`) push to `cursor/sw-v23-integration-460c`.
3. Zero spend: no real model/provider calls, no paid APIs, no account creation, no deploys. `SWARM_ALLOW_PAID` stays `false`. Tests use fakes only.
4. Never commit or print secrets, tokens, `.env` files, customer data or raw logs. Test tokens are fake literals such as `atk_policy_demo`. Check environment variables only with `test -n "$NAME"`.
5. Passing tests are *not* acceptance. Never write “accepted”, “complete”, “released” or “V2.3 done”. Use “implemented” and “tested”.
6. `src/swarm/contracts/v23.py`, `src/swarm/db/models.py` and `migrations/` belong to SW-W0-S2. Import from them; never edit them (unless you *are* SW-W0-S2).
7. Do not edit `.github/workflows/`, `pyproject.toml`, `uv.lock`, `package.json` or lockfiles.
8. If a step can be read two ways, choose the reading that changes fewer lines inside your own files, and write the choice under “Decisions” in the handoff.

## 1. Setup
```bash
git status --porcelain            # must print nothing; otherwise STOP (S1)
git fetch origin cursor/sw-v23-integration-460c
git ls-remote --exit-code origin refs/heads/cursor/sw-v23-integration-460c >/dev/null && echo INTEG_OK || echo INTEG_MISSING
```
If it prints `INTEG_MISSING`, STOP (S2): SW-W0-S1 or the executor creates it.
```bash
git checkout -b cursor/v20-w3-s5-compose-smoke origin/cursor/sw-v23-integration-460c
git log -1 --format='%H %s'       # record this SHA in the handoff as 'base'
command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh   # then: export PATH=$HOME/.local/bin:$PATH
uv sync
git clean -fdX -- var/
```

## 2. Dependency and environment check
Depends on: SW-W3-S1. Their PRs must already be merged into `cursor/sw-v23-integration-460c` (by the wave MERGE prompt).
Run every command below. Each must print `OK`. If any prints `MISSING`, STOP (condition S2 in section 10).

```bash
git fetch origin cursor/sw-v23-integration-460c
git cat-file -e origin/cursor/sw-v23-integration-460c:src/swarm/api/routes_v23.py && echo "OK src/swarm/api/routes_v23.py" || echo "MISSING src/swarm/api/routes_v23.py"
```

This session needs **no** secrets or environment variables.

## 3. Files you own (the ONLY files you may create or modify)
- `scripts/v20_compose_smoke.sh` — create
- `docs/evidence/v20/compose-smoke/README.md` — create
- `docs/evidence/v20/compose-smoke/latest.json` — create
- `docs/v2.3/sessions/SW-W3-S5.md` — create (your handoff)

## 4. Do NOT touch
- Any file not listed in section 3 (in particular: `src/swarm/api/app.py`, `src/swarm/api/store.py`, `src/swarm/cli.py`, `src/swarm/db/models.py`, `migrations/`, `docs/agents/*`, `docs/plans/v2.3/*`, `CHANGELOG.md`, `README.md`, `.github/`, unless listed above).
- The `inference_server` repository: read-only, and only through the commands in section 5.
- The branches `main`, `dev`, `cursor/sw-v23-integration-460c`, `cursor/v23-plan-460c`, and any other session's branch.
- Generated files that tests rewrite: `schemas/v1/*`, `docs/evidence/fix-004/*`, `var/*` — always restore them before committing (section 6).

## 5. Steps
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
#!/usr/bin/env bash
# V20-E10 compose full-path smoke for deploy/compose/product.yml.
#
# Brings up api + console + worker + postgres on loopback, probes the public
# surfaces with a throwaway token, restarts the api, probes again, tears down.
# Writes sanitized evidence to docs/evidence/v20/compose-smoke/latest.json.
# Secrets live only in a mktemp env file outside the repo and are never printed.
#
# Exit codes: 0 pass, 1 fail, 3 blocked (no docker / compose).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
OUT_DIR="docs/evidence/v20/compose-smoke"
OUT="$OUT_DIR/latest.json"
COMPOSE_FILE="deploy/compose/product.yml"
PROJECT="swarm-smoke-$$"
API_PORT="${SWARM_SMOKE_API_PORT:-18765}"
CONSOLE_PORT="${SWARM_SMOKE_CONSOLE_PORT:-18127}"
STARTED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
GIT_SHA="$(git rev-parse HEAD 2>/dev/null || echo unknown)"
STEPS_FILE="$(mktemp)"
mkdir -p "$OUT_DIR"

write_evidence() {
  local status="$1" reason="$2"
  python3 - "$OUT" "$status" "$reason" "$STARTED_AT" "$GIT_SHA" "$COMPOSE_FILE" "$STEPS_FILE" <<'PY'
import json, sys, datetime
out, status, reason, started, sha, compose, steps_file = sys.argv[1:8]
steps = []
with open(steps_file, encoding="utf-8") as fh:
    for line in fh:
        name, ok, code = line.rstrip("\n").split("\t")
        steps.append({"name": name, "ok": ok == "1", "http_status": code})
doc = {
    "schema_version": "1",
    "scenario": "V20-E10-compose-full-path-smoke",
    "status": status,
    "reason": reason,
    "compose_file": compose,
    "git_sha": sha,
    "started_at": started,
    "finished_at": datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "steps": steps,
    "secrets": "generated per run in a temp file outside the repo; never recorded",
    "spend": "none (SWARM_ALLOW_PAID=false, no provider network)",
}
with open(out, "w", encoding="utf-8") as fh:
    json.dump(doc, fh, indent=2)
    fh.write("\n")
PY
}

if ! command -v docker >/dev/null 2>&1 || ! docker compose version >/dev/null 2>&1; then
  write_evidence "blocked_env_no_docker" "docker and docker compose v2 are required"
  echo "blocked_env_no_docker: evidence written to $OUT"
  rm -f "$STEPS_FILE"
  exit 3
fi

ENV_DIR="$(mktemp -d)"
ENV_FILE="$ENV_DIR/product.env"
TOKEN="$(python3 -c 'import secrets; print("atk_smoke_" + secrets.token_hex(24))')"
PG_PASSWORD="$(python3 -c 'import secrets; print(secrets.token_hex(24))')"  # value hidden: generated per run, never echoed
umask 077
sed -e "s|^SWARM_SEED_LOOPBACK_TOKEN=.*|SWARM_SEED_LOOPBACK_TOKEN=$TOKEN|" \
    -e "s|^SWARM_API_AUTH_TOKEN=.*|SWARM_API_AUTH_TOKEN=$TOKEN|" \
    -e "s|^SWARM_PG_PASSWORD=.*|SWARM_PG_PASSWORD=$PG_PASSWORD|" \
    -e "s|^SWARM_HOST_PORT=.*|SWARM_HOST_PORT=$API_PORT|" \
    -e "s|^SWARM_CONSOLE_HOST_PORT=.*|SWARM_CONSOLE_HOST_PORT=$CONSOLE_PORT|" \
    deploy/env/product.env.example > "$ENV_FILE"
# The compose file reads ../env/product.env; point it at the temp file for this run only.
LINKED_ENV="deploy/env/product.env"
if [ -e "$LINKED_ENV" ]; then
  write_evidence "blocked_existing_env" "deploy/env/product.env exists; refusing to overwrite"
  echo "blocked_existing_env: move deploy/env/product.env aside first"
  rm -rf "$ENV_DIR" "$STEPS_FILE"
  exit 3
fi
ln -s "$ENV_FILE" "$LINKED_ENV"

compose() { docker compose -p "$PROJECT" -f "$COMPOSE_FILE" --env-file "$ENV_FILE" "$@"; }
cleanup() {
  compose down -v --remove-orphans >/dev/null 2>&1 || true
  rm -f "$LINKED_ENV"
  rm -rf "$ENV_DIR"
  rm -f "$STEPS_FILE"
}
trap cleanup EXIT

FAILED=0
step() {
  # step NAME EXPECTED_STATUS URL [curl args...]
  local name="$1" want="$2" url="$3"
  shift 3
  local code
  code="$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 "$@" "$url" || echo 000)"
  if [ "$code" = "$want" ]; then
    printf '%s\t1\t%s\n' "$name" "$code" >> "$STEPS_FILE"
  else
    printf '%s\t0\t%s\n' "$name" "$code" >> "$STEPS_FILE"
    FAILED=1
  fi
}

AUTH=(-H "Authorization: Bearer $TOKEN")
API="http://127.0.0.1:$API_PORT"
CONSOLE="http://127.0.0.1:$CONSOLE_PORT"

probe_all() {
  local tag="$1"
  step "$tag.health_live" 200 "$API/health/live"
  step "$tag.health_ready" 200 "$API/health/ready"
  step "$tag.unauthenticated_rejected" 401 "$API/v1/scheduler/queues"
  step "$tag.scheduler_queues" 200 "$API/v1/scheduler/queues" "${AUTH[@]}"
  step "$tag.ops_events" 200 "$API/v1/ops/events" "${AUTH[@]}"
  step "$tag.foreign_project_forbidden" 403 "$API/v1/scheduler/projects/proj_foreign_smoke" \
    -X POST -H "Content-Type: application/json" -d '{}' "${AUTH[@]}"
  step "$tag.console_healthz" 200 "$CONSOLE/healthz"
  step "$tag.console_proxies_api" 200 "$CONSOLE/health/live"
}

if ! compose up --build -d --wait --wait-timeout 420 >/dev/null 2>&1; then
  printf 'compose_up\t0\t000\n' >> "$STEPS_FILE"
  compose ps >&2 || true
  write_evidence "fail" "compose up did not become healthy"
  exit 1
fi
printf 'compose_up\t1\t000\n' >> "$STEPS_FILE"
probe_all "first_boot"

compose restart api >/dev/null 2>&1
for _ in $(seq 1 60); do
  curl -fsS --max-time 2 "$API/health/live" >/dev/null 2>&1 && break
  sleep 2
done
probe_all "after_api_restart"

if [ "$FAILED" = "0" ]; then
  write_evidence "pass" "all probes returned the expected status"
  echo "pass: evidence written to $OUT"
  exit 0
fi
write_evidence "fail" "one or more probes returned an unexpected status"
echo "fail: see $OUT"
exit 1
```
```bash
chmod +x scripts/v20_compose_smoke.sh
bash -n scripts/v20_compose_smoke.sh && echo SYNTAX_OK
```

### Step 2 — `docs/evidence/v20/compose-smoke/README.md` (create, exactly)
```markdown
# V20-E10 compose full-path smoke

`scripts/v20_compose_smoke.sh` brings up `deploy/compose/product.yml` (api, console, worker, postgres) on loopback, probes it, restarts the api, probes again, and tears everything down, volumes included.

| Exit code | `status` in `latest.json` | Meaning |
|---|---|---|
| 0 | `pass` | every probe returned the expected HTTP status, before and after the api restart |
| 1 | `fail` | compose did not become healthy, or a probe returned an unexpected status (see `steps`) |
| 3 | `blocked_env_no_docker` / `blocked_existing_env` | the environment cannot run the smoke; nothing was started |

Probes, each run on first boot and again after the api restart:
- `/health/live` and `/health/ready`;
- an unauthenticated scheduler read gives 401;
- an authenticated `/v1/scheduler/queues` and `/v1/ops/events` give 200;
- registering a foreign project gives 403;
- the console `/healthz` and its same-origin `/health/live` proxy.

Secrets are handled like this:
- The token and database password are generated for each run with `secrets.token_hex`.
- They are written only to a `mktemp` directory outside the repository, which the compose file reaches through a temporary `deploy/env/product.env` symlink that is removed on exit.
- They are never printed or recorded.

There is no spend: `SWARM_ALLOW_PAID=false` and there is no provider network.

A `blocked_*` result is honest evidence that the smoke did **not** run. It does not satisfy V20-E10. Only a `pass` run by an operator with Docker does.
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

## 6. Verify (run exactly; all must pass)
```bash
git clean -fdX -- var/            # F-15: stale runtime state breaks re-runs
# Private database for this session: concurrent sessions on one host must never share one.
sudo -u postgres psql -c "CREATE DATABASE swarm_sw_w3_s5 OWNER swarm;" || true
export SWARM_DATABASE_URL=postgresql+psycopg://swarm:swarm@127.0.0.1:5432/swarm_sw_w3_s5
uv run ruff check .
uv run mypy src/swarm
uv run alembic heads               # must print exactly ONE line ending in (head)
uv run pytest tests/contracts tests/spikes tests/api tests/broker tests/controller tests/chaos tests/deployment tests/evals tests/extensions tests/foundation tests/goals tests/pursuit tests/sdk tests/knowledge tests/load tests/memory tests/mission tests/objectives tests/onboarding tests/product tests/providers tests/recovery tests/regressions tests/release tests/runtime tests/selfdev tests/tools tests/ui tests/workers tests/workspace tests/e2e tests/acceptance tests/portability -q --ignore=tests/integration

# PostgreSQL integration (install steps in “PostgreSQL” below)
uv run pytest tests/integration -q -m integration

git checkout -- schemas/v1 docs/evidence/fix-004 var   # tests rewrite these tracked files
git status --porcelain            # every path listed must be one of YOUR files
```

### PostgreSQL (for the integration line)
```bash
pg_isready -h 127.0.0.1 || {
  sudo apt-get update && sudo apt-get install -y postgresql && sudo service postgresql start
  sudo -u postgres psql -c "CREATE USER swarm WITH PASSWORD 'swarm' SUPERUSER;" || true
}
```
Run this block before section 6. Section 6 creates your private database and exports `SWARM_DATABASE_URL` for **both** pytest lines; never unset it and never point it at the shared `swarm` database.
If `pg_isready -h 127.0.0.1` still fails after running this block twice, write `integration: SKIPPED (postgres unavailable: <last error line>)` in the handoff and continue. Never claim integration passed without running it.

## 7. Acceptance checklist (tick every box in the handoff)
- [ ] Every step in section 5 done; every acceptance box in section 5 ticked.
- [ ] `uv run ruff check .` and `uv run mypy src/swarm` pass.
- [ ] `uv run alembic heads` prints exactly one head.
- [ ] Full offline CI list passes (paste the final `N passed` line into the handoff).
- [ ] Integration run passed, or SKIPPED with reason in the handoff.
- [ ] `git status --porcelain` lists only files from section 3 + the handoff.
- [ ] No secrets, no network calls beyond section 5, no `accepted`/`complete` claims.
- [ ] The Codex review packet (section 11) is in the PR description and the handoff.

## 8. Commit, push, draft PR
```bash
git checkout -- schemas/v1 docs/evidence/fix-004 var
git add scripts/v20_compose_smoke.sh docs/evidence/v20/compose-smoke/README.md docs/evidence/v20/compose-smoke/latest.json docs/v2.3/sessions/SW-W3-S5.md
git status --porcelain            # nothing unexpected staged or left over
git commit -m "test(v2.0): E10 compose full-path smoke script and sanitized evidence" -m "Session: SW-W3-S5. Plan: docs/plans/v2.3/PLAN.md."
git push -u origin cursor/v20-w3-s5-compose-smoke
gh pr create --draft --base cursor/sw-v23-integration-460c --head cursor/v20-w3-s5-compose-smoke --title "[SW-W3-S5] V20-E10 product compose full-path smoke (Docker) — optional" --body-file docs/v2.3/sessions/SW-W3-S5.md
git ls-remote origin refs/heads/cursor/v20-w3-s5-compose-smoke   # must print the same SHA as: git rev-parse HEAD
```
If `gh pr create` is refused (read-only `gh`), the environment opens the PR: check that its base is `cursor/sw-v23-integration-460c` and that it is a draft, and put the PR URL (or the compare URL from section 10, step 4) into the handoff.
If push fails for network reasons, retry up to 4 times waiting 4 s, 8 s, 16 s, 32 s; then STOP (S8).
Docs to update: only your handoff file, plus any doc listed in section 3.

## 9. Handoff file (create before committing)
Create `docs/v2.3/sessions/SW-W3-S5.md` with exactly these headings:
```markdown
# SW-W3-S5 handoff
- Branch: <exact branch name>   Base SHA: <from setup>   Head SHA: <git rev-parse HEAD>
- PR: <url, or compare URL>
## Done
<bullet list of what you implemented>
## Verification
<each command from section 6 and its final result line; integration PASSED/SKIPPED(reason)>
## Acceptance
<copy the checkboxes from sections 5 and 7, ticked>
## Decisions
<choices you made under hard rule 8, or 'none'>
## Needs other owner
<files outside your scope that should change, with the exact change; or 'none'>
## Codex review packet
<the block from section 11, filled in>
## Status
implemented + tested (NOT accepted; needs Codex review)
```

## 10. STOP conditions (never wait for a human)
STOP immediately when any of these is true:
- **S1** `git status --porcelain` is not empty before Setup. (Do not commit, stash or discard anything; skip steps 1–4 below and only report.)
- **S2** a dependency check prints `MISSING`.
- **S3** a command in section 6, or a check in section 5, still fails after **2 attempts**. One attempt = one edit to *your own files* followed by re-running the failing command.
- **S4** a “currently reads” / before-block in section 5 does not match the file, or a function named in section 5 does not exist.
- **S5** finishing would require editing a file that is not in section 3.
- **S6** a required environment variable prints `MISSING`.
- **S7** an external gate check (inference_server sync point or approval line) in section 5 fails.
- **S8** `git push` still fails after 4 retries (waits 4 s, 8 s, 16 s, 32 s).

What to do on STOP, in this order:
1. Commit whatever is complete inside your own files: `git add <your files> docs/v2.3/sessions/SW-W3-S5.md` then `git commit -m "WIP(SW-W3-S5): <one-line reason>"`.
2. Write the handoff (section 9) with `## Status` = `BLOCKED: <condition id> <one-line reason>`, and under `## Needs other owner` the exact file, function and change you need. Commit it.
3. Push: `git push -u origin cursor/v20-w3-s5-compose-smoke` (plus your suffix).
4. Open the draft PR against `cursor/sw-v23-integration-460c` with the title prefix `[BLOCKED]`, or record the compare URL `https://github.com/pri8771/swarmai/compare/cursor/sw-v23-integration-460c...cursor/v20-w3-s5-compose-smoke?expand=1` in the handoff.
5. End the session with a final message: the condition id, the reason, the branch and the head SHA.
Never work around a STOP by editing other files, weakening tests, or adding `skip`/`xfail`.

If `tests/tools/test_v20_cancel_killbound.py` fails once in the full run and you did not touch `sandbox_runner.py` or that test, re-run the full list once. If it passes, record both result lines in the handoff under Verification and continue; if it fails twice, STOP (S3). (The known race was fixed by SW-FIX-FLAKE; a new failure is worth reporting.)

## 11. Codex review packet (put this in the PR description and in the handoff)
```markdown
### Codex review packet — SW-W3-S5
- PR: <PR URL — fill in after the PR exists>
- Branch: <exact branch name>  Base: origin/cursor/sw-v23-integration-460c @ <base SHA from Setup>
- Head SHA: <output of `git rev-parse HEAD`; must equal `git ls-remote origin refs/heads/<branch>`>
- Diff for review: `git diff <base SHA>...<head SHA>`
- Files to review: `scripts/v20_compose_smoke.sh`, `docs/evidence/v20/compose-smoke/README.md`, `docs/evidence/v20/compose-smoke/latest.json`, `docs/v2.3/sessions/SW-W3-S5.md`
- Review focus (AGENTS.md Code Review Rules): cross-tenant/project access; secret disclosure; financial accounting (unknown usage or cost is never zero); unbounded retries; silently changed model behaviour; recovery gaps after a crash/restart; unsupported release claims ("accepted", "complete").
- Checks run: <paste the final result line of every command in section 6>
- Verdict requested: `RECOMMEND_ACCEPT <head SHA>` or `REQUEST_CHANGES` with file:line findings.
```
