# SwarmAI Release Candidate (offline-verified)

**Label:** `offline-verified-release-candidate`  
**Not:** cloud-operating, live-qualified, or publicly launched.

## What this RC includes

- Pinned `uv.lock` + Python 3.12
- Migrations (`alembic`)
- Mock demos (parser-issue, self-development, load/chaos)
- Operator console (`apps/console`)
- Local deploy profiles + recovery sample
- License/notice: see repository root licensing notes; no paid Conductor required for mock path

## Fresh-install path

```sh
cd /path/to/swarm-ai
uv sync
uv run pytest tests/contracts tests/selfdev tests/regressions -q
uv run swarm release verify
uv run swarm demo parser-issue --mode mock --report-dir var/reports/fresh-install
```

## Matrix (honest)

| Claim | Status |
|---|---|
| Implemented | P01–P21 offline modules |
| Offline-tested | yes |
| Live-tested | **no** |
| Qualified (live cells) | **no** |
| Deployed to cloud | **no** |
| Still needed | provider zero-charge keys; optional cloud host auth |

## Non-goals of this RC

- No public launch
- No purchase of hosting
- No push of release tags without explicit authorization
- No secrets or personal deployment config in the tree
