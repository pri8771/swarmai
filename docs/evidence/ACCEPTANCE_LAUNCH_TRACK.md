# Acceptance + launch track (operator-authorized)

**Date:** 2026-09-23  
**Authorization:** operator asked to drive to accepted + launched after V3.0 implementation-complete; paid spend still forbidden; lead accept must not be invented.  
**PR:** https://github.com/pri8771/swarmai/pull/41  

## Accepted vs blocked (per artifact)

| Artifact / checklist item | State | Notes |
|---|---|---|
| V1.8 local SiteEpoch/backup/restore/drill | **evidence-complete (local)** | Live multi-host = USER_ACTION |
| V1.9 extensions/install/selfdev gates | **evidence-complete (local)** | Fresh/external install = USER_ACTION |
| V2.0 CandidateManifest + support/security/perf/reliability protocol | **evidence-complete (local freeze)** | Wall-clock campaign + independent review + lead accept = USER_ACTION |
| V2.3 scheduler/reservations/packs/portability/ops/fleet | **evidence-complete (deterministic)** | Multi-process private = USER_ACTION |
| V3.0 objectives/learning/allocator | **evidence-complete (deterministic)** | Integrated live suite + lead accept = USER_ACTION |
| FIX-003 offline+live tip binds | **pass this session** | `swarm release verify` label `offline-and-live-evidence-present-validated` |
| Lead accept any ART-* | **USER_ACTION** | Packages under `docs/evidence/v20/` and `v30/` |
| Main merge / tag / publish | **authorized track; execute if tools allow** | Remaining human clicks documented if blocked |

## Launch checklist (`docs/release/V1_RELEASE_CHECKLIST.md`) — worker progress

| Item | Worker result |
|---|---|
| `swarm release first-run` | pass |
| `swarm release freeze` | pass |
| `swarm release harden` | pass |
| `swarm release verify` | pass (tip-bound offline + live) |
| `swarm release validate` | re-run after final tip rebind; cells green when verify green |
| `swarm release demo-suite` | pass, `cost_usd: 0.0` |
| pytest contracts/product/release (+ recovery/objectives) | pass |
| Zero-spend proofs `cost_usd: 0.0` | pass (canary + demo + reliability) |
| No `.env`/secrets tracked | pass (`harden`) |
| CHANGELOG / STATUS updated | this commit set |
| Explicit human approval to merge/tag/publish | operator launch-track authorization present; ART lead sign still USER_ACTION |

## Exact human actions remaining

1. **Lead sign-off** on V2.0/V3.0 lead-accept packages (cannot be agent-invented).
2. **Optional:** start wall-clock reliability campaign; record real `started_at`.
3. **Optional:** fresh/external install on a clean host; second-host recovery.
4. **CI:** confirm latest tip offline job green on GitHub Actions.
5. **Merge button** on PR #41 (if write tools blocked for agent).
6. **Tag / publish** only after checklist green + lead decision (e.g. `v3.0.0-rc.1` vs accepted release).
7. Keep `SWARM_ALLOW_PAID=false` unless a later message authorizes paid spend.
