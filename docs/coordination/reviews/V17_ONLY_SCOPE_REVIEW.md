# V1.7-only delivery scope review

Decision: latest owner scope applied. Product acceptance is unchanged.
Owner requested: focus on getting V1.7 live and stop; provide a Fable prompt and a new ChatGPT lead-conversation prompt.

## Current evidence checked

Fresh GitHub read of cursor/v17-single-session still returned f2b8d5f7dfd65530e73c63438c229b9fa428f922.
The retrieved worker status named R27, reported last meaningful activity 2026-09-21T20:05:50Z, and continued publishing later scheduler timestamps. This is not evidence of new implementation or live V1.7 completion. No local worker/process was remotely inspected in this scope change.
Current execution control, root CLAUDE.md, delivery contract, startup router and execution_guard.py were checked before modification.

## Changes

- EXECUTION_CONTROL.json now has goal_version=1.7, allowed_phases=[v17], no future implementation/planning authority and an explicit stop after V1.7 handoff.
- execution_guard.py rejects forbidden phases before queue loading/selection. V1.7-only CLI mode does not require parked future queue files. Completion does not unlock V1.8-V3.
- CLAUDE.md, SESSION_START.md and FABLE_DELIVERY_CONTRACT.md now point only to V1.7 live delivery and required earlier prerequisites.
- FABLE_DELIVERY_START.md is the short worker prompt; V17_LEAD_CHAT_START.md is the new-conversation lead prompt.
- Required finish includes the real private/local running application URL, launch/restart/stop commands, exact source, source-bound checkpoints including R33c, and honest remaining gates. Public deployment is not authorized.

Historical roadmaps and old STATE/registry authorization metadata are retained as history. The latest owner directive and EXECUTION_CONTROL override their older V3 execution scope; they do not override acceptance evidence.
No application source, artifact acceptance, heartbeat ledger, local process, billing, credentials or external account was changed.

## Validation actually executed

Environment: isolated review container, Python 3.13.5.
The fetched original execution_guard.py was copied exactly and its Git blob identity checked against 6ebf2c8ac0e4b37545e42dfcbfa782602a4a2b47 before the scope patch.
Command: python3 -m unittest -v test_v17_scope
Result: 12 tests passed, including two actual subprocess CLI executions against temporary synthetic queue inputs.
Command: python3 -m py_compile execution_guard.py test_v17_scope.py
Result: passed.

Tested/published Git blob identities:
- execution_guard.py: 811e9788c7665bf01ae0780b34b7d92994f34531
- test_v17_scope.py: 450a03cfb878a8605d47ca43452ab78512dbf26a

Tests cover V1.7 allowed work, V2.3/V3 rejection even with ready packets, no automatic continuation after completion, malformed/broadened scope rejection, legacy compatibility, no mutation, preserved independent review/live-evidence rules, and no future-file requirement in V1.7-only CLI mode.
These are handoff-tool UNIT tests, not product or real-world evidence. Full application/DB/browser/provider/hosted CI tests were not run here. Existing guard tests and current real queue must be rerun on the worker checkout alongside its configured application checks.

## Execution expectation

Fable implements existing V1.7 micro-packets, exercises operational wiring and real-world checkpoints, returns an accessible running candidate and an exact evidence/blocker matrix, then stops. It does not start a new roadmap or continue into V1.8. Required lower-version, review, account, host and wall-clock gates stay truthful; none is implicitly waived by the scope reduction.
