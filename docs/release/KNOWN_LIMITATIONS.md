# Known Limitations (V1.0 RC)

- **Not publicly launched.** Awaiting explicit launch approval.
- Cloud provider live generation generally blocked under zero-spend.
- OpenAI deferred (payment-gated).
- Statistical model qualification is provisional (starter archive), not production-qualified.
- Console live mode is partial (capacity merge); fixtures cover primary UX.
- Full Ollama end-to-end missions are available but the V1 matrix uses bounded
  local proofs (journey, permissions, reliability, recovery, planner) for cost/time.
- PostgreSQL integration tests require `SWARM_DATABASE_URL`.
- No cloud hosting / multi-tenant SaaS in this RC.
- **Post-RC live slice (2026-09-23):** branch `cursor/v1.4-zero-spend-slice-main` lands G10 honesty + local
  brokered $0 inference off main. `swarm release verify` now fail-closes without tip-bound
  `var/evidence/offline_ci_pass.json` and `live_local_pass.json` (FIX-003). That failure means
  evidence not bound — not that packaging is absent. G12 remote dual, G13 qual, live G14,
  LIVE-142, lead accept, and FIX-004 Cursor CLI login remain open.
