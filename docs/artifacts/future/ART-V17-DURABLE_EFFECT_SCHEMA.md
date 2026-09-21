# ART-V17-DURABLE-EFFECT-SCHEMA — approvals and consequential effects

Status: accepted lead design
Target: V1.7
Owner: ChatGPT lead
Depends on: ART-V17-APPROVAL-BINDING, ART-V20-INTEGRATION-CONTRACT

## Existing schema observations

Current DB `ApprovalRow` lacks a first-class `project_id` column even though the domain Approval model has project ownership. Current ToolGateway duplicate protection is in-memory by operation_id. Current `AttemptReceiptRow` represents inference/network attempts, not arbitrary tool effects.

V2 requires durable action/effect state.

## Extend ApprovalRow

Add:
- project_id String(64), indexed, operationally non-null
- actor/grantor identity stays
- integration_id/version
- operation
- destination canonical digest/text
- effect_key nullable
- max_effect_count
- policy_version
- created_at
- accepted/used_count where policy requires one-shot or bounded use
- constraints JSONB remains

Keep payload_hash.

Do not backfill missing project_id with proj_demo/proj_local. Legacy unknown rows remain non-operational until reconciled.

## New ActionEffectRow

Table: `action_effects`

Fields:
- effect_id PK
- effect_key String(192)
- project_id index
- mission_id/task_id/attempt_id nullable/indexed
- action_id String(64)
- approval_id nullable
- integration_id / integration_version
- operation
- destination_digest
- payload_hash
- state: reserved|executing|unknown|succeeded|failed|denied|cancelled|reconciled
- external_id nullable
- lease_generation
- cancellation_generation
- pre_observation JSONB
- post_observation JSONB
- reconciliation JSONB
- created_at / started_at / finished_at / reconciled_at
- payload JSONB

Unique:
- project_id + effect_key for effects that must be at-most-one accepted intent.

Depending on integration semantics, multiple attempts may reference the same ActionEffectRow; do not create a new effect key simply to retry.

## New ActionAttemptRow optional/recommended

If multiple transport attempts need separate audit:
- action_attempt_id PK
- effect_id FK
- attempt_number
- started_at/finished_at
- transport/request ID
- outcome
- error class
- receipt payload

This separates intended effect from network attempts.

## Execution transaction model

1. normalize ActionEnvelope.
2. authorize project/scopes/approval.
3. durable reserve/get effect row by project/effect key.
4. if succeeded: return existing receipt; do not execute.
5. if unknown: reconcile before any retry.
6. if executable: mark executing in transaction.
7. adapter executes.
8. record attempt + post-observation.
9. set effect terminal or unknown.
10. emit EventEnvelope/outbox.

## Approval/effect binding

Before execution verify:
- approval.project_id == envelope.project_id
- integration/version
- operation
- destination
- payload hash or allowed constrained payload
- effect key
- expiry/revocation/usage count
- cancellation/lease generations where relevant

## Lane split

Session B:
- ActionEnvelope/ApprovalGrant/ActionReceipt domain contracts;
- ToolGateway behavior;
- adapter interface;
- effect-key calculation contract;
- integration-level unit/negative tests.

Session A:
- DB row/migration/repository transaction;
- central API/CLI wiring.

## Negative tests

- same effect retried after process restart: no second execution after succeeded;
- unknown effect: reconciliation required;
- approval project mismatch denied;
- destination/payload mutation denied;
- expired/revoked/used-up approval denied;
- cancellation generation changes before execute: deny;
- stale worker lease cannot execute consequential effect;
- two concurrent reservations for same project/effect key: one logical effect;
- project B reusing project A effect key cannot access A receipt or suppress B incorrectly.
