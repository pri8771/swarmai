# ART-V16-KNOWLEDGE-CONTRACT — Scoped reusable knowledge

Status: drafting
Target: V1.6
Owner: ChatGPT lead

## Goal

Reuse verified information and procedures across missions without turning all prior chat/history into an unbounded memory blob or violating project boundaries.

## Knowledge classes

1. Current work state — ephemeral mission/task facts.
2. Source artifact — immutable external/internal source with provenance.
3. Observation — extracted statement tied to source/version.
4. Hypothesis — unaccepted inference.
5. Accepted fact — reviewed statement with provenance/confidence/expiry.
6. Procedure — reusable process/instruction with version and applicability.
7. Summary — derived compression with links to underlying facts/sources.

Never silently convert a hypothesis or model-generated summary into an accepted fact.

## Required fields

Every reusable knowledge item:
- item_id/version;
- project/tenant scope;
- knowledge class;
- canonical statement/body;
- provenance refs;
- source hashes/versions;
- created/observed timestamp;
- author/producer;
- review/acceptance state;
- confidence where meaningful;
- expiry/staleness policy;
- supersedes/superseded_by;
- permission labels;
- retrieval tags/embedding refs if used.

## Retrieval policy

Permission filtering occurs **before** retrieval/ranking/context assembly.

Retrieval produces:
- selected item IDs;
- why each was selected;
- source/provenance refs;
- staleness/conflict flags;
- token/context cost.

No cross-project vector index query may reveal unauthorized metadata or nearest-neighbor existence.

## Contradictions

When new information conflicts:
- keep both observations;
- mark contradiction set;
- do not overwrite history;
- accepted fact becomes disputed/superseded only through explicit rule/review;
- future retrieval should prefer valid newer accepted facts while retaining provenance.

## Correction/deletion

Deletion/supersession must affect:
- primary record;
- retrieval index;
- cached summaries;
- export materialization;
- future prompt/context assembly.

Maintain tombstone/audit info where policy requires it without returning deleted content.

## Context budget

Knowledge reuse must prove value.

Measure:
- relevant facts retrieved;
- tokens loaded;
- tokens avoided versus full-history loading;
- answer/task quality;
- stale/irrelevant retrieval rate;
- cross-project isolation negatives.

V1.6 should prefer compact accepted evidence over whole-conversation replay.

## Acceptance evidence

- later mission reuses an accepted fact/procedure correctly;
- measured context savings versus full-source reload;
- superseding a fact changes future retrieval;
- deletion removes future retrieval;
- cross-project search/export/cache leak tests pass;
- irrelevant large history does not force full context load.
