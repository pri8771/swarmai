# V3.0 exit requirement audit (implementation-complete)

**Tip:** see `git rev-parse HEAD` on branch `cursor/cloud-agent-1790175458840-642hd`  
**Verdict:** V3.0 **implementation-complete is proven for local/deterministic scope** — **not** accepted, **not** launched. Integrated live evidence remains pending.

## V1.8

| Item | Evidence | Result |
|---|---|---|
| SiteAuthority/SiteEpoch durable state | `src/swarm/recovery/authority.py`, models + `a18tov30schema0001` | pass |
| Dispatch epoch-bound | `AdaptiveScheduler.choose_ready` + tests | pass |
| Result acceptance epoch-bound | reservations + restore reconcile; durable lease path still lease-generation primary | pass (local) |
| Consequential effect epoch-bound | `ConsequentialToolGateway._check_site_epoch` | pass |
| Redacted deployment manifest | `deploy/profiles.py` allow_paid_cloud=false | pass |
| Backup manifest/integrity | `recovery/backup.py` + tests | pass |
| Restore/reconcile | `recovery/restore.py` | pass |
| Split-brain negatives | drill + stale epoch tests | pass |
| Outage drill harness | `recovery/drill.py`, CLI `swarm recovery drill` | pass |
| Live outage/restore | multi-host | pending |

## V1.9

| Item | Evidence | Result |
|---|---|---|
| Extension manifest/lifecycle | `extensions/*` | pass |
| Project-scoped grant | registry tests | pass |
| No broker/gateway bypass | ExtensionLoader → V17 gateway | pass |
| Clean install / upgrade / rollback | `deploy/install.py` + CLI | pass |
| Support bundle redacts secrets | tests | pass |
| Selfdev PR candidate / no self-merge | `selfdev/policy.py` | pass |
| Fresh/external install | | pending |

## V2.0 candidate

| Item | Evidence | Result |
|---|---|---|
| Lower versions integrated | tip packages | pass |
| One Alembic head | `a18tov30schema0001` | pass |
| CandidateManifest frozen | `docs/evidence/v20/candidate_manifest.json` | pass |
| Deterministic CI/tests | offline pytest suites green this tip | pass (local) |
| Support matrix evidence-grounded | `docs/evidence/v20/support_matrix.json` | pass |
| Install/upgrade/rollback executable | plans + CLI | pass |
| Security review mapped | `docs/evidence/v20/security_review_map.json` | pass |
| Performance baseline executable | `docs/evidence/v20/performance_baseline.json` | pass |
| Reliability protocol frozen | `docs/evidence/v20/reliability_protocol_freeze.json` | pass |
| Wall-clock campaign | | pending |

## V2.3

| Item | Evidence | Result |
|---|---|---|
| Scheduler durable / fairness / aging | fairness + AdaptiveScheduler | pass |
| Reservation transactional/fail-closed | reservations + tests | pass |
| Provider/worker/tool capacity | ReservationService capacities | pass |
| Backpressure / cancel / drain | reservations + scheduler drain | pass |
| Scheduler SiteEpoch | AdaptiveScheduler | pass |
| Decision receipts | scheduling_receipts | pass |
| Capability packs lifecycle | capabilities + signature/revoke | pass |
| Portability export/import | product/portability | pass |
| Observability read surface | OpsEventLog | pass |
| Dashboard mutation action boundary | assert_dashboard_mutation_via_action | pass |
| Fleet placement/trust/locality | workers/fleet.py | pass |
| Pathological deterministic suite | test_v23_v20 + test_v18_v30_gaps | pass |
| Multi-process private evidence | | pending / UNKNOWN |

## V3.0

| Item | Evidence | Result |
|---|---|---|
| Immutable objective/version | ObjectiveRepository | pass |
| Trigger policies / dedupe / rate / max-active | objectives + tests | pass |
| Pause/revoke/expiry / stop | objectives | pass |
| MissionProposal + admission bridge | admit_to_mission | pass |
| Authority intersection | intersect_authority | pass |
| LearningProposal SM + holdout + review + canary + rollback + drift + contamination | learning + tests | pass |
| Allocator uses V2.3 scheduler path | ResourceAllocator | pass |
| Selfdev learning governance / no self-merge | policy | pass |
| Capability trust/signature/revocation | CapabilityPackRegistry | pass |
| Tenant fleet/audit + cross-tenant negatives | fleet tests | pass |
| Integrated live evidence suite | | pending |

## Operator-gated remaining

- Lead accept; FIX-004 Cursor CLI login; remote dual; LIVE-142; second host; wall-clock campaign; main merge; public launch; paid spend
