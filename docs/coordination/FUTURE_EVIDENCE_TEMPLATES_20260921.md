# SwarmAI future evidence templates

Date: 2026-09-21
Status: PLANNING ONLY

These are skeletons. Never fill fields with invented data.

## Generic evidence manifest

```json
{
  "schema_version": "1.0",
  "evidence_id": null,
  "artifact_ids": [],
  "case_ids": [],
  "candidate_id": null,
  "source_sha": null,
  "schema_revision": null,
  "policy_versions": {},
  "environment_ref": null,
  "started_at": null,
  "finished_at": null,
  "elapsed_seconds": null,
  "trigger": "manual|scheduler|event|campaign",
  "result": "passed|failed|blocked|unknown",
  "attempts": [],
  "receipts": [],
  "test_refs": [],
  "cost": {
    "known": false,
    "usd": null,
    "notes": null
  },
  "blockers": [],
  "redactions": [],
  "notes": null
}
```

Rules:
- preserve failed attempts;
- elapsed time comes from real timestamps;
- `usd=0` only when actually evidenced/known;
- no credentials/cookies/hidden answers.

## CandidateManifest skeleton

```json
{
  "candidate_id": null,
  "source_sha": null,
  "schema_revision": null,
  "migration_heads": [],
  "dependency_lock_digest": null,
  "deployment_manifest_digest": null,
  "artifact_registry_digest": null,
  "policy_versions": {},
  "provider_versions": {},
  "tool_versions": {},
  "extension_pack_versions": {},
  "test_protocol_versions": {},
  "eval_protocol_versions": {},
  "frozen_at": null,
  "invalidated_at": null,
  "invalidation_reason": null
}
```

## Recovery drill skeleton

```json
{
  "recovery_id": null,
  "backup_id": null,
  "case_ids": ["V18-DRILL-001"],
  "old_site": {"site_id": null, "epoch": null},
  "new_site": {"site_id": null, "epoch": null},
  "outage_started_at": null,
  "restore_started_at": null,
  "authority_activated_at": null,
  "service_recovered_at": null,
  "rpo_seconds": null,
  "rto_seconds": null,
  "lease_reconciliation": [],
  "unknown_effect_reconciliation": [],
  "stale_site_attempts": [],
  "result": null
}
```

## Scheduler decision receipt skeleton

```json
{
  "decision_id": null,
  "policy_version": null,
  "site_epoch": null,
  "candidate_set_digest": null,
  "eligible_ids": [],
  "deferred": [{"id": null, "reason": null}],
  "selected_ids": [],
  "resource_intent_refs": [],
  "fairness_before": {},
  "fairness_after": {},
  "timestamp": null
}
```

Do not include raw private prompt/task content.

## Objective trigger/proposal skeleton

```json
{
  "trigger_receipt": {
    "trigger_id": null,
    "objective_id": null,
    "objective_version": null,
    "trigger_type": null,
    "dedupe_key": null,
    "source_auth_ref": null,
    "observed_at": null,
    "admission_state": null,
    "rejection_reason": null,
    "site_epoch": null
  },
  "mission_proposal": {
    "proposal_id": null,
    "trigger_id": null,
    "mission_template": null,
    "input_refs": [],
    "requested_resources": {},
    "requested_scopes": {},
    "authority_intersection_digest": null,
    "state": null,
    "rejection_reason": null
  }
}
```

## LearningProposal evidence skeleton

```json
{
  "proposal_id": null,
  "target": {"type": null, "id": null},
  "parent_version": null,
  "candidate_version": null,
  "candidate_digest": null,
  "source_evidence_refs": [],
  "hypothesis": null,
  "metrics": {
    "primary": null,
    "guardrails": []
  },
  "calibration": {
    "dataset_digest": null,
    "result_ref": null
  },
  "frozen_protocol": {
    "heldout_dataset_digest": null,
    "scorer_version": null,
    "sample_rule": null,
    "stop_rule": null,
    "resource_envelope": null,
    "frozen_at": null
  },
  "heldout": {
    "access_policy": null,
    "started_at": null,
    "finished_at": null,
    "result_ref": null,
    "contaminated": false
  },
  "independent_review": {
    "reviewer_ref": null,
    "decision": null,
    "review_ref": null
  },
  "canary": {
    "scope": null,
    "started_at": null,
    "finished_at": null,
    "rollback_triggered": false,
    "result_ref": null
  },
  "final_state": null,
  "rollback_ref": null
}
```

## Live evidence folder convention

Recommended:
`docs/evidence/<artifact-or-campaign>/<run-id>/`

Possible files:
- manifest.json
- candidate.json
- environment.json
- receipts.jsonl
- deterministic-checks.txt/ref
- summary.md

Keep hidden held-out answer corpora outside worker-visible evidence paths.
