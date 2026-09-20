# V1.4 gate matrix (worker view — not lead acceptance)

Updated: 2026-09-20T22:42:30Z
Draft PR: https://github.com/pri8771/swarmai/pull/14 (do not merge)
Candidate tip: `ca6d425553420cd9f1be2dd7434c110ec9912eef`
Feature tip (multisurface): `cc64f46cc8e448bb7826f3ca1691f12841bdd13c`
LEAD-010 repairs tip: `b5ef431aef36212417693ca826024d67d0f19e4f`
cursor agent status: Not logged in (SKIP_CURSOR_PROBE not cleared; spawn not resumed)
CI: tip `b5ef431…` run `35541870705` **success** (prior); tip `ca6d425…` run `35542556517` **success**

| Gate | Packet | Implemented | Live evidence | Lead accepted | Notes |
|------|--------|-------------|---------------|---------------|-------|
| G10 | FIX-001–005 | LEAD-010 repairs on tip `b5ef431…` | [`g10/LEAD_ACCEPT_PACKAGE.md`](./g10/LEAD_ACCEPT_PACKAGE.md) | **no** | Packaged; not invented accepted |
| G11 | RUN-111 | yes + residual execute path | [`g11/multisurface-three-tasks.json`](./g11/multisurface-three-tasks.json) | **no** | 3 unfamiliar extract+triage; console/API/CLI same IDs; $0 |
| G12 | INF-121 | partial | local concurrent + kill-fallback | **no** | Remote dual live-blocked |
| G13 | EVAL-131 | screening paused | S/M/L/XL dual + third model; 60 cells n≥5 $0 | **no** | Provisional; not qualified |
| G14 | SWARM-141 | prep | offline graph/scale/elastic + evidence-exchange | **no** | Live multi-planner not claimed |
| G14f | LIVE-142 | not started | — | **no** | |

Rules: no invented passes; missing live capacity = live-blocked.  
Master index: [`EVIDENCE_INDEX.md`](./EVIDENCE_INDEX.md).
