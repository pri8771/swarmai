# G12 / INF-121 — dual-remote zero-charge test plan (prep only)

**Status:** preparation only — **not executed**, **not claimed**  
**Recorded (UTC):** 2026-09-20T23:04:00Z  
**Tip binding:** pending push  
**Spend:** $0 planned; no paid/uncertain routes

## Required gate (contract)

Overlapping real calls through **at least two independently authorized remote providers** in one mission, plus an actually available local route, with exact route identity, zero-charge eligibility, admission and reconciliation evidence.

## Freshness / eligibility checks (before any remote call)

For each candidate remote route `R`:

1. Confirm auth session / API key presence without logging secrets.
2. Confirm provider readiness probe is healthy and **free-eligible** (fail-closed registry).
3. Confirm remaining quota / zero-charge envelope > 0 for the planned request count.
4. Record exact `route_id`, account alias, model id, observed capability set, and probe timestamp.
5. If any check is stale/unknown/paid-only → **do not execute**; mark live-blocked.

Local route `L` (Ollama) remains the admission fallback/control.

## Bounded dual-remote scenario (execute only when both remotes verified)

1. Mission with `max_model_calls` ≥ 4, allow_paid=false.
2. Fire overlapping calls: `R1`, `R2`, and optionally `L` under the same mission broker.
3. Capture: reservation ids, settle receipts, route identities, costs (must be 0.0), denial behavior on exhaust.
4. Kill/disable one remote mid-flight → expect permitted wait/fallback, never paid substitute.
5. Evidence file: `docs/evidence/inf-121/dual-remote-overlap.json` with `live_dual_remote_claimed=true` only if all of the above pass.

## Human step (only if needed later)

If configured zero-charge remote sessions are stale, prepare the exact provider login/consent step for the operator — do **not** ask for a broad account redo, and do **not** invent eligibility.

## Explicitly not claimed now

- Dual remote overlap
- Paid fallback
- INF-121 lead accept
