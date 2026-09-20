# V1.4 evidence index (worker; not lead-accepted)

**Candidate tip:** pending push (FIX-003 identity + G12/G14 local $0)  
**Prior green tip:** `ca6d425553420cd9f1be2dd7434c110ec9912eef`  
**Updated (UTC):** 2026-09-20T22:51:33Z  
**Login:** Not logged in · SKIP uncleared · no merge/spend/launch

| Gate | Packet | Index / binder | Live claimed? |
|------|--------|----------------|---------------|
| G10 | FIX-001–005 | [`g10/LEAD_ACCEPT_PACKAGE.md`](./g10/LEAD_ACCEPT_PACKAGE.md), [`g10/findings-resolution-matrix.md`](./g10/findings-resolution-matrix.md) | CI green prior tip; **FIX-003 identity on tip (tests pass); lead accept pending** (not invented) |
| G11 | RUN-111 | [`g11/EVIDENCE_INDEX.md`](./g11/EVIDENCE_INDEX.md) + `g11/multisurface-three-tasks.json` | Residual multisurface $0 evidenced; **not lead-accepted** |
| G12 | INF-121 | [`g12/EVIDENCE_INDEX.md`](./g12/EVIDENCE_INDEX.md) + `inf-121/*` | Local admission+reconcile added; **remote dual live-blocked** |
| G13 | EVAL-131 | [`g13/EVIDENCE_INDEX.md`](./g13/EVIDENCE_INDEX.md) + `eval-131/*` | Provisional; **not qualified**; volume paused per LEAD-010 |
| G14 | SWARM-141 | [`g14/EVIDENCE_INDEX.md`](./g14/EVIDENCE_INDEX.md) + `swarm-141/*` | Offline admission-gated expand/contract added; **live multi-planner not claimed** |
| G14f | LIVE-142 | — | Not started |

Also: [`GATE_MATRIX.md`](./GATE_MATRIX.md), `fix-004/*`, `db-local/ready.json`.
