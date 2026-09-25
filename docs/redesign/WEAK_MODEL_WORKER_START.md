# Weak Local Model Worker Start

You are an implementation worker. Complete exactly ONE atomic artifact.

## Startup
1. Read `docs/redesign/ARTIFACT_BACKLOG.yaml`.
2. Read `docs/redesign/AI_NATIVE_ARTIFACT_PROTOCOL.md`.
3. Locate the assigned packet in `docs/redesign/backlog/`.
4. Confirm every dependency has accepted evidence.
5. Read only the packet's listed inputs plus direct dependency contracts/tests.

## Rules
- Do not redesign the packet.
- Do not work on a second packet.
- Do not refactor unrelated code.
- Do not change files outside packet outputs/required existing target files.
- If an exact output placeholder such as `<next>` or `<component>` exists, resolve it mechanically from repository convention discovered by E00; if there is more than one reasonable choice, stop as blocked and request a decision artifact.
- Reuse existing repository code when the E00 gap register says reuse/adapt.
- Never create a second scheduler, authority store, permission system, or inference framework when an accepted reuse path exists.
- Do not claim live evidence from mocks.
- Do not invent credentials, costs, token counts, model versions, or success.
- A failing test remains a failed run even if a later rerun passes.

## Execution
1. Restate the packet goal in one sentence.
2. Inspect inputs.
3. Make the smallest implementation.
4. Run the packet test.
5. Run the nearest existing focused regression tests for the touched module.
6. Record evidence at `docs/redesign/evidence/<PACKET_ID>.md`.

## Evidence format
```md
# <PACKET_ID> Evidence
Status: PASS | FAIL | BLOCKED
Commit: <sha or UNCOMMITTED>
Inputs read:
- ...
Files changed:
- ...
Commands:
- command
  - exit: 0
  - result: concise factual result
Acceptance checks:
- [x] ...
Regressions:
- ...
Known limitations:
- ...
```

Stop after evidence. Another worker or orchestrator decides what becomes ready next.
