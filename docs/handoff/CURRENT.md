# Handoff — V1.4 → V3.0 accept/launch track

**Date:** 2026-09-23  
**Branches:** `cursor/v3-accept-launch-e2a1` (work) → `cursor/cloud-agent-1790175458840-642hd` (PR #41)  
**Plan:** `/opt/cursor/artifacts/plans/v1_to_v3_roadmap_e96337c7.plan.md`  
**Spend:** `SWARM_ALLOW_PAID=false` · lead accept **not** invented · public launch **not** falsely claimed  

## Completed this track

| Item | Status |
|------|--------|
| Phases 0–9 implementation-complete | done (prior tip) |
| Offline CI mypy fix | done; CI green `35890028419` |
| Ollama live loopback canary | pass, `$0` |
| Local recovery drill | pass |
| Release harden/freeze/first-run/demo-suite/verify | pass (tip-bound evidence) |
| Lead-accept packages V2.0/V3.0 | prepared |
| Launch checklist worker cells | mostly green; lead/merge clicks remain |

## Still USER_ACTION

- Lead accept of ART-*
- Wall-clock reliability campaign
- Fresh/external install; second-host recovery
- FIX-004 Cursor CLI login; remote dual; LIVE-142; G13 sealed qual
- Merge / tag / publish human clicks if agent write APIs blocked
- Paid spend (forbidden unless later explicit message)

See `docs/evidence/ACCEPTANCE_LAUNCH_TRACK.md`.

---

# Handoff: V2.3 planning (2026-09-26, supersedes the "Still USER_ACTION" routing above for V2.3)

- **Branch:** `cursor/v23-plan-460c` (from `origin/dev` @ `8e1c0fde`); docs only.
- **Plan:** `docs/plans/v2.3/PLAN.md`, `AUDIT.md`, `OWNER_PREFLIGHT.md`, `prompts/`.
- **Integration:** `cursor/sw-v23-integration-460c`. Session PRs target it; `SW-MERGE-<wave>` merges them; the owner merges it into `dev`.
- **Reviewer:** Codex (D2). Every session handoff ends with a "Codex review packet": PR URL, head SHA (`git rev-parse HEAD` = `git ls-remote origin refs/heads/<branch>`), files, focus per AGENTS.md Code Review Rules, requested verdict `RECOMMEND_ACCEPT <sha>` or `REQUEST_CHANGES`.
- **Spend:** $0. Live calls only in SW-X2-S1, once SW-PREAPPROVAL-A3 is approved.
- **Owner actions:** `OWNER_PREFLIGHT.md` Part 3 (A3, A5) and Part 4 (R-1 public-repo secrets, R-2 stale PRs, R-3 integration → `dev` merge).
