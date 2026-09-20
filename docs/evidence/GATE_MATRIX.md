# V1.4 gate matrix (worker view — not lead acceptance)

Updated: 2026-09-20T22:20:00Z
Draft PR: https://github.com/pri8771/swarmai/pull/14 (do not merge)
Candidate tip: `f75c6cb5bb8e0d2d2d2c0c6e4061fe2909f11efc` (+ pending evidence tip)
LEAD-009 code: `108145ea…`
cursor agent status: Not logged in (SKIP_CURSOR_PROBE not cleared; spawn not resumed)
CI: tip `f75c6cb…` run `35539853498` **success** (prior); new evidence tip CI pending

| Gate | Packet | Implemented | Live evidence | Lead accepted | Notes |
|------|--------|-------------|---------------|---------------|-------|
| G10 | FIX-001–005 | LEAD-009 #1–6 + CI green | [`g10/LEAD_ACCEPT_PACKAGE.md`](./g10/LEAD_ACCEPT_PACKAGE.md) | **no** | Packaged for lead accept |
| G11 | RUN-111 | yes | accept-controls + restart-reopen + default-path-not-parser | **no** | Parser fixture-only |
| G12 | INF-121 | partial | local concurrent + kill-fallback | **no** | Remote dual live-blocked |
| G13 | EVAL-131 | screening | S/M/L/XL dual + third model S+M; 60 cells n≥5 $0 | **no** | Provisional; not qualified |
| G14 | SWARM-141 | prep | offline graph/scale/elastic + evidence-exchange | **no** | Live multi-planner not claimed |
| G14f | LIVE-142 | not started | — | **no** | |

Rules: no invented passes; missing live capacity = live-blocked.  
Master index: [`EVIDENCE_INDEX.md`](./EVIDENCE_INDEX.md).
