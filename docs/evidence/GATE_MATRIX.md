# V1.4 gate matrix (worker view — not lead acceptance)

Updated: 2026-09-20T20:41:48Z
Candidate tip: see branch `cursor/v1.4-live-integration-11e2` HEAD.
Draft PR: https://github.com/pri8771/swarmai/pull/14 (do not merge)

| Gate | Packet | Implemented | Live evidence | Lead accepted | Notes |
|------|--------|-------------|---------------|---------------|-------|
| G10 | FIX-001–005 | yes (CI) | FIX-004 recurring_verified; check-in auth_required | **no** | Lead review pending |
| G11 | RUN-111 | yes | accept-controls + restart-reopen | **no** | |
| G12 | INF-121 | partial | local concurrent + kill-route fallback | **no** | Remote dual-provider live-blocked |
| G13 | EVAL-131 | scaffold + local screening | provisional 1-sample cells | **no** | Underpowered; not qualified |
| G14 | SWARM-141 | not started | — | **no** | |
| G14f | LIVE-142 | not started | — | **no** | |

Rules: no invented passes; missing live capacity = live-blocked.
