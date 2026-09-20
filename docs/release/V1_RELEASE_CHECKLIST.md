# V1.0 Release Checklist

Use before any **authorized** public launch (not for the V1 stop-gate Draft PR).

## Must pass

- [ ] `uv run swarm release first-run`
- [ ] `uv run swarm release freeze`
- [ ] `uv run swarm release harden`
- [ ] `uv run swarm release verify`
- [ ] `uv run swarm release validate`
- [ ] `uv run swarm release demo-suite`
- [ ] `uv run pytest tests/contracts tests/product tests/release -q`
- [ ] Zero-spend proofs show `cost_usd: 0.0`
- [ ] No `.env` / secrets tracked in git
- [ ] `CHANGELOG.md` updated
- [ ] `docs/v1.0/STATUS.md` updated
- [ ] Explicit human approval to merge / tag / publish

## Must not claim without evidence

- [ ] cloud-operating
- [ ] statistically live-qualified
- [ ] public launch complete

## Stop gate (P71)

Draft PR only. **Do not** merge, tag, or launch until an operator explicitly
authorizes the public launch.
