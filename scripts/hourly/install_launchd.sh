#!/usr/bin/env bash
# Install SwarmAI FIX-004 hourly LaunchAgent (local Mac only; no cloud billing).
set -euo pipefail

REPO="${SWARM_HOURLY_REPO:-$(cd "$(dirname "$0")/../.." && pwd)}"
LABEL="${SWARM_HOURLY_LABEL:-com.swarmai.hourly}"
INTERVAL="${SWARM_HOURLY_INTERVAL:-3600}"
STATE_DIR="${SWARM_HOURLY_STATE_DIR:-$HOME/Library/Application Support/SwarmAI/hourly-runner}"
PLIST_DIR="$HOME/Library/LaunchAgents"
PLIST="$PLIST_DIR/${LABEL}.plist"
PYTHON="${SWARM_HOURLY_PYTHON:-}"
if [[ -z "$PYTHON" ]]; then
  for candidate in /usr/bin/python3 /opt/homebrew/bin/python3; do
    if [[ -x "$candidate" ]]; then
      PYTHON="$candidate"
      break
    fi
  done
fi
if [[ -z "${PYTHON:-}" ]]; then
  echo "no usable python3 found" >&2
  exit 1
fi

mkdir -p "$PLIST_DIR" "$STATE_DIR"

# macOS TCC often blocks LaunchAgents from reading ~/Downloads. Keep the
# executable copy under Application Support so scheduler jobs can start.
CHECKIN_SRC="$REPO/scripts/hourly/checkin.py"
CHECKIN="$STATE_DIR/checkin.py"
cp "$CHECKIN_SRC" "$CHECKIN"
chmod 755 "$CHECKIN"

cat >"$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>${LABEL}</string>
  <key>ProgramArguments</key>
  <array>
    <string>${PYTHON}</string>
    <string>${CHECKIN}</string>
    <string>--repo</string>
    <string>${REPO}</string>
    <string>--trigger</string>
    <string>scheduler</string>
  </array>
  <key>StartInterval</key>
  <integer>${INTERVAL}</integer>
  <key>RunAtLoad</key>
  <true/>
  <key>WorkingDirectory</key>
  <string>${STATE_DIR}</string>
  <key>EnvironmentVariables</key>
  <dict>
    <key>SWARM_HOST_ALIAS</key>
    <string>${SWARM_HOST_ALIAS:-mac-local}</string>
    <key>SWARM_HOURLY_STATE_DIR</key>
    <string>${STATE_DIR}</string>
    <key>SWARM_HOURLY_SKIP_REPO</key>
    <string>1</string>
    <key>SWARM_HOURLY_SKIP_CURSOR_PROBE</key>
    <string>1</string>
    <key>PATH</key>
    <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string>
  </dict>
  <key>StandardOutPath</key>
  <string>${STATE_DIR}/launchd.stdout.log</string>
  <key>StandardErrorPath</key>
  <string>${STATE_DIR}/launchd.stderr.log</string>
  <key>ProcessType</key>
  <string>Background</string>
</dict>
</plist>
EOF

launchctl bootout "gui/$(id -u)/${LABEL}" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"
launchctl enable "gui/$(id -u)/${LABEL}" 2>/dev/null || true

echo "installed ${PLIST}"
echo "interval=${INTERVAL}s repo=${REPO} checkin=${CHECKIN} python=${PYTHON}"
launchctl print "gui/$(id -u)/${LABEL}" 2>&1 | head -40
