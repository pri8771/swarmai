# V1.4 gate matrix (worker view — not lead acceptance)

Updated: 2026-09-20T21:25:04Z
Draft PR: https://github.com/pri8771/swarmai/pull/14 (do not merge)
Candidate tip: `aa6865a74249e046bfe697532accb00390bb5873` 
Prior CI-green docs tip: `3c82e0f…`; LEAD-009 code: `108145ea…`
cursor agent status: Not logged in (SKIP_CURSOR_PROBE not cleared; spawn not resumed)
CI: tip `3c82e0f` runs `35538395519` / `35538397490` **success** (offline+console)

| Gate | Packet | Implemented | Live evidence | Lead accepted | Notes |
|------|--------|-------------|---------------|---------------|-------|
| G10 | FIX-001–005 | LEAD-009 #1–6 + CI green | [`g10/LEAD_ACCEPT_PACKAGE.md`](./g10/LEAD_ACCEPT_PACKAGE.md) | **no** | Packaged for lead accept |
| G11 | RUN-111 | yes | accept-controls + restart-reopen + default-path-not-parser | **no** | Parser no longer default |
| G12 | INF-121 | partial | local concurrent + kill-fallback | **no** | Remote dual live-blocked |
| G13 | EVAL-131 | screening | dataset 5 holdouts/cell; S n=5 partial $0 screening | **no** | Provisional; not qualified |
| G14 | SWARM-141 | prep | offline graph/scale/elastic + evidence-exchange | **no** | Live multi-planner not claimed |
| G14f | LIVE-142 | not started | — | **no** | |

Rules: no invented passes; missing live capacity = live-blocked.  
Master index: [`EVIDENCE_INDEX.md`](./EVIDENCE_INDEX.md).
