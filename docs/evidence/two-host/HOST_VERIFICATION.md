# Two-host host verification & TH-01 evidence

**Date:** 2026-09-25T15:05Z  
**Branch tip (pre-commit):** see git after push  
**Hostname (operator correction):** `swarm.splitsignal.ai` — **not** `.com`

## Mac

| Check | Result |
|---|---|
| OS | macOS 26.6.2 Darwin 25.6.0 arm64 (Apple M5 Pro, 48 GiB) |
| Docker | 29.5.2 (linux/aarch64 engine) |
| Compose | 5.5.1 |
| cloudflared | 2026.6.1 installed; **no origin cert** |
| Port conflict | Host `127.0.0.1:8765` occupied by unrelated `jobs-automation dashboard`; server compose publishes **18765** |

## R730

| Check | Result |
|---|---|
| SSH Host `r730` / `swarm` | **Blocked** — hostname does not resolve; no usable SSH config Host entry |
| OS / virt / Docker / storage | **Not run** |

## DNS / ingress

| Check | Result |
|---|---|
| `swarm.splitsignal.ai` A/AAAA | **Empty** (dig 2026-09-25) — zone/record not configured yet |
| `swarm.splitsignal.com` | Resolves to AWS anycast — **superseded / do not use** |
| Cloudflare Tunnel | Not started (no cert/credentials); `--profile tunnel` remains off |

## TH-01 Mac containerized server (engineering verify)

Commands (repo root `swarm-ai-two-host-mvp`):

```sh
docker compose -f deploy/compose/server.yml build
docker compose -f deploy/compose/server.yml up -d
curl -fsS http://127.0.0.1:18765/health/live
curl -fsS http://127.0.0.1:18765/health/ready
```

Observed:

- Migrations applied to head (`9eb193b10f4e` … `a18tov30schema0001`)
- `/health/live` → `{"status":"ok","service":"swarm","version":"1.0.0rc1"}`
- `/health/ready` → `database":"up"`, `status":"ready"`, `allow_paid":false`
- After `up -d --force-recreate api db`, probe row `th01-durable` still present in Postgres volume
- Postgres **not** published to host; API bound to `127.0.0.1:18765` only
- Tunnel profile **not** enabled

**Not claimed:** R730 production deploy, public ingress, authenticated Cloudflare Access, or completed product mission path (TH-02+).

## Checks

| Check | Result |
|---|---|
| `pytest tests/deployment/test_deployment.py` | **passed** (8) |
| `swarm deploy doctor --profile server` | **ok** (DB URL missing in host env expected for doctor dry-run) |
| `swarm deploy doctor --profile mac_connector` | **ok** with `SWARM_SERVER_URL` |
| Linear MCP update | **blocked** (`needsAuth` / auth timeout) — see `docs/swarm-mvp/LINEAR_RECONCILIATION.md` |
| Runtime OpenCode/Hermes | **not started** |
| Live providers | **not run** (free-only / no spend) |
