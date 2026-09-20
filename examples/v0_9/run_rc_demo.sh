#!/usr/bin/env bash
# V0.9 example: zero-spend public demo suite
set -euo pipefail
cd "$(dirname "$0")/../.."
uv run swarm release install-check
uv run swarm release harden
uv run swarm release demo-suite
uv run swarm release verify
echo "V0.9 example suite finished (see var/reports/)"
