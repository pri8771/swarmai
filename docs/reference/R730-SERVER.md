# REFERENCE ONLY — R730 always-on server

> **Label:** Reference deployment guide for one operator host (Dell R730).  
> **Not** required for portable product install.  
> Primary path: [`docs/install/`](../install/README.md).

## Intent

Document how an always-on Linux server role can be bound to specific hardware when access exists. Product profiles remain generic (`server` compose). Do not write R730-specific IP/DNS into application source.

## Mapping to portable profiles

| Portable artifact | R730 usage |
|---|---|
| `deploy/compose/server.yml` | Run on the always-on host (or VM on it) |
| `deploy/env/portable.env` | Copy to host-local `server.env`; set strong DB password + seed token |
| `SWARM_HOST_PORT` | Choose a free loopback publish port on that host |
| Public DNS | Separate from this guide — see Cloudflare reference |

## Host verification checklist (deployment qualification)

When SSH/OS/Docker access exists:

1. Confirm OS/arch in doctor smoke (`x86_64` / `amd64` expected on this host)
2. Confirm Docker non-root / compose works
3. Bring up `server` profile on loopback first
4. Verify `/health/live` and `/health/ready`
5. Only then attach authenticated ingress

Evidence for historical two-host packets lives under `docs/evidence/two-host/` — that is qualification evidence, not the portable fresh-install example.

## Blockers

Lack of R730 access is recorded as a **particular deployment** blocker. It must not stop portable install docs, mock/standalone verification, or container-to-container protocol proofs.
