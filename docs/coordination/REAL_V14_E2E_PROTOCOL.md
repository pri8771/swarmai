# V1.4 real end-to-end mission protocol

Status: accepted protocol / execution not yet complete
Owner: ChatGPT engineering lead
Artifact: ART-V14-REAL-E2E
Priority: immediate

## Owner rule

V1.4 is not complete until SwarmAI completes at least one real end-to-end mission.

This artifact is mandatory in addition to the existing G12/G13/G14/LIVE-142 gates. It does not weaken or replace them.

## Purpose

Prove that the actual product can receive an unfamiliar real task, execute real model/tool work through the operational path, produce a useful result, and preserve review/apply boundaries.

The run must not use demo data, seeded answers, known-answer substitution, mock-success state, stubbed provider adapters, fake worker output or a test-only execution path.

## Real mission — default scenario

Use the current SwarmAI repository itself as the real work target.

Mission objective:

> Audit a bounded current SwarmAI subsystem for one real correctness, reliability or security defect. Do not tell the agents what the defect is. Inspect the actual repository, identify one defensible issue, propose a minimal patch in an isolated worktree, add or update a regression test, run the relevant test/check, and submit the result for independent review. Do not modify or merge the primary checkout.

Preferred bounded target:
- a current operational/runtime subsystem, not documentation-only work;
- small enough to finish within a bounded local mission;
- not one of the exact defects explicitly supplied to the model in recent worker packets.

If this default target would leak a known answer, choose another bounded current subsystem and record why.

## Required execution mode

- operational / real local execution;
- zero additional spend;
- actual installed local model route(s), inventoried before the run;
- all model calls through the governed broker;
- actual repository reads/tools;
- actual isolated worktree/diff;
- actual regression/check command;
- no automatic primary checkout apply;
- no main merge;
- no paid/remote fallback.

Remote providers are not required for this smoke artifact. G12 remains a separate gate.

Formal G13 qualification is not required to run this smoke. Any unqualified route must be labeled experimental/not-qualified and cannot be used to claim G13/G14 role qualification.

## Pre-run freeze

Record before execution:
- exact candidate SHA;
- exact command/API/CLI/UI entrypoint;
- execution mode;
- project/mission ID;
- exact local model IDs/routes available;
- broker configuration identity;
- allowed tools/scopes;
- max model calls;
- max wall time;
- max graph nodes/active sessions;
- expected output contract;
- zero-spend setting;
- no-known-answer/no-fixture declaration.

Do not change pass criteria after seeing model output.

## Minimum pass criteria

1. Mission is created through an operational product surface and persists with a real mission ID.
2. At least one actual local model inference executes through the governed broker. Evidence includes exact route/model, timestamp and available usage accounting.
3. The model is not supplied the expected defect/patch/answer.
4. SwarmAI actually inspects current repository content using permitted tools.
5. Result identifies a concrete issue with file/symbol/evidence references that independent lead review can verify.
6. If a patch is proposed:
   - changes occur only in an isolated worktree/sandbox;
   - a regression/check is added or selected;
   - the relevant real test/check command executes;
   - result includes pass/fail truthfully.
7. Review/acceptance controls the result. No automatic apply to primary checkout.
8. Cost remains $0.
9. Evidence is bound to exact candidate/config/mission/model identities.
10. ChatGPT independently reviews whether the issue is real and whether the result is useful/correct.

A model producing text that merely sounds plausible does not pass.

## Stronger V1.4-adaptive evidence when available

The real mission should also record whether:
- the planner created multiple tasks from the goal;
- evidence caused a new task/specialist to be added;
- a reviewer challenged/revised the result;
- graph contraction/stop occurred after convergence;
- multiple actual model configurations participated.

These observations are valuable, but this smoke artifact must not falsely claim the full G14 live-adaptive gate unless the existing G12/G13 prerequisites and G14 protocol are also satisfied.

## Evidence bundle

Create:
- `docs/evidence/v14-real-e2e/<run-id>/manifest.json`
- mission record/export
- broker/model-call receipt summary
- tool/action receipt summary
- task/graph history
- patch/diff reference if produced
- exact test/check output summary
- cost/usage summary
- independent lead review note

Never commit secrets, full prompts containing private data, raw credentials or browser/session state.

## Failure behavior

A failed real mission is useful evidence:
- preserve it;
- classify the failure;
- create a bounded repair packet;
- rerun a new preregistered attempt after repair.

Do not overwrite the failure or turn it into a pass.

## Completion rule

ART-V14-REAL-E2E may become verified only after an actual non-mock run and independent lead review.

V1.4 may not be called complete without this artifact verified, even if all synthetic/offline tests are green.
