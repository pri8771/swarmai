# ART-V17-APPROVAL-BINDING — R27c-R1 independent lead review

Date: 2026-09-22
Reviewer: ChatGPT engineering/product lead / formal acceptance authority
Decision: **BOUNDED SLICE ACCEPTED — R27c-R1**
Reviewed exact source: `codex/swarm-r27c-repair-20260922@fb34b2c00fc7cc2c81cb481dfa35df8e259bc04e`
Base: `cursor/v17-single-session@05fe7807db3509d68dd8a86a0616c9e8ffaa2307`
PR: #18
Parent artifact: `ART-V17-APPROVAL-BINDING` remains **drafting**
Live/checkpoint acceptance: **NOT GRANTED**

## Verdict

The two blocking findings from the prior R27c review are repaired at the exact reviewed SHA.

### 1. Durable lease/cancellation authority is now checked inside committed admission

The operational durable gateway no longer passes `fence_reader=None` for a mission-linked consequential action. It derives an `effect_fence_reader(envelope)`; `DurableEffectRepository.begin_execution()` invokes it inside the same transaction that locks the effect row, consumes approval authority and performs the single-winner CAS.

The lease reader validates the durable mission/project/task/attempt/active-lease/worker binding, worker state/generation, lease expiry and current task/source/cancellation authority. It takes row locks that serialize committed admission against mission cancellation/authority changes.

The added PostgreSQL regressions exercise a durable authority change after the gateway-local precheck and before committed admission and require fail-closed behavior with zero adapter calls and zero approval consumption. The lock-order regression also demonstrates cancellation waiting while admission holds authority locks.

### 2. Replacement approvals are accounted per effect without double-consuming the same grant

The effect now retains a `consumed_approval_ids` ledger. A distinct replacement grant authorizing a new attempt is atomically consumed once and becomes the current approval attribution. Returning to a grant already consumed for this effect does not consume it twice. Revoked/expired replacement grants remain denied.

Because approval consumption and effect mutation are in the same repository transaction, a failed execution CAS rolls back replacement-grant use and effect-ledger changes. The new durable busy-effect regression checks that property.

The required A -> B retry regression shows B is consumed exactly once and then cannot authorize a different second effect.

### Additional exact-source hardening

At the follow-up commit, terminal success replay and unknown reconciliation first validate the stored integration/payload and mission/task/attempt/lease/cancellation binding against the requesting envelope. A changed mission context therefore cannot reuse a prior effect shortcut or reach adapter reconciliation.

## Verification evidence considered

Native author-engineering evidence bound to `fb34b2c` reports:
- full offline suite: **474 passed, 0 skipped**;
- focused real-PostgreSQL effect admission/transaction/reservation suite: **33 passed**, repeated five times;
- Ruff clean;
- mypy clean;
- git diff check clean.

The earlier red reproducer and R27c lead review establish the two pre-repair failures. The reviewed diff directly addresses those failures.

These commands were executed by the repair author/Codex environment; this lead review independently inspected the exact diff, contracts, prior blocking review and source-bound evidence, but did not re-run the PostgreSQL suite itself.

GitHub Actions at this SHA is **not counted as green evidence**: observed jobs failed before exposing executable steps, consistent with the repository's existing hosted-runner/account infrastructure issue.

## Scope boundary

This accepts only the R27c-R1 engineering slice at exact SHA `fb34b2c00fc7cc2c81cb481dfa35df8e259bc04e`.

It does **not**:
- accept the parent `ART-V17-APPROVAL-BINDING`;
- count as CP5/CP6 or any live mission checkpoint;
- change the failed `v14-real-008/attempt2` result;
- authorize a third CP1 attempt;
- authorize provider/model/external issue actions, spend, deployment, main merge, public release, scheduler changes or V1.8+ work.

R27d's prior bounded acceptance remains valid because its reviewed source is an ancestor of the current base.

## Scheduling decision

**R27e is RELEASED TO CODEX** for direct isolated implementation, based on this exact accepted R27c-R1 SHA and the already accepted R27d slice.

R27e must remain on an isolated Codex repair branch/worktree and follow the existing `packets/R27e.md` contract. Its evidence is engineering evidence until independently reviewed.

**R28a remains HELD**. Its existing review-before dependency on R27e is unchanged; no R28a implementation should begin until an exact-SHA R27e lead verdict releases it.

No Fable routing, assignment, ACK or handoff is authorized or requested.
