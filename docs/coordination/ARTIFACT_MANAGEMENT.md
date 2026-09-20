# SwarmAI artifact-oriented project management

Version: 1.0
Adopted: 2026-09-20

## Core rule

The primary unit of project management is an **artifact**, not a task.

A task exists only to create, change, validate, or retire an artifact. A version/milestone is complete when its required artifact set is accepted.

Examples of artifacts:
- source candidate / PR;
- architecture or interface contract;
- regression suite;
- provider eligibility ledger;
- benchmark/task pool;
- qualification matrix;
- live-run evidence bundle;
- threat model;
- migration/recovery plan;
- runbook;
- acceptance report.

Story points remain a worker-sizing field attached to the work needed to advance an artifact. They are not the project-management hierarchy.

## Artifact identity

Every managed artifact has:
- `artifact_id`: stable identifier;
- `name`;
- `target_version`;
- `kind`;
- `owner`;
- `status`;
- `path_or_source_ref`;
- `dependencies`;
- `acceptance_refs`;
- `evidence_refs`;
- `worker_packets`;
- optional `story_points_next`;
- `next_action`;
- `blockers`;
- `supersedes` / `superseded_by` when applicable.

IDs stay stable even if file paths or commits change.

Recommended ID families:
- `ART-V10-...` through `ART-V19-...`;
- `ART-LIVE142-...` for final V1.4 campaign artifacts;
- `ART-V20-...`, `ART-V30-...` for later product milestones;
- `ART-OPS-...` for cross-version governance/operations.

## Lifecycle

Use these artifact states:

1. `planned` — desired artifact is defined.
2. `drafting` — work is actively changing the artifact.
3. `reviewable` — owner claims it meets its contract and provides source/evidence.
4. `verified` — independent lead review confirms the artifact's claimed properties, but a higher gate may still block milestone acceptance.
5. `accepted` — artifact satisfies its required role in the target milestone.
6. `blocked` — progress requires an unavailable dependency/human/external system.
7. `superseded` — a newer artifact/version replaces this one.
8. `rejected` — evidence/design does not satisfy the contract and will not be used.

Do not use `accepted` merely because CI is green. Acceptance means the artifact satisfies its own acceptance refs and any required independent review.

## Artifact graph

Artifacts form a dependency graph.

Examples:
- remote-overlap evidence depends on a provider-eligibility ledger;
- a V1.4 live adaptive proof depends on qualified route/role manifests;
- the final campaign depends on accepted/verified G10-G14 artifacts;
- a recovery drill depends on a recovery architecture + backup manifest + runnable deployment.

The lead should preferentially unblock upstream artifacts whose completion releases multiple downstream artifacts.

## Version completion

Each version has a required artifact set.

A version is accepted only when:
- every required artifact is `accepted` or explicitly waived by a versioned owner decision;
- no required artifact is merely `reviewable`, `verified`, or `blocked`;
- the candidate/source/evidence references are mutually consistent;
- the artifact registry points to the exact accepted versions.

Version numbers are therefore summaries of accepted artifact sets, not labels attached to partially completed code.

## Work assignment

Worker packets are subordinate to artifacts.

Each worker packet must name:
- the artifact it advances;
- intended state transition;
- acceptance condition for the packet;
- SP1-SP5 complexity estimate;
- changed paths/source refs;
- required evidence.

Default worker assignment remains SP1-SP3. Split SP4-SP5 when possible.

Example:

`W-121A`
- artifact: `ART-V12-PROVIDER-ELIGIBILITY`
- transition: planned -> reviewable
- SP2
- deliverable: exact-route auth/eligibility/quota/health ledger

## Lead behavior

The lead should:
- maintain the artifact registry as canonical project state;
- create useful architecture/design/evidence artifacts directly;
- review worker-produced artifacts independently;
- turn review findings into artifact-specific worker packets;
- work on future artifacts whenever current lead work is saturated/blocked;
- avoid duplicating routine worker implementation;
- keep future artifacts useful even before their implementation tranche starts.

The lead may create future architecture, contracts, benchmarks, threat models, migration plans, runbooks, acceptance protocols and research artifacts proactively.

## Worker behavior

Cursor should:
- advance the highest-priority dependency-ready artifact assigned to it;
- prefer completing a reviewable artifact over accumulating disconnected code;
- provide exact source/evidence refs with every review request;
- not self-accept artifacts;
- avoid work not tied to a registered artifact unless it is an urgent defect, in which case register the artifact/change immediately.

## Evidence

Evidence is itself an artifact when it is independently meaningful.

Evidence artifacts must be immutable or versioned after a run. Do not silently overwrite a failed run with a successful one. The registry should point to all relevant evidence, including failed/retried evidence where required.

## Future work

The owner explicitly wants useful future work to continue.

When current-version lead work is waiting or saturated, the lead should advance future **non-conflicting artifacts** directly: architecture, contracts, threat models, benchmark designs, deployment/recovery plans, migration plans, SDK/interface designs, acceptance protocols, research comparisons, and similar durable outputs.

Implementation work should still be coordinated so it does not destabilize the active release candidate. Future artifacts are allowed to mature ahead of implementation.

## Canonical files

- `ARTIFACT_REGISTRY.json` — machine-readable canonical state.
- `VERSION_ARTIFACT_MATRIX.md` — human-readable milestone view.
- `WORKER_PACKET_BACKLOG.md` — execution packets that advance artifacts.
- `WORKER_PERFORMANCE.json` — worker calibration by packet size.
- gate-specific protocols/evidence indexes — artifact-specific acceptance details.
