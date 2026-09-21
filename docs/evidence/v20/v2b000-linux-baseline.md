# V2B-000 Linux baseline evidence

Packet: `V2B-000` / `ART-V20-INTEGRATED-CANDIDATE`  
Host: Linux `cursor` 6.12.94+ x86_64 (not Windows)  
Recorded: `2026-09-21T16:16:00Z`  
Product tip after merge: to be bound at commit time.

## Merge

- Reviewed integration tip only: `cursor/v2-integration@9ce727842446b98cfa55c28c7e70808f57f17d7b`
- Merge commit local: `6830380d10fb942a37efa7416adba2bf49b4e347`
- Parents: `2693bb59d9142a753546ed55ccb787223572ea94` + `9ce727842446b98cfa55c28c7e70808f57f17d7b`
- Incoming commits (no unreviewed runtime V15 history):
  - `c3df96e` feat(ART-V12/V2A-001): close ProductStore operational broker bypass
  - `48a02e3` feat(ART-V11/V2A-002): prove actual API process restart reopen
  - `ee5a066` docs(ART-V11/V2A-002): rebind process-restart evidence to tip SHA
  - `9ce7278` docs(ART-V20/V2A-020a): integration receipt for verified 001/002 only
- Preserved branch-local `SESSION_INSTRUCTIONS.md` and `scripts/coordination/*` (no conflicts).
- `src/swarm/api/store.py` and `src/swarm/cli.py` changed only by the reviewed integration merge, not by extra Lane B edits.

## Commands (Linux equivalent of the Windows baseline)

| Command | Exit | Result |
|---|---|---|
| `uv run ruff check .` | 0 | All checks passed |
| `uv run mypy src` | 0 | Success: no issues found in 139 source files |
| `uv run pytest -q --ignore=tests/integration` | 0 | 287 passed in 18.11s |
| `uv run pytest -q` | 1 | 287 passed, 8 errors in 16.23s |
| `npm --prefix apps/console run lint` | 0 | oxlint exit 0; 2 warnings in `src/App.tsx` |
| `npm --prefix apps/console test -- --run` | 0 | 1 file / 17 tests passed (vitest 1.38s) |
| `npm --prefix apps/console run build` | 0 | `tsc -b && vite build` succeeded |

## Exact pytest -q errors (honest, not skipped-green)

Integration suite requires PostgreSQL. This host has no server on `127.0.0.1:5432`.

```
ERROR tests/integration/db/test_persistence.py::test_migrate_validate_roundtrip
ERROR tests/integration/db/test_persistence.py::test_graph_revision_conflict
ERROR tests/integration/db/test_persistence.py::test_unique_receipt_settlement
ERROR tests/integration/db/test_persistence.py::test_tenant_scope_filtering
ERROR tests/integration/db/test_persistence.py::test_artifact_metadata_without_blob
ERROR tests/integration/db/test_persistence.py::test_commit_before_enqueue_crash
ERROR tests/integration/db/test_persistence.py::test_enqueue_before_ack_replay
ERROR tests/integration/db/test_persistence.py::test_pooled_connection_pressure
sqlalchemy.exc.OperationalError: connection to server at "127.0.0.1", port 5432 failed: Connection refused
```

`SWARM_DATABASE_URL` was not set. This is a real environment miss, not a silenced skip.

## Console notes

- Node `v22.14.0` / npm `10.9.7`
- `npm ci` engine warnings for packages requiring `^22.22.2` (`@asamuzakjp/css-color`, `@asamuzakjp/dom-selector`, `jsdom`, `undici`). Install still succeeded; 0 vulnerabilities.
- oxlint warnings (exit still 0):
  - `src/App.tsx:637:10` `only-export-components`
  - `src/App.tsx:63:5` `set-state-in-effect`

## Not claimed

- Not a Windows Python/console run.
- Not artifact acceptance.
- No main merge / public deploy / spend / force push.
