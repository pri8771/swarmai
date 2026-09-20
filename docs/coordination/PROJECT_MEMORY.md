# SwarmAI compact project memory

Curated 2026-09-20 after LEAD-20260920-010. Read this, STATE, V1_4_EXECUTION_CONTRACT and unread/new message pointers; do not reload whole chats. This stores accepted decisions and verified observations, not secrets or proof of unperformed work.

## Owner authorization and product direction

Implementation is approved continuously through V1.4 inclusive: V1.0 repair -> V1.1 -> V1.2 -> V1.3 -> V1.4. Do not ask the operator to start each 0.1. Independent evidence review still gates acceptance. Main merge, release/tag/publication, public deployment, new billing/spend, destructive actions and V1.5+ implementation are not authorized. Stop feature work after V1.4.

SwarmAI is a reusable self-hostable elastic problem-solving runtime. Multiple capable planners/reviewers may coordinate smaller task-qualified workers. Approved inference routes should operate concurrently. Agents can propose specialists/splits/alternatives; software enforces permissions, dependencies and resource admission. Ordinary code/tools are first-class. CrewAI is not mandatory. Reuse sound libraries.

No operational demo data, fake providers/activity, supplied answers, mock-success fallback or quota bypass. Test fixtures may exist only as isolated test/dev fixtures and never count as live proof. The operator prefers zero additional spend; bounded verified-zero-charge live validation is authorized by the V1.4 contract.

## Verified source and CI

Audited main remains `b9141fa3150f853586dede0334a47b344571bc16` (`1.0.0rc1` historical baseline). Draft PR #14 current candidate is `cursor/v1.4-live-integration-11e2` at `f75c6cb5bb8e0d2d2d2c0c6e4061fe2909f11efc` (25 commits / 103 changed files versus main at lead review).

GitHub Actions run `35539853498` is current-tip green for executed CI: console npm install/lint/Vitest/build passed; Ruff passed; mypy passed across 139 source files; package/install check passed; Alembic head `9eb193b10f4e`; broad offline pytest **245 passed, 2 skipped**. CI DB integration is explicitly skipped because `SWARM_DATABASE_URL` is absent; the live-gated job is only a blocked notice, not live acceptance.

Source improvements independently confirmed: normal `create_app()` no longer seeds known demo tokens/fixture catalog by default; demo tokens are loopback-restricted; mission/history idempotency and project isolation improved; provider readiness is fail-closed; parser dogfood is opt-in; failed model output no longer installs GOOD_FIX; normal MissionRuntime supplies a broker; former force-progress scale path is absent from searched current source.

## G10 review — NOT accepted

LEAD-20260920-010 found remaining release blockers:

1. **Operational mock contamination:** ProductStore still defaults to `execution_mode="mock"`; `/capacity` builds a mock broker; providers/routes use mock catalog paths; console live snapshot spreads `MOCK_SNAPSHOT`; console defaults to mock and offers “Recover with mock fixtures”; Expand/Contract mutate local fixture state; demo side-effect endpoint ships in normal router. Normal operation must show real empty/unknown/observed state only.
2. **Worker/approval ownership:** worker and approval list routes expose global stores without project filtering. Approval resolve does not bind to durable approval ownership. Worker ownership/heartbeat must be project-scoped. Add two-project negative tests.
3. **Release evidence binding:** verifier can pass evidence with no candidate SHA; current test expects that. Behavioral evidence must require exact SHA, command + successful result/exit, mode, timestamp/freshness and relevant config/version identity.
4. **Bootstrap scoping:** a private bootstrap token no longer has a fixed value, but still gets hard-coded `proj_demo/proj_other` membership. Operational install identity/project mapping must be explicit or generated/persisted; demo project IDs stay fixture-only.
5. **FIX-004:** scheduler check-ins are evidenced, but `cursor agent status` and `whoami` remain **Not logged in**; unattended Cursor worker spawning is disabled/skipped.

G10 remains `changes_required_after_lead_review`. Current CI green does not override these source/integrity blockers.

## Later gates

G11/RUN-111: not accepted. Durable identity/restart/review evidence exists, but three unfamiliar tasks still need full execution across two families through console+API+CLI on same IDs. MissionRuntime also auto-copies accepted worktree changes into primary checkout; replace with explicit apply/review boundary.

G12/INF-121: local-only preparation; required concurrent two-remote-provider mission evidence absent.

G13/EVAL-131: current screening is S+M × six families × two local models, n=5 = 24 provisional cells / 120 trials. Useful screening only; L/XL, third actual config and preregistered acceptance/uncertainty criterion remain open.

G14/SWARM-141: offline graph/load prep only; real adaptive multi-planner expansion/contraction absent. LIVE-142 final 12-positive/6-negative/24-hour campaign has not started.

## Immediate work

Cursor should ACK LEAD-010 and prioritize: remove operational mock/fixture paths; complete worker/approval ownership and install bootstrap scoping; tighten release evidence binding; remove automatic primary-worktree promotion; then push one integrated candidate and rerun full current-tip CI/security regressions. Independent non-conflicting V1.1–V1.4 work may continue, but no gate may be called accepted early.

## Coordination and login

`coordination/swarm-control` is message/state transport, not source baseline. ChatGPT leads/reviews; Cursor implements/tests. Use fresh SHAs, isolated worktrees and conflict-safe writes. The lead review automation does not wake local Cursor.

Use platform aliases/methods/profile references in Git; keep real identities, keys, cookies/browser state, MFA/recovery data and sensitive return URLs outside Git. Existing Chrome rule: normal Priyansh/Default profile; no Playwright/Selenium/CDP for Google SSO. For Cursor worker auth, the only current human step is completing the fresh `cursor agent login` browser/passkey/MFA/consent flow, then verifying `status` + `whoami` before clearing the skip. No paid cloud automation.
