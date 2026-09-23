# V1.4 gate matrix — zero-spend slice off main (worker view — not lead acceptance)

**Updated:** 2026-09-23  
**Branch:** `cursor/v1.4-zero-spend-slice-main` (base `main` @ `b9141fa`)  
**Source lineage:** selective re-apply from `cursor/v1.4-live-integration-11e2` through LEAD-011 (`a17ae17`); **not** full tip / PR #14 merge  
**Draft PR (upstream unfinished):** https://github.com/pri8771/swarmai/pull/14 — **do not merge blindly**  
**Public launch:** **no**  
**Spend:** zero (`SWARM_ALLOW_PAID=false`)

| Gate | Packet | Implemented on this slice | Live evidence | Lead accepted | Notes |
|------|--------|---------------------------|---------------|---------------|-------|
| G10 | FIX-001–005 | **yes** (source + tests) | LEAD package docs; CI artifact binding pending commit | **no** | FIX-004 Cursor CLI login still open |
| G11 | RUN-111 | **partial** — durable missions, brokered local execute, console IDs | Local Ollama canary `$0` this session; LEAD-012 full package not re-landed | **no** | |
| G12 | INF-121 | **local only** — brokered inference | Not remote dual | **no** | Remote live-blocked |
| G13 | EVAL-131 | **not on slice** | — | **no** | Screening stayed on side branch |
| G14 | SWARM-141 | **not on slice** | — | **no** | Offline prep not re-landed |
| G14f | LIVE-142 | **not started** | — | **no** | |

Rules: no invented passes; missing live capacity = live-blocked.  
Handoff: [`docs/handoff/CURRENT.md`](../handoff/CURRENT.md).  
Abrupt-stop context: [`V1_4_ABRUPT_STOP.md`](./V1_4_ABRUPT_STOP.md).
