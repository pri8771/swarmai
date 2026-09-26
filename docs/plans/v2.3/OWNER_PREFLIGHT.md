# OWNER_PREFLIGHT (swarmai): everything the owner does once, before the SwarmAI V2.3 sessions run

This is the swarmai delta only. Do the inference_server preflight first: `pri8771/inference_server` → `docs/plans/v2.3/OWNER_PREFLIGHT.md` and `docs/plans/v2.3/SECRETS_SETUP.md` on branch `cursor/v23-plan-460c`. Anything that file already covers is referenced here, not repeated (owner decision D5: one preflight, done before sessions start).

Only one SwarmAI session needs anything from this list: **SW-X2-S1** (the live smoke). Waves W0–W4 and SW-X1-S1 use fakes and a synthetic key, so none of the items below blocks them. If an item is missing when SW-X2-S1 runs, that session stops at its gate (STOP S6 or S7), records the gap and pushes. It never waits.

## Status (2026-09-26)
- [x] Accounts: confirmed by the owner (D1). See Part 1.
- [ ] Secrets and env vars: `SPLITSIGNAL_API_KEY` and `SPLITSIGNAL_BASE_URL` come from the inference_server secrets prompt. Append `SECRETS_SWARMAI_SECTION.md` to that prompt for `SPLITSIGNAL_MODEL` and the swarmai check. See Part 2.
- [ ] Remaining decisions R-1 to R-3 (Part 4).
- [ ] Approvals SW-PREAPPROVAL-A3 and A5 (Part 3). Everything else there is already APPROVED 2026-09-26.

## Part 1: Accounts (D1: every account uses Sign in with Google as the owner's Google account (named in the inference_server preflight))
SwarmAI needs no account beyond those in the inference_server preflight Part 2.

| ID | Account | Used by swarmai for | Status |
|---|---|---|---|
| IS ACC-1 | GitHub `pri8771` (repo `pri8771/swarmai`, **public**) | branches, draft PRs, read-only `gh` | exists, signed in |
| IS ACC-2 | Cursor Dashboard → Cloud Agents → Secrets | the three `SPLITSIGNAL_*` values (Part 2) | exists, signed in |
| IS ACC-3 | OpenAI Codex (independent reviewer, D2) | every session PR and MERGE range. **Check:** Codex's GitHub connector can read `pri8771/swarmai` as well as `pri8771/inference_server` | exists; swarmai read access confirmed by the owner (D1) |

## Part 2: Secrets and environment variables
All three values sit under `# --- swarmai ---` (or `# --- shared ---`) in `~/Desktop/splitsignal-swarmai-secrets.env` (D6), and are then entered in Cursor Dashboard → Cloud Agents → Secrets. Sessions check them only with `test -n "$NAME"`; values are never printed or committed.

| Name | Source | Destination and scope | First needed by | Notes |
|---|---|---|---|---|
| `SPLITSIGNAL_API_KEY` | IS SEC-13: generated locally (`ss_live_<32 hex>_<43 base64url>`); group `shared` | Cursor **Runtime Secret**, repos `pri8771/inference_server` **and** `pri8771/swarmai` | SW-X2-S1 (usable once IS SP3 imports its digest) | Secret. Rotate at most every 90 days (IS SECRETS_SETUP §7). |
| `SPLITSIGNAL_BASE_URL` | IS SEC-14: `SPLITSIGNAL_PUBLIC_URL` + `/v1`; group `swarmai` | Cursor **Environment Variable**, repo `pri8771/swarmai` | SW-X2-S1 (live from IS SP4) | Not secret. It must end in `/v1`; the client strips the suffix. |
| `SPLITSIGNAL_MODEL` | Config value (C5). Recommended default `gemini/gemini-3.5-flash-lite`, the Gemini free-tier route id in the SplitSignal quickstart | Cursor **Environment Variable**, repo `pri8771/swarmai`; group `swarmai` in the Desktop file | SW-X2-S1 | Optional: when unset, SwarmAI uses the same default. If `/v1/models` does not list it, SW-X2-S1 substitutes the single listed `gemini/` id and asks you to update this value. |

Not needed: no provider keys (SwarmAI never calls Gemini or OpenRouter directly in V2.3), no database secret (sessions use a local PostgreSQL `swarm:swarm` test role on `127.0.0.1`, which is not a secret), and no `SWARM_ROUTER_*` (the legacy router is retired, IS X6).

## Part 3: Approvals
The decision lines are recorded in `docs/swarm-mvp/DECISIONS.md`. SW-X2-S1 accepts only the exact line `- SW-PREAPPROVAL-A3: APPROVED <date>`.

- [x] **SW-PREAPPROVAL-A1: APPROVED 2026-09-26. Lift the pause (B-01).** "My instruction 'get to V2.3 for both projects' lifts `pause: true` in `docs/agents/CURRENT.md`. V2.0 depth items E03–E10 and the V2.3 sessions may start."
- [x] **SW-PREAPPROVAL-A2: APPROVED 2026-09-26. Reviewer (D2).** "Codex is the independent reviewer. A session is accepted only by Codex `RECOMMEND_ACCEPT <sha>` on its exact head SHA."
- [x] **Integration-branch workflow: APPROVED 2026-09-26 (coordinator decision C1, under the owner's bundle approval).** "Agents never merge into `dev` or `main`. Session PRs target `cursor/sw-v23-integration-460c`. SW-MERGE prompts merge them after checks pass, labelled `Codex review pending` (as in inference_server C6). The owner merges integration into `dev`."
- [x] **D-SS1: APPROVED 2026-09-26 (coordinator-accepted C3; the owner may override).** "A route listed by SplitSignal's key-scoped `/v1/models` is treated as free. A response is refused only when it reports a known non-zero cost. An unknown cost is recorded as unknown (`null`), never as zero, and never releases budget."
- [x] **Spend cap $0: APPROVED 2026-09-26 (IS PREAPPROVAL-A6).** "No paid calls, no paid services and no account creation for SwarmAI."
- [ ] **SW-PREAPPROVAL-A3: PENDING. SplitSignal live smoke.** Proposed wording: "SW-X2-S1 may make one live run against `SPLITSIGNAL_BASE_URL` with `SPLITSIGNAL_API_KEY`. That is at most 2 chat calls (one non-streaming, one streaming), each with `max_tokens` 16, on one free route listed by `/v1/models`, with a 60 s wall-clock limit and a $0 budget. A known non-zero cost stops the run. Sanitized metadata only is committed to `docs/evidence/v23/splitsignal_live.json`." To approve, reply `approved A3`. The coordinator then changes the line in `docs/swarm-mvp/DECISIONS.md` to `- SW-PREAPPROVAL-A3: APPROVED <date>`.
- [ ] **SW-PREAPPROVAL-A5: PENDING. Multi-process/private evidence run (V23-A11, blocker B-04).** Proposed wording: "Agents may run the V2.3 acceptance campaign as two local processes that share one local PostgreSQL, with no provider or model calls and no deploy. The result is recorded as private evidence under `docs/evidence/v23/`." Without it, SW-W4-S1 records V23-A11 as `pending (owner gate)`. That result is allowed by the checklist item "complete or honestly pending", so it blocks nothing.

## Part 4: Remaining decisions (recommended answer first)
- **R-1: Secret injection for the public repo.** `pri8771/swarmai` is public, so Cursor may withhold secret injection. Recommended: in Cursor Dashboard → Cloud Agents → Secrets, allow secrets for `pri8771/swarmai`. The alternative is to make the repo private. Only SW-X2-S1 is affected. Without either change it stops at S6 and records `SPLITSIGNAL_API_KEY MISSING`.
- **R-2: Stale draft PRs (B-06).** Recommended: close #42, #43 and #44 (their content is already in `dev` or superseded), and leave the codex donor stack #18–#40 open until V2.3 is merged into `dev`. Agents cannot do this (`gh` is read-only).
- **R-3: After SW-W4-S1 and Codex acceptance.** You merge `cursor/sw-v23-integration-460c` into `dev` (C1). A later `dev` → `main` merge and tag stays yours (HL-01, B-07).

## Rollback
Remove `SW-PREAPPROVAL-A3` (set it to `REVOKED <date>`) to stop any live call. Remove the three `SPLITSIGNAL_*` entries from Cursor to disconnect SwarmAI. Revoke the key on SplitSignal with `python -m splitsignal.admin_keys revoke-key` (IS SECRETS_SETUP §7).
