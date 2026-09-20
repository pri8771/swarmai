# P20 Independent review (offline)

**Review ID:** `review_offline_p20`  
**Mock vs live:** offline evidence only — live P15/P16 skip_live

## Readiness distinction

| Layer | Status |
|---|---|
| Software (offline) | ready |
| Accounts provisioned | no |
| Deploy provisioned | no |
| Live-verified | no |

## Checklist (summary)

See `uv run swarm review report` for full JSON. Key lines:

- C04 no-spend canary policy — pass (live zero-charge still unproven)
- C05 qualification nulls — pass
- C08 stale worker authority — pass
- C10 live P15/P16 — **skip_live**
- C12 self-dev privilege expansion blocked — pass

## Findings

| ID | Sev | Status | Owner |
|---|---|---|---|
| F-LIVE-01 | high | blocked_live | operator — needs keys |
| F-REG-01 | medium | mitigated | broker-owner — regression pack |

## Commands

```sh
uv run pytest tests/regressions
uv run ruff check .
uv run mypy src/swarm
uv run swarm review report
```

No paid Conductor / subscription-to-API bypass required for the mock/offline path.
