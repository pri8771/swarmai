#!/usr/bin/env bash
# Install exactly one CURSOR-V17-SINGLE coordination heartbeat LaunchAgent.
set -euo pipefail

SESSION="CURSOR-V17-SINGLE"
BRANCH="cursor/v17-single-session"
LABEL="com.swarmai.coord-heartbeat-v17"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SOURCE="$ROOT/scripts/coordination/heartbeat.py"
APPDIR="$HOME/Library/Application Support/SwarmAI/coord-heartbeat-v17"
RUNNER="$APPDIR/heartbeat.py"
PLIST="$HOME/Library/LaunchAgents/${LABEL}.plist"

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
if [[ ! -f "$SOURCE" ]]; then
  echo "missing heartbeat source: $SOURCE" >&2
  exit 2
fi

# Fail closed: stop legacy SwarmAI heartbeat / hourly agents if somehow loaded.
for legacy in \
  com.swarmai.coord-heartbeat-a \
  com.swarmai.coord-heartbeat-b \
  com.swarmai.hourly \
  com.swarmai.autonomous-worker-a \
  com.swarmai.autonomous-worker-b
do
  launchctl bootout "gui/$UID/$legacy" >/dev/null 2>&1 || true
  launchctl disable "gui/$UID/$legacy" >/dev/null 2>&1 || true
done

mkdir -p "$APPDIR" "$HOME/Library/LaunchAgents"
cp "$SOURCE" "$RUNNER"
chmod 700 "$RUNNER"

cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>${LABEL}</string>
  <key>ProgramArguments</key>
  <array>
    <string>${PYTHON}</string>
    <string>${RUNNER}</string>
    <string>--branch</string><string>${BRANCH}</string>
    <string>--trigger</string><string>scheduler</string>
  </array>
  <key>EnvironmentVariables</key>
  <dict>
    <key>SWARM_GH_PATH</key><string>${GH}</string>
    <key>SWARM_COORD_HEARTBEAT_STATE_DIR</key><string>${APPDIR}</string>
    <key>PATH</key><string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string>
  </dict>
  <key>WorkingDirectory</key><string>${APPDIR}</string>
  <key>StartInterval</key><integer>300</integer>
  <key>RunAtLoad</key><false/>
  <key>StandardOutPath</key><string>${APPDIR}/stdout.log</string>
  <key>StandardErrorPath</key><string>${APPDIR}/stderr.log</string>
  <key>ProcessType</key><string>Background</string>
</dict>
</plist>
EOF

launchctl bootout "gui/$UID/${LABEL}" >/dev/null 2>&1 || true
launchctl bootstrap "gui/$UID" "$PLIST"
launchctl enable "gui/$UID/${LABEL}" >/dev/null 2>&1 || true

# Publish session_started immediately (does not rely on RunAtLoad alone).
SWARM_GH_PATH="$GH" SWARM_COORD_HEARTBEAT_STATE_DIR="$APPDIR" \
  "$PYTHON" "$RUNNER" \
  --branch "$BRANCH" \
  --trigger install \
  --status session_started \
  --packet BOOTSTRAP \
  --artifact cross-version \
  --note "CURSOR-V17-SINGLE session_started; legacy A/B LaunchAgents stopped; exactly one v17 producer installed." \
  --blocker "" \
  --spend-usd 0 \
  --force

echo "Installed ${LABEL} for ${SESSION}. Scheduler wakes every 5m; client self-throttles via HEARTBEAT_STATE.json."
