# SwarmAI MVP decisions

## DEC-TH-004 — Synthetic harness before live qualification; no auto routing

| Field | Value |
|---|---|
| Decision ID | DEC-TH-004 |
| Topic | Evaluation / qualification gate |
| Decision Maker | Implementation worker per architecture §8 |
| Decision | Prepare and run the graded synthetic harness independently of live route/budget grants. Live dispatch stays blocked until an approved `LiveGrant`. Fixture/oracle results never auto-change production routing; ProfileStore updates from synthetic runs are ephemeral and `simulated=True`. |
| Context | TH-07; starter.jsonl 128 cases; R730/DNS/CF and provider grants unavailable |
| Options Considered | (1) wait for live grants before harness, (2) prepare harness + block live, (3) promote provisional routes from oracle scores |
| Why | Architecture §8: prepare harness independently; no universal best model; no auto production routing from few examples |
| Date Recorded | 2026-09-25 |
| Actual Start Date | 2026-09-25 |
| Actual End Date | 2026-09-25 |
| Status | accepted |
| Consequences | TH-07 Mac eng complete; live qualification remains blocked pending grant + dispatch wiring |
| Related Files | `src/swarm/evals/synthetic_harness.py`, `docs/evidence/two-host/TH-07/` |
| Related Prompt | TH-07 authorized continuation |
| Related Jira/Linear | pending — see `LINEAR_RECONCILIATION.md` |

## DEC-TH-001 — Two-host deployment topology

| Field | Value |
|---|---|
| Decision ID | DEC-TH-001 |
| Topic | Deployment architecture |
| Decision Maker | Operator via Project coordinator mandate |
| Decision | R730 always-on server; Mac connector worker; authenticated `swarm.splitsignal.ai`; Compose per host |
| Context | Planning bundle was local-only; hardware roles now specified |
| Options Considered | (1) local-only Mac, (2) two-host R730+Mac, (3) immediate cloud SaaS |
| Why | Always-on product without Mac dependency; keep cloud-ready contracts |
| Date Recorded | 2026-09-25 |
| Actual Start Date | 2026-09-25 |
| Status | accepted |
| Consequences | Supersedes local-only deploy scope; R730/CF access become gates |
| Related Files | `ADR-002-two-host-architecture.md`, `deploy/compose/server.yml`, `deploy/compose/mac-connector.yml` |
| Related Prompt | two-host-architecture-update |
| Related Jira/Linear | pending — see `LINEAR_RECONCILIATION.md` |

## DEC-TH-003 — Runtime adapters require mediated qualification

| Field | Value |
|---|---|
| Decision ID | DEC-TH-003 |
| Topic | Optional OpenCode / Hermes runtimes |
| Decision Maker | Implementation worker per architecture mandate |
| Decision | Framework configuration alone does **not** enforce SwarmAI contracts. OpenCode/Hermes stay non-admissible until capability-by-capability SwarmAI kernel mediation is proven. Missing/unqualified capabilities are marked unavailable. Native remains default. |
| Context | TH-06 optional adapters; OpenCode binary present on Mac; Hermes not installed |
| Options Considered | (1) claim qualified from vendor config, (2) honest discovery + unavailable caps, (3) block all optional runtimes including native |
| Why | Architecture §6 and P16 stop conditions forbid false badges and contract weakening |
| Date Recorded | 2026-09-25 |
| Actual Start Date | 2026-09-25 |
| Actual End Date | 2026-09-25 |
| Status | accepted |
| Consequences | `GET /v1/runtimes` admits only `native` today; OpenCode=`discovered_unqualified`; Hermes=`unavailable` |
| Related Files | `src/swarm/runtime/adapters/`, `docs/evidence/two-host/TH-06/` |
| Related Prompt | TH-06 authorized continuation |
| Related Jira/Linear | pending — see `LINEAR_RECONCILIATION.md` |

## DEC-TH-002 — Parallel lane vs V1.7

| Field | Value |
|---|---|
| Decision ID | DEC-TH-002 |
| Topic | Ownership / branching |
| Decision Maker | Implementation worker (per mandate: do not overwrite other worker) |
| Decision | Use isolated branch/worktree `cursor/two-host-mvp-b28d`; leave `cursor/v17-single-session` and CURSOR-V17-SINGLE heartbeat untouched |
| Context | Coordination ASSIGNED_WAITING_FOR_WORKER (GPT-6 Sol) for V1.7; Project mandates two-host MVP |
| Options Considered | (1) hijack V1.7 branch, (2) wait for V1.7 acceptance, (3) parallel lane |
| Why | Continue authorized work without overwriting another owner’s scope |
| Date Recorded | 2026-09-25 |
| Status | accepted |
| Related Files | `STATE.md`, `SOURCE_BASELINE.json` |

## DEC-V23-001: Owner and coordinator decisions for V2.3 (2026-09-25/26)

| Field | Value |
|---|---|
| Decision ID | DEC-V23-001 |
| Topic | V2.3 execution: pause lift, review, branching, SplitSignal, secrets |
| Decision Maker | Owner (D1–D6, B-01); coordinator (C1–C5; the owner may override) |
| Date Recorded | 2026-09-26 |
| Status | accepted (C1–C5: coordinator-accepted) |
| Supersedes | `docs/agents/CURRENT.md` `pause: true` / `pause_state` (by B-01); HL-07 "PRs target `dev` only" for V2.3 work (by C1); open "name a reviewer" / independent-review blockers (by D2). The earlier entries are kept and marked. |
| Related Files | `docs/plans/v2.3/PLAN.md` §0 and §5.2, `docs/plans/v2.3/OWNER_PREFLIGHT.md`, `docs/plans/v2.3/AUDIT.md` |
| Related Prompt | V2.3 planning prompt, 2026-09-26 (`docs/PROMPT_LOG.md`) |
| Related Jira/Linear | pending (see `docs/JIRA_SYNC_PENDING.md`) |

Owner decisions:
- D1: Every third-party account uses Sign in with Google with the owner's Google account. All accounts exist and are signed in; Codex has read access.
- D2: The independent reviewer is Codex. Every session that needs review ends with a "Codex review packet" (PR URL placeholder, head SHA command, files to review, review focus per the AGENTS.md Code Review Rules). A session is accepted only by Codex `RECOMMEND_ACCEPT <sha>` on its exact head SHA.
- D3: The only cross-repo dependency: SplitSignal (inference_server) issues SwarmAI an API key, and SwarmAI calls SplitSignal as a standard OpenAI-compatible API. Nothing else crosses repos.
- D4: Both projects finish V2.3 together, coordinated through sync points SP1–SP6 (`docs/plans/v2.3/PLAN.md` §5.2).
- D5: All owner blockers go into one preflight (`docs/plans/v2.3/OWNER_PREFLIGHT.md`), done before sessions start. Nothing may block partway: a missing gate makes a session STOP, record and push; it never waits.
- D6: Secrets live in a plain-text file on the owner's Mac (`~/Desktop/splitsignal-swarmai-secrets.env`, section `# --- swarmai ---`), then in Cursor Dashboard → Cloud Agents → Secrets. swarmai is public, so Cursor may withhold secret injection unless the owner allows it.
- B-01: The owner's instruction "get to V2.3 for both projects" lifts `pause: true` (2026-09-26).

Coordinator decisions (owner may override):
- C1: Agents may not merge into `dev` or `main`. Integration branch `cursor/sw-v23-integration-460c` (created from `origin/dev`). Every session branches from it and opens a draft PR to it. `SW-MERGE-<wave>` prompts merge session PRs after checks pass, labelled `Codex review pending`. The owner merges integration into `dev`. For V2.3, "merged to dev" means "merged into `cursor/sw-v23-integration-460c`".
- C2: inference_server's integration branch is `cursor/is-v23-integration-460c`.
- C3: D-SS1. A route listed by SplitSignal's key-scoped `/v1/models` is treated as free. A response is refused only when it reports a known non-zero cost. An unknown cost is recorded as unknown (`null`), never zero, and never releases budget (F-13 semantics).
- C4: inference_server `/v1/models` returns `{"object":"list","data":[...]}`. SwarmAI stays tolerant of both that and `ModelPage` (`items`).
- C5: SwarmAI env var names are exactly `SPLITSIGNAL_BASE_URL` (public URL + `/v1`), `SPLITSIGNAL_API_KEY` and `SPLITSIGNAL_MODEL` (recommended default `gemini/gemini-3.5-flash-lite`, used when unset).

Pre-approvals (exact lines; SW-X2-S1 reads the A3 line):
- SW-PREAPPROVAL-A1: APPROVED 2026-09-26 (pause lift, B-01)
- SW-PREAPPROVAL-A2: APPROVED 2026-09-26 (Codex reviewer, D2)
- SW-PREAPPROVAL-A3: APPROVED 2026-09-26 (owner, chat) (SplitSignal live smoke; wording in OWNER_PREFLIGHT Part 3)
- SW-PREAPPROVAL-A5: APPROVED 2026-09-26 (owner, chat) (multi-process/private evidence run; wording in OWNER_PREFLIGHT Part 3)

## DEC-V23-002: Cross-reference — owner decisions D7 and D8 (2026-09-26)

| Field | Value |
|---|---|
| Topic | SSO scope and the plaintext secrets file (recorded in inference_server) |
| Decision Maker | Owner |
| Date Recorded | 2026-09-26 |
| Status | accepted |
| Supersedes | D6's open vault question, for both repos (by D8). Nothing in swarmai is deleted. |
| Related Files | `docs/plans/v2.3/JOINT_PLAN.md` (byte-identical with inference_server); inference_server `docs/DECISIONS.md` D7/D8, `docs/DEFERRED_FEATURES.md`, `docs/plans/v2.3/OWNER_PREFLIGHT.md` Part 8 (branch `cursor/v23-plan-460c`) |

- D7: SplitSignal's v2.1 SSO is deferred and not part of V2.3 acceptance. SwarmAI does not use SSO; there is no swarmai change.
- D8: the Desktop file `~/Desktop/splitsignal-swarmai-secrets.env` (including the `# --- swarmai ---` group and `SPLITSIGNAL_API_KEY`) is a testing-only measure. Pre-launch: rotate every SEC-* key, including the SwarmAI key, before any non-owner traffic; then delete the Desktop file. The risk is closed as "accepted by owner, rotation required before launch".
