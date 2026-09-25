# P4 portability acceptance evidence

**Lane:** P4  
**Date:** 2026-09-25  
**Branch:** `cursor/v2-portable-tests-ac53`  
**Scope:** multi-hostname/path/platform probes + two-container protocol proof  
**Named lab host required:** no

## What was proven (deterministic / offline)

| Probe | Result | Location |
|---|---|---|
| Alternate hostnames / API URLs | pass | `tests/portability/test_portable_config.py` |
| Worker identities / roles | pass | same |
| Install / workspace paths (no personal checkout paths) | pass | same |
| Support matrix accept / reject unsupported platform-arch | pass | same |
| Fresh startup outside original checkout | pass | `tests/portability/test_portable_protocol.py` |
| Correct claim → execute → accept | pass | same |
| Capability grant cannot widen; unverified caps do not enroll | pass | same |
| Revocation blocks claims | pass | same |
| Tenant / placement isolation | pass | same |
| Persistent recovery (portability export/import) | pass | same |
| Two-container compose structure (generic coordinator/worker) | pass | `tests/portability/test_two_container_compose.py` |
| In-process proof script | pass | `scripts/portable_protocol_proof.py --mode inprocess` |

## Two-container Docker twin

- Compose: `deploy/compose/portable-protocol.yml` (`coordinator` + `worker` + private `db`)
- Opt-in live Docker: `SWARM_PORTABLE_DOCKER=1 pytest tests/portability/test_two_container_compose.py::test_two_container_docker_proof`
- Default CI runs compose **validation** + in-process protocol only (no Docker build in offline job)

## Coordination with P1 / P2

- Shared contracts: `src/swarm/product/portable_config.py`
  - `PublicEndpointConfig` — P1 freeze should validate against this (not a single hardcoded hostname)
  - `WorkerIdentitySpec` / `SupportMatrix` — P2 roles + matrix expansion
- Protocol harness: `src/swarm/product/portable_protocol.py` uses existing registry / fleet / capability packs

## Gaps (honest)

- Live Docker two-container run not executed in default CI (opt-in)
- Real cross-host physical proof remains separate evidence
- P1 hostname freeze defect and P2 enrollment/support-matrix product wiring land on their lanes
