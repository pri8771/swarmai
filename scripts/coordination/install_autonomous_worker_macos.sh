#!/usr/bin/env bash
set -euo pipefail

HOST="HOST-MAC-DEV"
SESSION="A"
BRANCH="cursor/v2-runtime-lane"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SOURCE="$ROOT/scripts/coordination/autonomous_worker.py"
APPDIR="$HOME/Library/Application Support/SwarmAI/autonomous-worker-$HOST"
RUNNER="$APPDIR/autonomous_worker.py"
PLIST="$HOME/Library/LaunchAgents/com.swarmai.autonomous-worker-a.plist"

PYTHON="$(command -v python3 || true)"
GH="$(command -v gh || true)"
AGENT="$(command -v agent || command -v cursor-agent || true)"

if [[ -z "$PYTHON" ]]; then echo "python3 is required" >&2; exit 2; fi
if [[ -z "$GH" ]]; then echo "GitHub CLI (gh) is required and must be authenticated" >&2; exit 2; fi
if [[ -z "$AGENT" ]]; then
  echo "Cursor CLI agent is required. Install Cursor CLI, then run: agent login" >&2
  exit 3
fi

mkdir -p "$APPDIR" "$HOME/Library/LaunchAgents"
cp "$SOURCE" "$RUNNER"
chmod 700 "$RUNNER"

cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.swarmai.autonomous-worker-a</string>
  <key>ProgramArguments</key>
  <array>
    <string>$PYTHON</string>
    <string>$RUNNER</string>
    <string>--workspace</string><string>$ROOT</string>
    <string>--host</string><string>$HOST</string>
    <string>--session</string><string>$SESSION</string>
    <string>--branch</string><string>$BRANCH</string>
  </array>
  <key>EnvironmentVariables</key>
  <dict>
    <key>SWARM_GH_PATH</key><string>$GH</string>
    <key>SWARM_AGENT_PATH</key><string>$AGENT</string>
  </dict>
  <key>StartInterval</key><integer>60</integer>
  <key>RunAtLoad</key><true/>
  <key>StandardOutPath</key><string>$APPDIR/stdout.log</string>
  <key>StandardErrorPath</key><string>$APPDIR/stderr.log</string>
</dict>
</plist>
EOF

launchctl bootout "gui/$UID/com.swarmai.autonomous-worker-a" >/dev/null 2>&1 || true
launchctl bootstrap "gui/$UID" "$PLIST"
SWARM_GH_PATH="$GH" SWARM_AGENT_PATH="$AGENT" "$PYTHON" "$RUNNER" --workspace "$ROOT" --host "$HOST" --session "$SESSION" --branch "$BRANCH" || true

echo "Installed SwarmAI autonomous worker A."
echo "Workspace: $ROOT"
echo "Cursor agent: $AGENT"
echo "Assignment poll: every 60 seconds"
echo "State/logs: $APPDIR"
