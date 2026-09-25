# SwarmAI V2.0 Status — Implementation-complete candidate (lead accept USER_ACTION)

**Date:** 2026-09-25  
**Public launch:** **NO** (track authorized; not claimed complete)  
**Spend:** zero (`SWARM_ALLOW_PAID=false`)  
**Lead accept:** **false** — see `docs/evidence/v20/LEAD_ACCEPT_PACKAGE.md`  
**Acceptance campaign:** freeze + harness landed (Lane F) — **versions not accepted**

## What landed

- CandidateManifest freezer (`src/swarm/release/candidate.py`)
- Lower-version V1.5–V1.9 implementation packages on tip
- Alembic head `a18tov30schema0001` (single linear head)
- Evidence-grounded support matrix, security control map, performance harness receipts,
  and frozen reliability protocol under `docs/evidence/v20/`
- This-session zero-spend proofs: offline suite, Ollama loopback canary, local recovery drill,
  release harden/first-run/freeze/demo-suite (`docs/evidence/launch/`)
- **Lane F:** frozen §10 campaign (`benchmarks/v20_acceptance/scenarios.freeze.json`),
  harness (`src/swarm/acceptance/`), matrices, `docs/v2.0/ACCEPTANCE_CAMPAIGN.md`

## Not claimed

- Accepted V1.7 / V1.8 / V1.9 / V2.0 (harness explicitly forbids)
- Elapsed reliability campaign results
- Invented lead accept or LiveGrant
- Two-host proof from local processes
