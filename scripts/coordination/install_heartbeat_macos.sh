#!/usr/bin/env bash
set -euo pipefail

HOST="HOST-MAC-DEV"
SESSION="A"
BRANCH="cursor/v2-runtime-lane"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SOURCE="$ROOT/scripts/coordination/heartbeat.py"
APPDIR="$HOME/Library/Application Support/SwarmAI/coord-heartbeat-$HOST"
RUNNER="$APPDIR/heartbeat.py"
PLIST="$HOME/Library/LaunchAgents/com.swarmai.coord-heartbeat-a.plist"

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

mkdir -p "$APPDIR" "$HOME/Library/LaunchAgents"
cp "$SOURCE" "$RUNNER"
chmod 700 "$RUNNER"

cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.swarmai.coord-heartbeat-a</string>
  <key>ProgramArguments</key>
  <array>
    <string>$PYTHON</string>
    <string>$RUNNER</string>
    <string>--host</string><string>$HOST</string>
    <string>--session</string><string>$SESSION</string>
    <string>--branch</string><string>$BRANCH</string>
    <string>--trigger</string><string>scheduler</string>
  </array>
  <key>EnvironmentVariables</key>
  <dict><key>SWARM_GH_PATH</key><string>$GH</string></dict>
  <key>StartInterval</key><integer>900</integer>
  <key>RunAtLoad</key><true/>
  <key>StandardOutPath</key><string>$APPDIR/stdout.log</string>
  <key>StandardErrorPath</key><string>$APPDIR/stderr.log</string>
</dict>
</plist>
EOF

launchctl bootout "gui/$UID/com.swarmai.coord-heartbeat-a" >/dev/null 2>&1 || true
launchctl bootstrap "gui/$UID" "$PLIST"
SWARM_GH_PATH="$GH" "$PYTHON" "$RUNNER" --host "$HOST" --session "$SESSION" --branch "$BRANCH" --trigger install --force
echo "Installed SwarmAI coordination heartbeat A. Scheduler wakes every 15m; client self-throttles after lead graduation."
