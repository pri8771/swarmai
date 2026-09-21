# Final delivery-readiness review — 2026-09-21

Reviewer: ChatGPT engineering/product lead.
Decision: execution handoff prepared; NO product milestone accepted by this review.

## Source and evidence inspected

- Current application branch `cursor/v17-single-session` still resolved to `f2b8d5f7dfd65530e73c63438c229b9fa428f922` during this review.
- Current session router, recovery queue (blob `48d707a274399dc1e659a1edbc0dc0ab9003df82`), its fine packets/gates, future V3 fine-packet/gate definitions, R27c transaction spec, R-LATER-V17 specs, and existing plan validator were read.
- Latest heartbeat snapshot retrieved: `2026-09-21T23:23:56Z`; last meaningful activity `2026-09-21T20:05:50Z`; packet R27; same application SHA. The record simultaneously says working and paused on external blockers.
- These observations establish a publishing daemon with stale reported activity, NOT ongoing implementation. The worker host/process was not remotely inspected in this review.

## Current product position

Still below working V1.7. Existing V1.5/V1.6/V1.7 components and historical tests are useful, but the current audit/queue records operational wiring, durability and real-checkpoint gaps.
V14 real-007 remains changes-required in the current queue. CP3 has missing cancellation/concurrent-accept cases. CP4 requires actual mission-path evidence. V1.7 requires completed durable effects, adapters, real external action and integrated CP6. Later-version plans do not establish implemented or accepted V2/V3.

## Newly found handoff gaps

1. The prior `validate_plan.py` treats evidence_only/review_pending as generally satisfied dependencies and ignores gate state for planned work. That structural ready set must not be used as live-execution authorization.
2. Its cycle check examines direct dependency edges but not the split expansion used during satisfaction evaluation. The new guard tests split-expansion cycles explicitly.
3. R34b did not explicitly depend on R33c real-world proof or R17c complete worker/API wiring.
4. R27d approval immutability/revocation could be skipped along the R27c -> R27e -> R28a path.
5. R27c's prose overstates cancellation across a database/network boundary. The delivery contract defines committed begin_execution as admission ordering and requires reconciliation of already-admitted remote work, rather than promising to retract in-flight external effects.
6. A live HTTP cookie fixture must not be mislabeled as actual browser/UI automation.

## Changes made

- `FABLE_DELIVERY_CONTRACT.md`: one explicit execution assignment through V3; real V1.7 first; safe takeover; bounded retry behavior; on-path wiring; exact evidence identities; external account and cleanup rules; accurate distributed semantics; continued independent work under blockers.
- `EXECUTION_CONTROL.json`: additive prerequisites over existing queues. It does not replace queues or mutate acceptance.
- `tools/execution_guard.py`: read-only guard for phase-specific readiness, expanded dependencies, external/review/freeze holds, preflight-only account access, and heartbeat versus activity.
- `tools/test_execution_guard.py`: focused unit regressions.
- `SESSION_START.md`: routes to execution mode rather than the completed planning assignment.
- `FABLE_DELIVERY_START.md`: short saved launch prompt.

No application source, active heartbeat ledger, worker process, account, billing setting, main branch, deployment or artifact acceptance was changed by this review.

## Tests actually executed by the lead

Environment: isolated review container, Python 3.13.5 (within repository >=3.12,<3.14 requirement).
Command: `python3 -m unittest -v test_execution_guard` against the exact local contents subsequently published to GitHub.
Result: 31 tests passed. Python syntax compilation also passed. A missing-dependency KeyError found by the first run was repaired before the final passing run.
Cases include missing references, ordinary/split cycles, repair-parent handling, evidence-only and review-pending live denial, external gate handling, runtime probe separation, explicit review holds, added R33c handoff dependency, future freeze requirements, phase selection, no input mutation, and the actual retrieved stale-activity heartbeat shape.

Tested file identities (Git blob SHA):
- execution_guard.py: `6ebf2c8ac0e4b37545e42dfcbfa782602a4a2b47`
- test_execution_guard.py: `130327dec4e89c8224df0d5d483586c473eb9369`

Scope limits: these are synthetic UNIT tests of lead handoff tooling, not live SwarmAI evidence. The full application, PostgreSQL integration, browser, provider calls, CI, and real-world checkpoint were NOT run here. Ruff was unavailable; its installation attempt failed because the review container could not resolve the package host. No Ruff/mypy pass is claimed. The worker must rerun both validators on its complete fresh checkout and run the configured repository checks before product claims.

## Expected next round

Deliver material implementation and source-bound evidence, not another broad plan or repeated verification labeled new code. First: CI/heartbeat hygiene and R27 durability chain; while real review holds wait, execute independent fixture, worker recovery and defect-proof packets. Then complete actual runtime integration and the real external checkpoint, and advance through the existing V1.8–V3 graphs when their hard handoffs are satisfied.

V3 is the requested destination, not a promised single-session acceptance result. Credentials, independent review, physical hosts, unresolved lead freeze decisions and the required 24-hour/other real elapsed campaigns still constrain what can be truthfully completed. A useful run exhausts genuinely executable work and returns exact remaining dependencies instead of idling or fabricating completion.

No new account was created: the preferred real-world checkpoint uses an existing authenticated GitHub identity through SwarmAI itself. The owner's conditional unsubscriber Google Cloud alias permission is retained only for a genuinely necessary later identity test.
