# V1.4 gate matrix (worker view — not lead acceptance)

Updated: 2026-09-20T21:50:00Z
Draft PR: https://github.com/pri8771/swarmai/pull/14 (do not merge)
Candidate tip: `3b0011f0605573ab77318981691f588ac72f912f`
LEAD-009 code: `108145ea…`; package tip: `6dd568c…` / `0ba0913…`
cursor agent status: Not logged in (SKIP_CURSOR_PROBE not cleared; spawn not resumed)
CI: tip `3b0011f…` run `35539303334` **success** (offline+console+live-gated notice)

| Gate | Packet | Implemented | Live evidence | Lead accepted | Notes |
|------|--------|-------------|---------------|---------------|-------|
| G10 | FIX-001–005 | LEAD-009 #1–6 + CI green | [`g10/LEAD_ACCEPT_PACKAGE.md`](./g10/LEAD_ACCEPT_PACKAGE.md) | **no** | Packaged for lead accept |
| G11 | RUN-111 | yes | accept-controls + restart-reopen + default-path-not-parser | **no** | Parser fixture-only; default path re-verified |
| G12 | INF-121 | partial | local concurrent + kill-fallback | **no** | Remote dual live-blocked |
| G13 | EVAL-131 | screening | S+M × 6 families × 2 models n=5 $0 (24 cells) | **no** | Provisional; not qualified; L/XL open |
| G14 | SWARM-141 | prep | offline graph/scale/elastic + evidence-exchange | **no** | Live multi-planner not claimed |
| G14f | LIVE-142 | not started | — | **no** | |

Rules: no invented passes; missing live capacity = live-blocked.  
Master index: [`EVIDENCE_INDEX.md`](./EVIDENCE_INDEX.md).
