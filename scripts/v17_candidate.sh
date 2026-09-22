#!/usr/bin/env bash
# Private/local V1.7 candidate service (loopback only). launchd label: com.swarmai.v17-candidate
# Usage: scripts/v17_candidate.sh {run|start|stop|restart|status|logs}
# Config (never in Git): ~/Library/Application Support/SwarmAI/v17-candidate/candidate.env
set -euo pipefail
LABEL="com.swarmai.v17-candidate"
APPDIR="$HOME/Library/Application Support/SwarmAI/v17-candidate"
ENVFILE="$APPDIR/candidate.env"
PLIST="$HOME/Library/LaunchAgents/${LABEL}.plist"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
UV="${UV_BIN:-$HOME/.local/bin/uv}"
PORT="${SWARM_CANDIDATE_PORT:-18771}"

run() {
  # Executed by launchd: source private env, exec the API on loopback.
  set -a; . "$ENVFILE"; set +a
  cd "$REPO"
  exec "$UV" run swarm serve --host 127.0.0.1 --port "$PORT"
}

write_plist() {
  mkdir -p "$APPDIR" "$HOME/Library/LaunchAgents"
  cat > "$PLIST" <<PL
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>${LABEL}</string>
  <key>ProgramArguments</key>
  <array><string>/bin/bash</string><string>${REPO}/scripts/v17_candidate.sh</string><string>run</string></array>
  <key>EnvironmentVariables</key>
  <dict><key>PATH</key><string>${HOME}/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string>
        <key>SWARM_CANDIDATE_PORT</key><string>${PORT}</string></dict>
  <key>WorkingDirectory</key><string>${REPO}</string>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>${APPDIR}/stdout.log</string>
  <key>StandardErrorPath</key><string>${APPDIR}/stderr.log</string>
  <key>ProcessType</key><string>Background</string>
</dict>
</plist>
PL
}

case "${1:-status}" in
  run) run ;;
  start)
    [[ -f "$ENVFILE" ]] || { echo "missing $ENVFILE (SWARM_DATABASE_URL, SWARM_SEED_LOOPBACK_TOKEN, SWARM_ALLOW_PAID=false, OLLAMA_BASE_URL, SWARM_REPO_ROOT)" >&2; exit 2; }
    write_plist
    launchctl bootout "gui/$UID/$LABEL" >/dev/null 2>&1 || true
    launchctl bootstrap "gui/$UID" "$PLIST"
    launchctl enable "gui/$UID/$LABEL" >/dev/null 2>&1 || true
    echo "started $LABEL on http://127.0.0.1:$PORT (source: $REPO @ $(git -C "$REPO" rev-parse --short HEAD))" ;;
  stop)
    launchctl bootout "gui/$UID/$LABEL" >/dev/null 2>&1 && echo "stopped $LABEL" || echo "$LABEL not loaded" ;;
  restart) "$0" stop; sleep 1; "$0" start ;;
  status)
    launchctl print "gui/$UID/$LABEL" 2>/dev/null | grep -E "state|pid" | head -3 || echo "$LABEL not loaded"
    curl -s -o /dev/null -w "health/live %{http_code}\n" "http://127.0.0.1:$PORT/health/live" || true ;;
  logs) tail -n "${2:-50}" "$APPDIR/stdout.log" "$APPDIR/stderr.log" ;;
  *) echo "usage: $0 {run|start|stop|restart|status|logs}" >&2; exit 2 ;;
esac
