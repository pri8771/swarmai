# R03 — G13 selective transplant

Donor: `cursor/v2-product-lane@534476393257794c4e8ebf8d65f44fd090ab28eb`

Brought onto `cursor/v17-single-session`:

- `benchmarks/g13/pool_freeze_v3/**` (corpus + identities + digests)
- `src/swarm/evals/g13_*` + `task_pool_freeze_v3.py`
- `scripts/g13_freeze_task_pool_v3.py`
- `tests/evals/test_task_pool_freeze_v3.py`
- `docs/evidence/g13/TASK_POOL_FREEZE_V3.md`

Excluded: coordination heartbeat/autonomous topology.

Smoke: imports OK; 8 focused tests passed; ruff/mypy clean on transplanted modules.
`hidden_reference` fields are opaque IDs only (no answer content).

No invent-accept. R04 runs current-topology verifier + digest bind next.
