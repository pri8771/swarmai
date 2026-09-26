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
