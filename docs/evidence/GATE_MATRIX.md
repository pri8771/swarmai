# V1.4→V3 gate matrix — implementation lane (worker view — not lead acceptance)

**Updated:** 2026-09-23  
**Branch:** `cursor/cloud-agent-1790175458840-642hd`  
**Public launch:** **no**  
**Spend:** zero (`SWARM_ALLOW_PAID=false`)

| Gate | Packet | Implemented on tip | Live evidence | Lead accepted | Notes |
|------|--------|--------------------|---------------|---------------|-------|
| G10 | FIX-001–005 | **yes** | tip-bind pending fresh CI | **no** | FIX-004 Cursor CLI login USER_ACTION |
| G11 | RUN-111 | **partial→landing** | local $0 canary shape; restart proofs transplanted as docs | **no** | |
| G12 | INF-121 | **local only** | Not remote dual | **no** | Remote live-blocked |
| G13 | EVAL-131 | **screening transplanted** | provisional only | **no** | Not qualified |
| G14 | SWARM-141 | **offline prep** | — | **no** | Live multi-planner not claimed |
| G14f | LIVE-142 | **not started** | — | **no** | |
| V1.5–V3.0 | ART-V15+ | in progress per plan | — | **no** | |

Rules: no invented passes; missing live capacity = live-blocked.
