#!/usr/bin/env bash
# Linux heartbeat installer for Lane B / product-lane when the host is not Windows.
# Does not emulate Windows Task Scheduler. Uses a tmux 5-minute wake loop.
set -euo pipefail

HOST="HOST-WIN-DEV"
SESSION="B"
BRANCH="cursor/v2-product-lane"
TMUX_SESSION="swarm-heartbeat-b"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SOURCE="$ROOT/scripts/coordination/heartbeat.py"
APPDIR="${XDG_STATE_HOME:-$HOME/.local/state}/SwarmAI/coord-heartbeat-$HOST"
RUNNER="$APPDIR/heartbeat.py"
STDOUT_LOG="$APPDIR/stdout.log"
STDERR_LOG="$APPDIR/stderr.log"
TMUX_CONF="/exec-daemon/tmux.portal.conf"

PYTHON="$(command -v python3 || true)"
GH="$(command -v gh || true)"
if [[ -z "$PYTHON" ]]; then
  echo "python3 is required" >&2
  exit 2
fi
if [[ -z "$GH" ]]; then
  echo "GitHub CLI (gh) is required and must be authenticated" >&2
  exit 2
fi

mkdir -p "$APPDIR"
cp "$SOURCE" "$RUNNER"
chmod 700 "$RUNNER"
: > "$STDOUT_LOG"
: >> "$STDERR_LOG"

tmux_bin() {
  if [[ -f "$TMUX_CONF" ]]; then
    tmux -f "$TMUX_CONF" "$@"
  else
    tmux "$@"
  fi
}

if tmux_bin has-session -t "=$TMUX_SESSION" 2>/dev/null; then
  tmux_bin kill-session -t "=$TMUX_SESSION"
fi

LOOP=$(cat <<EOF
set -euo pipefail
export PATH="\$HOME/.local/bin:\$PATH"
export SWARM_GH_PATH="$GH"
while true; do
  date -u '+%Y-%m-%dT%H:%M:%SZ scheduler-wake' | tee -a "$STDOUT_LOG"
  "$PYTHON" "$RUNNER" --host '$HOST' --session '$SESSION' --branch '$BRANCH' --trigger scheduler \\
    >>"$STDOUT_LOG" 2>>"$STDERR_LOG" || echo "scheduler-exit:\$?" >>"$STDERR_LOG"
  sleep 300
done
EOF
)

tmux_bin new-session -d -s "$TMUX_SESSION" -c "$ROOT" -- bash -lc "$LOOP"

export SWARM_GH_PATH="$GH"
"$PYTHON" "$RUNNER" --host "$HOST" --session "$SESSION" --branch "$BRANCH" --trigger install --force

echo "Installed SwarmAI coordination heartbeat B on Linux (tmux $TMUX_SESSION)."
echo "OS: $(uname -s) — not Windows Task Scheduler."
echo "Scheduler wakes every 5m; client self-throttles to HEARTBEAT_STATE.json cadence."
echo "State/logs: $APPDIR"
echo "tmux session: $TMUX_SESSION"
