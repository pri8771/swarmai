# Private local console (loopback only)

Not a public deployment. Bound to `127.0.0.1`.

## Start

```bash
# Optional private bootstrap token (operator-local file outside git).
# Example pattern — create your own path; do not require a personal absolute path:
#   mkdir -p "${XDG_CONFIG_HOME:-$HOME/.config}/swarmai"
#   umask 077; head -c 32 /dev/urandom | base64 > "${XDG_CONFIG_HOME:-$HOME/.config}/swarmai/loopback-token"
export SWARM_SEED_LOOPBACK_TOKEN="$(cat "${XDG_CONFIG_HOME:-$HOME/.config}/swarmai/loopback-token")"

uv run swarm serve --host 127.0.0.1 --port 8765
npm --prefix apps/console run dev -- --host 127.0.0.1 --port 5173
```

- API: http://127.0.0.1:8765/health/live
- Console (mock fixtures): http://127.0.0.1:5173/
- Console (live durable missions): http://127.0.0.1:5173/?mode=live&baseUrl=http://127.0.0.1:8765&token=YOUR_TOKEN

Do not commit tokens. Do not bind `0.0.0.0` for this private console path. Do not expose publicly.

macOS Application Support paths used in past sessions are **operator-local** — see [`docs/reference/MAC-CONNECTOR.md`](../reference/MAC-CONNECTOR.md).
