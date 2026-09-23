# ART-V16-PROVENANCE — reusable knowledge schema and lifecycle

Status: drafting
Target: V1.7 milestone / V1.6 capability group
Owner: ChatGPT lead
Depends on: ART-V16-KNOWLEDGE-CONTRACT

## Data model

KnowledgeItem:
- item_id
- version
- project_id
- mission_id optional
- class: source|observation|hypothesis|accepted_fact|procedure|summary
- topic
- body
- provenance_refs[]
- source_digests[]
- producer_type / producer_ref
- acceptance_state: unreviewed|accepted|disputed|superseded|deleted
- confidence optional
- created_at / observed_at
- expires_at optional
- supersedes[]
- permission_labels[]
- retrieval_labels[]
- content_digest

KnowledgeLink:
- from_item_id/version
- relation: derived_from|supports|contradicts|supersedes|summarizes
- to_item_id/version
- evidence_ref

Tombstone:
- item_id
- deleted_version
- deleted_at
- reason_class
- replacement_ref optional

## Write rules

- model output defaults to observation/hypothesis, never accepted_fact;
- accepted_fact requires explicit deterministic/reviewer policy;
- summary stores links to source items and cannot outlive deleted/unauthorized dependencies;
- edits create a new version, never silent overwrite;
- deletion creates tombstone and removes retrieval visibility.

## Retrieval contract

1. resolve actor/project permission;
2. filter permitted knowledge IDs/versions;
3. filter stale/deleted/superseded according to query mode;
4. rank only the permitted candidate set;
5. assemble bounded context;
6. emit retrieval receipt listing selected IDs, versions, provenance and token cost.

Permission filtering after vector ranking is forbidden because ranking metadata can leak cross-project existence.

## Conflict behavior

Contradictions create explicit links. Retrieval may return a conflict set; it must not manufacture a single truth unless acceptance/supersession policy resolved it.

## Implementation packets — Session B

- V2B-003a SP2: schema/versioned file-or-DB repository.
- V2B-003b SP2: permission-first retrieval API + receipts.
- V2B-003c SP2: supersession/deletion/contradiction logic.
- V2B-003d SP2: mission-memory migration adapter from existing MemoryStore.

## Acceptance evidence

- accepted fact reused by a later mission;
- hypothesis never promoted automatically;
- cross-project query returns no content or existence leak;
- supersession changes future retrieval;
- deletion removes item and dependent summary visibility;
- retrieval reports tokens/selected provenance;
- bounded retrieval beats whole-history context cost on a fixed mission set.
