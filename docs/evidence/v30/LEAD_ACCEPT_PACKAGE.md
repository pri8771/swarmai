# V3.0 lead accept package

**Status:** worker-prepared for independent lead review — **not** lead-accepted  
**Branch tip:** see `git rev-parse HEAD` on PR #41 lane  
**Spend:** `SWARM_ALLOW_PAID=false`  
**Self-permission:** false (objectives/learning cannot expand spend/merge/deploy)

## Implementation-complete (local / deterministic)

| Area | Evidence | Worker status |
|---|---|---|
| ObjectiveContract versions / trigger / dedupe / rate / stop | `src/swarm/objectives/`, tests | pass |
| MissionProposal admission bridge | `admit_to_mission` | pass |
| LearningProposal SM + holdout + review + canary + rollback + drift | `src/swarm/learning/`, tests | pass |
| Allocator → V2.3 scheduler | `ResourceAllocator` | pass |
| Selfdev learning governance / no self-merge | `selfdev/policy.py` | pass |
| Capability trust/signature/revocation | `CapabilityPackRegistry` | pass |
| Tenant fleet + cross-tenant negatives | fleet tests | pass |
| CLI/API surfaces | `swarm objectives|learning|fleet`, `/v1/objectives`, `/v1/learning` | pass |

Exit audit: `docs/evidence/V3_EXIT_REQUIREMENT_AUDIT.md`  
Receipt: `docs/evidence/v30/objectives_learning_complete.json`

## USER_ACTION blockers (not claimed)

- Lead accept of ART-V30 / ART-V20 / prior ART-*
- Integrated private-live V3 evidence suite
- Wall-clock reliability campaign (V2.0)
- Fresh/external install evidence
- Second-host / multi-process private evidence
- FIX-004 Cursor CLI login
- Remote dual / LIVE-142 / G13 sealed qualification
- Paid spend (`SWARM_ALLOW_PAID` remains false)

## What is not claimed

- Accepted V3.0
- Public launch complete
- Lead signature on any ART
