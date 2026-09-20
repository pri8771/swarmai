# SwarmAI compact project memory

Curated 2026-09-20. Read this, STATE, the execution contract and unread AGENT_MESSAGES; do not reload whole chats. Target <=1,200 words. This stores accepted decisions and source observations, not secrets or proof of unperformed work.

## Current owner authorization

The owner approved the roadmap direction through V3.0 and authorized IMPLEMENTATION NOW through V1.4 inclusive, targeting real live operation with no known unresolved issues. Execute V1.0 repair -> V1.1 -> V1.2 -> V1.3 -> V1.4 without asking again to start each 0.1. Earlier repair-only/per-0.1 implementation stops are superseded within this tranche.

Read `V1_4_EXECUTION_CONTRACT.md`; start with `START_CURSOR_TO_V1_4.md`. Independent engineering/evidence review still applies. Ready branch work may continue while review waits, but missing review is not acceptance. Main merge, release/tag/publication, public deployment, new billing/spend, destructive actions and V1.5+ implementation are NOT authorized. Final candidate is submitted for lead review and operator merge approval. No new feature work beyond V1.4.

Live means real data, inference and tools in a protected local/already-authorized private environment; not public hosting. The quality target is all mandatory gates passed, no known unresolved supported-V1.4 defects and no unexpected application errors in the accepted campaign. No finite test guarantees no future bugs. Expected denials/outages must be handled honestly, not hidden.

## Product direction

Reusable self-hostable elastic problem-solving swarm, separate from business/household projects. Multiple capable planners/reviewers may work with smaller task-qualified agents. All approved inference routes can run concurrently. Agents propose specialists/splits/alternative approaches; software controls permissions, dependencies and capacity. Dynamic expansion/contraction, not a permanently small fixed team. Ordinary code/tools are first-class. CrewAI is not mandatory.

Reuse good libraries instead of rebuilding execution, providers, storage or browser infrastructure. Empirically test standard task families/sizes; include total planning/repair/review overhead. Load scoped accepted evidence/context, not entire histories. No operational demo data, fake providers/activity, supplied answers or mock-success fallbacks. Keep isolated regression tests, never pass them off as live execution.

Operator preference: zero additional spend; free-cloud coordination where feasible, optional R730/T640/Mac workers/local inference, tested local recovery. Existing resource/model capacity must be verified. No cards/top-ups/paid fallback. Current tranche allows bounded actual free/local validation under the recorded contract envelopes, not unbounded model use or private-data transfer outside approved scopes. Cloud hosting/site recovery is V1.8, not claimed at V1.4.

## Verified baseline and limitations

Last source observed: main `b9141fa3150f853586dede0334a47b344571bc16`, package `1.0.0rc1`. V1 RC PR #12 and status PR #13 were merged; version/merge status is not behavioral proof.

Pinned source/CI audit: `AUDIT_V1_2026-09-20.md`. Main CI `35529361557`, job `106127102217`, failed Ruff with 33 findings; mypy/pytest skipped; workflow scheduled only contracts/spikes. No independent full-suite execution or live credential/provider/browser/cloud test was performed by the lead. Main metadata reported unprotected, not a complete ruleset assessment.

Audit identified default demo tokens, project/history/idempotency authorization holes, file-presence checks overstating verification, parser-specific GOOD_FIX fallback, local-only sequential demonstrated mission, hashing presented as swarm reasoning, force-progress admission bypass, configured/unprobed credentials treated as ready, synthetic recovery/timeout helpers and disconnected fixture API versus CLI runtime. Preserve useful broker/contracts/components; reproduce against fresh source before changing them. No observed production breach or charge is claimed.

Cursor ACK `CURSOR-20260920-001` posted. Integration branch `cursor/v1.4-live-integration-11e2` worktree `/Users/pchordia/Downloads/swarm-ai-v14` at source `b9141fa`. First regression `uv run ruff check .` reproduced 33 findings (exit 1). Repair of FIX-001–005 in progress; no gate acceptance claimed. The lead updated coordination documents, not application code. Fetch source and messages to discover later changes.

## Immediate work and gates

G10 FIX-001 complete CI; FIX-002 auth/project isolation/idempotency; FIX-003 truthful evidence/readiness; FIX-004 login/session records and actual hourly runner; FIX-005 remove runtime fixture/known-answer/bypass dependence. Parallelize only distinct ownership, especially overlapping API/store/runtime edits.

Then RUN-111/G11 unified generic durable console/API/CLI mission; INF-121/G12 real concurrent remote providers plus local path with broker admission; EVAL-131/G13 measured model/family/size qualification; SWARM-141/G14 real adaptive graph; LIVE-142 final live acceptance. Contract contains specific tests, bounded budgets and a 24-hour observed private operating campaign. Missing live access blocks acceptance, not independent coding. Failed evidence cannot be censored or reclassified to manufacture success.

Future: 1.5 distributed workers; 1.6 richer scoped knowledge; 1.7 integrated tools/session recovery; 1.8 cloud-first/local site recovery; 1.9 independent beta/self-development; 2.0 accepted elastic product. V3: ongoing multi-mission goals, governed learning and fleet/resource coordination.

## Coordination

Stable transport: `coordination/swarm-control`, not necessarily latest app source. Work on scoped branches and a dedicated integration branch. ChatGPT leads/independently reviews; Cursor implements/tests. Fetch before reading; preserve dirty work; use current blob SHAs or fast-forward coordination worktrees. Append immutable IDs/ACKs and compact Done/Evidence/Next/Blocked messages. Never invent another agent's reply. Archive acknowledged history with pointers.

Existing hourly ChatGPT review checks/writes GitHub but does not launch local Cursor. Cursor runner still requires actual local/entitlement verification; no paid runner is authorized. One scheduled worker with no-overlap lease, bounded resumable invocations and truthful host availability. A sleeping/offline host cannot guarantee hourly work. Actual scheduled heartbeats remain pending until observed.

## Login/session context

Use `../onboarding/PLATFORM_ACCESS.md`. Existing local rule: normal Priyansh/Default Chrome; no Playwright/Selenium/CDP for Google SSO. Prior onboarding reports are historical, not current-session proof. Retain aliases, login methods, safe entry points, profile/secret references and last actual checks in Git. Keep real identities, keys, cookies/browser state, MFA/recovery material and sensitive redirect URLs outside Git.

Restore the correct login and return to the intended Apply/dashboard page; ask only for the essential password/passkey/MFA/CAPTCHA/consent step. Wrong account, expired signed URL and IDE-local links differ from normal logout. Opening a form is not submitting it. The owner's exact failed Apply destination has not been reproduced here.

Bots/Claude planning is being handed to a separate conversation; do not absorb those venture codebases into SwarmAI or start their implementation from this tranche.
