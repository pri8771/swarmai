# Astra exact-source review and owner-target reconciliation — 2026-09-22

Recommendation: **REWORK_FOUND**, implementation only. Native formal verdict requested; no self-acceptance or live authorization.

Owner directive: "My goal is to reach 2.7 on each, I'll be happy with 2.3." Swarm's canonical ladder defines V2.3 operational platform / CP23 (existing scheduler, fair multi-mission operation, packs, portability, observability, fleet policy, at least two physical nodes and real external interaction). No V2.7 contract was found; request a lead proposal for owner review, not an invented milestone. No Fable dispatch.

Fresh Git supersedes the handoff's pending R29a status: R29a 1ea1ca5, R28d-1 a2cfb3c and R28d-2 6dbf8c4 already have native engineering verdicts. Current pending source is **86f8e0c90e399c683d68ba9628ef48af4723f33f**, tree **b42a7a11f298cdefe89319bfaa91f1ce91aa55d4**, branch codex/swarm-r28d3-async-gateway-20260922. Earlier request is 6e549d79:docs/coordination/reviews/CODEX_R28D4_CANCELLATION_AND_PENDING_APPLY_REPAIR_REQUEST_20260922.md.

## New independent exact-source finding

A bounded mechanical reviewer reproduced the cancellation/admission race; root independently repeated the actual probe with current-source PYTHONPATH and no database/provider/model/live environment. An actual RevocableFenceProvider snapshot sees generation0; its actual cancel() finishes at generation1 while effect still reserved; admission then uses stale snapshot, writes late.txt and records succeeded receipt before worker raises cancellation. This is synthetic local concurrency evidence, not a live mission or external effect. It disproves the claimed cancellation admission closure at this exact source.

Root read the actual lock/read/commit paths. Request the smallest repair: serialize local revocation with store.begin_execution through admission return/commit, release before adapter execution; retain draining/accounting for already-admitted operations. Keep existing durable lease lock order and authority. A second unlocked check is insufficient. The fixture-only proposal is unapplied; it prepares tables on the explicitly disposable PostgreSQL backend rather than hiding the durable path.

## Executed checks

- Focused offline11 passed; full actual owned PostgreSQL622 passed,2 failed,13 skipped. Both failures are new runtime tests lacking schema setup when inheriting SWARM_DATABASE_URL; they are separate from the production race.
- Mypy174 passed. Full Ruff inherited api/store.py I001 remains reported, not called clean. Hosted CI account billing/spend startup block remains ungreen.
- Owned Unix socket56421; exact disposable DB only; public tables after suite0, remaining database count0. No service start/stop or other DB touched. Source clean/unchanged.
- Full retained evidence and scripts: ../evidence/CODEX-ASTRA-R28D-20260922/ (SHA256SUMS). Previous live attempt e9178259 remains immutable failed evidence; old grant consumed.

## Requested formal disposition and next bounded task

1. Confirm REWORK_FOUND for86f8e0c, release only the local admission/revocation atomicity repair and missing-schema fixture correction from this reviewed candidate. No new run grant implied.
2. After new exact-source checks and independent review, issue an engineering verdict. A new R28d successor live assignment would need owner-approved exact host/route/model/target and call/token/time caps, incremental $0 entitlement and expiry; current user grants none.
3. Independently reconcile existing R30a source/evidence and, if prerequisites are accepted, release one bounded R30b offline diagnosis/preparation task via native packet. Do not duplicate implemented R30a or unlock held R28d-dependent tasks.
4. Reconcile target metadata to V2.3 floor/V2.7 requested and propose missing V2.7 definition for owner review.

Consolidated grant needs were delivered to owner before any live action: CP1 exhausted attempts/new preregistration; CP2 sealed references and ≥2 zero-charge providers; CP3 approved isolated recovery/second host; CP4 scoped A/B knowledge/model proof; CP5 exact adapter/session targets; R33c private pri8771/swarmai one approved issue/comment/close with gateway readbacks; isolated backup/recovery/elapsed CP23; owner CI billing disposition or approved no-cost runner. No grant inferred from prior prose or current authentication. No scheduler, model/mailbox/public/application action, spend, main merge or deploy.
