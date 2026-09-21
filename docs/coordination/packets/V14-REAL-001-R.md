# V14-REAL-001-R — repair generic implement materialization, then rerun real E2E

- Artifact: `ART-V14-REAL-E2E`
- Session: Cursor A / HOST-MAC-DEV / `cursor/v2-runtime-lane`
- Story points: SP2
- Priority: immediate Session-A packet
- Trigger: failed real mission `V14-REAL-001` / mission `d9379d80277644998353a9ca3614eba7`
- Failed evidence tip: `57afbd6ce19dee694621be21898d25a40cd066db`
- Required protocol: `docs/coordination/REAL_V14_E2E_PROTOCOL.md`
- Intended artifact transition: remain `drafting` until a new real run independently passes; do not self-accept.

## Failure to repair

The real operational mission used actual local Ollama inference through the governed broker at $0 and correctly preserved review/apply boundaries, but the implement step produced model text with no material worktree diff. Review rejected the run as `implementation_missing` / `wrong_result_rejected`. Preserve that failed evidence unchanged.

## Required repair

1. Trace the generic mission implementation path from task goal/context -> model response -> patch/file materialization -> isolated worktree diff.
2. Fix only the generic materialization/validation defect that caused a valid model-produced implementation candidate to yield an empty diff. Do **not** hard-code `token_hash.py`, its defect, an expected answer, a target function, or a canned patch.
3. A model response that cannot be parsed/applied safely must remain an honest failed implementation result with a specific reason. Never synthesize a fallback answer.
4. Keep all edits in the mission worktree. No automatic primary-checkout apply, no main merge.
5. Add a deterministic regression using a temporary/held-out repository fixture and a model-response-shaped patch that is unrelated to the previous `token_hash.py` mission. The test must prove:
   - valid generic patch materializes into the isolated worktree and creates a non-empty diff;
   - malformed/no-op output is rejected rather than accepted;
   - supplied known-answer fallback is absent.
6. Run focused mission/runtime/worktree tests plus Ruff/mypy for changed source; push a source SHA and request lead review. Preserve all failed test evidence.

## New real-run requirement after source repair

After the source repair is green, preregister and execute a **new** V1.4 real E2E attempt against a different bounded current subsystem than the failed `token_hash.py` run. The model must not be told the defect or patch.

The new attempt must include:
- exact candidate SHA and operational entrypoint;
- observed local model inventory and exact route/model;
- governed broker receipts and $0 accounting;
- actual current repository/tool reads;
- isolated worktree and real material diff when a defect is proposed;
- added/selected real regression/check with actual command/result;
- review rejection if the result is unsupported/wrong/no-op;
- no primary checkout mutation and no merge;
- immutable evidence bundle under a new run ID.

Do not reuse or overwrite `v14-real-001` evidence. A second failure is evidence, not a reason to alter pass criteria.

## Acceptance for this packet

The packet is reviewable when both are supplied:
1. generic source repair + unrelated regression proving correct materialization/fail-closed behavior; and
2. a new preregistered real local mission result bound to the repaired candidate.

`ART-V14-REAL-E2E` becomes verified only if ChatGPT independently confirms that the new actual mission satisfies `REAL_V14_E2E_PROTOCOL.md`. This packet does not claim G12 remote overlap, G13 qualification, G14 live adaptation, or LIVE-142.

## Non-goals / boundaries

- no paid/remote provider use;
- no known-answer fallback or demo mission;
- no provider admission changes;
- no V2A-003c edits in the same patch unless explicitly isolated after this packet is submitted;
- no public deployment, release, main merge, or destructive reset.
