# SwarmAI future code map — likely extension points V1.8 through V3.0

Date: 2026-09-21
Status: PLANNING ONLY
Reference source snapshot: `cursor/v17-single-session` created from reviewed integration baseline.

Workers must re-inspect current source before editing.

## Reuse policy

Do not introduce a second orchestration framework, second authority database, second scheduler authority path, or second tool permission system.

Current reusable seams:
- PostgreSQL + SQLAlchemy + Alembic: `src/swarm/db/**`
- outbox: `src/swarm/db/outbox.py`
- mission scheduler: `src/swarm/controller/scheduler.py`
- mission/controller: `src/swarm/controller/**`
- worker registry: `src/swarm/workers/registry.py`
- runtime checkpoints/session: `src/swarm/runtime/**`
- knowledge/memory: `src/swarm/memory/**`
- tools/actions: `src/swarm/tools/**`
- contracts: `src/swarm/contracts/**`
- self-development: `src/swarm/selfdev/**`
- deploy/install doctor: `src/swarm/deploy/**`
- observability/reliability: `src/swarm/observability/**`
- product journeys: `src/swarm/product/**`
- tests already grouped under matching domains.

## V1.5–V1.7 actual surfaces and ownership (audited at `f2b8d5f`; Fable planning pass)

Read this before the V1.8+ maps: those maps extend these files. "Wired" = reachable from the mission path today.

| Concern | Production surface | Tests | Wired | Packets that own it next |
|---|---|---|---|---|
| Mission path | `src/swarm/mission/runtime.py` (`MissionRuntime.run`), `mission/worker.py` (`RepoWorker`, effect sites `:66`, `:593`, `:599`), `mission/worktree.py`, `mission/acceptance.py` | `tests/mission/` | yes | R28d, R25a, R02a, R17b |
| Inference broker | `src/swarm/broker/broker.py`, `mission/brokered_inference.py` | `tests/broker/` | yes | — (do not touch) |
| Durable leases / results | `src/swarm/db/lease_fencing.py` (`LeaseLifecycleService`, `_assert_accept_fence`) | `tests/integration/db/test_lease_*` | **no** | R28b (one read function), R17b |
| Worker protocol | `src/swarm/workers/service.py`, `client.py`, `recovery_harness.py`; harness `scripts/r17_cp3_separate_process_recovery.py` | `tests/workers/` | **no** | R17a, R17b, R17c |
| In-memory worker registry | `src/swarm/workers/registry.py`, used by `api/store.py:53`, `load/`, `chaos/` | `tests/workers/test_workers.py` | yes (wrong authority) | R17c |
| Controller / scheduler | `src/swarm/controller/mission.py` (`reconcile_leases` no-op `:142`), `controller/scheduler.py` | `tests/controller/` | yes | R17b; V2.3 extends `scheduler.py`, never replaces it |
| Knowledge | `src/swarm/knowledge/repository.py`, `retrieval.py`, `budget.py`, `memory_adapter.py`; contracts `contracts/knowledge.py` | `tests/knowledge/` | **no** | R25a, R25b |
| Legacy memory | `src/swarm/memory/store.py` (`retrieve_context`, unfiltered) | `tests/memory/` | CLI only | R25a |
| Action contracts | `src/swarm/contracts/actions.py` | `tests/tools/` | **no** | R28b, R29a |
| Effect store | `src/swarm/tools/effects.py`; rows in `db/models.py` (`ApprovalRow :257`, `ActionEffectRow :284`) | `tests/tools/test_v17_gateway_negatives.py` | **no** | R27a–R27e, R31b |
| V1.7 gateway | `src/swarm/tools/v17_gateway.py` | same | **no** | R27a, R27c, R27e, R28a–R28d |
| Legacy gateway | `src/swarm/tools/gateway.py` (`_seen_ops`), used by `runtime/session.py`, `tools/permission_mission.py` | `tests/tools/test_gateway_sandbox.py`, `tests/runtime/` | tests/CLI proof only | R28c |
| Adapters | `src/swarm/tools/adapters/` (`local_sandbox`, `api_mcp` echo, `browser_session` simulator), `tools/session_recovery.py` | same | **no** | R28d, R29a, R30b, R31a, R31b |
| API / CLI (shared wiring) | `src/swarm/api/routes_v1.py`, `api/store.py`, `src/swarm/cli.py` | `tests/api/` | yes | R25a (one CLI handler), R17c (worker routes) |
| Migrations | `migrations/versions/`: `9eb193b10f4e` → `a15lease003a0001` → `a16know003a0001` → `a17effect004a0001` (single head) | — | — | R27a adds `a17effect004b0001` |
| Coordination tooling | `scripts/coordination/heartbeat.py`, `.github/workflows/ci.yml` | — | — | OPS-CI-01 |
| Live fixture (new) | `sandbox/live_fixture/` — test infrastructure, never imported by `src/` | `tests/live_fixture/` | n/a | R30a |

Single-worker rule for shared files: `cli.py`, `api/store.py`, `api/routes_v1.py`, `db/models.py`, `pyproject.toml` and `migrations/` are touched by at most one packet at a time; specs name them explicitly under *Surfaces*.

## V1.8 suggested code map

### Site authority
Prefer:
- new `src/swarm/recovery/` package OR `src/swarm/runtime/authority.py` if small;
- durable model/repository in `src/swarm/db/models.py` + `repositories.py`;
- migration under Alembic.

Touch existing boundaries:
- `controller/scheduler.py`: dispatch requires active epoch;
- worker lease/result path: result includes/validates epoch;
- `tools/gateway.py`: consequential effect reservation/acceptance validates epoch;
- runtime checkpoints: preserve epoch reference where required.

Tests:
- `tests/deployment/`
- `tests/workers/`
- `tests/tools/`
- `tests/integration/`

### Backup/restore
Prefer:
- `src/swarm/recovery/backup.py`
- `src/swarm/recovery/restore.py`
- `src/swarm/deploy/` for operator-facing commands/doctor integration.

Do not serialize secrets into backup manifests.

## V1.9 suggested code map

### Extensions
Prefer new:
- `src/swarm/extensions/contracts.py`
- `src/swarm/extensions/registry.py`
- `src/swarm/extensions/loader.py`

Integrate through:
- `tools/registry.py`
- `tools/gateway.py`
- existing project policy/auth layer.

Do not let extensions call providers/tools outside normal broker/gateway.

### Install/upgrade
Reuse:
- `src/swarm/deploy/doctor.py`
- `src/swarm/deploy/profiles.py`
- Alembic;
- existing release/install verification.

### Selfdev
Extend:
- `src/swarm/selfdev/policy.py`
- `src/swarm/selfdev/runner.py`

Keep branch/worktree isolation and independent review boundary.

## V2.0 suggested code map

Avoid large new feature packages.

Primary work is integration/hardening across:
- `src/swarm/db/**`
- `api/**`
- `cli.py`
- deploy;
- product journey;
- observability/reliability.

Add candidate manifest under product/release layer rather than duplicating source state.

## V2.3 suggested code map

### Multi-mission scheduler
Evolve:
- `src/swarm/controller/scheduler.py`

Likely split into:
- `controller/scheduler.py` public scheduler facade;
- `controller/fairness.py`;
- `controller/reservations.py`;
- `controller/scheduling_receipts.py`.

Persist scheduler state in DB repositories. Do not retain fairness debt only in process memory.

### Capability packs
Either extend V1.9 extensions or add:
- `src/swarm/capabilities/packs.py`
- `src/swarm/capabilities/registry.py`

Avoid a separate permission engine.

### Portability
Prefer:
- `src/swarm/product/portability.py`
- existing `contracts/export_schemas.py`.

### Observability
Extend:
- `src/swarm/observability/**`

Use one normalized operational event/receipt model.

### Fleet
Extend:
- `src/swarm/workers/**`
- scheduler placement logic.

Do not introduce a second worker registry.

## V3.0 suggested code map

### Persistent objectives
Prefer new:
- `src/swarm/objectives/contracts.py`
- `src/swarm/objectives/repository.py`
- `src/swarm/objectives/triggers.py`
- `src/swarm/objectives/admission.py`

MissionProposal must enter the existing normal mission creation/admission path.

### Governed learning
Prefer new:
- `src/swarm/learning/contracts.py`
- `src/swarm/learning/repository.py`
- `src/swarm/learning/evaluation.py`
- `src/swarm/learning/canary.py`
- `src/swarm/learning/rollback.py`

Reuse:
- eval framework;
- review framework;
- selfdev runner;
- observability;
- evidence contracts.

### Resource allocator
Extend V2.3 scheduler rather than create a parallel scheduler:
- `controller/resource_allocator.py` may prepare policy inputs;
- actual admission remains in scheduler/reservation path.

### Capability ecosystem
Extend V2.3 pack/extension registry with trust/provenance/signature/revocation.

### Fleet tenancy/audit
Extend worker/fleet + observability/audit receipt model.

## Dependency policy

Adding an external dependency requires evidence that existing stdlib/current dependencies cannot cleanly satisfy the contract.

Current stack already includes the major needed primitives:
- Pydantic for contracts;
- SQLAlchemy/PostgreSQL for durable state/unique constraints/transactions;
- Alembic for migrations;
- FastAPI for control/API;
- httpx for remote adapters;
- pydantic-ai/DBOS available for bounded workflow durability;
- pytest/mypy/Ruff for verification.

Prefer these over adding commodity infrastructure during the critical implementation path.
