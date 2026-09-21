# SwarmAI future risk register — V1.8 through V3.0

Date: 2026-09-21
Status: PLANNING ONLY

## R1 — second authority path

Risk:
A recovery system, extension, objective scheduler, or learning runtime creates its own bypass around normal mission/broker/tool authority.

Prevention:
All future work must enter existing mission admission, broker, worker, ToolGateway/effect, and project authorization boundaries.

Fail closed:
Reject unbound path.

## R2 — split brain after recovery

Risk:
Old and restored control planes both dispatch or accept effects.

Prevention:
Monotonic SiteEpoch bound at dispatch/result/effect.

Fail closed:
Stale epoch denied; no "best effort" acceptance.

## R3 — backup leaks secrets

Risk:
Backup/export/support bundle captures tokens, cookies, secret env values.

Prevention:
Reference secret names/IDs only; redaction tests.

Fail closed:
Bundle generation fails on detected secret material.

## R4 — extension becomes permission escalation

Risk:
Installed plugin/pack requests broader capabilities than project/user/global policy.

Prevention:
effective scopes are intersection of declaration + project grant + actor + global policy.

Fail closed:
deny and record reason.

## R5 — V2 evidence drifts from candidate

Risk:
Evidence collected before/after source/config changes is mixed into one readiness claim.

Prevention:
CandidateManifest + invalidation rules + evidence binding.

Fail closed:
new candidate identity required.

## R6 — scheduler fairness only in memory

Risk:
restart resets fairness/aging and permits starvation/gaming.

Prevention:
durable scheduling state + policy version.

Fail closed:
no dispatch if required scheduler state cannot be reconciled.

## R7 — partial multi-resource reservation

Risk:
worker reserved but provider/tool capacity not reserved, causing duplicates/deadlocks/cost leak.

Prevention:
reservation-intent state machine with prepare/ready/release/expiry/reconciliation.

Fail closed:
no execution until ready.

## R8 — queue head blocking

Risk:
incompatible first task prevents eligible later tasks from running.

Prevention:
eligibility-aware deterministic selection and negative tests.

## R9 — portability leaks deleted/unauthorized data

Risk:
export uses stale index/cache/summary or includes another project's content.

Prevention:
export resolves current authorization/supersession/tombstones at materialization time.

## R10 — observability becomes control bypass

Risk:
admin dashboard writes directly to DB/controller.

Prevention:
all mutations use same V1.7 ActionEnvelope/approval path.

## R11 — objective = permanent permission

Risk:
long-lived objective is treated as evergreen authority despite revocation, policy change, expiry, or version change.

Prevention:
authority intersection at every trigger/proposal/admission; immutable objective versions.

## R12 — trigger storm amplifies project fair share

Risk:
many objectives/events create more scheduling entitlement.

Prevention:
fairness at project level; triggers/missions do not multiply project credit.

## R13 — learned policy sees its held-out answers

Risk:
self-evaluation contamination.

Prevention:
sealed held-out corpus/access policy; contamination terminal state.

## R14 — threshold tuning after results

Risk:
learning proposal changes scorer/sample/threshold after seeing held-out data.

Prevention:
freeze proposal/eval protocol before held-out; digest binding.

Fail closed:
results invalidated/contaminated.

## R15 — learning widens authority indirectly

Risk:
"optimization" changes route/tool/data/spend behavior outside existing authorization.

Prevention:
protected-authority diff before evaluation and canary.

Fail closed:
blocked as authority change.

## R16 — self-development changes its own reviewer/governance

Risk:
code proposal weakens the mechanism that will approve it.

Prevention:
protected paths/policies for proposal; separate owner/governance change process.

## R17 — canary cannot rollback cleanly

Risk:
accepted/active work continues on failed candidate after rollback.

Prevention:
version-bound execution + stale candidate fencing + deterministic rollback receipt.

## R18 — hidden cost/fairness regression

Risk:
throughput improvement comes from starving another project or moving work to unreported costly route.

Prevention:
primary metric always paired with fairness/resource/cost guardrails and total orchestration overhead.

## R19 — over-engineering with new infrastructure

Risk:
future work adds queues/databases/orchestrators that duplicate PostgreSQL/current scheduler/DBOS/tool gateway.

Prevention:
reuse current stack by default; external dependency requires explicit gap justification.

## R20 — prep artifact mistaken for accepted truth

Risk:
plans/schemas created now are later treated as current implementation/evidence.

Prevention:
all prep docs marked PLANNING ONLY; worker rereads current registry/source before execution.
