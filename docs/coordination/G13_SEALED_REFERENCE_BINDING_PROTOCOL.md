# G13 sealed-reference binding protocol

Status: lead-owned preregistration / not yet satisfied
Artifact: `ART-V13-TASK-POOL`
Authority: `docs/coordination/EVAL_131_QUALIFICATION_PROTOCOL.md`

## Purpose

Keep held-out grader/reference content inaccessible to implementation/evaluation workers while still binding every counted trial to an immutable reference identity. This protocol does not create hidden answers and does not authorize counted qualification by itself.

## Trust boundary

Worker-visible Git may contain:

- held-out input records;
- opaque `hidden_reference_id` values;
- dataset/split/prompt/tool/scorer/model-config identities;
- a commitment over `<case_id, hidden_reference_id>` membership;
- schemas and public acceptance rules.

Worker-visible Git must not contain:

- plaintext reference answers;
- hidden grader outputs;
- secret rubrics/expected values;
- a fallback resolver that synthesizes or guesses a reference;
- credentials or private storage locations.

The sealed reference bundle must live in a lead/operator-controlled location not readable by the worker executing held-out tasks. Its storage mechanism is deliberately not invented here; until an actual authorized non-worker-readable location exists, the task pool remains not ready for counted qualification.

## Binding record

Before the first counted W-131B observation, the lead must record an immutable binding receipt containing at minimum:

- task-pool/freeze identity and exact source commit;
- sealed-reference interface ID/version;
- case-id -> opaque-reference-id commitment digest;
- sealed bundle content digest;
- scorer/grader contract identity and implementation digest;
- prompt/tool protocol identities;
- size-classifier identity;
- independence-checker identity;
- creation timestamp;
- access boundary used for the sealed bundle;
- statement that the held-out worker cannot read bundle contents before/during execution.

The receipt may expose digests and identities, not hidden content.

## Qualification harness behavior

For a counted trial the harness must:

1. verify the exact frozen task-pool/source identity;
2. verify the sealed bundle content digest and membership commitment before resolving any reference;
3. provide only the input/prompt/permitted resources to the model/worker;
4. collect the immutable model/output attempt first;
5. resolve the hidden reference only inside the grader boundary;
6. persist trial/result/overhead identities without returning hidden answer material to the worker;
7. fail closed on absent/mismatched bundle, unknown reference id, digest drift, scorer drift or worker-visible reference content.

A missing sealed bundle is `blocked`, never a reason to substitute known answers, public fixtures or generated expected outputs.

## Acceptance checks

The task-pool freeze cannot authorize counted qualification until all are true:

- worker-visible corpus passes answer/grader/reference-leak negatives;
- required independent held-out depth passes mechanically;
- contamination checks pass against calibration/burned pools;
- all frozen identities are non-floating;
- exact-tip offline verification is green;
- the lead creates and verifies the binding receipt against a real sealed bundle in a non-worker-readable location;
- `counted_qualification_ready` is recomputed from those facts rather than manually asserted.

## Current state

As of 2026-09-21T10:49:09Z, retry 04 has a real worker branch but its exact-tip offline pytest is red and no lead-controlled sealed reference bundle/content-digest binding has been established. Therefore counted qualification remains prohibited.
