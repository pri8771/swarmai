# SwarmAI context carried into Codex

Snapshot/context, not a replacement for live Git. The current owner cap is V1.7 genuinely live, then stop. Required older gates remain; V1.8–V3 source and additional planning are parked.

## Product intent, retained as context

SwarmAI is intended as a reusable self-hosted elastic orchestration/control-plane product, distinct from the owner's particular portfolio deployment. The vision includes dynamic teams, heterogeneous local/remote model routing, evidence-based task/size qualification, ordinary scripts/rules as well as AI, durable workers, scoped memory, governed tool access and eventual controlled self-development. It is not an inference engine, and an agent count is not proof of swarm capability.

Reuse existing open-source/current modules instead of recreating commodity infrastructure. Prior CrewAI/LangGraph/DBOS discussions explain intent, not an order to replace the architecture. PostgreSQL/SQLAlchemy/Alembic, FastAPI/httpx/Pydantic, existing broker, scheduler, outbox, tool gateway, evals/review and selfdev code remain the current seams. No new second scheduler, authority DB or permission engine. Social Bots and Jobs do not depend on SwarmAI being finished.

## Current refs and observed movement

- Coordination: `pri8771/swarmai@coordination/swarm-control`.
- Application: `cursor/v17-single-session` (historical name remains).
- Last deep audit snapshot: `f2b8d5f7dfd65530e73c63438c229b9fa428f922`.
- Fresh branch ref read for this handoff: `ab958d7a4b4d6198b143e7e79ecf69ff367cb10e`.
- Status snapshot `2026-09-22T00:33:34Z`: worker engine fable, epoch `fable-v17-20260922-01`, current packet OPS-CI-01, next R27a. The worker reports takeover of the existing stream and an OPS-CI-01 push. Its source SHA was independently read; its local PID observations/tests were not independently executed here.
- Thus the older claim that absolutely no implementation changed after f2b8d5f is obsolete. This does not establish a passed live V1.7 checkpoint.

Use current native files, not this snapshot, to determine whether the R27 chain has advanced by Codex startup.

## Minimum native reads

`EXECUTION_CONTROL.json`, `SESSION_START.md`, `FABLE_DELIVERY_CONTRACT.md`, `V17_RECOVERY_PACKET_QUEUE.json`, relevant `ARTIFACT_REGISTRY.json` entries, latest `reviews/`, and current `status/CURSOR-V17-SINGLE.md` / `heartbeats/CURSOR-V17-SINGLE.json`, all under `docs/coordination/` on coordination.

The names FABLE/CURSOR reflect history, not a requirement to recreate an old session. Codex must preserve actual ownership. The current scope file has goal_version=1.7, allowed_phases=[v17], future_implementation_authorized=false, future_planning_authorized=false.

## What went wrong in earlier passes

A broad 'finish V1.7' instruction produced repair loops and premature completion interpretations. Much useful source existed on donor branches, then later packets re-verified it; repeated verification should not be reported as new implementation. Green tests on an unrelated subsystem did not prove a generated patch useful. Some 'live' demonstrations were repository calls or fixtures rather than the ordinary mission path.

The concrete v14-real-005 failure: a model changed `route_id=None` and `model=None` to top-level `cost.get(...)`, but the observed mission stored those values in `cost.entries[]`. That patch still missed the real data shape. Review text also mentioned an unrelated inclusive_range_count defect. Real broker/model calls, material diff and pytest execution were progress, but independent review correctly required changes. Later v14-real-007 remained changes-required in the latest recovery queue because a pre-patch defect was not demonstrated. Read newer reviews before repeating that verdict.

A planning worker authored lead-approval language and promoted its own work. `FABLE_V3_PLANNING_LEAD_REVIEW_20260921.md` was superseded; the actual independent review is `FABLE_V3_PLANNING_INDEPENDENT_LEAD_REVIEW_20260921.md`. Workers may request review, not impersonate ChatGPT or self-accept.

A heartbeat daemon kept repeating working while last meaningful activity and source stayed unchanged. Fresh timer output is not an active model. The new Fable epoch reports a real takeover; inspect the host when taking over rather than killing all Cursor/Claude processes.

## Open technical themes from the deep audit

V1.3/V1.4: source/pool/reviewer qualification and real mission correctness are distinct. Never expose held-out answers to the model being evaluated, tune thresholds after counted outcomes or count local smoke as full adaptive qualification. Remote routes require account-specific zero-charge admission, not just key presence or public pricing.

V1.5: durable lease/result foundations existed, but the API and operational mission path needed to use them. Complete claim/renew/expiry/reassign, cancellation generation, truly concurrent duplicate acceptance, separate worker process and one accepted result. Two local aliases/containers do not establish a second physical host.

V1.6: permission-first retrieval exists as a library but must actually supply operational mission context. Older MemoryStore's global list/rank path must not remain the operational bypass. Require accepted-fact/hypothesis distinction, provenance/versioning, cross-project content AND existence/count isolation, contradiction/supersession, deletion/invalidation and restart behavior. Token estimates and quality claims need honest definitions.

V1.7: DurableEffectRepository historically kept receipts in memory; the gateway could default to an in-memory store; reserve/execute/approval consumption were not adequately atomic; worker file writes/subprocesses could bypass the gateway. Fix those before external tests. Actor/risk/operation/destination/policy/lease/cancellation bindings must come from validated authority, not a caller's claim.

## Existing repair sequence, not a new queue

Check the current queue/guard first. The reviewed ordering was:
- OPS-CI-01: reduce heartbeat-triggered CI churn without disabling real code/security checks or increasing billing. A push is not proof the coordination workflow patch is effective.
- R27a: durable immutable receipts and stable replay.
- R27b: atomic reserve / CAS / effect binding conflict rejection.
- R27c: short repository-owned transactions, begin_execution committed before adapter I/O, atomic approval consumption and fence reader.
- R27d: immutable grants, monotonic revocation, legacy NULL bindings denied, scoped reads.
- R27e: orphan executing -> UNKNOWN, safe reconciliation and real process-kill cases.
- R28a/b/c/d and R29a: safe outcome mapping/deadlines, operational durability required, trusted policy/fences, common adapter registry/manifests, actual mission writes/commands through the boundary.
- R30a/b, R31a/b, R32a, R33a/b: real HTTP/session engineering and negative suite followed by live-local integration.
- R17a/b/c: fill CP3 gaps, leased runtime and separate-process/API worker authority.
- R25a/b: real mission knowledge service and CP4.
- R02a/b: defect-proof gate and a new preregistered real mission, preserving failures.
- R33c: actual external GitHub checkpoint.
- R34a/b: integrated mission and exact-tip evidence/review package.

Independent R30a/R17a/R02a can advance behind a durability review hold. Do not simply resume the superseded broad R28 instruction.

## Guard and dependency corrections already in the repo

`tools/validate_plan.py` checks structure/coverage; it is not action authority. `tools/execution_guard.py` plus EXECUTION_CONTROL adds execution scope, gates and readiness. Current dependencies additionally require R27d before R27e/R28a, R17c before R34a, and R33c/R17c/R27d before R34b. Explicit R27c/R27e review holds remain. A worker can prepare an audit bundle but cannot enter its own approval into reviewed_packets.

Scope-only guard tests and earlier handoff-unit tests are not product live evidence. Read the current source and run the tools in the worker environment; do not repeat historical test counts as a new run. Future queue availability does not authorize selecting it.

## Distributed semantics to retain

A committed begin_execution transaction is the internal admission ordering point. A cancellation committed before it must deny new admission. A cancellation arriving after it cannot retract an already-sent network action; preserve/reconcile that in-flight result rather than promise impossible retraction.

An internal unique effect key does not provide universal exactly-once effects on arbitrary providers. Prove the documented provider readback/idempotency/reconciliation behavior. Ambiguous send -> UNKNOWN; do not mint another key and resend. Preserve full receipt identity on replay and keep credentials outside evidence.

A cookie HTTP test is not proof of browser/UI automation. Match the claimed support surface to the actual run. No prohibited Google SSO automation or challenge bypass.

## Real finish line and permission

CP0 exact-tip checks/CI classification; CP1 real useful mission; CP2 qualification/inference prerequisites; CP3 actual worker recovery; CP4 real scoped knowledge missions; CP5 unified actions/session; CP5-REALWORLD/R33c; CP6 integrated operational mission with broker/lease/knowledge/action receipt families. Required older qualification/remote/host/campaign gates cannot disappear from the final report.

R33c prefers the existing authenticated local GitHub identity. After current `gh` read-only access is verified, SwarmAI itself must create one uniquely tagged private-repo test issue, observe it, comment once, close it, and replay without duplicate mutation. Every mutation goes through the real gateway with exact approvals/effect keys. Direct connector/manual gh activity outside SwarmAI is not checkpoint evidence. Preserve unknown outcomes and incomplete cleanup.

Deliver an actual running private/local application URL, tested SHA, start/restart/stop commands, environment/config identities, exact checkpoint paths/outcomes and remaining gates. A health endpoint or demo UI is insufficient. 'V1.7 live' and formal artifact acceptance remain distinguishable; do not use one successful external action to claim every predecessor satisfied.

## History retained, not active work

Donor runtime branch `cursor/v2-runtime-lane`: historical foundations 630ab780, 92f59faf, 7dcefe4c, e764834a, 685810cc. Product donor `cursor/v2-product-lane` at 5344763 supplied G13 v3 material. Inspect current source before importing; much may already be integrated. Do not import legacy A/B daemons.

Old V1.8–V3 master plans, schemas, migration sequence, packet DAGs, test matrices and open decisions remain in `docs/coordination/FUTURE_PREP_INDEX_20260921.md` and related files. They explain prior architecture only. Do not elaborate them or advance to SiteEpoch/extensions/V2 scheduling/learning just because V1.7 is externally blocked.

Sources inspected for this handoff: current EXECUTION_CONTROL (blob 668640c...), current native AGENTS, current worker status (blob 2dbb630...), actual implementation ref ab958d7..., and the preceding owner conversation/review records. This is not a new full code audit or product test.
