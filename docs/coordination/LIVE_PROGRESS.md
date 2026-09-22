# SwarmAI live progress

Latest observed scheduler heartbeat: 2026-09-22T01:54:40Z

## Current operating model

Repository authority defines exactly one implementation session under `OWNER_V17_LIVE_ONLY`:

| Role | Identity | Scope |
|---|---|---|
| Implementation | `CURSOR-V17-SINGLE` / Fable | Current truth -> V1.7 live/reviewable candidate only |
| Heartbeat | `CURSOR-V17-SINGLE` | One five-minute scheduled producer; liveness only |
| Operator | owner | Final authority |
| ChatGPT | lead / independent reviewer | Canonical review and acceptance; no competing implementation lane |

Implementation branch: `cursor/v17-single-session@889c9c16bb30c9569267741dfc74c10d8ae10d69`.
The worker ended its implementation session at a truthful `BLOCKED_FRONTIER`; the launchd candidate remains a private loopback service at `http://127.0.0.1:18771`. Legacy A/B assignments and heartbeats are historical and do not count.

## Heartbeat

- Active epoch: `fable-v17-20260922-01`; producer registered.
- Status: `review_requested`; latest scheduler publication `01:54:40Z`.
- Last meaningful worker activity recorded at `01:50:07Z`.
- Timer publications after the handoff are liveness publications only and must not be represented as continuing implementation.

## Lead reviews this run

### R27c / ART-V17-APPROVAL-BINDING

**CHANGES REQUIRED remains in force.** Current descendant source still shows both blocking defects from the prior review: the operational gateway reaches committed admission with `fence_reader=None`, and a distinct replacement approval on an already-consumed effect can be validated without consuming/rebinding the new grant.

Repair: `R27c-R1`. `R27e` and `R28a` remain held. Parent artifact remains canonical `drafting`.

### R27d approval integrity

**BOUNDED SLICE ACCEPTED; parent artifact unchanged** at source `1b9afc510b5cac875ae5b6291c123f132938ede1`.

Accepted: insert-only approvals, non-resettable usage, monotonic project-scoped revocation, project-filtered lookup/non-disclosure behavior, and fail-closed legacy null binding rows. Local bound evidence: 6 focused PostgreSQL tests; full `422 passed, 2 skipped`; Ruff clean; mypy clean.

Review: `docs/coordination/reviews/ART-V17-APPROVAL-BINDING-R27D-LEAD-REVIEW.md`.

### R17a / local durable recovery checkpoint

**LOCAL HARNESS CHECKPOINT ACCEPTED; artifact lifecycle unchanged** at `e5bd6350569fb10146517430ca6f7fa097de84a4`.

Useful proof: real separate OS processes + PostgreSQL, victim `SIGKILL`, expiry/reassignment, stale-result rejection, cancellation-generation rejection, and 20/20 concurrent duplicate-result races with exactly one accepted result. It does not satisfy final CP3 because tasks were harness-seeded rather than produced by the operational mission path, the harness directly advanced mission cancellation generation, and physical multi-host proof remains absent.

Review: `docs/coordination/reviews/ART-V15-RECOVERY-EVIDENCE-R17A-LEAD-REVIEW.md`.

### R02a / V14 defect-proof gate

**BOUNDED RUNTIME GUARD ACCEPTED; ART-V14-REAL-E2E unchanged** at `ef8a2cc25c9caf8665804a28453c6f81f82d4a11`.

The new gate requires a patch-carried regression to fail cleanly on pre-patch production source and pass on patched source; collection/config errors do not count. Local bound evidence: 8 focused tests; 50 mission tests; full `433 passed, 2 skipped`; Ruff clean; mypy clean.

`v14-real-008` then failed honestly: the model emitted a verbatim/full-file echo, no material diff and no patch regression; no semantic review or acceptance was reached. Next bounded repair is `R02c`, then a new preregistered mission.

Review: `docs/coordination/reviews/ART-V14-REAL-E2E-R02A-LEAD-REVIEW.md`.

## Candidate / checkpoint truth

- Private local candidate: loopback `127.0.0.1:18771`, launchd `com.swarmai.v17-candidate`; health/readiness and authentication mechanics were demonstrated locally. This is not proof that V1.7 subsystems are wired into the mission path.
- CP0: local suite/lint/type evidence is green; hosted CI remains externally unavailable.
- CP1: not passed; `v14-real-008` is a preserved failed attempt.
- CP2: not run; canonical G13 still requires actual HOST-WIN-DEV executable verification + lead-held sealed-reference binding; G12 remains 0 admitted remote routes.
- CP3: strong local harness checkpoint accepted as evidence, but not operational-mission or physical multi-host completion.
- CP4/CP5/CP6: not passed; knowledge/action boundary are not yet on the same operational mission path.

## CI

Latest inspected hosted run `35676958677` on `963acaefacc2f5c320a6cab57835a32a737cef3a` failed before runner allocation: `offline`, `console`, and `live-gated` each have zero steps and `runner_id=0`. Treat as external Actions non-evidence, not a source failure.

## Top next actions

1. Resume the single authorized Fable implementation session and execute `R27c-R1`; do not proceed to `R27e`/`R28a` until independent re-review accepts the repaired source.
2. In dependency-independent work, execute `R02c` echo/no-material-diff repair and the bounded mission-cancel/control-plane method; preserve tests and current safety semantics.
3. After R27c-R1 review, continue the existing V1.7 queue only. Do not start V1.8+ and do not create a second implementation lane.

## Human action

The Fable implementation session has stopped at `BLOCKED_FRONTIER`; its timer cannot resume the model. Reopen/reuse that one existing `CURSOR-V17-SINGLE` session so it can read the lead reviews and execute `R27c-R1`/independent repairs. Separately, GitHub Actions may be restored only within the existing/no-additional-spend entitlement; do not authorize new charges.

No main merge, public release/deploy, force push, paid fallback or additional spend is authorized.
