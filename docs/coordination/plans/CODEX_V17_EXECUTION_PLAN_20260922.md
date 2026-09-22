# SwarmAI — V1.7 execution plan

Target: genuine SwarmAI V1.7, then stop. Current executable phase remains
V1.7 even where historical files describe later ceilings.

## Baseline

- Accepted R28d-2 candidate: `6dbf8c43463cbdbd8c87561af2abcdde59969765`.
- R28d-2 wires worker effects through the local gateway and has focused,
  offline, and owned-PostgreSQL evidence.
- Current released artifact: exactly one `R28d live_local` brokered mission,
  private and incremental-$0, with action receipts and cleanup.
- Remote GitHub Actions cannot start its hosted runners because of the account
  billing/spending gate; this remains external CI evidence, not a source error.

## Ordered path

1. **R28d host/worktree preflight.** Use an isolated R730 checkout at the
   accepted source, co-located with the already-running local Ollama service.
   Verify the source, worktree isolation, existing model identity, route, and
   zero-cost policy without inference. The source's loopback-only guard stands:
   do not tunnel a LAN endpoint or weaken it.
2. **One R28d live-local mission.** Run exactly one bounded throwaway-target
   mission through the broker and action gateway. Record source SHA, model/route,
   request count, $0 cost, action receipt IDs, fs/proc receipt coverage, changed
   files, and cleanup state. Stop on authentication, cost, scope, or model
   failure; record the blocker rather than retrying outside the assignment.
3. **R28d evidence review.** Package under `docs/evidence/v17-recovery/R28d/`,
   run deterministic validators, and request the reserved lead review. Do not
   merge, deploy, schedule, or advance a later packet before disposition.
4. **Remaining V1.7 packets.** Follow the existing packet DAG after each
   independent release/review: tool/browser session paths, scoped knowledge,
   real external checkpoint only with its separate action approval, integrated
   recovery/mission proof, and operator runbook. Preserve the single existing
   heartbeat stream.
5. **V1.7 review package.** Supply a running private/local candidate, actual
   mission/recovery/knowledge/action receipts, exact source/evidence identities,
   supported integration proof, and accurate operator start/restart/stop
   guidance. Stop at V1.7.

## Current safe implementation work

- R730 preflight is **BLOCKED**: SSH and Git are present, but Python/uv, a
  SwarmAI checkout, and existing repository authentication are absent. See
  `CODEX_R28D_R730_PREFLIGHT_20260922.md`.
- Do not install a runtime, create credentials, proxy the model, or use a
  browser certificate bypass to change that result. Run the released mission
  only after an existing, independently authorized R730 runtime/checkout is
  available and loopback preflight succeeds.
- If the host lacks checkout/auth/runtime access, write the exact blocked
  frontier and continue offline/reviewable V1.7 work; do not proxy the model or
  create a second scheduler.
