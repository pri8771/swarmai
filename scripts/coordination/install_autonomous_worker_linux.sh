#!/usr/bin/env bash
# Linux autonomous-worker installer for Lane B / product-lane when the host is not Windows.
# Does not emulate Windows Task Scheduler. Uses a tmux 60-second poll loop.
set -euo pipefail

HOST="HOST-WIN-DEV"
SESSION="B"
BRANCH="cursor/v2-product-lane"
TMUX_SESSION="swarm-autonomous-b"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SOURCE="$ROOT/scripts/coordination/autonomous_worker.py"
APPDIR="${XDG_STATE_HOME:-$HOME/.local/state}/SwarmAI/autonomous-worker-$HOST"
RUNNER="$APPDIR/autonomous_worker.py"
STDOUT_LOG="$APPDIR/stdout.log"
STDERR_LOG="$APPDIR/stderr.log"
TMUX_CONF="/exec-daemon/tmux.portal.conf"

PYTHON="$(command -v python3 || true)"
GH="$(command -v gh || true)"
AGENT="$(command -v agent || command -v cursor-agent || true)"

if [[ -z "$PYTHON" ]]; then
  echo "python3 is required" >&2
  exit 2
fi
if [[ -z "$GH" ]]; then
  echo "GitHub CLI (gh) is required and must be authenticated" >&2
  exit 2
fi
if [[ -z "$AGENT" ]]; then
  echo "Cursor CLI agent is required. Install Cursor CLI, then run: agent login" >&2
  exit 3
fi

mkdir -p "$APPDIR"
cp "$SOURCE" "$RUNNER"
chmod 700 "$RUNNER"
: >> "$STDOUT_LOG"
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
export SWARM_AGENT_PATH="$AGENT"
while true; do
  date -u '+%Y-%m-%dT%H:%M:%SZ worker-wake' | tee -a "$STDOUT_LOG"
  "$PYTHON" "$RUNNER" --workspace '$ROOT' --host '$HOST' --session '$SESSION' --branch '$BRANCH' \\
    >>"$STDOUT_LOG" 2>>"$STDERR_LOG" || echo "worker-exit:\$?" >>"$STDERR_LOG"
  sleep 60
done
EOF
)

tmux_bin new-session -d -s "$TMUX_SESSION" -c "$ROOT" -- bash -lc "$LOOP"

echo "Installed SwarmAI autonomous worker B on Linux (tmux $TMUX_SESSION)."
echo "OS: $(uname -s) — not Windows Task Scheduler."
echo "Workspace: $ROOT"
echo "Cursor agent: $AGENT"
echo "Assignment poll: every 60 seconds"
echo "Identity fence: $HOST / session $SESSION / $BRANCH"
echo "State/logs: $APPDIR"
echo "tmux session: $TMUX_SESSION"
