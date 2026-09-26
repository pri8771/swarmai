# JOINT V2.3 PLAN — inference_server (SplitSignal) + swarmai (SwarmAI)

Identical copy in both repos at `docs/plans/v2.3/JOINT_PLAN.md` on branch `cursor/v23-plan-460c` (inference_server [PR #32](https://github.com/pri8771/inference_server/pull/32), swarmai [PR #70](https://github.com/pri8771/swarmai/pull/70)). Written 2026-09-26 01:32 UTC by the joint planning agent. It sits on top of each repo's own `PLAN.md`, `OWNER_PREFLIGHT.md` and `prompts/`; where they differ, this file gives the joint order and the repo files give the detail.

Owner decisions in force: D1 (Google sign-in as `priyansh.chordia@gmail.com` everywhere; every account exists), D2 (Codex reviews), D3 (the only cross-repo dependency is the SwarmAI API key plus the OpenAI-compatible API), D4 (finish together), D5 (one preflight), D6 (secrets in `~/Desktop/splitsignal-swarmai-secrets.env`). Coordinator decisions: C1/C6 (session merges go into the integration branches only, labelled `Codex review pending`; the owner merges to `main`/`dev` later), IS C8 (deploy/live steps are skipped while secrets are missing).

**Approval IDs are namespaced in this file.** `IS-An` = the line `PREAPPROVAL-An` in inference_server `docs/DECISIONS.md`. `SW-An` = the line `SW-PREAPPROVAL-An` in swarmai `docs/swarm-mvp/DECISIONS.md`. Both repos have an `A3` and an `A5`, and they are different approvals (§8).

---

## 1. One-page summary

**What V2.3 means**

| Repo | V2.3 target | Integration branch | Who merges it |
|---|---|---|---|
| inference_server (SplitSignal, OpenAI-compatible inference API) | ROADMAP v2.3 "Observability and analytics", cumulative v0.1–v2.3: code-complete and offline-tested on the integration branch, v0.5 hosted live on Render Free, every REVIEW REQUIRED session accepted by Codex. Later live gates (DNS, Stripe live, SSO vendor, provider accounts, legal) are tracked, not blocking (IS DEC-1). | `cursor/is-v23-integration-460c` | owner → `main` (IS-A9), after Codex |
| swarmai (SwarmAI, consumes SplitSignal with an API key) | Every item of the "V2.3 implementation-complete" checklist true on the integration branch; ART-V23 acceptance 1–10 as a frozen deterministic harness; the SplitSignal adapter tested offline and smoke-tested live (SP4/SP5); multi-process/private evidence complete or honestly pending. | `cursor/sw-v23-integration-460c` | owner → `dev` (C1), later `dev` → `main` (B-07) |

The only runtime link: SwarmAI calls `POST /v1/chat/completions` and `GET /v1/models` at `SPLITSIGNAL_BASE_URL` (SplitSignal public URL + `/v1`) with `SPLITSIGNAL_API_KEY` (`ss_live_…`) and `SPLITSIGNAL_MODEL` (default `gemini/gemini-3.5-flash-lite`). The contract is `swarmai-consumer 1.x` (§7).

**Current state (inference_server row updated 2026-09-26 ~07:45 UTC; swarmai row as dated)**

| Repo | Integration tip | Merged | Pushed, not merged yet | Not started |
|---|---|---|---|---|
| inference_server (updated 2026-09-26 ~07:45 UTC) | `c685c3d` (IS-FIX follow-ups on top of IS-W8-MERGE `91dc1f7`) | IS-W0-S1, IS-W0-S2, IS-W1-S1…S11, IS-W3-S1…S9, IS-W3-FIX1, IS-W5-S1…S7, IS-W7-S1…S5 (36 sessions) with the IS-W2/W4/W6/W8-MERGE wiring; IS-FIX-flaky-key-repr, -webhook-ssrf-rebind, -statements-close-all, -invite-accept-page, -web-routes, -readiness-docs (REVIEW REQUIRED sessions and the rebinding/definer fixes `Codex review pending`) | — | IS-W2-DEPLOY (pending owner secrets, C8), then a redeploy for SP5 |
| swarmai (updated 2026-09-26 ~03:20 UTC) | `c34e1b0e` | SW-W0-S1…S3, SW-W1-S1…S13, SW-W2-S1, SW-W2-S2, SW-W3-S1…S5, SW-W4-S1, SW-X1-S1 (25 sessions; X1-S1 merged `2b27bc20` after SP1/SP2) + follow-ups SW-FIX-RETRY, SW-FIX-COMPOSE, SW-FIX-ALEMBIC, SW-FIX-FLAKE and docs re-runs (all `Codex review pending`) | — | SW-X2-S1 (needs SP4 + SW-PREAPPROVAL-A3), SW-MERGE-X |

The plan branch `cursor/v23-plan-460c` is not yet an ancestor of either integration branch. For swarmai, the next SW-MERGE run merges it automatically. inference_server does not merge its plan branch; its sessions paste prompts from it.

Sync points (updated 2026-09-26 ~03:20 UTC): **SP1 and SP2 reached** (IS-W2-MERGE, `cursor/is-v23-integration-460c` @ `9ca12671`: `docs/api/v1/consumers/swarmai.md` blob `1a4a31c9`, fixtures, `scripts/mock_splitsignal.py`). SP3–SP6 pending: SP3/SP4 need IS-W2-DEPLOY with the owner secrets (not yet stored, so C8 applies today). IS-W8-MERGE (`91dc1f7`) recorded `SP6: offline-tested` (not reached); SP5 needs a redeploy after IS-W2-DEPLOY (2026-09-26 ~07:45 UTC).

**What remains:** 1 inference_server run (IS-W2-DEPLOY, then a redeploy for SP5; 2026-09-26 ~07:45 UTC) and 12 swarmai runs (13 in total, §4), plus the owner preflight (§2), the Codex review of both integration trees and the owner merges.

---

## 2. OWNER PREFLIGHT (one list for both repos, in this order)

Do items 1–8 in one sitting before launching slot 3 (§3). Slots 1–2 need nothing from you, so they can run while you do this.

- [x] **1. Accounts (D1).** GitHub `pri8771`, Cursor Dashboard, OpenAI Codex (reads both repos), Supabase, Google Cloud, Google AI Studio, Render. All exist and use Google sign-in (IS ACC-1…ACC-7). Nothing to do.
- [ ] **2. Secrets: run ONE computer-use prompt.** Copy the fenced prompt in inference_server `docs/plans/v2.3/SECRETS_SETUP.md` §9 (branch `cursor/v23-plan-460c`, [link](https://github.com/pri8771/inference_server/blob/cursor/v23-plan-460c/docs/plans/v2.3/SECRETS_SETUP.md)) into Claude computer use or Codex with computer control on your Mac. It handles both repos: the Desktop file `~/Desktop/splitsignal-swarmai-secrets.env` gets **17 names** under 4 group headers, and Cursor My Secrets gets **15 names** (SEC-1…SEC-15; `SPLITSIGNAL_MODEL` is SEC-15, a config value). It never prints a value. Send its final report (starts with `secrets done`) to the coordinator unchanged.
- [ ] **3. Public-repo secrets for swarmai (swarmai R-1).** `pri8771/swarmai` is public, and Cursor may withhold secret injection for public repos unless allowed. The public Cursor docs (checked 2026-09-26) do not say where that switch is, so the prompt looks for it. Approve by replying `approved public-repo secrets`:
  > "The secrets computer-use prompt may allow Cursor secret injection for `pri8771/swarmai` only, if the Cursor dashboard offers such a setting (SECRETS_SETUP §9 STEP G-PUBLIC). If no setting is shown, it asks me to choose between keeping the repo public and making it private (STEP I)."

  If you prefer, make `pri8771/swarmai` private instead (GitHub → Settings → General → Danger Zone → Change visibility). Only SW-X2-S1 needs the secrets; without them it STOPs and records `SPLITSIGNAL_API_KEY MISSING`.
- [ ] **4. Verify the secrets (no values shown).** Start one **new** Cursor agent on `pri8771/inference_server` and one on `pri8771/swarmai`, and paste the matching block from SECRETS_SETUP §10. Every inference_server name must print `SET`; on swarmai, `SPLITSIGNAL_API_KEY` and `SPLITSIGNAL_BASE_URL` must print `SET` (a missing `SPLITSIGNAL_MODEL` is harmless).
- [ ] **5. Approve SW-A3 (swarmai live smoke).** Reply `approved SW-A3`. The coordinator then writes `- SW-PREAPPROVAL-A3: APPROVED <date>` in swarmai `docs/swarm-mvp/DECISIONS.md`. Proposed wording:
  > "SW-X2-S1 may make one live run against `SPLITSIGNAL_BASE_URL` with `SPLITSIGNAL_API_KEY`: at most 2 chat calls (one non-streaming, one streaming), each with `max_tokens` 16, on one free route listed by `/v1/models`, with a 60 s wall-clock limit and a $0 budget, and only after inference_server has recorded `SP4: reached` (the streamed call only after `SP5: reached`). These calls are in addition to the at most 5 calls of IS-A6; the joint maximum is 7 free-tier calls. A known non-zero cost stops the run. Sanitized metadata only is committed to `docs/evidence/v23/splitsignal_live.json`."
- [ ] **6. Approve SW-A5 (multi-process evidence run, V23-A11).** Reply `approved SW-A5`. Proposed wording:
  > "Agents may run the V2.3 acceptance campaign as two local processes that share one local PostgreSQL, with no provider or model calls and no deploy. The result is recorded as private evidence under `docs/evidence/v23/`."

  Without it, SW-W4-S1 records V23-A11 as `pending (owner gate)`, which the checklist allows ("complete or honestly pending").
- [ ] **7. Close the stale swarmai draft PRs (swarmai R-2, B-06).** Close [#42](https://github.com/pri8771/swarmai/pull/42), [#43](https://github.com/pri8771/swarmai/pull/43) and [#44](https://github.com/pri8771/swarmai/pull/44): their content is already in `dev` or superseded. Leave the Codex donor stack #18–#40 open until V2.3 is merged into `dev`. Agents cannot do this (`gh` is read-only).
- [ ] **8. Approve this joint plan.** Reply `approved joint plan` on either plan PR. That confirms the joint schedule (§3), the SP marker lines (§7), and the joint live-call cap of 7.

**Already approved (nothing to do):** IS-A1…IS-A9 (2026-09-26, including IS-A4 deploy, IS-A5 hosted DB, IS-A6 $0 cap with ≤ 5 live calls, IS-A9 owner-only `main` merge); SW-A1 (pause lift), SW-A2 (Codex reviewer), C1 (integration-branch workflow), D-SS1/C3, SW $0 cap.

**Owner-only actions later (no agent does these):**
- **Render repoint: pre-approved (IS-A4), done by an agent.** IS-W2-DEPLOY repoints the Free service `inference-router` to `Dockerfile.consumer` through the Render API. Do not change Render yourself.
- **Merges.** After the joint acceptance (§6) and Codex acceptance: you merge `cursor/is-v23-integration-460c` into `main` ([PR #34](https://github.com/pri8771/inference_server/pull/34) is that integration PR, marked DO NOT MERGE until then), and you merge `cursor/sw-v23-integration-460c` into `dev`. A later `dev` → `main` merge and tag in swarmai stays yours.
- **Optional, 2 minutes, after slot 3:** open `SPLITSIGNAL_PUBLIC_URL/app/signin` and sign in with Google (IS OWNER_PREFLIGHT Part 7). It blocks nothing.

---

## 3. JOINT SCHEDULE

Sessions in one slot run in parallel (they own disjoint files). A gate is checked before the next slot starts; the commands are in §4.3. `EXECUTED` means the session's branch and handoff are on origin.

| Slot | inference_server (IS) | swarmai (SW) | Max at once | Gate to pass before the next slot |
|---|---|---|---|---|
| 0 | **EXECUTED** IS-W0-S1, IS-W0-S2 (both merged, integration `a685c884`) | **EXECUTED** SW-W0-S1…S3, SW-W1-S1…S13, SW-W2-S1, SW-W2-S2 (all merged, integration `94cdc07b`) | — | — |
| 1 | **EXECUTED** IS-W1-S1…S11 (all merged by IS-W2-MERGE) | **EXECUTED** SW-W3-S1, SW-W3-S2, SW-W3-S3, SW-W3-S4 (merged) | 9 | **G1**: 11 IS-W1 branches and 4 SW-W3 branches pushed with handoffs, none STOPPED |
| 2 | **EXECUTED** IS-W2-MERGE (integration `9ca1267`) | SW-MERGE-W3 (also merges the plan branch) | 2 | **G2 = SP1 + SP2**: `docs/api/v1/consumers/swarmai.md` and `scripts/mock_splitsignal.py` on `cursor/is-v23-integration-460c`; SW-W3-S1…S4 merged on `cursor/sw-v23-integration-460c`. **Owner preflight items 2–4 done before slot 3.** |
| 3 | IS-W2-DEPLOY (needs the secrets; writes SP3/SP4; **not executed**, C8) + **EXECUTED** IS-W3-S1…S9 and IS-W3-FIX1 (merged by IS-W4-MERGE) | **EXECUTED** SW-W4-S1, SW-W3-S5 (merged; integration `ed388b7b`); **EXECUTED** SW-X1-S1 (SP1 reached; merged `2b27bc20`) | 13 | **G3 = SP3 + SP4**: `docs/evidence/m1/hosted-v05.md` has `SP3: reached` and `SP4: reached`; 9 IS-W3 branches pushed; SW-W4-S1 and SW-X1-S1 pushed |
| 4 | **EXECUTED** IS-W4-MERGE (integration `032d555`; SP5 not written: no hosted v0.5) | **EXECUTED** by the integrator: W3-S5, W4-S1 and X1-S1 merged directly into `cursor/sw-v23-integration-460c` (tip `c34e1b0e`); SW-MERGE-X remains for SW-X2-S1 | 2 | **G4 = SP5**: `hosted-v05.md` has `SP5: reached` (if not, the W6/W8 redeploy fallback makes it); SW-W4-S1 and SW-X1-S1 merged |
| 5 | **EXECUTED** IS-W5-S1…S7 (merged by IS-W6-MERGE) | — (SwarmAI is done except SW-X2-S1, which waits for SP6) | 7 | **G5**: 7 IS-W5 branches pushed |
| 6 | **EXECUTED** IS-W6-MERGE (integration `c36f72c`; SP5 fallback skipped, C8) | — | 1 | **G6**: IS-W6-MERGE handoff on the integration branch |
| 7 | **EXECUTED** IS-W7-S1…S5 (merged by IS-W8-MERGE) | — | 5 | **G7**: 5 IS-W7 branches pushed |
| 8 | **EXECUTED** IS-W8-MERGE (integration `91dc1f7`; `SP6: offline-tested`, SP5 fallback skipped) and the IS-FIX follow-ups (integration `c685c3d`) | — | 1 | **G8 = SP6**: `docs/evidence/v2.3-offline.md` contains `swarmai-consumer 1.` and `SP6: reached` |
| 9 | — | SW-X2-S1 (live smoke; SP4 always, SP5 if recorded, SP6 check) | 1 | **G9**: SW-X2-S1 pushed with `docs/evidence/v23/splitsignal_live.json` |
| 10 | — | SW-MERGE-X again (merges X2-S1) | 1 | **G10**: joint acceptance §6 |
| 11 | Codex reviews the IS integration tree; owner merges → `main` | Codex reviews the SW integration range; owner merges → `dev` | — | done |

Why this order: SwarmAI's remaining work (W3/W4/X1) finishes in slots 1–4 alongside inference_server W1–W4. SW-X2-S1 runs after IS-W8-MERGE, so one run records SP4, SP5 and SP6 and needs no re-run (a re-run would need a new approval, because its calls would exceed the joint cap of 7).

---

## 4. LAUNCH LIST

### 4.1 How to launch

- **Prompt source.** Always paste the prompt file from the plan branch `cursor/v23-plan-460c` (latest), not a copy in an integration branch:
  - IS: `https://github.com/pri8771/inference_server/blob/cursor/v23-plan-460c/docs/plans/v2.3/prompts/<ID>.md`
  - SW: `https://github.com/pri8771/swarmai/blob/cursor/v23-plan-460c/docs/plans/v2.3/prompts/<ID>.md`
- **One prompt = one new Cursor cloud agent.** Paste the whole file, nothing else. Start it on the repo named in the list.
- **Model:** any model. Weak models are fine: every prompt is self-contained, gives exact commands and ends in STOP conditions instead of guessing. If you have a choice, give the MERGE sessions and IS-W2-DEPLOY the strongest model you have; it is not required.
- **Secrets reach only agents started after the secrets were saved.** Start IS-W2-DEPLOY, the IS-W4/W6/W8-MERGE sessions and SW-X2-S1 as new agents after preflight items 2–4.
- **Cross-repo reads.** SW-X1-S1 and SW-X2-S1 read the private inference_server repo with `gh api`. Launch them from an environment that has both repos (as the coordinator environment does), or first check in the agent that `gh api repos/pri8771/inference_server --jq .full_name` prints `pri8771/inference_server`; otherwise they STOP (S7) without changing anything.
- **Branch suffix.** If Cursor forces a suffix (for example `-4662`), the prompts tell the agent to append it once to the session branch and record it. The integration branches already end in `-460c`; they never get a second suffix.

### 4.2 Ordered launch list (everything not yet executed)

| # | Slot | Repo | Prompt file | Parallel with | Needs |
|---|---|---|---|---|---|
| 1 | 1 | inference_server | **EXECUTED** `prompts/IS-W1-S7.md` | 2–9 | — |
| 2 | 1 | inference_server | **EXECUTED** `prompts/IS-W1-S8.md` | 1, 3–9 | — |
| 3 | 1 | inference_server | **EXECUTED** `prompts/IS-W1-S9.md` | 1–2, 4–9 | — |
| 4 | 1 | inference_server | **EXECUTED** `prompts/IS-W1-S10.md` (the SwarmAI contract) | 1–3, 5–9 | — |
| 5 | 1 | inference_server | **EXECUTED** `prompts/IS-W1-S11.md` (R) | 1–4, 6–9 | — |
| 6 | 1 | swarmai | `prompts/SW-W3-S1.md` | 1–5, 7–9 | — |
| 7 | 1 | swarmai | `prompts/SW-W3-S2.md` | 1–6, 8–9 | — |
| 8 | 1 | swarmai | `prompts/SW-W3-S3.md` | 1–7, 9 | — |
| 9 | 1 | swarmai | `prompts/SW-W3-S4.md` | 1–8 | — |
| 10 | 2 | inference_server | **EXECUTED** `prompts/IS-W2-MERGE.md` | 11 | G1 |
| 11 | 2 | swarmai | `prompts/SW-MERGE-W3.md` | 10 | G1 |
| 12 | 3 | inference_server | **NOT EXECUTED** (C8) `prompts/IS-W2-DEPLOY.md` (R; secrets; new agent) | 13–24 | G2 + preflight 2–4 |
| 13–21 | 3 | inference_server | **EXECUTED** `prompts/IS-W3-S1.md` (R), `IS-W3-S2.md`, `IS-W3-S3.md` (R), `IS-W3-S4.md` (R), `IS-W3-S5.md`, `IS-W3-S6.md`, `IS-W3-S7.md`, `IS-W3-S8.md` (R), `IS-W3-S9.md` | each other, 12, 22–24 | G2 |
| 22 | 3 | swarmai | `prompts/SW-W4-S1.md` | 12–21, 23–24 | G2 (SW-W3 merged) |
| 23 | 3 | swarmai | `prompts/SW-X1-S1.md` (both-repo environment) | 12–22, 24 | G2 (SP1) |
| 24 | 3 | swarmai | `prompts/SW-W3-S5.md` (optional) | 12–23 | G2 (SW-W3-S1 merged) |
| 25 | 4 | inference_server | **EXECUTED** `prompts/IS-W4-MERGE.md` (secrets; new agent) | 26–28 (other repo) | G3 |
| 26 | 4 | swarmai | `prompts/SW-MERGE-W3.md` (re-run; only if #24 was pushed) | 25 | G3 |
| 27 | 4 | swarmai | `prompts/SW-MERGE-W4.md` | 25 | #26 finished |
| 28 | 4 | swarmai | `prompts/SW-MERGE-X.md` (merges SW-X1-S1) | 25 | #27 finished |
| 29–35 | 5 | inference_server | **EXECUTED** `prompts/IS-W5-S1.md` (R), `IS-W5-S2.md`, `IS-W5-S3.md`, `IS-W5-S4.md` (R), `IS-W5-S5.md` (R), `IS-W5-S6.md`, `IS-W5-S7.md` | each other | G4 |
| 36 | 6 | inference_server | **EXECUTED** `prompts/IS-W6-MERGE.md` (secrets; new agent) | — | G5 |
| 37–41 | 7 | inference_server | **EXECUTED** `prompts/IS-W7-S1.md` (R), `IS-W7-S2.md` (R), `IS-W7-S3.md` (R), `IS-W7-S4.md` (R), `IS-W7-S5.md` | each other | G6 |
| 42 | 8 | inference_server | **EXECUTED** `prompts/IS-W8-MERGE.md` (secrets; new agent) | — | G7 |
| 43 | 9 | swarmai | `prompts/SW-X2-S1.md` (secrets; both-repo environment; new agent) | — | G8 + SW-A3 approved |
| 44 | 10 | swarmai | `prompts/SW-MERGE-X.md` (re-run; merges SW-X2-S1) | — | G9 |

(R) = REVIEW REQUIRED: merged into the integration branch as `Codex review pending` (C6); Codex reviews before the owner merges `main`.

Peak concurrency: 9 in slot 1, 13 in slot 3. If you want fewer at once, launch in list order and start the next as one finishes; the gate rule does not change.

### 4.3 Check before launching the next slot

Run this in any agent that has both repos (read-only; prints names, SHAs and marker lines only):

```bash
cd /agent/repos/inference_server && git fetch -q origin
echo "IS integration: $(git rev-parse --short origin/cursor/is-v23-integration-460c)"
git ls-remote origin 'refs/heads/cursor/is-w*' | awk '{print substr($1,1,8), $2}'
for f in docs/api/v1/consumers/swarmai.md scripts/mock_splitsignal.py docs/evidence/m1/hosted-v05.md docs/evidence/v2.3-offline.md; do
  git cat-file -e origin/cursor/is-v23-integration-460c:$f 2>/dev/null && echo "PRESENT $f" || echo "ABSENT  $f"; done
for f in docs/evidence/m1/hosted-v05.md docs/evidence/v2.3-offline.md; do
  git show origin/cursor/is-v23-integration-460c:$f 2>/dev/null | grep -E '^SP[1-6]: |swarmai-consumer 1\.' ; done
git ls-tree --name-only origin/cursor/is-v23-integration-460c docs/handoffs/ | sed 's#docs/handoffs/##'
cd /agent/repos/swarmai && git fetch -q origin
echo "SW integration: $(git rev-parse --short origin/cursor/sw-v23-integration-460c)"
git ls-remote origin 'refs/heads/cursor/sw-*' 'refs/heads/cursor/v23-*' | awk '{print substr($1,1,8), $2}'
git ls-tree --name-only origin/cursor/sw-v23-integration-460c docs/v2.3/sessions/ | sed 's#docs/v2.3/sessions/##'
```

| Gate | Pass when |
|---|---|
| G1 | IS: branches for IS-W1-S1…S11 exist (the names contain `is-w1-s<n>`), each with `docs/handoffs/IS-W1-S<n>.md` whose first line is not `Status: STOPPED`. SW: branches for SW-W3-S1…S4 exist, each handoff `docs/v2.3/sessions/SW-W3-S<n>.md` without `BLOCKED`. |
| G2 | `PRESENT docs/api/v1/consumers/swarmai.md` and `PRESENT scripts/mock_splitsignal.py` (SP1, SP2); `IS-W2-MERGE.md` in IS handoffs; `SW-W3-S1.md`…`SW-W3-S4.md` and `SW-MERGE-W3.md` in SW sessions. |
| G3 | Lines `SP3: reached …` and `SP4: reached …` printed; 9 `is-w3-*` branches with handoffs; SW-W4-S1 and SW-X1-S1 branches with handoffs. If IS-W2-DEPLOY STOPPED, see §5 before slot 4 (slot 4 can still run; its redeploy then skips). |
| G4 | `IS-W4-MERGE.md` in IS handoffs; `SW-W4-S1.md`, `SW-X1-S1.md`, `SW-MERGE-W4.md` in SW sessions. `SP5: reached` is expected here; if it is missing, IS-W6/W8-MERGE make one streaming call as the fallback. |
| G5 / G7 | 7 `is-w5-*` / 5 `is-w7-*` branches with handoffs. |
| G6 | `IS-W6-MERGE.md` in IS handoffs. |
| G8 | `SP6: reached …` and a `swarmai-consumer 1.` line printed from `v2.3-offline.md`. |
| G9 | SW-X2-S1 branch pushed; its handoff states SP4/SP5/SP6 and the call count (≤ 2). |

---

## 5. A STOPPED session: the resume procedure

**How you notice.** An IS session ends with the line `STOPPED <ID>: <reason>. Handoff docs/handoffs/<ID>.md @ <sha>`, its handoff starts with `Status: STOPPED`, and its PR title (or PR description) starts with `[STOPPED]`. A swarmai session ends with a message naming the STOP condition (S1–S8), its handoff `docs/v2.3/sessions/<ID>.md` has `## Status` = `BLOCKED: …`, and its draft PR starts with `[BLOCKED]`. In both repos the work so far is committed (`WIP …`) and pushed. Nothing is lost.

**Step 1: read the handoff's STOP reason and fix the cause.**

| Cause (STOP condition) | Fix, then resume |
|---|---|
| An env var printed `MISSING` (IS STOP 4, SW S6) | Finish preflight items 2–4, then resume in a **new** agent (old agents never see new secrets). |
| An approval line is missing (SW S7, IS approval grep) | Approve the item in §2; the coordinator writes the line; resume. |
| An external gate is not reached (SW S7: SP1/SP4) | Wait until the gate passes (§4.3), then resume. |
| A dependency is not merged yet (IS setup `NO_CHECK_SH`, SW dependency check) | Run the wave's MERGE prompt first, then resume. |
| A check still fails after 2 attempts, or the prompt contradicts the code (IS STOP 1/2/6, SW S3/S4) | The coordinator (Codex or Claude) reads the handoff, fixes the prompt on `cursor/v23-plan-460c` and records the fix in that repo's `PROMPT_FIXES.md`; then resume with the fixed prompt. |
| A file outside the owned list is needed (IS STOP 3, SW S5) | The coordinator decides the owner of that file (usually the next MERGE session) and records it; resume or leave it for the MERGE session. |
| Context ran out (IS STOP 7) | Resume immediately. |
| Push failed after retries (SW S8) | Retry later; resume. |

**Step 2: start a NEW Cursor agent** on the same repo and paste this preamble, filled in, followed by the whole prompt file (the latest version from `cursor/v23-plan-460c`):

```text
RESUME. This session continues <SESSION_ID>, which stopped earlier.
- Its branch <BRANCH> already exists on origin at <SHA>. Do not create a new branch:
  git fetch origin <BRANCH> && git checkout -B <BRANCH> origin/<BRANCH>
  Wherever the prompt creates or names the session branch, use <BRANCH>
  (inference_server prompts: run `git config splitsignal.session-branch <BRANCH>`).
- Read <HANDOFF PATH> first. It stopped because: <REASON>. That cause is now fixed: <WHAT CHANGED>.
- Keep every commit already on the branch. Skip steps whose results are already committed; start at the
  handoff's "Next bounded action". Never rebase, amend or force-push. If the prompt's dependency check
  needs newer integration files, run `git merge --no-ff origin/<INTEGRATION BRANCH>` into your branch.
- Live calls already made by earlier runs of this session: <N, from the handoff or evidence file>.
  The prompt's call cap counts calls across all runs of this session.
- When you finish, replace the STOPPED/BLOCKED status line in the handoff and drop the [STOPPED]/[BLOCKED]
  prefix from the PR title (or the PR description in the handoff).
Then follow the prompt below exactly.
```

**Special cases.**
- **MERGE prompts** (IS-Wn-MERGE, SW-MERGE-*) need no preamble: re-run the same prompt. They skip sessions already merged and pick up the rest.
- **IS-W2-DEPLOY** is safe to re-run: migrations are additive, `import-key` is idempotent on the digest, and the Render env is replaced as a whole. Keep the live chat calls within 2 across runs (IS-A6). If it stopped before any chat call, the full 2 are still available.
- **SW-X2-S1** STOPs before any network call when a gate is missing, so a resume after the gate passes still has its 2 calls. If it already made calls, a further run needs a new owner line `SW-PREAPPROVAL-A3-R<n>: APPROVED`, because those calls exceed the joint cap of 7.
- If a session keeps stopping after one resume, leave it STOPPED. The wave's MERGE session lists it as carried over and the next wave continues where its dependencies allow.

---

## 6. Final V2.3 acceptance (joint evidence checklist)

Both repos must pass their own list and the joint list before the owner merges.

**inference_server (on `cursor/is-v23-integration-460c`)**
- [ ] Every IS session W0–W8 is merged, or listed as carried over with a reason in a MERGE handoff.
- [ ] `scripts/check.sh` ends with `check.sh: OK` on the integration tip (Postgres required; only the documented probe skips).
- [ ] `docs/api/v1/openapi.yaml` is version `1.3.0` and its contract tests pass; all 11 new migrations are applied in tests.
- [ ] `docs/evidence/v2.3-offline.md` maps ROADMAP v0.3–v2.3 to tests and SHAs, lists the open owner gates, and has the section `## SwarmAI consumer contract (joint sync points)` with `Consumer contract version: swarmai-consumer 1.x` and `SP1`…`SP6` lines.
- [ ] `docs/evidence/m1/hosted-v05.md` has the IS-W2-DEPLOY section plus the W4/W6/W8 redeploy sections, and the lines `SP3: reached`, `SP4: reached`, `SP5: reached`; no secret values.
- [ ] `docs/splitsignal/release/v2.3-readiness.md` lists what "VERSION v2.3 reached" still needs. `PROGRESS.md` has `CODE-COMPLETE vX.Y @ <sha>` lines and no `VERSION v2.3 reached` line unless every gate and review is recorded.
- [ ] Live calls ≤ 5 in total (IS-A6), each recorded with request id and usage, no content; spend $0.
- [ ] Codex has reviewed the integration tree, including every session labelled `Codex review pending`, and recorded `RECOMMEND_ACCEPT <sha>` (IS-A2, IS-A9).

**swarmai (on `cursor/sw-v23-integration-460c`)**
- [ ] SW-W0…W4, SW-X1-S1 and SW-X2-S1 are merged (SW-W3-S5 and SW-W1-S13 are optional), each labelled `Codex review pending` until reviewed.
- [ ] The full offline verify, the PostgreSQL integration tests, ruff and mypy pass on the integration tip (one private database per run).
- [ ] `docs/v2.3/EXIT_CHECKLIST.md` has every "V2.3 implementation-complete" item true with a citation, or honestly pending (V23-A11 without SW-A5).
- [ ] The V2.3 probes A01–A10 pass (10/10) through `scripts/v23_acceptance_campaign.py`; evidence under `docs/evidence/v23/`.
- [ ] The EXIT_CHECKLIST row "SplitSignal consumer adapter" reads `done (fake SplitSignal); live SP4 verified, SP5 <verified/not reached>; SP6 reached`, and `docs/evidence/v23/splitsignal_live.json` has no key and no content (`grep -c ss_live_` and `grep -c '"content"'` print 0).
- [ ] `docs/v2.3/STATUS.md` has the SP1–SP6 table.
- [ ] Live calls ≤ 2 (SW-A3); spend $0.
- [ ] Codex has reviewed each PR and the merged range (SW-A2, B-03).

**Joint**
- [ ] Both evidence files cite the same contract: `swarmai-consumer 1.x` (inference_server `docs/evidence/v2.3-offline.md`, swarmai `docs/v2.3/STATUS.md` and `docs/evidence/v23/splitsignal_live.json`).
- [ ] The SP1–SP6 states agree: every SP that swarmai records as verified or reached is `reached` in inference_server's evidence.
- [ ] Joint live calls ≤ 7 (IS-A6 5 + SW-A3 2), spend $0, no paid service, no new account.
- [ ] Neither repo contains a secret: `git grep -nE 'ss_live_[0-9a-f]{32}_|AIza|rnd_|postgresql://[^@ ]*:[^@ ]*@'` prints only the synthetic test key and placeholders.
- [ ] The Desktop secrets file stays on the Desktop only (D6); no value appears in any PR, handoff or chat.
- [ ] Then the owner merges inference_server integration → `main` and swarmai integration → `dev`.

---

## 7. Consistency check between the two plans (2026-09-26)

### 7.1 Shared contract facts (now identical in both plans)

| Fact | Agreed value | Where it is defined |
|---|---|---|
| Env names | `SPLITSIGNAL_BASE_URL` (public URL + `/v1`), `SPLITSIGNAL_API_KEY`, `SPLITSIGNAL_MODEL` (default `gemini/gemini-3.5-flash-lite`; `mock/ok` against the mock) | IS-W1-S10 §3, IS SECRETS_SETUP §5/§8, SW PLAN C5/§5.1 |
| Contract path and version | inference_server `docs/api/v1/consumers/swarmai.md`; `Consumer contract version: swarmai-consumer 1.0.0` at freeze, additive-only `1.x` until V2.3; independent of the `openapi.yaml` document version (1.0.0 → 1.1.0 W4 → 1.2.0 W6 → 1.3.0 W8) | IS-W1-S10 steps 6–7, IS PLAN §8.1, SW PLAN §5.1 |
| `/v1/models` | OpenAI list shape `V1ModelList` = `{"object":"list","data":[{"id","object":"model","created","owned_by"}]}`, no pagination, ≤ 1000 items (already in `openapi.yaml` on the IS integration branch) | IS-W1-S10, SW PLAN C4/§5.1 (SwarmAI also tolerates `ModelPage`) |
| Streaming | `text/event-stream` `ChatCompletionChunk`s; finish chunk carries `splitsignal`; usage chunk (`choices: []`) only with `stream_options.include_usage` (SwarmAI sends it); `data: [DONE]`; `: keep-alive` heartbeats; a failure after headers is `event: error` + `ErrorEnvelope`, status stays 200, no `[DONE]` | IS-W1-S10 §3, SW PLAN §5.1 |
| Errors | `ErrorEnvelope{error:{code, message, request_id, retryable, field_paths?, retry_after_s?, reason?, …}}`; every error has `X-Should-Retry: false`; 403 `forbidden` with `reason` `scope_missing` / `route_not_allowed`; `Retry-After` (1..3600 s) only on 429/503; at most 2 retries, only when `retryable`, never before `Retry-After`, never after a 200 header | IS-W1-S10, SW `_CODE_CLASS` (every code is in the IS `ErrorCode` enum) |
| Rate-limit headers | the six `x-ratelimit-*` headers are optional and informational; the real server sends none until real quota windows exist (AUD-08, IS-W1-S6); the mock and SwarmAI's fake send demo values; never used for admission or retry timing | IS-W1-S10, IS PLAN §8.1, SW PLAN §5.1 |
| Key | `Authorization: Bearer ss_live_<32 lowercase hex>_<43 base64url>`; generated by the owner (IS SEC-13, `openssl`); imported by IS-W2-DEPLOY with `admin_keys import-key --label swarmai --scopes models:read,inference:write,usage:read --from-env SPLITSIGNAL_API_KEY`; only its SHA-256 digest is stored; ≤ 90 days | IS SECRETS_SETUP §5, IS-W2-DEPLOY step 4, SW PLAN §5.1 |
| Sync points | SP1–SP6 with the same conditions: files or column-0 `SPn: reached` lines on `cursor/is-v23-integration-460c`; consumed on `cursor/sw-v23-integration-460c` | IS PLAN §8.1 = SW PLAN §5.2 |
| Secret counts | 17 names in the Desktop file (15 Cursor names + 2 Google OAuth), 4 group headers; 15 Cursor names (SEC-1…SEC-15) | IS SECRETS_SETUP §8/§9, IS OWNER_PREFLIGHT Part 5, SW OWNER_PREFLIGHT Part 2 |

### 7.2 Mismatches found and fixed (both `cursor/v23-plan-460c` branches and the `/agent/audit` mirrors)

1. **Rate-limit headers.** IS-W1-S10 required six `x-ratelimit-*` headers on chat success and 429, while IS-W1-S6 removes them from the real server (AUD-08) and SwarmAI's fake sends them. Fixed: optional and informational everywhere (IS-W1-S10, IS PLAN §8.1, SW PLAN §5.1, SW-X1-S1 Step 0).
2. **Contract version.** IS-W1-S10 said `swarmai-consumer 1.0.0` "pinned to openapi.yaml 1.0.0", but W4/W6/W8 bump openapi to 1.1.0–1.3.0; SwarmAI said "openapi 1.0.0, 1.x". Fixed: consumer version is independent and additive (`1.x`), with a grep-able `Consumer contract version:` line (IS-W1-S10, both PLANs).
3. **SP6 could never be observed.** SW-X2-S1 greps `docs/evidence/v2.3-offline.md` for `swarmai-consumer 1.`, but IS-W8-MERGE never wrote it. Fixed: IS-W8-MERGE step 5 writes the contract section with the version and `SP1`…`SP6` lines.
4. **SP3/SP4/SP5 were not machine-checkable, and SwarmAI had no SP4 gate before its live calls.** Fixed: IS-W2-DEPLOY writes `SP3:`/`SP4:` lines, IS-W4-MERGE writes `SP5:`; SW-X2-S1 Step 0b stops with no call unless `SP4: reached` exists and adds `--stream` only when `SP5: reached` exists (IS-W2-DEPLOY, IS-W4-MERGE, SW-X2-S1 body regenerated by `tools/gen_prompts.py`, both PLAN SP tables).
5. **SP5 lost under C8.** Only IS-W4-MERGE made the streaming call; if its redeploy was skipped (secrets missing, C8), SP5 never happened. Fixed: IS-W6-MERGE and IS-W8-MERGE make the one streaming call when no `SP5: reached` line exists (still 1 call per redeploy, IS-A6).
6. **Joint live-call budget.** IS-A6 counted "at most 5 calls in total", but SW-A3's 2 calls hit the same owner Gemini connection, and SP6 re-runs of SW-X2-S1 could add more. Fixed: joint maximum 7 stated in both preflights and PLANs, SW-A3 proposed wording updated, SW-X2-S1 scheduled after IS-W8-MERGE so no re-run is needed.
7. **Approval ID collision.** Both repos have `A3` and `A5` with different meanings. Fixed: IS-An / SW-An namespace notes in both PLANs and preflights and in this file (§8). The grep-able decision lines themselves are unchanged (`PREAPPROVAL-An` vs `SW-PREAPPROVAL-An` never collided in a grep).
8. **Secret counts and `SPLITSIGNAL_MODEL`.** IS SECRETS_SETUP said `SPLITSIGNAL_MODEL` is "not in the Desktop file or the §9 prompt" and counted 16/14; swarmai C5 puts it in the file (17/15). Fixed: `SECRETS_SWARMAI_SECTION.md` merged into IS SECRETS_SETUP (SEC-15, §9 E1/G/H/final report, §10), IS OWNER_PREFLIGHT Part 5 lists SEC-15, IS PLAN §6 says SEC-1…SEC-15.
9. **Public-repo secret setting.** The IS prompt told the computer-use agent not to change the setting; swarmai R-1 recommended allowing it. Fixed: SECRETS_SETUP §9 STEP G-PUBLIC (allow for `pri8771/swarmai` only, if offered) and STEP I (owner chooses public or private), plus preflight item 3.
10. **Streaming usage chunk.** SW PLAN described the usage chunk as always present; IS sends it only with `stream_options.include_usage`. Fixed in SW PLAN §5.1 (SwarmAI's base client already sends the option).
11. **`/v1/models` shape abbreviated.** SW PLAN §5.1 showed `{data:[{id, owned_by}]}`. Fixed to the full OpenAI list shape.
12. **Base URL handling and model fallback wording.** IS-W1-S10 said the client passes the base URL unchanged and has no fallback; SwarmAI strips `/v1`, and its smoke tool may re-run once with a listed id. Fixed: IS-W1-S10 allows both URL styles (identical requests) and distinguishes the explicit, recorded smoke re-run from runtime substitution (never allowed).
13. **Generic "SW integration session".** IS docs named the swarmai side generically. Fixed: they name SW-X1-S1 (adapter) and SW-X2-S1 (live smoke).

### 7.3 Not resolved here

- **Retry timing in SwarmAI code.** SwarmAI's merged `RetryOwner` (SW-W0-S3) clamps waits to 30 s, which could retry before a longer SplitSignal `Retry-After`. The contract now forbids that. SW-X1-S1 Step 0 checks the code and records a follow-up under "Needs other owner" if it retries early; the code fix needs a separate swarmai session (not scheduled).
- **IS-A4 text on the IS integration branch.** `docs/DECISIONS.md` on `cursor/is-v23-integration-460c` names the branch `cursor/is-v23-integration` (copied before the `-460c` rename); the plan branch and OWNER_PREFLIGHT say `cursor/is-v23-integration-460c`. Sessions grep only `^PREAPPROVAL-A4: APPROVED`, so nothing breaks. The next IS MERGE session (or the coordinator) should append a clarification line; this plan does not touch integration branches.
- **Cursor's public-repo switch.** Not documented publicly; §2 item 3 and SECRETS_SETUP §9 STEP G-PUBLIC/I handle both outcomes.

---

## 8. Approval ID map

| Joint ID | Decision line (exact) | Repo file | Meaning | Status |
|---|---|---|---|---|
| IS-A1 | `PREAPPROVAL-A1` | inference_server `docs/DECISIONS.md` | V2.3 definition (DEC-1…DEC-7) | APPROVED 2026-09-26 |
| IS-A2 | `PREAPPROVAL-A2` | same | Codex reviewer | APPROVED |
| IS-A3 | `PREAPPROVAL-A3` | same | SplitSignal plans P-v1.1…P-v2.3 | APPROVED |
| IS-A4 | `PREAPPROVAL-A4` | same | Render repoint/redeploy by agents | APPROVED |
| IS-A5 | `PREAPPROVAL-A5` | same | hosted DB migrations, role, key import | APPROVED |
| IS-A6 | `PREAPPROVAL-A6` | same | $0 cap; ≤ 5 IS live calls | APPROVED |
| IS-A7 | `PREAPPROVAL-A7` | same | optional `otel` dependencies | APPROVED |
| IS-A8 | `PREAPPROVAL-A8` | same | CI workflow | APPROVED |
| IS-A9 | `PREAPPROVAL-A9` | same | owner-only `main` merge | APPROVED |
| SW-A1 | `SW-PREAPPROVAL-A1` | swarmai `docs/swarm-mvp/DECISIONS.md` | pause lift (B-01) | APPROVED 2026-09-26 |
| SW-A2 | `SW-PREAPPROVAL-A2` | same | Codex reviewer | APPROVED |
| SW-A3 | `SW-PREAPPROVAL-A3` | same | SplitSignal live smoke, ≤ 2 calls, $0 (§2 item 5) | **PENDING** |
| SW-A5 | `SW-PREAPPROVAL-A5` | same | multi-process evidence run (§2 item 6) | **PENDING** |
