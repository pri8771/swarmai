# SwarmAI Release Candidate (offline-verified)

**Label:** `offline-verified-release-candidate` (V0.9)  
**Not:** cloud-operating, statistically live-qualified, or publicly launched.

## What this RC includes

- Pinned `uv.lock` + Python 3.12
- Migrations (`alembic`)
- V0.1–V0.8 product modules (missions, routing, scale, memory, tools, selfdev, reliability, product UX)
- V0.9 install-check / harden / demo-suite
- Operator console (`apps/console`)
- Local deploy profiles + recovery sample
- User + security docs under `docs/user/` and `docs/security/`

## Fresh-install path

```sh
cd /path/to/swarm-ai
uv sync
uv run swarm release install-check
uv run swarm release harden
uv run swarm release verify
uv run swarm release demo-suite
# or: bash examples/v0_9/run_rc_demo.sh
```

## Matrix (honest)

| Claim | Status |
|---|---|
| Implemented | V0.1–V0.9 modules |
| Offline-tested | yes |
| Live-local tested | partial (Ollama / zero-spend proofs) |
| Cloud live-tested | **no** |
| Qualified (statistical) | **no** |
| Deployed to cloud | **no** |
| Public launch | **no** |

## Non-goals of this RC

- No public launch
- No purchase of hosting
- No push of release tags without explicit authorization
- No secrets or personal deployment config in the tree
