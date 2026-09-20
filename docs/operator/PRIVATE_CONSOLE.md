# Private local console (loopback only)

Not a public deployment. Bound to `127.0.0.1`.

## Start

```bash
# Optional private bootstrap token (outside git):
#   ~/Library/Application Support/SwarmAI/secret-drop/loopback-token.txt
export SWARM_SEED_LOOPBACK_TOKEN="$(cat "$HOME/Library/Application Support/SwarmAI/secret-drop/loopback-token.txt")"

uv run swarm serve --host 127.0.0.1 --port 18765
npm --prefix apps/console run dev -- --host 127.0.0.1 --port 43127
```

- API: http://127.0.0.1:18765/health/live
- Console (mock fixtures): http://127.0.0.1:43127/
- Console (live durable missions): http://127.0.0.1:43127/?mode=live&baseUrl=http://127.0.0.1:18765&token=YOUR_TOKEN

Do not commit tokens. Do not bind `0.0.0.0`. Do not expose publicly.

## Verified this session

- API health OK on 18765
- Console HTTP 200 on 43127
- Mission create/list shared with `var/missions` MissionStore
