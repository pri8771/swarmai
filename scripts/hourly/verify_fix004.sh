#!/usr/bin/env bash
# One-shot FIX-004 verification: manual invocation + launchd-triggered check-ins.
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
STATE_DIR="${SWARM_HOURLY_STATE_DIR:-$HOME/Library/Application Support/SwarmAI/hourly-runner}"
export SWARM_HOURLY_REPO="$REPO"
export SWARM_HOURLY_STATE_DIR="$STATE_DIR"
export SWARM_HOURLY_LABEL="${SWARM_HOURLY_LABEL:-com.swarmai.hourly}"
export SWARM_HOURLY_INTERVAL="${SWARM_HOURLY_INTERVAL:-60}"
export SWARM_HOURLY_PYTHON="${SWARM_HOURLY_PYTHON:-/usr/bin/python3}"

mkdir -p "$STATE_DIR" "$REPO/docs/evidence/fix-004"
chmod +x "$REPO/scripts/hourly/"*.sh "$REPO/scripts/hourly/"*.py

# Reset prior verification counters for a clean evidence pass.
rm -f "$STATE_DIR/state.json" "$STATE_DIR/checkins.jsonl" "$STATE_DIR/hourly.lock"
: > "$STATE_DIR/launchd.stdout.log"
: > "$STATE_DIR/launchd.stderr.log"

echo "== manual invocation =="
"$SWARM_HOURLY_PYTHON" "$REPO/scripts/hourly/checkin.py" --repo "$REPO" --trigger manual

echo "== install launchd interval=${SWARM_HOURLY_INTERVAL}s python=${SWARM_HOURLY_PYTHON} =="
bash "$REPO/scripts/hourly/install_launchd.sh"

echo "== launchd kickstart #1 =="
launchctl kickstart -k "gui/$(id -u)/${SWARM_HOURLY_LABEL}" || true
sleep 8
echo "== launchd kickstart #2 =="
launchctl kickstart -k "gui/$(id -u)/${SWARM_HOURLY_LABEL}" || true
sleep 8

echo "== waiting for two scheduler check-ins (up to 90s) =="
deadline=$((SECONDS + 90))
while (( SECONDS < deadline )); do
  count=$("$SWARM_HOURLY_PYTHON" -c "import json,pathlib; p=pathlib.Path(r'''$STATE_DIR/state.json''');
print(json.loads(p.read_text()).get('scheduler_checkins',0) if p.exists() else 0)")
  echo "scheduler_checkins=${count}"
  if [[ "$count" -ge 2 ]]; then
    echo "two scheduler check-ins observed"
    break
  fi
  sleep 5
done

# Restore production interval 3600 after verification window.
export SWARM_HOURLY_INTERVAL=3600
bash "$REPO/scripts/hourly/install_launchd.sh"

cp "$STATE_DIR/state.json" "$REPO/docs/evidence/fix-004/runner-state.json"
cp "$STATE_DIR/checkins.jsonl" "$REPO/docs/evidence/fix-004/checkins.jsonl" 2>/dev/null || true
"$SWARM_HOURLY_PYTHON" - <<'PY'
import json
from pathlib import Path
state = json.loads(Path.home().joinpath("Library/Application Support/SwarmAI/hourly-runner/state.json").read_text())
print(json.dumps({
  "invocation_count": state.get("invocation_count"),
  "scheduler_checkins": state.get("scheduler_checkins"),
  "manual_checkins": state.get("manual_checkins"),
  "recurring_verified": state.get("recurring_verified"),
  "cursor_agent_auth": state.get("cursor_agent_auth"),
  "last_run_at": state.get("last_run_at"),
}, indent=2))
PY
