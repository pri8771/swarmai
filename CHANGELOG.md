# Changelog

All notable changes to SwarmAI are documented here.

## [Unreleased] — V2.3 implementation-complete candidate (2026-09-26)

### Added
- V2.3 scheduler: shared contracts + migration `a23opsplatform0001`, WDRR fairness, durable `SchedulingStore` (PostgreSQL), DispatchIntent reservations, scheduler epoch lease + singleton ticker, `SchedulerService` with the 11 pathological cases.
- Capability-pack lifecycle with keyed HMAC signatures (F-02); portability bundle v2 with value-based secret scan and tombstones (F-03); fleet trust classes, drain state machine and deterministic placement; durable ops events + trace graph.
- `routes_v23.py` API surface, `swarm v23` offline CLI, console Ops tab + worker drain/revoke, router client + bounded native loop (fake router), pursuit PostgreSQL write-through, durable holds/lessons, sandbox kill-bound, compose smoke script.
- `scripts/v23_acceptance_campaign.py` and deterministic probes V23-A01…A10.

### Fixed
- F-01: `GET /v1/ops/events` scoped to the principal's projects.
- F-13: unknown-usage holds never free budget; release requires reconciliation evidence.
- F-14: single `CURRENT_SCHEMA_REVISION` pinned to the Alembic head.
- F-16: `POST /v1/release/candidate-freeze` is admin-only.
- V20-E10: compose `worker` no longer inherits the API HTTP healthcheck (connector process check) (SW-FIX-COMPOSE).
- Tests: acceptance probe V20-S11 no longer clears `SWARM_*` for the rest of the process, which had sent Alembic schema tests to the default database in whole-repo runs (SW-FIX-ALEMBIC); V20-E08 kill-bound tests made deterministic (SW-FIX-FLAKE).
- F-06: upstream `Retry-After` bounded; a value above `max_retry_after_seconds` (or non-finite) is now a terminal give-up (`retry_after_exceeds_cap`), never a retry at the cap (SW-FIX-RETRY).

### Evidence
- `docs/evidence/v23/acceptance_campaign.json`: deterministic 10/10 pass; live router `blocked:router_not_configured`; compose smoke `pass` (re-run on `1b3f48ad` after SW-FIX-*; dev VM); multi-process `pending_owner_approval`.
- `docs/v2.3/EXIT_CHECKLIST.md`.

### Notes
- Not accepted. Multi-process gate pending owner approval. Zero spend (no provider calls; cost unknown ≠ $0).
- SplitSignal adapter (SW-X1-S1) merged after inference_server SP1/SP2 (IS `9ca12671`); live use pending SP4 and a LiveGrant.

## Unreleased (V2.3 tracking reset)

- docs: corrected V2.3/V3.0 status claims (scaffold, not implementation-complete).
- config: froze scheduler policy `v23-wdrr-1` and V2.3 deterministic acceptance manifest.

## [2026-09-23] — V1.4→V2.0 track + accept/launch track; V2.3/V3.0: scaffolds only — see docs/v2.3/STATUS.md

### Added
- V1.5–V3.0 implementation packages: leases/workers, knowledge, V17 gateway, SiteEpoch recovery,
  extensions/install, CandidateManifest, V2.3 scheduler/reservations/packs/portability/ops/fleet,
  V3.0 objectives + learning governance
- Lead-accept packages and launch-track evidence under `docs/evidence/v20/`, `v30/`, `launch/`
- P4 portable acceptance: `tests/portability/`, `PublicEndpointConfig` / support matrix contracts,
  in-process protocol harness, and generic two-container `deploy/compose/portable-protocol.yml`
- P2 portable roles: `server`/`worker`/`combined` process roles, enrollment via P4
  `WorkerIdentitySpec` / `SupportMatrix`, capability authority (labels ≠ access), placement
  contracts, bounded workspace grants, generic `deploy/compose/worker.yml` (+ optional macOS adapter)

### Fixed
- CLI mypy type conflicts that failed GitHub Actions offline CI

### Evidence (zero-spend)
- Ollama loopback live canary `cost_usd: 0.0`
- Local recovery drill; release harden/verify/demo-suite/first-run/freeze
- Offline pytest suites green; CI offline green on tip after mypy fix

### Notes
- **Not lead-accepted.** ART lead sign remains USER_ACTION.
- **Not a completed public launch claim.** Operator authorized the accept/launch track;
  merge/tag/publish still require remaining human clicks if tooling blocks the agent.
- `SWARM_ALLOW_PAID=false` remains in force.

## [1.0.0-rc.1] — 2026-09-20

### Added
- V1 public contract freeze (`swarm release freeze`)
- First-run guided setup (`swarm release first-run`)
- V1 validation matrix (`swarm release validate`)
- V0.9 install-check / harden / demo-suite
- V0.8 product experience (projects, history, console tabs, journey proof)
- V0.2–V0.7 routing, scale, memory, tools, self-dev, reliability

### Security
- Git-tracked secret scan; local `.env` allowed when gitignored
- Zero-spend default (`SWARM_ALLOW_PAID=false`)

### Notes
- **Not a public launch.** V1 RC awaits explicit launch approval.
- Draft PR only at V1.0 stop gate — no merge/tag/publish without authorization.

## Earlier

See `docs/v0.*/STATUS.md` for version dogfood evidence.
