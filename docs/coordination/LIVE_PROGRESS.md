# SwarmAI live progress

Latest observed scheduler heartbeat: 2026-09-22T00:53:40Z

## Current operating model

Repository authority currently defines exactly one implementation session:

| Role | Identity | Scope |
|---|---|---|
| Implementation | `CURSOR-V17-SINGLE` | Current truth -> V1.7 implementation-complete/reviewable candidate |
| Heartbeat | `CURSOR-V17-SINGLE` | Exactly one 5-minute scheduled producer |
| Operator | owner | Final authority |
| ChatGPT | planning / coordination / independent review | No competing implementation lane |

Implementation branch: `cursor/v17-single-session@9ff6859d3920106af9a55937c78937b785506ede`.
Legacy A/B assignment JSONs remain disabled historical state; older two-lane heartbeat text does not override the current repo directive.

## Heartbeat

- Active epoch: `fable-v17-20260922-01`; producer registered.
- Current-epoch scheduler receipts observed at `00:38:24Z`, `00:43:29Z`, `00:48:35Z`, and `00:53:40Z`; cadence is healthy around five minutes.
- Status: `working`; packet `R27d`; artifact `ART-V17-APPROVAL-BINDING`.
- Heartbeat liveness is not implementation acceptance.

## Latest review decision — R27c / ART-V17-APPROVAL-BINDING

**CHANGES REQUIRED** for source `8dbe5d810d732f17806ac9611bec78383201ac82` / evidence bundle `9ff6859d3920106af9a55937c78937b785506ede`.

Useful evidence retained: repository-owned durable transactions, committed effect admission, atomic receipt finalization, cross-process visibility test, one-shot approval race test, and locally bound verification reporting 16 focused tests x5, full suite 416 passed / 2 skipped, Ruff clean, mypy clean.

Two blockers prevent lead acceptance:

1. `ConsequentialToolGateway.execute_envelope()` calls durable `begin_execution(..., fence_reader=None)`. The repository can perform an authoritative fence read inside the admission transaction, but the operational gateway does not wire it; its generation check is only a pre-admission comparison against gateway-local integers. A durable lease/cancellation change can therefore race that pre-check unless the authoritative reader is wired into the committed admission path.
2. On a retry of an existing effect under a distinct fresh approval, the effect row's prior `approval_consumed_at` causes `_consume_approval()` to validate the new approval without incrementing its use count or rebinding the approval. A new broad `max_effect_count=1` grant can therefore authorize the retry without being consumed.

Repair packet: `R27c-R1`. Required regressions: durable-fence TOCTOU blocks adapter execution and consumes no approval; replacement approval B on a provable `not_applied` retry is consumed exactly once and cannot authorize another effect. Preserve same-grant no-double-consume, revocation/expiry denial, immutable replay, unknown reconciliation, and one-shot race behavior.

Review record: `docs/coordination/reviews/ART-V17-APPROVAL-BINDING-R27C-LEAD-REVIEW.md`.

`ART-V17-APPROVAL-BINDING` remains canonical `drafting`; no lifecycle promotion occurred. `R27d` may continue. `R27e` and `R28a` remain held pending repaired R27c review.

## CI

Exact-tip Actions run `35673524977` for `9ff6859d3920106af9a55937c78937b785506ede` concluded failure, but `offline`, `console`, and `live-gated` each contain zero steps and `runner_id=0`. Treat this as external Actions availability/billing non-evidence, not source/test evidence.

## Other acceptance truth

- G13: canonical task pool remains `reviewable`, not verified/frozen; actual HOST-WIN-DEV executable verification plus real sealed-reference binding remain required before counted qualification.
- V1.4: `ART-V14-REAL-E2E` remains drafting / changes-required; a new preregistered mission must demonstrate an objectively real pre-patch defect and correct targeted regression.
- V1.5: local durable result/worker/recovery evidence is useful, but actual second-physical-host evidence remains unsatisfied.
- G12 remote: 0 admitted remote routes; no paid fallback.
- worker-pc: last G13 static audit completed without branch/commit and cannot substitute for executable acceptance; no new dispatch under the current single-session directive.

## Top next actions

1. Finish dependency-independent `R27d`; prepare and execute bounded `R27c-R1`; keep `R27e`/`R28a` held until independent re-review.
2. Continue only dependency-independent single-session work while external V14/G13/G12/V15 blockers remain; do not create parallel implementation lanes.
3. Restore GitHub Actions availability only within the existing/no-additional-spend entitlement; do not authorize new charges.

## Human action

GitHub Actions remains externally unavailable before runner allocation. Restore Actions only if it can be done within the existing/no-additional-spend entitlement. No main merge, public release/deploy, force push, or additional spend is authorized.
