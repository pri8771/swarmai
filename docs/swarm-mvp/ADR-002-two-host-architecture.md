# ADR-002 — Two-host architecture (supersedes local-only deploy scope)

**Status:** accepted  
**Date Recorded:** 2026-09-25  
**Actual Start Date:** 2026-09-25  
**Architecture Version impact:** deployment topology MINOR (new host roles + compose profiles)  
**Related Prompt:** `internal/two-host-architecture-update.md`  
**Related Decision:** DEC-TH-001

## Context

Original MVP planning assumed a single-operator local install. Operator direction now requires always-on server hardware (R730), Mac as connected worker, and authenticated public hostname `swarm.splitsignal.ai`.

## Decision

| Role | Host |
|---|---|
| Always-on server (API, coordinator, Postgres, artifacts, bounded workers) | R730 |
| Connected worker (coding + permitted local capabilities) | Mac |
| Authenticated ingress | `swarm.splitsignal.ai` via Cloudflare Tunnel (preferred) |

- Docker Compose packages services **per host**; SwarmAI owns scheduling/leases.
- No Postgres replication to Mac; authoritative mission state on server.
- Worker protocol: enrollment, heartbeats, leases, incarnation fencing, durable result submission (existing V2A-004 envelopes).
- Optional OpenCode/Hermes are runtime adapters behind qualification — not kernels.
- Prefer isolated Linux VM on R730 if least disruptive once host access exists; decision deferred until R730 verification.

## Supersedes

Local-only / single-host deployment as the **target topology** for this MVP build.

## Preserves

Existing security defaults (non-root, no public DB ports, loopback publish on Mac verify, `SWARM_ALLOW_PAID=false`), lease/effect/worker code, product packets P00–P19.

## Consequences

Host-specific R730/Cloudflare config is blocked until access verification. Mac can exercise the server compose path locally as TH-01 engineering evidence (not production deploy).
