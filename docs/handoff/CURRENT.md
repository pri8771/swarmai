# Handoff — V1.4 → V3.0 implementation lane

**Date:** 2026-09-23  
**Branch:** `cursor/cloud-agent-1790175458840-642hd`  
**Plan:** `/opt/cursor/artifacts/plans/v1_to_v3_roadmap_e96337c7.plan.md`  
**Spend:** `SWARM_ALLOW_PAID=false` · **no** public launch · **no** self-accept  

## Completed (implementation-complete, not lead-accepted)

| Phase | Status |
|-------|--------|
| 0 Bootstrap + FUTURE docs | done |
| 1 V1.4 G11–G14 evidence transplant | done (remote/LIVE still blocked) |
| 2 V1.5 lease/workers transplant | done (multi-host UNKNOWN) |
| 3 V1.6 knowledge transplant | done (task quality UNKNOWN) |
| 4 V1.7 action gateway transplant | done |
| 5 V1.8 SiteEpoch/backup/restore/drill | done (local drill pass; epoch wired into gateway/scheduler) |
| 6 V1.9 extensions/install/selfdev gate | done (external install pending; CLI/API reachable) |
| 7 V2.0 CandidateManifest freezer | done (elapsed reliability pending) |
| 8 V2.3 fairness/reservations/packs/portability/fleet/ops | done (multi-process live UNKNOWN) |
| 9 V3.0 objectives + learning + allocator | done (integrated live pending; CLI/API wired) |

## Gap-close (post PR #41 claim audit)

Closed without operator gates:
- SiteEpoch fencing on consequential gateway + AdaptiveScheduler dispatch
- Reservation drain/cancel/backpressure
- Objective rate/expiry/stop/authority intersection
- Fleet tenant placement + cross-tenant negatives
- Ops event read surface + dashboard mutation boundary assert
- Capability pack signature/revocation trust
- Selfdev learning-governance gate
- CLI: recovery drill/backup, install plans, extensions, objectives, learning, fleet, candidate-freeze
- API: `/v1/objectives`, `/v1/learning/proposals`, `/v1/recovery/drill`, `/v1/install/clean-plan`, `/v1/ops/events`, `/v1/release/candidate-freeze`

## Still operator-gated

- Lead accept of any ART-*
- FIX-004 Cursor CLI login
- Remote dual / LIVE-142 / HOST-WIN-DEV qualification
- Second-host recovery / multi-process private-live
- Wall-clock reliability campaign
- Main merge / tag / public launch / paid spend
