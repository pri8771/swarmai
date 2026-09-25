# Configurable URLs and ingress

Install and run without editing application code: set environment variables and compose overrides.

## Environment variables

| Variable | Purpose | Example (placeholder) |
|---|---|---|
| `SWARM_BIND_HOST` | API listen address inside process/container | `127.0.0.1` or `0.0.0.0` (compose internal) |
| `SWARM_PORT` | API listen port inside process/container | `8765` |
| `SWARM_HOST_PORT` | Host publish port (compose) | `8765` |
| `SWARM_SERVER_URL` | Worker → server base URL | `http://127.0.0.1:8765` |
| `SWARM_API_BASE_URL` | Canonical API base (P4 `PublicEndpointConfig`) | `https://coordinator.example.test` |
| `SWARM_PUBLIC_BASE_URL` | Optional public/edge URL | `https://edge.example.test` |
| `SWARM_PUBLIC_HOSTNAME` | DNS hostname for ingress templates | `coordinator.example.test` |

Aligned with `src/swarm/product/portable_config.py`. Do **not** bake a personal or production hostname into committed env *examples*. Product code hostname hardcoding is Lane P1; examples here stay portable.

## Console / clients

Point the operator console at your API:

```text
http://127.0.0.1:5173/?mode=live&baseUrl=http://127.0.0.1:8765&token=YOUR_LOCAL_TOKEN
```

Prefer query `baseUrl` over assuming any public DNS name.

## Ingress

Default: **loopback only** (`127.0.0.1:PORT`). No public deploy without authentication.

Optional authenticated tunnel sidecar is documented as a **reference** guide:

→ [`docs/reference/CLOUDFLARE-TUNNEL.md`](../reference/CLOUDFLARE-TUNNEL.md)

Generic ingress requirements:

1. Terminate TLS at a trusted edge or reverse proxy
2. Require operator authentication (Access / mTLS / equivalent) before API routes
3. Keep Postgres and inference admin ports off the public internet
4. Map `SWARM_PUBLIC_HOSTNAME` / `SWARM_API_BASE_URL` / `SWARM_PUBLIC_BASE_URL` in **runtime** config files that are gitignored

## Compose port publish pattern

```yaml
ports:
  - "127.0.0.1:${SWARM_HOST_PORT:-8765}:8765"
```

Override `SWARM_HOST_PORT` when multiple local stacks collide — any free port is fine; no host-specific default is required for product correctness.
