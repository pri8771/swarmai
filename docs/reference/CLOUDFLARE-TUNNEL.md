# REFERENCE ONLY — Cloudflare Tunnel ingress

> **Label:** Reference guide for Cloudflare Tunnel + Access in front of a SwarmAI API.  
> **Not** required for portable loopback install.  
> Primary path: [`docs/install/URLS_AND_INGRESS.md`](../install/URLS_AND_INGRESS.md).

## Intent

Publish an authenticated hostname to a private origin without opening Postgres or raw host ports. Never enable the tunnel profile without origin certificates **and** an Access (or equivalent) policy.

## Portable placeholders

Committed example: `deploy/cloudflare/tunnel.example.yml`

- Uses placeholder tunnel id and hostname `coordinator.example.test`
- Copy to **gitignored** `deploy/cloudflare/tunnel.runtime.yml` on the server host
- Mount credentials via `CLOUDFLARED_CREDENTIALS_DIR` (never commit `tunnel.json`)

```sh
# After cert + tunnel credentials exist on the host:
docker compose -f deploy/compose/server.yml --profile tunnel up -d
```

Set runtime:

- `SWARM_PUBLIC_HOSTNAME` to the real DNS name
- `SWARM_API_BASE_URL` to `https://<that-hostname>`

## Security rules

1. No unauthenticated public API
2. Protect all non-health routes with Access
3. Prefer exposing `/health/live` (and optionally ready) narrowly if probes need them
4. Do not put Cloudflare account ids, API tokens, or tunnel credentials in git
5. Do not treat DNS cutover as product acceptance by itself

## Historical hostname

Operator deployments may use a personal DNS name. That name is **deployment config**, not a product constant. Fresh-install examples must keep `coordinator.example.test` (or similar) placeholders.

## Blockers

Missing Cloudflare/DNS access blocks **this ingress path’s** qualification — not mock/standalone portable engineering.
