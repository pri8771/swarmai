# ADR-002 — Two-host architecture (operator reference topology)

**Status:** accepted (operator deployment topology — **REFERENCE** for named hosts)  
**Date Recorded:** 2026-09-25  
**Actual Start Date:** 2026-09-25  
**Architecture Version impact:** deployment topology MINOR (new host roles + compose profiles)  
**Related Prompt:** `internal/two-host-architecture-update.md`  
**Related Decision:** DEC-TH-001  
**Portable product install (primary):** [`docs/install/`](../install/README.md)  
**Labelled reference guides:** [`docs/reference/`](../reference/README.md)

## Context

Original MVP planning assumed a single-operator local install. Operator direction for *this* deployment required always-on server hardware (R730), Mac as connected worker, and an authenticated public hostname. Those names are **deployment config / reference**, not portable product constants.

## Decision

| Role | Host (this deployment) |
|---|---|
| Always-on server (API, coordinator, Postgres, artifacts, bounded workers) | R730 (**REFERENCE**) |
| Connected worker (coding + permitted local capabilities) | Mac (**REFERENCE**) |
| Authenticated ingress | Operator DNS via Cloudflare Tunnel (**REFERENCE**) |

- Docker Compose packages services **per host**; SwarmAI owns scheduling/leases.
- No Postgres replication to Mac; authoritative mission state on server.
- Worker protocol: enrollment, heartbeats, leases, incarnation fencing, durable result submission (existing V2A-004 envelopes).
- Optional OpenCode/Hermes are runtime adapters behind qualification — not kernels.
- Prefer isolated Linux VM on R730 if least disruptive once host access exists; decision deferred until R730 verification.
- Generic product docs must use placeholders (`coordinator.example.test`) and must not require R730/Mac/CF to complete a fresh install.

## Supersedes

Local-only / single-host deployment as the **only** documented topology for this MVP build. Portable install docs restore a first-class generic path; this ADR remains the labelled reference for the named two-host deployment.

## Preserves

Existing security defaults (non-root, no public DB ports, loopback publish for local verify, `SWARM_ALLOW_PAID=false`), lease/effect/worker code, product packets P00–P19.

## Consequences

Host-specific R730/Cloudflare config is blocked until access verification and does not block portable eng. Mac can exercise the server compose path locally as TH-01 engineering evidence (not production deploy).
