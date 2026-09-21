# ART-V16-DURABLE-SCHEMA — knowledge persistence decision

Status: accepted lead design
Target: V1.7 milestone / V1.6 capability group
Owner: ChatGPT lead
Depends on: ART-V16-PROVENANCE, ART-V20-INTEGRATION-CONTRACT

## Decision

Do not turn the legacy file-backed MemoryStore into the final V2 authority.

Use the existing MemoryStore only as a migration/input adapter and regression fixture. V2 durable reusable knowledge is project-scoped, versioned and stored in PostgreSQL.

Do not overload `FindingRow` into the entire knowledge system. Findings are mission/task evidence; reusable accepted facts/procedures/summaries need their own lifecycle/version semantics.

## New tables

### knowledge_items

Composite identity may be logical `item_id + version`; implementation may use a surrogate row ID but both logical fields are required.

Fields:
- row_id PK
- item_id String(64), indexed
- version Integer
- project_id String(64), indexed
- mission_id nullable
- class String(32): source|observation|hypothesis|accepted_fact|procedure|summary
- topic String/Text
- body Text
- acceptance_state String(32)
- confidence Float nullable
- producer_type String(32)
- producer_ref String(128) nullable
- permission_labels JSONB
- retrieval_labels JSONB
- source_digests JSONB
- provenance_refs JSONB
- content_digest String(128)
- observed_at nullable
- expires_at nullable
- created_at
- superseded_at nullable
- deleted_at nullable
- payload JSONB

Constraints:
- unique(item_id, version)
- index(project_id, class, acceptance_state)
- content_digest does not imply dedupe across project boundaries.

### knowledge_links

Fields:
- link_id PK
- project_id
- from_item_id / from_version
- relation
- to_item_id / to_version
- evidence_ref nullable
- created_at

Relations:
derived_from|supports|contradicts|supersedes|summarizes

Cross-project links are forbidden by default.

### knowledge_tombstones

Fields:
- item_id
- project_id
- deleted_version
- deleted_at
- reason_class
- replacement_item_id/version nullable

Tombstone exists so caches/index rebuilds cannot resurrect deleted content.

## Retrieval query rule

The DB/repository query MUST apply `project_id` and authorization labels before producing any candidate rows for semantic/text ranking.

Pseudo:
1. SELECT permitted project rows WHERE not deleted and lifecycle filter.
2. apply ACL/permission-label predicate.
3. only then rank/score/search.
4. fetch provenance/links inside same permitted project boundary.
5. generate RetrievalReceipt.

No global embedding/vector search followed by project filtering.

## RetrievalReceipt

Persist or emit versioned receipt:
- receipt_id
- project_id
- actor/scope digest
- query digest (avoid raw sensitive query when policy requires)
- selected item IDs/versions
- omitted reason counts
- token_budget / tokens_used
- retrieval policy/version
- created_at

V2.3 observability consumes these.

## Migration from MemoryStore

Migration adapter:
- read legacy memory.jsonl;
- require/validate record.project_id;
- map durable_fact -> observation or accepted_fact only according to explicit migration policy; do NOT assume legacy durable_fact is accepted truth;
- transient_context stays non-reusable/ephemeral unless explicitly promoted;
- model_obs becomes observation/routing evidence;
- outcome becomes observation unless acceptance provenance proves otherwise;
- preserve original memory_id/provenance in payload;
- produce migration report counts/errors;
- do not delete legacy file until operator/backup policy allows.

## Lane split

Session B:
- domain models;
- repository Protocol/service;
- permission-first retrieval logic;
- migration adapter;
- unit/security tests.

Session A:
- central SQLAlchemy Base registration/import;
- Alembic migration ordering;
- integrated DB session wiring.

Session B should not edit central migration files directly.

## Security tests

- project A cannot retrieve project B content by text, ID, tag, count, or routing preference;
- project A query cannot reveal that B has a matching item;
- superseded/deleted item is absent from default retrieval;
- deletion + index/cache rebuild does not resurrect;
- summary depending on deleted source is hidden/invalidated according to policy;
- cross-project link creation rejected;
- legacy record with missing/unknown project is quarantined, not assigned a guessed project.
