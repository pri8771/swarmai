# Fable 5.1 planning assignment — V1.7 through V3.0

Use this file as the authoritative short launch prompt.

Work in `pri8771/swarmai`.

PLANNING BRANCH: `fable/v3-planning`

Do all planning/consolidation commits on `fable/v3-planning`. Treat `coordination/swarm-control` as read-mostly live truth during this pass because the active implementation worker is still heartbeating there. Do NOT edit the active Cursor implementation branch or its heartbeat/status files. At finish, leave the planning branch ready for ChatGPT lead review; do not merge it yourself.

Follow the root `CLAUDE.md` and the canonical coordination branch. First recover relevant past Claude/Fable/ChatGPT conversation memory for SwarmAI intent, then verify every current-status claim against live Git. Check the active heartbeat, latest lead review, artifact registry, and current packet before planning.

## Assignment

You are the architecture/planning worker for this pass. Do NOT start broad V1.7–V3 implementation.

Create/refine the definitive artifact-oriented execution system that lets a less-capable worker (benchmark: Sonnet 4.6) implement packets correctly without inventing architecture.

Priorities:
1. shortest truthful path to V1.7 implementation-complete + live-checkpointed;
2. cement V1.8–V2.3 so V1.7 work will not cause rearchitecture;
3. define V3 contracts/invariants/interfaces enough to preserve compatibility;
4. fully specify the next ~20 dependency-ready micro-packets; progressively less detail farther out.

## Requirements

- Reuse existing repo plans; consolidate rather than duplicate.
- Keep tasks predominantly tiny/SP1–SP2-like: one artifact concern, ~1–3 production files, focused tests.
- Every packet needs: artifact, dependencies, likely code surfaces, exact behavior, negative tests, evidence/live gate, exit condition.
- Separate implementation-complete, live-checkpointed, verified, accepted, external-pending, and wall-clock-pending.
- Start time-bound campaigns as early as dependencies permit; never backfill time.
- Preserve one IMPLEMENTATION-worker/one-heartbeat topology unless operator changes it. This Fable pass is planning-only and may run while Cursor implements because Fable must not touch product implementation or the active heartbeat.
- Use donor branches selectively; never wholesale-merge legacy coordination.
- Default zero spend; no main merge/public release/destructive production action.
- No second scheduler/authority DB/permission system unless a documented gap proves it necessary.
- Keep machine-readable DAGs in sync with human plans.
- Do not self-accept artifacts.

## Token/model efficiency

- Read `SESSION_START.md`, heartbeat/status, active queue, and router first.
- Do not reread unchanged large docs unless routed by the active task.
- Prefer Git search/diff/targeted reads.
- If subagents/models are available, use cheaper/lower models for bounded mechanical audits, indexing, file mapping, or consistency checks. Reserve Fable 5.1 for architecture, cross-system reasoning, safety, acceptance design, and final synthesis.

## Deliverables in Git

On the isolated planning branch, update/consolidate the proposed canonical coordination system so it contains:
- concise current-state/handoff truth;
- artifact DAG through V3.0;
- detailed next ~20 micro-packets;
- dependency graph;
- code ownership/surface map;
- migration ordering;
- test/negative/live-evidence matrix;
- wall-clock/external gates;
- model-routing/delegation recommendations;
- open decisions/freeze points;
- first executable worker queue after planning review.

Do not create duplicate plan files when an existing canonical file can be updated.

## Finish

When the planning branch is coherent, stop broad planning work and return only:
- planning branch name and exact Git SHA(s);
- audited current version position;
- files updated/consolidated;
- packet/artifact counts;
- critical path to V1.7, V2.3, V3.0;
- first 5 executable micro-packets;
- human/external blockers;
- recommended worker model + effort for execution;
- `READY_FOR_LEAD_REVIEW`.
