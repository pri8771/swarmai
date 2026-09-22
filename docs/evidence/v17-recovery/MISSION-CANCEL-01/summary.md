# MISSION-CANCEL-01 — durable mission cancellation generation (service method)

Packet: MISSION-CANCEL-01 (new, hold-independent) · Artifact: ART-V15-WORKER-PROTOCOL · Worker engine: fable
Base source SHA: `b4e2a77b1e0e9d294e268ac931329ec4e7dc9733` · Tested source SHA: see `verify-receipt.json`.

## Why
CP3 finding (2026-09-22): `cancel_active_lease` cancels one lease but never bumps the mission's durable `cancellation_generation`, and no mission-cancel service method existed; the CP3 harness had to bump the row itself. The V1.5 worker protocol requires the durable generation bump **before** advisory worker notification, with the durable generation as the authority.

## Source changes
- `src/swarm/db/lease_fencing.py`
  - `LeaseLifecycleService.revoke_mission_work(*, mission_id, reason="revoked", notify_leases=True, now=None) -> MissionCancellation`: locks the mission row, increments `cancellation_generation`, writes an outbox event `mission.cancellation_generation_bumped`, then (if `notify_leases`) advisory-cancels every active lease of the mission via `cancel_active_lease` (reason "revoked" returns tasks to `ready` so they are re-claimable under the new generation). Mission stays runnable.
  - `LeaseLifecycleService.cancel_mission(*, mission_id, reason="cancelled", now=None)`: the same durable bump first, then `status="cancelled"` (terminal; tasks cancelled).
  - `TaskLeaseRepository.list_active_for_mission`; `MissionCancellation` dataclass.
- `src/swarm/workers/service.py`: `DurableWorkerService.revoke_mission_work` / `cancel_mission` pass-throughs (control-plane API).
- `scripts/r17_cp3_separate_process_recovery.py`: the cancellation step now calls the product method (`notify_leases=False` first to prove the fence holds without notification, then the advisory path). Finding text updated; earlier runs preserved.
- `tests/integration/db/test_mission_cancellation.py`: 4 tests — revoke without notification fences accept (`cancellation_generation_stale`) and renew (`cancellation_generation_stale`) and leaves the mission runnable; revoke with notification fences the old holder and a fresh claim under the new generation is accepted (exactly one); `cancel_mission` is terminal (status cancelled, task cancelled, no further claims); generation is monotonic and durable with two outbox events, unknown mission → `mission_missing`.

## Not in scope (recorded)
Task-level cancellation still uses the mission-level generation (the existing fence model): bumping fences every in-flight lease of the mission. The API route `POST /v1/missions/{id}/cancel` is not yet wired to this durable method — that belongs to the leased execution mode (R17b).

## Checks
- `uv run pytest tests/integration/db/test_mission_cancellation.py -v` → 4 passed (`pytest-output.txt`); harness tests 4 passed.
- Full suite → 437 passed, 13 skipped. Ruff clean; mypy clean.
- Fresh counted CP3 run on the pushed tip: see the next evidence commit.
