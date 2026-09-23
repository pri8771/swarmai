# V1.0 Release Checklist

Use before any **authorized** public launch.

**Track date:** 2026-09-23  
**PR:** https://github.com/pri8771/swarmai/pull/41  
**Spend:** `SWARM_ALLOW_PAID=false`

## Must pass

- [x] `uv run swarm release first-run` — pass (this session)
- [x] `uv run swarm release freeze` — pass (this session)
- [x] `uv run swarm release harden` — pass (this session)
- [x] `uv run swarm release verify` — pass (`offline-and-live-evidence-present-validated` at tip bind)
- [ ] `uv run swarm release validate` — re-confirm on **final** tip after CandidateManifest rebind
- [x] `uv run swarm release demo-suite` — pass, `cost_usd: 0.0`
- [x] `uv run pytest tests/contracts tests/product tests/release -q` — pass (plus recovery/objectives suites)
- [x] Zero-spend proofs show `cost_usd: 0.0` — Ollama live canary + demo-suite
- [x] No `.env` / secrets tracked in git — harden clean
- [x] `CHANGELOG.md` updated — accept/launch track entry
- [x] `docs/v1.0/STATUS.md` / `docs/v2.0/STATUS.md` / `docs/v3.0/STATUS.md` updated
- [ ] Explicit human **lead** accept of ART-V20/V3.0 packages — **USER_ACTION** (packages prepared; not invented)
- [ ] Explicit human approval click to **merge / tag / publish** if agent tools are write-blocked

## Must not claim without evidence

- [ ] cloud-operating
- [ ] statistically live-qualified
- [x] public launch complete — **not claimed**; track authorized, lead/merge/tag may remain

## Stop gate

Operator authorized the acceptance/launch **track** after V3.0 implementation-complete.  
Do **not** invent lead accept. Do **not** enable paid spend.  
Merge/tag only when remaining USER_ACTION items are signed or explicitly waived by the lead.
