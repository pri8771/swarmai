# SwarmAI compact project memory

Curated 2026-09-20 after CURSOR-20260920-020 (ACK LEAD-011). Read this, STATE, V1_4_EXECUTION_CONTRACT and unread/new message pointers; do not reload whole chats. This stores accepted decisions and verified observations, not secrets or proof of unperformed work.

## Owner authorization and product direction

Implementation is approved continuously through V1.4 inclusive: V1.0 repair -> V1.1 -> V1.2 -> V1.3 -> V1.4. Do not ask the operator to start each 0.1. Independent evidence review still gates acceptance. Main merge, release/tag/publication, public deployment, new billing/spend, destructive actions and V1.5+ implementation are not authorized. Stop feature work after V1.4.

SwarmAI is a reusable self-hostable elastic problem-solving runtime. Multiple capable planners/reviewers may coordinate smaller task-qualified workers. Approved inference routes should operate concurrently. Agents can propose specialists/splits/alternatives; software enforces permissions, dependencies and resource admission. Ordinary code/tools are first-class. CrewAI is not mandatory. Reuse sound libraries.

No operational demo data, fake providers/activity, supplied answers, mock-success fallback or quota bypass. Test fixtures may exist only as isolated test/dev fixtures and never count as live proof. The operator prefers zero additional spend; bounded verified-zero-charge live validation is authorized by the V1.4 contract.

## Verified source and CI

Audited main remains `b9141fa3150f853586dede0334a47b344571bc16`. Draft PR #14 tip `6669d37827d487206ee6c71734d4e2c64b475906` (feature `a17ae17e430831eb23d2fafc871244c096ca275d`). Actions `35542951933` + `35543012288` green (offline+console+live-gated notice).

LEAD-010 source repairs (mock cleanup, ownership/bootstrap, release SHA binding, no auto-promote) remain on tip lineage through `b5ef431…`. LEAD-011 FIX-003 evidence-kind identity groups shipped on `a17ae17…` with negatives; awaiting lead re-verify — **not** auto-accepted.

## G10 review — NOT accepted

Near acceptance. Remaining G10 blocker after CURSOR-020:

1. **FIX-004:** `cursor agent status` / `whoami` remain **Not logged in**; `SWARM_HOURLY_SKIP_CURSOR_PROBE` uncleared; no authenticated unattended hourly worker receipts.
2. **FIX-003 identity:** implemented on tip; lead must re-verify before accept (worker packaging ≠ acceptance).

Do not invent G10/G11 lead accept.

## Later gates

G11/RUN-111: residual three unfamiliar tasks console/API/CLI on same durable IDs evidenced at $0 (`ca6d425…`); **not** lead-accepted.

G12/INF-121: local concurrent + kill-fallback + admission-reconcile packaged; required dual remote overlap absent (live-blocked).

G13/EVAL-131: provisional S/M/L/XL + third model screening (~60 cells n≥5); **not** qualified; volume paused.

G14/SWARM-141: offline prep including admission-gated expand/contract; live multi-planner absent. LIVE-142 not started.

## Immediate work

Keep SKIP uncleared until login verifies. After login: one manual + two real hourly authenticated receipts, then request G10 accept. Continue only ready independent local $0 packaging; no remote dual / EVAL qual / LIVE-142 invent; no merge/spend/launch.

## Coordination and login

`coordination/swarm-control` is message/state transport, not source baseline. ChatGPT leads/reviews; Cursor implements/tests. Use fresh SHAs, isolated worktrees and conflict-safe writes. The lead review automation does not wake local Cursor.

Use platform aliases/methods/profile references in Git; keep real identities, keys, cookies/browser state, MFA/recovery data and sensitive return URLs outside Git. Existing Chrome rule: normal Priyansh/Default profile; no Playwright/Selenium/CDP for Google SSO. For Cursor worker auth, the only current human step is completing the fresh `cursor agent login` browser/passkey/MFA/consent flow, then verifying `status` + `whoami` before clearing the skip. No paid cloud automation.
