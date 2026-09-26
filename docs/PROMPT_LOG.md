# Prompt log

A short record of planning and coordination prompts that changed repo docs. Append only. Never paste secrets or full transcripts.

## 2026-09-26: V2.3 audit, plan and owner decisions (Cursor cloud agent)

- **Prompt (summary):**
  - First, a read-only audit of swarmai (`main`, `dev`) toward V2.3, with one weak-model-proof prompt per Cursor session.
  - Then a revision for owner decisions D1–D6 and B-01 (Google sign-in for every account; Codex reviewer; SplitSignal is the only cross-repo dependency; sync points; one preflight, nothing blocks partway; plaintext Desktop secrets file; pause lifted).
  - Then coordinator decisions C1–C5 (integration branch `cursor/sw-v23-integration-460c`, IS integration branch `cursor/is-v23-integration-460c`, D-SS1 with unknown cost never zero, `/v1/models` OpenAI list shape, exact `SPLITSIGNAL_*` names).
  - Prompts must not use "as appropriate", "etc.", "similar to" or "if needed" without an explicit rule, and every prompt needs STOP conditions.
  - Commit the plan to `cursor/v23-plan-460c` from `origin/dev`, append-only to the canonical docs. Do not open the PR, and do not touch the executor's integration branch or worktrees.
- **Output:**
  - `docs/plans/v2.3/`: AUDIT, PLAN with a SYNC POINTS table, OWNER_PREFLIGHT, SECRETS_SWARMAI_SECTION, 26 session prompts plus 6 SW-MERGE prompts, and the generator with its validated reference code.
  - DEC-V23-001 in `docs/swarm-mvp/DECISIONS.md`.
  - Append-only updates to `docs/agents/CURRENT.md`, `docs/agents/context.json`, `docs/swarm-mvp/STATE.md`, `docs/handoff/CURRENT.md`, `CONTRIBUTING.md`, `docs/coordination/VERSION_ARTIFACT_MATRIX.md` and `docs/coordination/OWNER_RESUME_TO_V3.md`.
  - Folded in the executor's PROMPT_FIXES entry: a private PostgreSQL database per session.
- **Branch:** `cursor/v23-plan-460c` from `origin/dev` @ `8e1c0fde`. The owner opens the PR.
- **Not done:** no product code change on this branch, no deploy, no spend, no live call. SW-PREAPPROVAL-A3 and A5 are pending (OWNER_PREFLIGHT Part 3).
