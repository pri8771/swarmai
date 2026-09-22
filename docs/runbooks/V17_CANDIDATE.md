# V1.7 private/local candidate — run, restart, stop

Not a public deployment. Loopback only. Zero spend (`SWARM_ALLOW_PAID=false`).

| Item | Value |
|---|---|
| URL | `http://127.0.0.1:18771` (loopback only; not reachable from other hosts by design) |
| Health | `GET /health/live`, `GET /health/ready` (public) |
| API | `/v1/...` — requires `Authorization: Bearer <loopback token>`; unauthenticated → 401 |
| Source checkout | `/Users/pchordia/swarmai-v17` (branch `cursor/v17-single-session`) — tested SHA is in the handoff |
| Service | launchd `com.swarmai.v17-candidate` (RunAtLoad + KeepAlive) → `scripts/v17_candidate.sh run` → `uv run swarm serve --host 127.0.0.1 --port 18771` |
| Config (not in Git) | `~/Library/Application Support/SwarmAI/v17-candidate/candidate.env` (mode 600): `SWARM_DATABASE_URL`, `SWARM_SEED_LOOPBACK_TOKEN`, `SWARM_ALLOW_PAID=false`, `OLLAMA_BASE_URL`, `SWARM_REPO_ROOT` |
| Database | PostgreSQL 16 (Homebrew) `swarmai_v17_live`, migrated to head `a17effect004b0001` |
| Inference | Ollama at `http://127.0.0.1:11434` (local models only) |
| Logs | `~/Library/Application Support/SwarmAI/v17-candidate/stdout.log`, `stderr.log` |

## Commands (from the checkout)

```sh
scripts/v17_candidate.sh start     # (re)install the launchd agent and start
scripts/v17_candidate.sh status    # launchd state + health/live code
scripts/v17_candidate.sh restart
scripts/v17_candidate.sh stop
scripts/v17_candidate.sh logs 100
```

After pulling a new tip: `uv sync && SWARM_DATABASE_URL=... uv run alembic upgrade head && scripts/v17_candidate.sh restart`.

## Notes

- launchd agents cannot read `~/Downloads`/`~/Documents`/`~/Desktop` (macOS TCC); the checkout lives at `~/swarmai-v17` for that reason.
- The older V1.4 server on port 18765 (`~/Downloads/swarm-ai-v14`) is a separate, historical process and is not this candidate.
- Real missions are run with `uv run swarm mission run ...` against the same database, so they appear in `GET /v1/missions` / `/v1/history`.
