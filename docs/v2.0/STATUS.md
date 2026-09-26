# SwarmAI V2.0 Status — Implementation-complete candidate (lead accept USER_ACTION)

**Date:** 2026-09-25  
**Tip:** `cursor/sw-v23-integration-460c` @ `10fd924efd866fbaa8ce7348b24aad3019a13ecc` (V2.3 integration; `origin/dev` unchanged at `8e1c0fde`)  
**Schema head:** `a23opsplatform0001` (`CURRENT_SCHEMA_REVISION`)  
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
- V2.0 eng depth complete: E03–E06 and E08–E09 are now implemented and offline-tested with evidence on the V2.3 integration branch (`docs/v2.3/EXIT_CHECKLIST.md`); E10 compose smoke `pass` on a dev VM after the worker healthcheck fix (SW-FIX-COMPOSE; not an operator host); E07's live run and E11 stay open
