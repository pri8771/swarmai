# Future prep packet ID reconciliation

Date: 2026-09-21
Status: PLANNING ONLY

The prep catalog uses coarse phase IDs such as V18-01 and V23-01 for readability.
Where canonical artifact documents already define implementation packet IDs, those canonical IDs win.

## V1.8

Prep group V18-01 maps primarily to:
- V2A-018a — site authority model + guard.
- V2A-018d — stale epoch/split-brain negatives.

Prep group V18-02 maps to:
- V2A-018b — backup manifest + local DB/artifact backup CLI.
- V2A-018c — restore/reconcile CLI.

Prep group V18-03 is the integrated drill/evidence phase after V2A-018a-d.

## V1.9

Prep group V19-01 maps to:
- V2B-019a — manifest models/validation.
- V2B-019b — entry-point registry for one extension kind.
- V2B-019c — migrate one built-in tool/provider behind interface.
- V2B-019d — install/disable/compatibility tests.

V19-02/03/04 remain prep group labels for install/upgrade/external-install/selfdev acceptance work unless canonical coordination later assigns exact packet IDs.

## V2.3

Canonical ART-V23-OPS-PLATFORM packet IDs:
- V23A-001 — scheduler decision schema + durable project/mission deficit records.
- V23A-002 — weighted deficit scheduler behind existing admission boundary.
- V23A-003 — restart/anti-amplification regressions.
- V23B-001 — capability-pack manifest/validator + project enablement contract.
- V23B-002 — export/import bundle schema + secret/authority stripping.
- V23B-003 — trace/read model for scheduler/effect/artifact graph.
- V23A-004 — fleet trust/placement/drain policy.
- V23X-001 — frozen multimission fairness benchmark manifest.

The more granular ART-V23-MULTIMISSION-SCHEDULER draft also decomposes V23A-002/003 into 002a/002b/002c and 003a/003b. At implementation time, the lead should freeze one consistent granularity in canonical coordination before assigning work.

Prep groups map:
- V23-01 -> V23A-001, V23A-002*, V23A-003*, scheduler portion of V23X-001.
- V23-02 -> V23B-001.
- V23-03 -> V23B-002.
- V23-04 -> V23B-003.
- V23-05 -> V23A-004.
- V23-06 -> V23X-001 + integrated evidence/review.

## V3 persistent objectives

Canonical ART-V30-OBJECTIVE-CONTRACT packet IDs:
- V30A-001 — objective/version + TriggerReceipt repository/dedupe.
- V30A-002 — schedule occurrence/restart/missed-run reconciliation.
- V30A-003 — authenticated event/replay/cross-project validation.
- V30A-004 — MissionProposal + normal mission-admission bridge.
- V30A-005 — pause/revoke/expiry/stop fencing.
- V30A-006 — V2.3 fairness/resource integration + anti-amplification tests.
- V30A-007 — learning-candidate version/authority diff/rollback integration.
- V30A-008 — audit/status/operator surface.

Prep V30-01 is the coarse umbrella for V30A-001 through V30A-008.

## V3 learning/allocator/selfdev/ecosystem/audit

The current canonical artifact docs define artifacts/contracts but not a fully frozen packet ID set for all these source tranches.

Prep group labels V30-02 through V30-07 must not be treated as canonical packet IDs until the lead freezes a packetization in coordination.

## Rule

When executing:
1. canonical artifact contract;
2. current coordination packet ID;
3. prep grouping;
in that order of authority.

## Machine-readable form (Fable planning pass, 2026-09-21, proposed)

The mapping above now lives in the DAG files so it can be checked:
- `V17_TO_V23_PACKET_QUEUE.json`: each packet's `aliases` lists its contract-embedded ID(s) and coarse phase ID.
- `FUTURE_EXECUTION_GRAPH_V18_TO_V30.json`: each coarse phase group lists `maps_to` execution IDs; `v30_packets` holds the canonical `V30A-001…008` and a **proposed** packetization (`V30B`–`V30F`, `V30X`, flagged `proposed: true`, `requires_lead_freeze: true`) for the tranches this document says have no frozen IDs yet.
- The three dangling placeholders (`V1.5-result-fencing`, `V1.7-effect-boundary`, `V16-knowledge`) were replaced by real packet IDs (`R15`, `R34`/`R33`, `R25`).
- `tools/validate_plan.py` fails on any unresolved ID, cycle, alias collision, unknown artifact, or uncovered V1.7–V3.0 registry artifact.

The authority order in **Rule** is unchanged.
