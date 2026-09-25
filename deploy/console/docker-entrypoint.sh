#!/bin/sh
# Write runtime-config.js for the static console (loopback product compose).
# Never prints token values.
set -eu

MODE="${SWARM_CONSOLE_MODE:-live}"
SAME_ORIGIN="${SWARM_CONSOLE_SAME_ORIGIN:-true}"
TOKEN="${SWARM_CONSOLE_TOKEN:-}"
UPSTREAM="${SWARM_CONSOLE_API_UPSTREAM:-http://api:8765}"

escape_js() {
  printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g'
}

TOKEN_JS="$(escape_js "$TOKEN")"
MODE_JS="$(escape_js "$MODE")"

cat > /usr/share/nginx/html/runtime-config.js <<EOF
/* Generated at container start — loopback product use only. */
window.__SWARM_CONSOLE__ = {
  mode: "${MODE_JS}",
  sameOrigin: ${SAME_ORIGIN},
  token: "${TOKEN_JS}"
};
EOF

CONF="/etc/nginx/conf.d/console.conf"
if [ -f "$CONF" ]; then
  # Rewrite default upstream while preserving proxy_pass path behavior.
  sed -i "s|proxy_pass http://api:8765;|proxy_pass ${UPSTREAM};|g" "$CONF"
fi

exit 0
