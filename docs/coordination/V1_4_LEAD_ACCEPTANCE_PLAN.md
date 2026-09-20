# SwarmAI V1.4 lead acceptance plan

Preregistered by ChatGPT engineering lead on 2026-09-20 after owner authorization through V1.4. This document narrows execution ambiguity; it does not weaken or replace `V1_4_EXECUTION_CONTRACT.md`. If there is a conflict, the execution contract controls.

## Purpose

Cursor owns implementation, local operation and evidence production. The lead owns acceptance criteria, independent source/CI review, evidence validity and gate promotion. The operator retains final main-merge/release authority and any human login/MFA/consent steps.

The fastest valid route to V1.4 is to stop treating every possible improvement as a release blocker. Close the exact gates below, preserve failed/blocked evidence, and do not spend cycles on later-version capabilities.

## Current gate order

### G10 / V1.0 repair

Acceptance requires all of the following on one reviewable candidate application tree:

- current-tip Ruff, mypy, package/install, Alembic, applicable offline Python tests and console npm install/lint/test/build pass;
- CI DB integration may remain honestly blocked if no authorized CI DSN exists, provided local authorized DB integration evidence is current and separately labeled;
- authentication/project/idempotency security regressions pass;
- normal operational startup has no seeded fixture activity or known demo identities;
- behavioral evidence is bound to exact candidate/config/command/result/mode/freshness and required identity versions;
- provider readiness fails closed on unknown auth/price/quota/health/qualification;
- normal operational mission/runtime paths do not substitute known answers, mock-success state or quota bypasses;
- FIX-004 proves the actual unattended worker mechanism: authenticated Cursor CLI, one bounded authenticated manual invocation, then two genuine hourly scheduler-triggered worker invocations with lease/no-overlap and sanitized receipts.

Passing CI alone does not close FIX-004.

### G11 / V1.1 — one generic durable mission path

Use the same current candidate and operational mode. Required evidence:

1. At least three unfamiliar missions across at least two supported task families.
2. Actual console UI creates or opens at least one of those mission IDs. A script that merely returns a console-shaped object is insufficient.
3. API and CLI can observe the same durable mission IDs and artifacts.
4. Execute real work, not only create metadata.
5. Actual service restart, then reopen the same durable mission.
6. Cancellation is observed through another interface.
7. Intentionally wrong output is rejected and produces no acceptance receipt.
8. Unsupported family/task returns an honest unsupported/failed outcome.
9. Review/acceptance controls the outcome.
10. Accepted work remains isolated until an explicit reviewed apply action; no automatic primary-checkout promotion.

Evidence from before G10 operational-mode/auth/evidence changes must be rerun where those changes could affect behavior.

### G12 / V1.2 — governed concurrent inference

Acceptance requires one real mission with:

- two independently authorized remote provider routes issuing overlapping inference calls;
- one actually available local route;
- every model attempt routed through the governed broker, including retries/review/evaluation calls used by that mission;
- exact provider/account alias/model/config identity;
- verified current zero-additional-spend eligibility before admission;
- timestamps/request identifiers sufficient to prove overlap;
- atomic reservation/reconciliation with no double allocation;
- controlled route kill/disable followed by an actually executed permitted alternative, or an honest wait if no alternative is permitted;
- no paid fallback, top-up or quota bypass.

Local-local concurrency is preparation, not the G12 live gate.

### G13 / V1.3 — empirical qualification

Use `EVAL_131_QUALIFICATION_PROTOCOL.md`. The product support matrix required for V1.3 is:

- required task families: `coding`, `planning`, `reasoning`, `extraction`;
- sizes: S, M, L, XL;
- at least three actual exact model configurations;
- at least one qualified route for every required family × size combination;
- every model/family/size cell must have measured screening evidence or a specific evidenced incompatibility;
- any model configuration used as a G14 planner/reviewer must also pass the separate role-qualification requirement for the maximum complexity it will handle.

`review` and `summarization` may remain additional/experimental product families; reviewer-role qualification is mandatory for any route used as a reviewer.

### G14 / V1.4 — elastic swarm organization

Acceptance requires a live mission, not a scripted graph animation, where:

- at least two capable planning/review model configurations contribute;
- agents propose graph changes and software validates/adopts/rejects them;
- new evidence causes additional specialists/tasks to be created;
- later convergence causes tasks/agents to merge, retire, reassign or cancel;
- useful independent work overlaps;
- permissions, dependencies and broker admission apply to expansion;
- accepted effects are not rerun;
- logical agents, active sessions, in-flight model requests and worker processes are reported separately.

Separately preserve 10/50/100 logical-assignment scheduler/load evidence. Those are not proof of 100 simultaneous reasoning model calls.

Compare the same task set under:
1. single-agent execution,
2. fixed-team execution,
3. elastic execution.

Report quality, latency, total model calls/tokens, planning/delegation/retry/recombination/review overhead and cases where elastic execution does not help.

## Final LIVE-142 acceptance

After G10-G14 are implemented on one candidate, execute `LIVE_142_CAMPAIGN_PROTOCOL.md`.

Mandatory:
- 12 preregistered positive missions;
- six preregistered negative scenarios;
- real provider overlap/local fallback;
- real adaptive graph behavior;
- service restart/reopen;
- 24-hour protected observation window;
- all attempts retained;
- zero known unresolved defects in the declared supported V1.4 workflows at acceptance;
- zero unexpected application errors in the accepted campaign;
- no unapproved spend, public deployment, secret leakage or duplicate consequential effects.

Expected denials, unsupported outcomes, provider exhaustion and intentional failures are not unexpected application errors when handled according to contract.

## Lead work versus Cursor work

Lead-owned:
- acceptance definitions and preregistration;
- source/CI/evidence review;
- evaluation statistical rule;
- final campaign slots and negative scenarios;
- provider-evidence requirements;
- gate promotion and punch lists.

Cursor-owned:
- application implementation;
- regression tests;
- local browser/CLI/runtime execution;
- provider/session verification;
- model calls and evidence capture;
- candidate branch/PR maintenance.

Operator-only when necessary:
- password/passkey/MFA/CAPTCHA/consent;
- approval of spend if ever desired (currently not authorized);
- final main merge/release/public deployment approval.

## Stop conditions

Immediately stop the affected campaign/gate and return to repair if any of these occur:

- secret/private identity leakage into Git/evidence;
- unapproved charge or billing activation;
- authorization/project boundary violation;
- broker/admission bypass;
- known-answer/mock-success fallback on an operational path;
- duplicate consequential side effect;
- evidence record cannot be tied to the exact candidate/config/run;
- runtime/config change invalidates already-collected behavioral evidence.

Do not redefine a failed gate after observing failure. Version a new protocol/eval/campaign and rerun affected evidence instead.
