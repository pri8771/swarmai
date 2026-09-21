# SwarmAI future operator journeys — acceptance-oriented E2E scenarios

Date: 2026-09-21
Status: PLANNING ONLY

Purpose: define end-to-end journeys early so implementation does not optimize only for unit tests.

## Journey J18-01 — recover a failed site

1. Product has active project, mission state, worker leases and one known/unknown effect mix.
2. Create valid backup at consistency point.
3. Simulate/control-plane outage.
4. Restore to new site authority.
5. New epoch activates.
6. Reconcile leases/results/effects.
7. Old site attempts dispatch/result/effect and is denied.
8. Operator sees recovery receipt and RPO/RTO.

Success:
no duplicate accepted consequential effect and no stale authority acceptance.

## Journey J19-01 — install from empty environment

1. Fresh supported host.
2. Install prerequisites.
3. Run Swarm installer/doctor.
4. Initialize DB/migrations.
5. Start product.
6. Create project.
7. Run deterministic/basic supported mission.
8. Produce support bundle.
9. Confirm no hidden seeded product state.

## Journey J19-02 — extension lifecycle

1. Install versioned extension.
2. Inspect declared permissions.
3. Enable for project A with subset grant.
4. Project A uses allowed operation.
5. Project B is denied.
6. Attempt undeclared operation is denied.
7. Drain extension.
8. New work stops.
9. Disable/uninstall.
10. Historical receipts remain.

## Journey J19-03 — self-development

1. Select bounded real issue.
2. Freeze issue/tests/constraints.
3. Swarm opens isolated branch/worktree.
4. Produces candidate change.
5. Runs deterministic checks.
6. Independent reviewer accepts/rejects.
7. Product cannot merge itself.
8. Failed attempts remain evidence.

## Journey J20-01 — upgrade and rollback

1. Start from supported previous install with real data.
2. Create pre-upgrade backup.
3. Upgrade package/schema.
4. Validate product journeys.
5. Inject failure or use known rollback exercise.
6. Roll back according to supported policy.
7. Validate preserved data/authority.
8. Bind evidence to exact CandidateManifest.

## Journey J23-01 — fair multi-project congestion

1. Projects A/B/C enqueue heterogeneous work.
2. A submits many missions.
3. Provider quota and workers are constrained.
4. Scheduler makes durable decisions.
5. B/C continue receiving bounded fair service.
6. Incompatible head task does not block eligible task.
7. Kill/restart scheduler.
8. Fairness/reconciliation remains coherent.
9. Decision receipts explain selections without private raw content.

## Journey J23-02 — portable project

1. Project has accepted knowledge, pack grants, policies.
2. Export bundle.
3. Verify secret values absent.
4. Import to clean compatible environment.
5. Reconcile pack/schema versions.
6. Run supported mission.
7. Deleted/unauthorized data remains absent.

## Journey J30-01 — recurring objective

1. Create objective with schedule, rate/max-active, tools/data/provider bounds, expiry.
2. Activate.
3. Real schedule occurrence creates TriggerReceipt.
4. Proposal enters normal mission admission.
5. Restart process around a later occurrence.
6. No duplicate mission.
7. Pause blocks next proposal.
8. Reactivate if policy allows.
9. Revoke; future proposals stop permanently for that version.
10. Expiry/stop-condition behavior is deterministic.

## Journey J30-02 — event duplicate

1. Authenticated external/internal event delivered twice.
2. One trigger dedupe key becomes authoritative.
3. Exactly one proposal/admitted mission.
4. Second event yields duplicate receipt/denial, not new work.

## Journey J30-03 — governed learning rollback

1. Operational evidence motivates bounded routing/procedure change.
2. Create LearningProposal.
3. Calibration runs.
4. Freeze candidate/scorer/datasets/thresholds.
5. Sealed held-out runs.
6. Independent review.
7. Canary activates for bounded scope.
8. Force guardrail regression.
9. Deterministic rollback restores parent.
10. Stale candidate worker attempt is fenced.
11. Rollback/failure evidence retained.

## Journey J30-04 — self-improvement without self-permission

1. Swarm identifies bounded code improvement.
2. Creates governed selfdev proposal.
3. Isolated branch implementation.
4. Tests/evals.
5. Proposal tries to modify its own approval/governance file and is rejected.
6. Valid bounded diff proceeds to independent review.
7. Swarm creates PR candidate.
8. Operator/reviewer, not Swarm, controls merge/release.
