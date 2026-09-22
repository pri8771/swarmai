# SwarmAI cross-agent operating contract

## Authority
- Operator: final authority for scope, spend, main merge, public release/deploy, destructive production actions.
- ChatGPT: engineering/product lead, artifact planner, audit/acceptance reviewer.
- Active implementation worker: the ONE session named by `docs/coordination/SESSION_START.md` and current heartbeat.
- GitHub evidence is current truth; memory/past chats are intent/context only.

## Startup
Read, in order:
1. `docs/coordination/SESSION_START.md`
2. current worker status + heartbeat
3. current machine-readable packet queue
4. only the active artifact contract(s)
5. live source/diff/tests

Do not use legacy lane/topology docs unless the active packet explicitly references them as donor/history.

## Work model
Artifact -> small packet -> focused code/test -> commit -> push -> heartbeat -> evidence -> next dependency-ready packet.

Prefer SP1/SP2-like packets and split broad work before implementation. Avoid unrelated refactors.

## Current topology
Exactly one active implementation worker/session and one heartbeat producer unless the operator explicitly changes topology.
Old A/B Cursor lanes and worker-pc assignments are donor/history only unless reactivated explicitly.

## Evidence truth
Never self-accept.
Never convert a failed run into a pass after repair; create a new preregistered run.
Mocks/synthetic tests are useful but do not count as required live evidence.
Required elapsed time cannot be compressed or backfilled.

## Reuse
Prefer existing SwarmAI modules, PostgreSQL/SQLAlchemy/Alembic, FastAPI/httpx/Pydantic, current broker, ToolGateway, scheduler, worker system, outbox, eval/review and selfdev infrastructure.
Do not add a second scheduler, authority DB, permission system, or orchestration framework without an explicit gap decision.

## Protected boundaries
No secrets in Git.
No paid fallback by default.
No main merge/public release/destructive production action without explicit operator authorization.
No permission/spend/release/self-review escalation by persistent objectives, learning, extensions, or self-development.

## Review authority
No worker may impersonate the ChatGPT lead, fabricate a lead review, or promote its own branch as approved. Worker-produced review suggestions are advisory only. Canonical promotion requires an actual operator/ChatGPT lead decision after independent inspection.

## Current scope and Codex portfolio routing
SwarmAI's latest owner cap is **V1.7 live, then stop** under `docs/coordination/EXECUTION_CONTROL.json`; V1.8-V3 implementation and further planning are parked.
When explicitly asked to manage Bots, Jobs and Swarm together, read `CODEX_START.md` and `docs/coordination/portfolio/README.md` from `coordination/swarm-control`. That package is a routing/context hub, NOT a replacement for each project's authority, queue or evidence. Do not import SwarmAI's heartbeat policy into Social Bots, merge the repositories, start overlapping workers, or treat portfolio coordination as a new product feature.
