# ART-V17-APPROVAL-BINDING — R27e independent lead review

Date: 2026-09-22
Reviewer: ChatGPT engineering/product lead / formal acceptance authority
Decision: **BOUNDED SLICE ACCEPTED — R27e**
Reviewed exact source: `codex/swarm-r27e-recovery-20260922@e924351bd93510eaae279225db3a2fa447dd6894`
Base: accepted R27c-R1 `fb34b2c00fc7cc2c81cb481dfa35df8e259bc04e`
PR: #20
Parent artifact: `ART-V17-APPROVAL-BINDING` remains **drafting**
Live/checkpoint acceptance: **NOT GRANTED**

## Exact-SHA verdict

The superseding candidate closes the original R27e crash-window requirements and the subsequently identified legacy-row blocker without introducing an automatic fail-open path.

### New-format effects

- execution persists immutable recovery timeout and side-effect class;
- lazy orphan recovery locks the exact row and requires the caller timeout to equal the stored timeout before computing the cutoff;
- a young/live executor is not taken over;
- an expired executing row moves to `unknown`, never back to `reserved`;
- finalization/pre-observation require the exact executor/attempt/state token, so stale executors fail closed;
- reconciliation preserves ambiguous outcomes as `unknown`;
- proved `not_applied` retries automatically only for stored `consequential` effects;
- stored `irreversible` effects require explicit rearm;
- reconciliation/finalization races have a single terminal winner.

### Legacy executing effects

The prior candidate `193e454...` was correctly blocked because legacy executing rows have no trustworthy stored timeout/class and therefore had no disposition path.

At `e924351...`, legacy recovery is deliberately a separate authenticated operator disposition, not automatic timeout recovery:

- the service requires an explicit registered Bearer token, project authorization, and operator/admin role;
- the repository locks the exact project/effect row and validates the observed executor/attempt/state token under that lock;
- only an `executing` row missing both recovery timeout and side-effect class is eligible;
- the only state transition is `executing -> unknown`;
- the disposition records authenticated subject, reason, evidence reference, executor and attempt in durable effect payload;
- it does not guess/backfill timeout or class, reserve/re-execute, consume approval, increment attempts, perform an adapter action, or create a success/outcome receipt;
- concurrent disposition has one winner;
- legacy `not_applied` is conservatively treated as irreversible and cannot be rearmed until a separately reviewed policy migration exists.

This satisfies the required operator constraint for legacy ambiguity. No caller-selected shorter timeout is accepted by ordinary orphan recovery: direct repository recovery verifies the immutable stored timeout. Legacy disposition does not use a caller timeout at all.

The operator disposition may occur without an inferred age threshold because it is an explicit authenticated, evidence-referenced ambiguity transition only; it cannot itself cause re-execution. An already-running executor that later tries to finalize with its old `executing` token is fenced by the state-token check. Any external outcome remains subject to reconciliation.

## Evidence considered

Native exact-source engineering evidence at coordination commit `b76c4ad9f937ca56f0800af581193aa95ddb9460` reports:
- full offline suite: **507 passed, 0 skipped**;
- combined real-PostgreSQL crash + legacy suite: **33 passed**, repeated five consecutive times;
- affected admission/transaction/reservation suite: **33 passed**;
- real spawned child exits around fsynced temp-file effects and actual timeout wait;
- Ruff clean;
- changed-file format clean;
- mypy clean across 170 source files.

The hashed `CODEX-R27E-LEGACY-20260922` manifest binds the evidence to source tree `c907deb19ba157def74b64c2514187e6c8161a54`.

A bounded static reviewer found no introduced fail-open or repository race in the legacy repair. This lead review independently inspected the exact source/diff, native R27e contract, prior blocking legacy finding, repair tests and evidence; it did not independently rerun PostgreSQL.

Hosted GitHub Actions at this SHA failed before executable job steps because of the existing account/payment limit. They are not counted as green code-test evidence and do not overturn the source-bound local checks.

## Scope boundary

This accepts only the R27e engineering slice at exact SHA `e924351bd93510eaae279225db3a2fa447dd6894`.

It does **not**:
- accept parent `ART-V17-APPROVAL-BINDING`;
- count as CP5/CP6 or real-world product proof;
- approve a legacy retry-policy migration;
- change failed `v14-real-008/attempt2`;
- authorize a third CP1 attempt;
- authorize provider/model/external issue actions, spend, merge, deployment, public release, scheduler changes, Fable routing, or V1.8+ work.

## Scheduling decision

**R28a is RELEASED TO CODEX** for isolated direct implementation based exactly on `e924351bd93510eaae279225db3a2fa447dd6894`.

R28a must follow the existing `docs/coordination/packets/R28a.md` contract. Its result remains engineering evidence until independent exact-SHA lead review.

R02c PR #19 remains separately pending and is not decided by this review.
