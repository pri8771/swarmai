# SwarmAI future schema contracts — closure proposal

Date: 2026-09-21
Status: PLANNING ONLY
These are planning contracts. The packet JSON, migration ownership sequence and transaction algorithms define the implementation order. Final Fable must reconcile concrete types/backfills against source before freezing the plan; no new source migration is authored by this document.

## V1.8 SiteAuthority

### SiteAuthority
- authority_domain_id
- site_id
- epoch: monotonic integer
- state: active|recovering|fenced|retired
- activated_at
- fenced_at optional
- source_site_id optional
- recovery_id optional
- policy_version
- policy_digest
- proof_ref: independently verifiable old-site fencing evidence
- content_digest

Invariant:
Only one authoritative epoch may authorize new consequential work for a deployment authority domain.

### AuthorityBinding
Attach to dispatch/lease/result/effect:
- authority_domain_id
- site_id
- site_epoch
- authority_digest

Compare the complete domain/site/epoch/digest binding, not epoch alone. A restored DB cannot self-certify globally current authority. Reject absent, stale or mismatched binding at:
- task dispatch;
- lease renewal where contract requires;
- result acceptance;
- consequential effect execution/acceptance.

### BackupManifest
- backup_id
- source_site_id
- source_epoch
- source_commit_sha
- schema_revision
- migration_heads[]
- created_at
- consistency_point
- database_artifact_digest/reference
- config_manifest_digest/reference
- secret_refs[] (names only)
- included_state_classes[]
- excluded_state_classes[]
- tool/provider/extension version refs
- integrity_digest

### RecoveryReceipt
- recovery_id
- backup_id
- old_site_id/epoch
- new_site_id/epoch
- reconciliation_started_at/finished_at
- lease_actions[]
- unknown_effects[]
- fenced_stale_epochs[]
- final_state
- evidence_digest

## V1.9 ExtensionManifest

- extension_id
- version
- package/content digest
- publisher/provenance
- compatibility range
- declared capabilities
- read_data_classes[]
- write_data_classes[]
- tool_operations[]
- provider access requirements[]
- network scopes[]
- filesystem scopes[]
- secrets_refs_required[]
- migrations[]
- entrypoints
- tests/verification refs
- risk_class

### ProjectExtensionGrant
- project_id
- extension_id/version
- enabled
- granted capability subset
- granted data scopes
- granted tool/provider scopes
- approval ref
- enabled_at
- revoked/draining state
- grant_generation (monotonic; included in in-flight execution bindings)

Invariant:
Effective permission = intersection(manifest declaration, project grant, actor policy, global policy).

## V2.0 CandidateManifest

- candidate_id
- source_sha
- schema_revision/migration heads
- dependency lock digest
- runtime/deployment manifest digest
- policy versions
- provider/tool/extension versions used in evidence
- artifact registry digest
- test protocol versions
- eval protocol versions
- frozen_at
- invalidated_at optional
- invalidation_reason optional

All counted candidate evidence binds to candidate_id.

## V2.3 Scheduling

### SchedulerPolicy
- policy_id/version/digest
- project weights
- aging rules
- deadline bonus limits
- max_active constraints
- resource classes
- backpressure rules
- tie-break rule

### ProjectSchedulingState
- project_id
- virtual_time/fairness_credit
- active_missions
- queued_work
- last_service_at
- policy_version
- round_number and round_cursor
- last_credited_round

Credit accrues once per persisted round, with bounded restart catch-up; never per API poll.

### DispatchIntent (earlier prose alias: ResourceReservationIntent)
- intent_id
- project_id/mission_id/task_id
- attempt_id optional
- required resources[]
- status: preparing|ready|released|expired|unknown
- created_at/expires_at
- site_epoch
- authority_domain_id/site_id/authority_digest
- scheduler_generation
- dispatch_id: stable across restart/redelivery
- policy_version

Each resource entry:
- resource_type
- resource_id/scope
- amount
- reservation_ref
- state
- settlement_receipt_ref (idempotent debit/refund/reconciliation)

Task dispatch only after intent is ready.
Reuse existing worker/provider/tool reservation owners; this intent coordinates their references and does not create another capacity or budget authority.

### SchedulerDecisionReceipt
- decision_id
- policy_version
- candidate_set_digest
- eligible IDs
- denied/deferred IDs + reason classes
- selected ID(s)
- resource intent refs
- fairness state before/after
- timestamp
- site_epoch

Do not include private raw task/model content.

## V2.3 CapabilityPack

- pack_id/version
- digest/signature/provenance
- required Swarm version
- declared schemas/migrations
- procedures/templates
- adapter refs
- capabilities
- permissions required
- tests
- dependency packs
- lifecycle state

Project enablement is separate from installation.

## V2.3 PortabilityBundleManifest

- bundle_version
- export_id
- source project/site refs
- schema versions
- knowledge/provenance item refs/digests
- pack refs
- policy refs
- artifact/evidence refs
- secret reference names only
- excluded nonportable state
- content digests
- created_at

## V3.0 ObjectiveContract

- objective_id
- version
- project_id
- owner/authority ref
- desired_outcome
- allowed mission templates[]
- trigger policy
- resource/spend envelope
- allowed tools/integrations
- allowed data/privacy scope
- provider/model eligibility constraints
- rate limit
- max_active_missions
- start_at/expiry
- stop conditions
- pause/revoke policy
- approval rules
- state
- parent_version optional
- content_digest

### TriggerReceipt
- trigger_id
- objective_id/version
- trigger_type
- dedupe_key
- source/auth refs
- observed_at
- due_at optional
- admission_state/rejection_reason
- site_epoch
- receipt_digest

### MissionProposal
- proposal_id
- objective_id/version
- trigger_receipt_id
- mission_template_id/version
- exact input/artifact references
- requested resources
- requested tool/data/provider scopes
- authority intersection digest
- state
- rejection reason optional

MissionProposal is not execution authority. Normal mission admission still applies.

## V3.0 LearningProposal

- proposal_id
- target_type/target_id
- parent_version
- candidate_version/content_digest
- exact diff/parameter delta
- source mission/evidence refs
- hypothesis
- primary metric
- guardrail metrics
- risk class
- affected scopes
- calibration dataset/version/digest
- held-out dataset/version/digest
- held-out access policy
- scorer version
- frozen sample/confidence/stop rule
- resource envelope
- canary scope/duration/count
- rollback target/procedure
- proposer identity/runtime
- state
- independent reviewer decision/ref
- timestamps

State machine:
observed
-> proposed
-> static_validated
-> calibration_passed
-> frozen
-> heldout_running
-> heldout_passed
-> independently_reviewed
-> canary_running
-> accepted

Side/terminal:
rejected|contaminated|blocked|expired|rolled_back|superseded

### LearningTransitionReceipt
- proposal_id
- from_state/to_state
- actor
- source/candidate digest
- evidence refs
- policy/scorer versions
- timestamp
- reason

## V3 resource allocation

### ObjectiveResourceRequest
- objective/project
- urgency/deadline
- requested capacity
- provider/worker/tool classes
- locality/privacy constraints
- authorized budget envelope
- fairness context

### AllocationDecision
- request ref
- scheduler policy/version
- allocation/reservation refs
- denied/deferred reason
- explanation
- fairness/quotas before/after

Allocation never authorizes a denied tool/provider/data scope.

## Audit invariant across all versions

Every consequential state transition should be reconstructible from immutable or append-only receipts/references without needing private model chain-of-thought or secret material.

V1.7 prerequisite: execution attempt number and receipt sequence are separate; every finalize carries executor/attempt/execution_generation. Shared authority storage is introduced/backfilled by 18-02 and enforced by 18-03/04. Keep legacy rows nonauthoritative until explicit reconciliation. Candidate manifests remain artifact manifests rather than a mandatory new DB table.
