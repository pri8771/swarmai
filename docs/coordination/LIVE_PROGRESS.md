# SwarmAI live progress

Updated: 2026-09-21T19:54:00Z

## Current operating model

| Role | Identity | Scope |
|---|---|---|
| Implementation | `CURSOR-V17-SINGLE` | Current truth -> V1.7 implementation-complete/reviewable candidate |
| Heartbeat | `CURSOR-V17-SINGLE` | Exactly one 5-minute scheduled producer |
| Operator | owner | Final authority |
| ChatGPT | planning / coordination / independent review | No competing implementation lane |

Implementation branch: `cursor/v17-single-session` @ `a0e1a882a2da6980ac03a513a97bb1f28e787a01` at this lead review.
Legacy A/B assignments remain generation 7, disabled, with empty queues. Repository owner directive continues to supersede older two-lane reset text.

## Heartbeat

- Protocol: `SINGLE_SESSION_HEARTBEAT.md`; epoch `single-v17-20260921-01`; producer registered.
- Post-registration scheduler receipts observed at `19:24:47Z`, `19:29:53Z`, `19:34:59Z`, `19:40:04Z`, and `19:45:09Z`, all at healthy approximately five-minute cadence.
- Latest observed manual progress receipt is `19:51:50Z`; session remains fresh/working.
- Heartbeat is liveness/progress only and does not accept artifacts.

## Latest independent review — ART-V14-REAL-E2E

Decision: **CHANGES REQUIRED** for `v14-real-007` / evidence commit `46461a39b4903b1bdc0735fb526d0cd38c6cd8f5`.

The run is useful operational evidence: real mission `609fc23e9cb04117a032eb3d50a0104b`, actual brokered local `qwen2.5-coder:14b` work at reported `$0`, isolated material diff, target-relevant `tests/workspace` verification, grounded reviewer path, and no automatic primary-checkout apply.

It does **not** verify ART-V14-REAL-E2E. The proposed patch is mostly typing modernization and changes provenance from order-preserving list de-duplication to unordered `set` accumulation. That behavioral change was not shown to repair any real defect and can destabilize observable provenance ordering. The run's own manifest also records that its reviewer explanation about `typing.Set` was incorrect and flags provenance-order risk. No targeted regression demonstrates a pre-patch defect fixed by the patch.

Canonical review: `docs/coordination/reviews/ART-V14-REAL-E2E-V14-REAL-007-LEAD-REVIEW.md` (`08b6520347effe67b4fbceb986957a02680cefcb`). Preserve `v14-real-007` unchanged as failed independent-review evidence. Required next step is a **new preregistered real mission** on another bounded subsystem with an objectively defensible defect and a target regression/check.

`ART-V14-REAL-E2E` remains `drafting`; no artifact lifecycle promotion occurred.

## G13 progress

- R03 selectively transplanted the G13 v3 pool implementation from donor `534476393257794c4e8ebf8d65f44fd090ab28eb` without the retired coordination topology.
- R04 Mac verification reported 240 held-out inputs, 15 semantic archetypes per required cell, digest match, Ruff/mypy clean, and 11 focused tests green. This is useful current-environment evidence, but the canonical registry still requires actual HOST-WIN-DEV executable verification before lead freeze; Mac verification does not impersonate Windows.
- R05 reviewer-calibration implementation is now pushed: evidence tip `6529f408b4aefd23a8129aa84a66a2d5ecb27ec7`, current descendant `da026d1d0ec610e226d56cdda796269fc1573d09`; receipt claims 10/10 calibration cases and negatives green. No held-out qualification started and no qualification acceptance is claimed.
- Real sealed-reference content digest remains unbound. Counted qualification remains prohibited until canonical prerequisites are legitimately satisfied.

## V1.5 / recovery progress

- R13 confirmed the durable lease schema/token-hash foundation is already present on the single-session branch without downgrading later V2A-003b/c or V17 effect work.
- Evidence at `a0e1a882a2da6980ac03a513a97bb1f28e787a01` reports 11 focused lease-foundation tests passed against the local operator DB and Alembic head `a17effect004a0001`.
- This is verification/recovery progress only; `ART-V15-LEASE-FENCING` is not self-accepted and live Mac+Windows multi-host evidence remains incomplete.

## CI / blockers

- GitHub Actions is externally blocked before job execution. CP0 classified the annotation as account billing/spending-limit related: jobs do not start, record zero steps, and therefore are not source-test failures or executable CI evidence.
- Operator action required: restore GitHub Actions billing / spending-limit availability under GitHub **Billing & plans**. Do not spam reruns until that is fixed.
- `ART-V13-TASK-POOL` remains canonical `reviewable`, not verified/frozen; actual HOST-WIN-DEV executable verification and sealed-reference binding remain unresolved.
- G12 remote overlap remains blocked at 0 admitted remote routes.
- `ART-V14-REAL-E2E` remains drafting / changes required after v14-real-007.
- V1.5 live multi-host evidence remains incomplete.

## Top next actions

1. Run a new preregistered V14 real mission on a different bounded operational subsystem and require a demonstrated pre-patch defect/invariant failure plus a correct targeted regression/check.
2. Continue G13 implementation/reviewer machinery without counted held-out qualification; preserve the explicit Windows-verification and sealed-reference blockers until legitimately resolved.
3. Continue dependency-independent V1.5/V1.7 verification/recovery work while GitHub Actions is unavailable; retain truthful local test receipts and do not infer CI success.

## Human action

Restore GitHub Actions billing/spending-limit availability so exact-tip CI jobs can actually start. No main merge, public release/deploy, force push, or additional spend is authorized.
