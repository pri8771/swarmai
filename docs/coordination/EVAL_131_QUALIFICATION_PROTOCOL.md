# EVAL-131 empirical qualification protocol

Protocol version: 1.0
Preregistered: 2026-09-20
Authority: V1.4 execution contract + lead acceptance plan.

This protocol is frozen before additional qualification samples are used for gate acceptance. Changing thresholds, scoring, sample rules or held-out references after observing qualification results requires a new protocol version and invalidates affected qualification claims.

## Required support coverage

Required V1.3 product families:

- coding
- planning
- reasoning
- extraction

Required sizes:

- S
- M
- L
- XL

Required model configurations:

- at least three actual exact configurations, identified by provider/route/account alias/model/version and relevant inference settings;
- a local model counts as an actual configuration only when availability is actually probed;
- model aliases that resolve to the same exact model/config do not count as separate configurations.

Every model × required-family × size cell needs measured screening evidence or a specific evidenced incompatibility. A cell may remain unqualified; every family × size must have at least one qualified route.

## Screening versus qualification

Screening:
- initial held-out minimum: n=5 independent observations per cell;
- screening results are `provisional`, never `qualified`;
- screening is used to choose which cells deserve more samples, not to claim production fitness.

Qualification:
- begin only after the task set, scorer, prompt/tool versions, model configuration and acceptance threshold are locked;
- use held-out observations not used for prompt/routing calibration;
- sample in batches of five;
- minimum n=15 before qualification is possible;
- maximum n=60 per cell for this tranche unless a stricter pre-existing policy applies;
- successful early stopping is allowed when the criterion is met;
- interrupted cells below the criterion remain provisional;
- a cell reaching n=60 without meeting the criterion is unqualified for V1.3.

A perfect 5/5 screening result is still not enough: its one-sided 90% Wilson lower confidence bound is below 0.80.

## Primary quality criterion

For each cell, define a binary trial success from the locked deterministic/rubric checks.

A route qualifies for a family × size cell only when all are true:

1. one-sided 90% Wilson lower confidence bound for success rate is >= 0.80;
2. zero forbidden/unauthorized tool actions;
3. all mandatory deterministic safety/format checks pass on every accepted trial;
4. no grader/reference leakage to the worker;
5. evidence is bound to exact candidate, dataset, grader, prompt, tool and model/config identities;
6. total overhead accounting is present.

Reference qualification thresholds at batch boundaries:

| n | minimum successes needed for Wilson lower >= 0.80 |
|---:|---:|
| 15 | 14 |
| 20 | 19 |
| 25 | 23 |
| 30 | 27 |
| 35 | 32 |
| 40 | 36 |
| 45 | 40 |
| 50 | 44 |
| 55 | 48 |
| 60 | 52 |

The implementation must calculate the bound, not hard-code this table as the only source of truth.

## Trial independence and held-out integrity

- Calibration/prompt-development tasks and held-out qualification tasks must have separate IDs/hashes.
- The worker may see the task input and permitted resources, but not hidden reference answers or hidden grading outputs.
- Do not commit plaintext hidden answers to a worker-accessible branch before the run.
- Git may contain task-pool IDs, source/license metadata, hashes, schemas and public acceptance rules.
- Any task seen during prompt/routing tuning is calibration, not held-out evidence.
- Retries on the same task are attempts, not new independent observations. Preserve all attempts and count retry overhead.
- If an input is materially regenerated, record a new task ID/version and why it is independent.

## Role qualification for G14 planners/reviewers

The four-family matrix above is product task routing. G14 additionally requires role fitness.

Planner:
- a configuration used as a planner must meet the same statistical criterion on planning tasks at the maximum size it will plan;
- planning evidence must score decomposition quality, dependency correctness, permitted-resource compliance and useful task creation, not prose style alone.

Reviewer:
- every configuration used as a reviewer must meet the same statistical criterion on a separately versioned review benchmark at the maximum complexity it will review;
- reviewer scoring must include wrong-result rejection, evidence/acceptance consistency and forbidden-action detection;
- because current review screening has been weak, benchmark/grader debugging must occur only on calibration tasks; after a new review benchmark version is locked, held-out results may be collected.

Do not use a route as a G14 reviewer merely because it is strong at another family.

## Size classification

Size is determined from structured features, not prompt token count alone. At minimum include:

- number of rules/acceptance obligations;
- number of entities/files/data sources;
- dependency depth;
- estimated tool steps;
- required output components;
- risk/permission complexity.

The classifier/version must be persisted with each observation.

## Required overhead accounting

For every evaluated route/cell and for direct-vs-pipeline comparisons record:

- input/output tokens where available;
- actual model attempts;
- planning calls;
- worker calls;
- review calls;
- retries/repairs/escalations;
- subdivision/recombination calls;
- wall time and model latency;
- local/remote route identity;
- charge/usage observation or explicit unknown;
- deterministic tool time when material.

Unknown cost/usage remains unknown; do not invent zero.

## Selection policy

Runtime routing may select a cell only when:

- the exact family/size cell is qualified;
- route auth/health/price/quota evidence is current and independently admissible;
- privacy/permission constraints permit the route.

If no qualified route exists:
- subdivide to qualified smaller-size cells when semantically valid;
- use bounded repair/escalation when a qualified alternative exists;
- otherwise return blocked/unsupported/waiting honestly.

Never use `provisional` as an alias for qualified.

## Efficient next sampling

Current n=5 screening should be used to avoid blanket expansion:

1. Complete missing screening coverage for the third model on required L/XL cells, unless a specific resource incompatibility is documented.
2. Select the strongest candidate route(s) per required family × size.
3. Add held-out samples only to those candidate cells in batches of five.
4. Stop a cell once qualified, maxed out, or clearly abandoned in favor of another qualified route.
5. Maintain enough reviewer-role sampling for the exact configurations intended for G14.

The gate requires coverage and qualified routes, not that every model qualify everywhere.
