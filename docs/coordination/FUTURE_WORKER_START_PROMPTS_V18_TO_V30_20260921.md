# SwarmAI future worker start prompts — prepared handoffs

Date: 2026-09-21
Status: PLANNING ONLY

These are future bootstrap prompts. Before use, update branch/session identity and reread canonical state.

## Start V1.8

You are implementing SwarmAI V1.8 recovery/site-authority capability on the current authorized implementation branch.

Read canonical ARTIFACT_REGISTRY, current STATE, V1.8 artifact contracts, FUTURE_CODE_MAP, FUTURE_SCHEMA_CONTRACTS, FUTURE_TEST_EVIDENCE_MATRIX, FUTURE_PACKET_CATALOG, and FUTURE_RISK_REGISTER.

Goal: implement ART-V18-SITE-EPOCH, deployment manifest, backup/restore/reconciliation, split-brain safety and outage-drill harness without inventing a second authority path.

Extend the existing PostgreSQL worker/result/tool-effect boundaries. SiteEpoch must fence dispatch, result acceptance and consequential effect acceptance. Backup/export must not contain secrets. Preserve unknown effects instead of blindly retrying.

Execute packets V18-01 -> V18-02 -> V18-03 in dependency order. Run deterministic/integration checks and produce real evidence only where actually available. Do not self-accept, merge main, release publicly or spend.

## Start V1.9

Implement V1.9 installability/extensions/beta/self-development on top of accepted/reviewable V1.7/V1.8 boundaries.

Read canonical registry and V1.9 contracts plus future prep docs.

Implement:
1. versioned ExtensionManifest + project-scoped grants/lifecycle;
2. all extension execution through existing broker/ToolGateway;
3. clean install/doctor;
4. upgrade/migration/rollback;
5. redacted support bundle;
6. real bounded self-development PR-candidate workflow.

No extension may widen provider/tool/data authority. Selfdev cannot self-merge/release or modify its own approval/evidence boundary.

## Start V2.0

Build the V2.0 integrated candidate, not new product architecture.

Integrate only reviewed lower-version source. Freeze CandidateManifest. Resolve migration head. Run full configured checks. Execute support/install/upgrade/rollback/security/performance evidence against the exact candidate. Freeze reliability protocol before campaign. Never backfill elapsed evidence.

## Start V2.3

Implement the V2.3 operational platform by evolving existing scheduler/worker/extension/observability seams.

Critical order:
1. durable project-level scheduling/fairness state;
2. transactional multi-resource reservation intent;
3. backpressure/cancel/drain/SiteEpoch;
4. SchedulerDecisionReceipt;
5. capability packs;
6. portability;
7. observability;
8. fleet policy;
9. frozen pathological/live evidence campaign.

Do not add a second scheduler or authority database. Project fair share cannot be multiplied by creating many missions/objectives.

## Start V3.0

Implement persistent governed operations on top of V2.3.

Order:
1. ObjectiveContract/version repository;
2. trigger receipts/dedupe/schedule-event reconciliation;
3. MissionProposal -> normal mission admission;
4. pause/revoke/expiry/stop/rate/max-active;
5. LearningProposal state machine;
6. calibration/freeze/sealed held-out/independent review;
7. canary/rollback/drift;
8. resource allocator using V2.3 scheduler;
9. controlled selfdev using learning governance;
10. capability ecosystem;
11. tenant/fleet audit;
12. integrated private-live evidence.

Persistent objectives are not permanent permissions. Models may propose; deterministic policy + independent evidence decides. Protected authority, spend, secrets, release/merge/deploy and held-out answers cannot be autonomously expanded or manipulated.
