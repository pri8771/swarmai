# Cemented execution architecture — V1.7 through V2.3

Closure-sweep proposal. Exact packet contracts and dependencies are in `V17_TO_V23_PACKET_QUEUE.json` and the generated `FUTURE_PACKET_CATALOG_V18_TO_V30_20260921.md`. Baseline approval does not independently approve these amendments. Implementation begins from reviewed handoffs, with lower artifact acceptance reported separately.

## Authority and interfaces

- PostgreSQL/SQLAlchemy/Alembic remain runtime authority. Existing controller scheduler owns dispatch, lease service owns current worker/attempt authority, broker owns provider eligibility/reservations, KnowledgeService owns permission-first knowledge and ActionGateway owns mutations.
- API/CLI/console compose those services; no file cache, extension, objective or worker can update acceptance/permission authority directly.
- Action admission authenticates principal, normalizes/recomputes semantic binding, intersects current policy/manifest grants, checks current lease/status/expiry/revisions, and consumes exact approval atomically before external IO. Local mutation is included even when idempotent. Receipts and execution attempts have separate identities.
- `begin_execution` and finalize/reconcile use explicit execution tokens; late writers cannot mutate a newer attempt. Timeout is unknown, not remote cancellation. Approved safe retry requires actual non-application/quiescence or destination-enforced idempotency.
- AdapterRegistry is the only execution registration path. AdapterManifest is a subset of ExtensionManifest; typed credential-bearing integrations stay in the trusted control plane, separated from the unprivileged test sandbox.

## V1.8 recovery

`18-00` binds reviewed CP6. `18-00a` freezes the supported authority profile. `18-01/02` create authority contracts/persistence and all shared binding columns, so `18-03/04` only wire dispatch/renew/result/effect fences. `18-05/06` define/create consistent backup. `18-07` restores read-only, reconciles state and activates only after old-site fencing proof. `18-08/09` provide adversarial tests and actual outage evidence.

Domain/epoch checks extend the same lease/effect services, including cancellation. A restored copy cannot prove itself newer than a still-running site. Initial private profile uses explicit external isolation before restore activation; automatic multi-site failover is unsupported until an independent authority/fencing mechanism is reviewed. Unknown effects remain unknown. RPO/RTO targets require operator-defined deployment/resource constraints before counted evidence.

## V1.9 installation, extensions and self-development

Installation and per-project enablement are distinct. Effective authority intersects immutable package declaration, current project grant, authenticated actor and global policy. Revocation bumps generation and blocks cached adapters. Built-in/private digest-pinned extensions reuse AdapterRegistry; arbitrary downloaded code cannot import into the credentialed control plane.

Install/doctor/upgrade/rollback has one durable phase record per operation, verified backup and truthful OS support. Rollback uses supported compatibility or restores exact prior binary+snapshot; no pretend downgrade. The selfdev path is SwarmAI inspect->bounded isolated diff->protected tests->review candidate, not an external IDE performing the task. PR publication and merge/release retain their authority boundary.

## V2.0 integration and observation

`20-01` audits reviewed integration and splits actual hardening findings; it is not a general rewrite packet. CandidateManifest is immutable content in the existing artifact store. `20-02/03` freeze and validate source/schema/lock/config/policy/protocol identity. `20-04..07` bind install, rollback, security and performance to that identity.

Prepare `20-08a` early. `20-08b` starts the real 168h window only after independent protocol/candidate preflight; it is not automatically ready merely because unit tests passed. Compatible drills can overlap when preregistered. Keep the frozen deployment unchanged while the single worker advances later code on a descendant checkout. Material identity change invalidates affected evidence; old failures remain. `20-09` reviews all required lower-version artifacts and elapsed/live evidence without merging or publishing.

## V2.3 operations

Extend the current scheduler with persisted weighted-deficit rounds/cursor; accrue credits once per round, debit once at ready dispatch and settle once from usage. Queue polling cannot manufacture credit. All children/retries stay charged to their project. Resource units are a frozen fairness abstraction, not billing or permission.

DispatchIntent composes existing broker/worker/tool reservations in deterministic order, compensates idempotently and conservatively holds unknown capacity. No new authoritative budget ledger. Scheduler restart acquires one generation, reconciles intents and preserves capped credits. Drain/cancel uses existing generations and denies future admission; no rollback promise for already-issued remote requests.

Capability packs are an extension kind, not a second ecosystem DB. Portability strips live grants/secrets/leases/approvals and re-admits imported content. Observability is scoped/read-only; mutations re-enter authorized services. Fleet placement intersects capability, trust and locality before assigning work.

`23-12` freezes fairness before counting. `23-13` requires actual distinct nodes, constrained capacity and non-fixture external resource. `23-14` independently reviews the result and hands off the V3 base. Missing hosts/routes block evidence, not unrelated implementation.

## Compatibility into V3

Objectives create idempotent MissionProposal objects, not dispatch. Learning proposes immutable versions and cannot relax protected authority. Allocator only supplies existing scheduler inputs; audit links existing receipts. See the V3 contracts in the generated catalog and algorithms A30; all six registry artifacts remain required.
