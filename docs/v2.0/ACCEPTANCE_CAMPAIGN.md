# V2.0 acceptance campaign (Lane F freeze)

**Date frozen:** 2026-09-25  
**Freeze ID:** `v20-acceptance-campaign-20260925`  
**Machine catalog:** `benchmarks/v20_acceptance/scenarios.freeze.json`  
**Harness:** `src/swarm/acceptance/`  
**Hostname:** `swarm.splitsignal.ai`  

## Discipline

- Freeze scenarios and pass criteria **before** relying on campaign runs.
- Separate gates: **deterministic** · **live** · **host** · **elapsed**.
- Predeclare elapsed observation windows; **do not simulate** elapsed time.
- **Never** mark V1.7–V2.0 accepted from harness output.
- **Never** invent or auto-approve `LiveGrant`; spend stays zero unless operator grant + separate live qualification.
- Implementation ≠ eng verification ≠ live qualification ≠ independent review ≠ operator acceptance.

## Commands

```sh
uv run swarm acceptance freeze
uv run swarm acceptance run
uv run swarm acceptance run --gates deterministic
uv run swarm acceptance matrix
uv run python scripts/v20_acceptance_campaign.py
uv run pytest tests/acceptance -q
```

## Frozen scenarios (mandate §10)

| ID | Scenario | Primary gate | Also |
|---|---|---|---|
| V20-S01 | Finite multi-mission goal | deterministic | live |
| V20-S02 | Failed approach → strategy change | deterministic | live |
| V20-S03 | Ongoing goal across cycles | deterministic | elapsed |
| V20-S04 | Blocked then available prerequisite | deterministic | — |
| V20-S05 | Collaboration + bounded delegation | deterministic | live |
| V20-S06 | Context succession | deterministic | live |
| V20-S07 | Server restart / worker disconnect / stale return | deterministic | host |
| V20-S08 | Duplicate triggers / lost acks | deterministic | — |
| V20-S09 | Pause / redirect / cancel / budget exhaustion | deterministic | live |
| V20-S10 | Memory correction / lesson rollback | deterministic | live |
| V20-S11 | SDK / UI parity | deterministic | live |
| V20-S12 | Authorized model/tool execution with artifacts | live | deterministic |

Pass/fail criteria for each scenario are sealed in the freeze JSON and verified by `swarm acceptance freeze`.

## Version matrices (accepted = false)

| Version | Required scenarios | Accepted |
|---|---|---|
| V1.7 | S05 S06 S07 S08 S12 | **false** |
| V1.8 | S01 S03 S04 S08 S09 | **false** |
| V1.9 | S01 S02 S03 S04 S05 S08 S09 S10 | **false** |
| V2.0 | S01–S12 | **false** |

Readiness strings from the harness (`harness_*`, `blocked_*`) are **not** acceptance.

## Evidence paths

- `docs/evidence/v20/acceptance_campaign_freeze.json`
- `docs/evidence/v20/acceptance_version_matrices.json`
- `docs/evidence/v20/acceptance_campaign_summary.json`
- `docs/evidence/v20/acceptance_campaign_runs/latest.json`

## Deterministic probe map (post scaffold wire)

| ID | Probe | Product surface |
|---|---|---|
| V20-S01–S04, S09 | Goal store lifecycle | `swarm.goals` |
| V20-S05 | `delegation_bounds` | collab board + graph spawn + pursuit admit |
| V20-S06 | `succession_fence` | `CollaborativeMissionBoard` X→Y fence |
| V20-S07 | `restart_stale_return` | Goal restart + worker generation fence (host also-gate still blocked) |
| V20-S08 | `duplicate_trigger_idempotency` | Goal triggers + API idempotency + pursuit dedupe |
| V20-S10 | `lesson_rollback` | learning repository |
| V20-S11 | `sdk_ui_parity` | SDK client ↔ `/v1/goals` UI contract |
| V20-S12 | `live_grant_gate` | live blocked without operator LiveGrant |

## External gates (continue eng)

| Gate | Policy |
|---|---|
| Live | Blocked until operator-approved LiveGrant; harness refuses invent/auto-dispatch |
| Host (R730 / two-host) | Blocked; two local processes ≠ two-host proof |
| Elapsed reliability | Not started; wall-clock only |
| Independent review / operator accept | Separate; required for version acceptance |
