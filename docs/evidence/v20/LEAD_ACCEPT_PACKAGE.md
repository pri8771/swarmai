# V2.0 lead accept package

**Status:** worker-prepared for independent lead review — **not** lead-accepted  
**Branch:** `cursor/v3-accept-launch-e2a1` → PR #41 tip (see `git rev-parse HEAD`)  
**Spend:** `SWARM_ALLOW_PAID=false`  
**Public launch claim:** **no** until lead signs + merge/tag  

This package does **not** invent lead acceptance.

## Required ART-V20 artifacts → evidence

| Artifact | Path / proof | Worker status |
|---|---|---|
| ART-V20-INTEGRATED-CANDIDATE | `docs/evidence/v20/candidate_manifest.json` + Alembic `a18tov30schema0001` | implementation-complete |
| ART-V20-SUPPORT-MATRIX | `docs/evidence/v20/support_matrix.json` | evidence-grounded local + loopback |
| ART-V20-INSTALL-JOURNEY | `uv run swarm release install-check` / `first-run` (session receipts) | executable local |
| ART-V20-UPGRADE-ROLLBACK | `swarm install upgrade-plan` / `rollback-plan` CLI | executable local |
| ART-V20-RELIABILITY-PROTOCOL | `docs/evidence/v20/reliability_protocol_freeze.json` | frozen; campaign **USER_ACTION** |
| ART-V20-SECURITY-REVIEW | `docs/evidence/v20/security_review_map.json` | mapped; independent review **USER_ACTION** |
| ART-V20-PERFORMANCE-BASELINE | `docs/evidence/v20/performance_baseline.json` + mock load/chaos/reliability | protocol executed locally |
| ART-V20-RELEASE-REVIEW | this package + `docs/evidence/launch/` | awaiting lead |

## Zero-spend proofs this session

| Proof | Result | Receipt |
|---|---|---|
| Offline suite (91 passed, 1 skipped) | pass | `var/evidence/offline_ci_pass.json` |
| Ollama loopback canary | pass, `cost_usd: 0.0` | `docs/evidence/launch/ollama_live_canary.json` |
| Recovery local drill | pass | `docs/evidence/launch/recovery_drill_local.json` |
| `swarm release harden/install-check/first-run/freeze/demo-suite` | pass | `docs/evidence/launch/zero_spend_suite_receipt.json` |
| CI offline (mypy fix) | success | runs `35890021376` / `35890028419` |

## USER_ACTION (lead / operator only)

1. Sign lead accept for ART-V20 (and lower ART-* as required).
2. Start wall-clock reliability campaign after freeze — never backfill elapsed time.
3. Independent security/release review.
4. Approve merge to `main` / tag / publish if still desired after review.

## Suggested lead commands

```bash
git fetch origin && git checkout <tip-sha>
gh run view 35890028419
uv run ruff check . && uv run mypy src/swarm
uv run pytest tests/contracts tests/product tests/release tests/recovery tests/objectives -q
uv run swarm release verify
uv run swarm release validate
# optional live:
uv run swarm providers canary --route rt_ollama_default --policy bounded_probe \
  --mode live --billing-known-zero
```
