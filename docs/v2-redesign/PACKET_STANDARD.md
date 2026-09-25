# Atomic Subtask Packet Standard

Every executable packet MUST use this shape:

```yaml
id: E##-T##-S##
title: one imperative outcome
status: READY|BLOCKED|IN_PROGRESS|DONE
depends_on: []
reads: [exact/path]
writes: [exact/path]
tests: [exact command]
constraints: [no unrelated refactor]
acceptance: [binary observable condition]
```

Then include WHY, INPUT CONTRACT, IMPLEMENTATION STEPS, TEST CASES, FAILURE/STOP CONDITIONS, RETURN.

## Mechanical requirements
- WHY: 1-3 sentences.
- INPUT CONTRACT: exact types/functions/events consumed.
- IMPLEMENTATION STEPS: numbered edits/commands. Never say "design", "figure out", "improve", "make robust", or "handle edge cases" without enumerating them.
- TEST CASES: exact fixture/input/expected output.
- STOP: list ambiguity conditions that require a blocker instead of guessing.
- RETURN: changed files, focused test output, commit SHA, limitations.

## Universal rules
1. Search target package for an equivalent first; E00 IMPLEMENTATION_MAP becomes authoritative.
2. Extend compatible existing code. Never create a second scheduler, authority DB, permission system, provider registry, or event bus.
3. Public interfaces typed in repository style.
4. DB change = model + Alembic migration + repository/store test.
5. External side effect = stable operation_id + retry/idempotency behavior.
6. Secrets are handles/references, never prompts/logs/analytics/lessons/Git.
7. Inference calls emit normalized usage metadata; missing = null/unknown, never zero.
8. Tool calls emit execution metadata + evidence pointer.
9. Organizational changes emit durable events.
10. Pause/stop checked at assignment boundaries and before external side effects.
11. Never weaken acceptance because a model says success.
12. Prefer existing/open-source dependencies over rebuilding infrastructure.

## Validation
Focused test first, then:
```bash
uv run ruff check <changed-python-paths>
uv run mypy src/swarm
uv run pytest <focused-tests> -q
```
Full suite at task/epic gates unless explicitly required.

## Size
XS = schema/model/test only.
S = one behavior + tests.
M = split it. No weak-model packet should intentionally exceed S.

Valid: add AgentIdentity model + serialization test; add one DB migration; implement one adapter health probe; add memory-edge repository methods; add MCP discovery normalization test.
Invalid: "build memory", "add MCP", "make agents autonomous", "create cloud UI".

## Review
Implementer proves packet tests. Separate reviewer/task gate checks contract compatibility. Reviewer does not rewrite implementation in the same review packet.
