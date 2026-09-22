#!/usr/bin/env bash
# Manual progress heartbeat on the single CURSOR-V17-SINGLE stream (Fable engine).
# Usage: hb.sh --packet R27b --artifact ART-... --status working --note "..." --next-action "..." [--blocker "..."]
APPDIR="$HOME/Library/Application Support/SwarmAI/coord-heartbeat-v17"
cd "$APPDIR" && SWARM_GH_PATH=/opt/homebrew/bin/gh SWARM_COORD_HEARTBEAT_STATE_DIR="$APPDIR" \
  SWARM_HB_ENGINE=fable SWARM_HB_EPOCH=fable-v17-20260922-01 \
  /opt/homebrew/bin/python3 heartbeat.py --branch cursor/v17-single-session --trigger manual --spend-usd 0 "$@"
