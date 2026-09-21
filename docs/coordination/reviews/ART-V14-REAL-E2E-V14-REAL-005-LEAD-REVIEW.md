# Lead review — ART-V14-REAL-E2E / v14-real-005

Date: 2026-09-21
Decision: CHANGES REQUIRED
Reviewed candidate: cursor/v17-single-session @ 9e82a5c5f90f04027e5d2dc1edf7941806205ddd
Evidence packaging tip observed: fe6acbf6097bb32250115c5cd8b6a21acf9d060a
Protocol: docs/coordination/REAL_V14_E2E_PROTOCOL.md

## What passed operationally

The run provides genuine useful runtime evidence:
- real persisted mission ID f876c99e15c643d4a160c026f6ee1c54;
- real local qwen2.5-coder:14b calls through the broker;
- $0 recorded spend;
- actual repository read;
- isolated worktree;
- material diff;
- actual pytest command: tests/mission, 37 passed;
- no primary checkout auto-apply;
- repair round after first no-diff attempt;
- evidence retained.

This proves the materialization/runtime path progressed substantially.

## Why it does NOT verify ART-V14-REAL-E2E

The protocol requires independent lead review that the identified issue and patch are real/useful/correct.

The proposed diff changes:
- route_id=None -> cost.get("route_id")
- model=None -> cost.get("model")

But the actual mission record cost schema contains:
- cost.entries[] where each entry has route_id/model;
- no top-level cost.route_id;
- no top-level cost.model.

Therefore the patch still resolves both values to None for the observed real mission shape. It does not correctly repair the claimed accounting loss.

Additionally, the worker reviewer text references an unrelated inclusive_range_count fix while reviewing this ledger diff. That is evidence of stale/contaminated reviewer context and cannot be trusted as independent semantic review.

The verification command ran tests/mission only. It did not add/run a focused cost-ledger regression proving the claimed defect/fix.

## Required repair

1. Harden review so it must be grounded in the actual diff + target subsystem and rejects unrelated/stale review text.
2. Require a focused regression/check tied to the claimed defect, not only a broad unrelated test directory.
3. Run a NEW preregistered real mission after the repair.
4. The new run must identify a defect whose semantics can be independently verified from repository/data evidence.
5. Preserve v14-real-005 as useful failed independent-review evidence; never convert it to pass.

## Artifact state

ART-V14-REAL-E2E remains drafting / changes required.
No V1.4 completion claim.
