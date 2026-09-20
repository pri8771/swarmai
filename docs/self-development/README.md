# Controlled self-development (P19)

Optional pack: swarm proposes a tested improvement as a **patch artifact**.
No auto-merge, auto-deploy, or production writes.

## Commands

```sh
uv run pytest tests/selfdev
uv run swarm demo self-development --mode mock
```

## Guarantees (offline)

- Codegen worker ≠ runtime operator ≠ independent reviewer
- Isolated worktree/branch name only — no main write
- Host secrets not forwarded into sandbox
- Failing tests → rejected
- Privilege-expansion markers / forbidden paths → rejected
- Self-approval of merge impossible (`merged` always false here)
