# SwarmAI V2.0 Status — Implementation-complete candidate (lead accept USER_ACTION)

**Date:** 2026-09-25  
**Tip:** `origin/dev` @ `dd7726eb8c22986ef72847994c8e435a81a869b6`  
**Schema head:** `a20pursuitpersist0001`  
**CandidateManifest:** rebound to tip (V20-E01) — **not** lead-accepted  
**Public launch:** **NO** (track authorized; not claimed complete)  
**Spend:** zero (`SWARM_ALLOW_PAID=false`)  
**Lead accept:** **false** — see `docs/evidence/v20/LEAD_ACCEPT_PACKAGE.md`  
**Acceptance campaign:** freeze + harness landed — S01–S11 deterministic green; S12 `blocked_live_grant`; **versions not accepted**

## What landed

- CandidateManifest freezer (`src/swarm/release/candidate.py`) rebound to tip `dd7726eb` / `a20pursuitpersist0001`
- FAST_TRACK L1–L6 eng on tip (#61/#63/#62/#64/#65/#60)
- Lower-version V1.5–V1.9 implementation packages on tip
- Evidence-grounded support matrix, security control map, performance harness receipts,
  and frozen reliability protocol under `docs/evidence/v20/`
- **Lane F:** frozen §10 campaign (`benchmarks/v20_acceptance/scenarios.freeze.json`),
  harness (`src/swarm/acceptance/`), matrices, `docs/v2.0/ACCEPTANCE_CAMPAIGN.md`

## Not claimed

- Accepted V1.7 / V1.8 / V1.9 / V2.0 (harness explicitly forbids)
- Elapsed reliability campaign results
- Invented lead accept or LiveGrant
- Two-host proof from local processes
- V2.0 eng depth complete (see Project Context `internal/v20-gap-audit.md` E03–E06)
