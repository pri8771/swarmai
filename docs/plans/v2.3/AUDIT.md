# SwarmAI audit — road to V2.3

Audit date: 2026-09-25 (UTC ~22:50–23:10). Auditor: Cursor cloud agent (read-only audit; no edits, commits, branches or PR mutations in either repo).
Scratch clones used for running checks: `/tmp/swarmai-dev` (@ `origin/dev`) and `/tmp/swarmai-main` (@ `origin/main`). The source checkout `/agent/repos/swarmai` was left clean on `main`.

**Revision 2026-09-26.** This revision applies owner decisions D1–D6 and B-01 and coordinator decisions C1–C5 (the table is in PLAN.md §0). It adds SW-X2-S1 (live smoke), the six SW-MERGE prompts, the SYNC POINTS table (PLAN.md §5.2), `OWNER_PREFLIGHT.md` and `SECRETS_SWARMAI_SECTION.md`. It also folds in the executor's `PROMPT_FIXES.md` (private PostgreSQL database per session). Findings and blockers below carry their resolution inline. The original text is kept.

### Refs at revision time (2026-09-26 ~01:00Z)
| Ref | SHA | Note |
|---|---|---|
| swarmai `origin/dev` | `8e1c0fde` | unchanged; plan base |
| swarmai `origin/cursor/sw-v23-integration-460c` | `d628d28d` | created by the executor from `origin/dev`; W0-S1..S3 and W1-S1..S3 merged (branches `cursor/sw-<id>-460c`) |
| inference_server `origin/cursor/v23-plan-460c` | `28232556` | IS plan: adds C6 (merge with `Codex review pending`) |
| inference_server `origin/cursor/is-v23-integration-460c` | `a685c884` | exists; IS-W0-S2 merged. **SP1 not reached yet** (`docs/api/v1/consumers/swarmai.md` absent) |

---

## 1. Baseline

| Item | Value |
|---|---|
| Repo | `pri8771/swarmai` (default branch `main`) |
| Local checkout | `/agent/repos/swarmai`, branch `main`, clean, up to date with `origin/main` |
| `origin/main` | `08b910f981eff2ab66873a71055090f2c60f2a91` (2026-09-23, "Merge pull request #41 …") |
| `origin/dev` | `8e1c0fdec24c131e7612d88076220945230f4c3b` (2026-09-25 21:12Z, "Merge pull request #69 … v20-agents-context") |
| `main...dev` | main is **0 ahead / 70 behind** dev; merge-base = `08b910f9` (dev is a strict superset of main) |
| `main→dev` diff | 256 files, +43,029 / −310 |
| Alembic head | main: `a18tov30schema0001`; dev: `a20pursuitpersist0001` (single head on each) |
| Package version | `pyproject.toml` `version = "1.0.0rc1"` on both branches |
| Tags | `v3.0.0-impl.1`, `v0.1.0-rc.1` (labels, not accepted releases) |
| Recorded AI state (`docs/agents/*` on dev) | `pause: true`, `v20_work: STOPPED`, verified tip `dd7726eb` (**stale by 2 docs-only merges #66, #69**) |
| `inference_server` `origin/main` | `6aeec2d410b9c89340def7622138337f93c16309` (docs-only bootstrap) |

### "Both branches"
Interpreted as the two long-lived branches of this repo: **`main`** (release line, frozen by rule HL-01 "no merge to main") and **`dev`** (integration line where all V1.7→V2.0 work lands; rule HL-07 "PRs target dev only"). Every other branch is a short-lived lane, donor or coordination branch (see §2).

---

## 2. Branch map

| Branch | Tip | Relation to `dev` | Status / meaning |
|---|---|---|---|
| `main` | `08b910f9` | 0 ahead, 70 behind | Release line. PR #41 "V1.4→V3.0 implementation-complete lane (no launch)" merged 2026-09-23. Untouched since. |
| `dev` | `8e1c0fde` | — | Integration line. FAST_TRACK L1–L6 (#60–#65), portable P1–P4 (#53–#58), V1.7–V2.0 lanes (#46–#52) merged 2026-09-25. CI green. |
| `coordination/swarm-control` | `753ffbe4` | 4126 ahead / 92 behind | Heartbeat/coordination state branch (`[skip ci]` heartbeats every few minutes). Not product code. |
| `plan/swarmai-v2-redesign-20260925` | `8598e6ac` | 20 ahead | "Planning donor only" per `docs/swarm-mvp/EXECUTION_MAP.md`. |
| `cursor/v20-fast-track-docs-4635` | `fca35cfd` | 1 ahead / 4 behind | Open draft **PR #67** (docs, V20-E02). |
| `cursor/v2-product-completion-plan-11e2` | `6ff29049` | 1 ahead / 21 behind | Open draft **PR #59** (plan). |
| `cursor/v20-tracking-tipsync-02dc` | `2f2e1659` | 1 ahead / 4 behind | Leftover of closed PR #68 (CandidateManifest rebind WIP). |
| `cursor/v20-native-model-loop-6d50` | `dd7726eb` | 0 ahead | Empty branch placeholder for V20-E05 (no commits). |
| `cursor/two-host-mvp-b28d` | `180eb73a` | 0 ahead / 62 behind | Fully merged into dev; still an open draft **PR #44 → main**. |
| `cursor/openrouter-free-live-de09` | `f8f234fd` | 5 ahead / 71 behind | Open draft **PR #43 → main** (OpenRouter free canary; blocked by missing key). |
| `cursor/restore-live-local-tests-712f` | `fd8b5c3b` | 3 ahead / 71 behind | Open draft **PR #42 → main**. |
| `codex/swarm-*-20260922` (≈25 branches) | e.g. `f25eb19e` | ~175 ahead / 92 behind | Stacked draft **PRs #18–#40** on each other (not on dev). "V1.7 donor" per plan; modules like `broker/durable_remote.py`, `providers/multiplex.py`, `tools/fences.py`, `tools/effect_recovery.py`, `mission/action_boundary.py` exist **only** there. |
| `cursor/v1.4-live-integration-11e2` | — | — | Open draft **PR #14 → main** (historical). |

GitHub state: **0 issues** (issues enabled, never used), **0 milestones**, only default labels. Tracking lives in repo docs (`docs/agents/`, `docs/swarm-mvp/`, `docs/coordination/`) and a (needsAuth) Linear queue. Recent CI (`ci` workflow: jobs offline, integration, console, live-gated) is **green** on dev tip `8e1c0fde` (run 36190284972) and on every FAST_TRACK merge.

Open PR count: 26 drafts (list in §8). None target V2.3.

---

## 3. What "V2.3" means (with sources)

**Defined explicitly** — not an assumption. Sources (identical on `main` and `dev`):

- `docs/artifacts/future/ART-V23-OPS_PLATFORM.md` — "V2.3 operational platform architecture". Five artifact families + 7 invariants + a 10-point acceptance protocol.
- `docs/artifacts/future/ART-V23-MULTIMISSION_SCHEDULER.md` — fair multi-mission scheduler contract (weighted deficit round robin, `ProjectQueueState`, `MissionQueueState`, `DispatchIntent`, `SchedulingDecisionReceipt`, restart/epoch rules, 11 pathological cases, ±15%/≥200-decision tolerance proposal).
- `docs/artifacts/future/ART-V23-PORTABILITY_BUNDLE.md` — export/import bundle contract.
- `docs/coordination/VERSION_ARTIFACT_MATRIX.md` — "V2.3 — next major milestone": ART-V23-MULTIMISSION-OPS, -CAPABILITY-PACKS, -PORTABILITY, -OBSERVABILITY, -FLEET-POLICY.
- `docs/coordination/FUTURE_VERSION_EXIT_CHECKLISTS_20260921.md` §"V2.3 implementation-complete" — 16-item checklist (quoted in §3.2).
- `docs/v2.3/STATUS.md` — claims "Operational platform implementation-complete (local)"; "Multi-process/private live evidence: UNKNOWN". **This claim is not supported by the code (see §4.2).**

### 3.1 Dependency chain
`ART-V23-MULTIMISSION_SCHEDULER.md`: "Depends on: V2.0 integrated candidate, ART-V15 durable workers, ART-V12 broker." `ART-V23-OPS_PLATFORM.md`: "Do not assign these packets until they are non-conflicting with the active V2.0 critical path and the lead has registered/frozen the relevant V2.3 artifact contracts." → V2.0 engineering depth items (V20-E03…E07) are prerequisites, not optional.

### 3.2 V2.3 implementation-complete checklist (verbatim source) and current truth

| # | Checklist item | Current state on dev `8e1c0fde` |
|---|---|---|
| 1 | scheduler state durable | ❌ `DurableFairnessStore` is a process-local dict. ORM tables `project_scheduling_state`/`scheduler_policies` exist but have **zero call sites**. |
| 2 | project-level fairness defined | ⚠️ Contract defined in ART; code uses `debt += 1/weight`, `debt -= 0.5` heuristic — not WDRR; no mission-level fairness. |
| 3 | aging/priority deterministic | ⚠️ `AdaptiveScheduler` ages by tick; per-process; no persisted policy version. |
| 4 | reservation intent transactional/fail-closed | ⚠️ `ReservationService` is in-memory; no `preparing/ready/compensating/expired` states; no expiry recovery. |
| 5 | provider/worker/tool capacity integrated | ❌ `ResourceAllocator` reserves string IDs against a local capacity dict; not connected to broker `QuotaLedger`, worker leases or tool gateway. |
| 6 | backpressure bounded | ⚠️ floor check only; no queue-depth/fan-out caps. |
| 7 | cancellation/drain fenced | ⚠️ boolean `draining` flags per object; no cancellation-generation check on dispatch. |
| 8 | scheduler bound to SiteEpoch | ⚠️ `AdaptiveScheduler` calls `SiteAuthorityService.require_epoch`; no scheduler epoch / single dispatch authority. |
| 9 | decision receipts emitted | ⚠️ `SchedulingReceiptLog` in memory, only from `ResourceAllocator`; missing most ART fields (policy_version, candidate_set_hash, deficits before/after, wait age…). |
| 10 | capability packs lifecycle complete | ❌ register/grant/revoke only; no `installed→enabled_for_project→draining→disabled→uninstalled`; "signature" is an unkeyed SHA-256 (forgeable). |
| 11 | portability export/import complete | ⚠️ exports config + ref lists only; no mission history/receipts/knowledge/tombstones/artifact hashes; no ID remap; no schema compatibility check; key-name-only secret detection. |
| 12 | observability read surface complete | ❌ `GET /v1/ops/events` exists but **nothing in production emits events** (always empty); no trace linking. |
| 13 | dashboard mutation uses action boundary | ⚠️ `assert_dashboard_mutation_via_action()` helper exists; nothing calls it outside a unit test. |
| 14 | fleet placement/trust/locality complete | ⚠️ tenant/project/locality filter exists; trust class names differ from ART (4 legacy vs 5 ART classes); no drain states; placement picks `candidates[0]` (dict order). |
| 15 | pathological deterministic suite passes | ❌ none of the 11 ART pathological cases are tested. |
| 16 | multi-process/private evidence complete or honestly pending | ❌ not started; STATUS says UNKNOWN. |

**Verdict:** V2.3 is at **"scaffold/contract-shape"** level (≈700 lines across 8 modules, 14 unit tests), not implementation-complete. The `docs/v2.3/STATUS.md` and CHANGELOG "implemented" wording is doc/code drift.

### 3.3 Target definition used by this plan (ASSUMPTIONS flagged)
- **Target = "V2.3 implementation-complete" on `dev`** (after C1: on `cursor/sw-v23-integration-460c`, which the owner merges into `dev`), i.e. all 16 checklist items true with deterministic + PostgreSQL-integration evidence, acceptance items 1–10 implemented as a frozen deterministic harness, and live/multi-process evidence **honestly pending**.
- **ASSUMPTION A1 (owner confirm):** "get to V2.3" means implementation-complete, not "V2.3 accepted". Acceptance additionally requires independent review, operator acceptance and multi-process/private live evidence (owner-gated; see blockers).
- **ASSUMPTION A2 (owner confirm):** V2.0 engineering depth items V20-E03, E04, E05, E06 are in scope (prerequisites per ART). V20-E07 (live adapter) is in scope only as "fake/free first, honest `blocked_missing_implementation` otherwise". V20-E08/E09/E10 are included as optional parallel sessions; V20-E11 stays deferred.
- **ASSUMPTION A3 (owner confirm):** the `pause: true` recorded in `docs/agents/CURRENT.md` is lifted by the owner's V2.3 request. Session SW-W0-S1 records this; if the owner disagrees, all code sessions must not start. **Resolved 2026-09-26 (B-01):** the owner's instruction "get to V2.3 for both projects" lifts the pause. The plan commit records it in `docs/swarm-mvp/DECISIONS.md` and `docs/agents/CURRENT.md`.
- **ASSUMPTION A4:** package version stays `1.0.0rc1` until the owner decides a version bump (tag/publish are owner actions). Version labels in docs follow the ART roadmap, not package metadata.
- Note: `docs/reviews/CURSOR_REVIEW_2026-09-25/CURSOR_REVIEW_2026-09-25.md` proposes a *different* V1.0–V2.0 roadmap and assesses the product as "V1.0 RC, unaccepted". It does not define V2.3. This plan follows the ART/coordination roadmap, which is the only one that defines V2.3.

---

## 4. Current-state findings

### 4.1 Stack & entrypoints
- Python 3.12 (`uv`), FastAPI (`src/swarm/api/app.py:create_app`, router `src/swarm/api/routes_v1.py`, 2,000+ lines), SQLAlchemy 2 + Alembic (`migrations/versions/`, 7 revisions), PostgreSQL 16 for integration, pydantic-ai[dbos], React/Vite console (`apps/console`), CLI `swarm = swarm.cli:main` (`src/swarm/cli.py`, single large file).
- 236 source files under `src/swarm/` (36 packages). Key durable authority: `db/lease_fencing.py` (1.5k lines), `db/repositories.py`, `api/store.py` (`ProductStore`, 1.2k lines), `api/durable_authority.py` (file-backed JSON).
- Durable pattern today: **file-backed JSON under `var/`** is authoritative for goals/pursuit/workers; PostgreSQL repos exist for missions/leases/effects; `GoalAuthorityRepository` and `PursuitStateRepository` have **zero call sites** (V20-E03).

### 4.2 V2.3 modules (all process-local)
| Module | Lines | Reality |
|---|---|---|
| `src/swarm/controller/fairness.py` | 46 | dict of `ProjectFairnessState`; heuristic debt |
| `src/swarm/controller/reservations.py` | 122 | in-memory capacity dict, epoch & drain check |
| `src/swarm/controller/scheduling_receipts.py` | 76 | in-memory list |
| `src/swarm/controller/resource_allocator.py` | 66 | ignores `rank_projects` result (dead `if … pass`) |
| `src/swarm/controller/scheduler.py` | 155 | per-mission `AdaptiveScheduler`; dependency check is a no-op (`all(True for _ in deps)`) |
| `src/swarm/capabilities/__init__.py` | 102 | registry/grant; unkeyed "signature" |
| `src/swarm/product/portability.py` | 128 | config/ref export only |
| `src/swarm/workers/fleet.py` | 172 | tenant/locality placement over in-memory registry |
| `src/swarm/observability/ops_events.py` | 100 | in-memory; no emitters |

### 4.3 Checks run (exact commands, results)
All in scratch clones with `uv 0.12.19`, Python 3.12.3, PostgreSQL 16 (installed locally for the audit via apt; `swarm/swarm@127.0.0.1:5432/swarm`).

| Tree | Command | Result |
|---|---|---|
| dev `8e1c0fde` | `uv run ruff check .` | All checks passed |
| dev | `uv run mypy src/swarm` | Success: no issues in 236 files |
| dev | `uv run alembic heads` | `a20pursuitpersist0001 (head)` |
| dev | CI offline pytest list (33 dirs, `--ignore=tests/integration`) | **484 passed, 29 skipped, 0 failed** (20.2 s) |
| dev | `SWARM_DATABASE_URL=… uv run pytest tests/integration -q -m integration` | **69 passed** |
| dev | `alembic upgrade head` → `downgrade base` → `upgrade head` on empty DB | clean round-trip |
| dev | `apps/console`: `npm ci && npm run lint && npm run test && npm run build` | lint: warnings only (2); tests 21 passed; build OK |
| dev | `uv run swarm release harden` | ok=true |
| dev | tracked-file secret regex scan (`sk-…`, `AKIA…`, `ghp_…`, `xox[bp]-…`, PEM) | no hits |
| dev + audit reference code (scratch only, never pushed) | Reference implementations embedded in prompts SW-W0-S2 (contracts, ORM, migration, memory store), SW-W0-S3, SW-W1-S1 (WDRR), SW-W1-S10 (F-13) applied to a scratch branch: ruff, mypy (240 files), `alembic heads` → `a23opsplatform0001 (head)`, offline list → **548 passed, 1 skipped**; integration → **70 passed** | Reference code in prompts is known-green against dev `8e1c0fde`. Sources kept in `/agent/audit/swarmai/tools/ref/`. |
| main `08b910f9` | ruff / mypy (184 files) / alembic heads | pass / pass / `a18tov30schema0001` |
| main | pytest all non-integration dirs | **302 passed, 28 skipped** |
| (note) | Same dev suite on a `git archive` extract without `.git` | 20 failures in `tests/release/*` — tests call `git rev-parse HEAD`; **environmental, not a code defect**. Sessions must run tests inside a real git checkout. |
| skipped | Docker compose smoke (`deploy/compose/product.yml`) | Docker not available in audit VM → not run. |
| skipped | live-gated suites | No LiveGrant / credentials; zero-spend policy. |

**Test hygiene trap:** running `tests/release` rewrites tracked `schemas/v1/COMPATIBILITY.md` and `schemas/v1/product_contract.v1.json`; the full suite also rewrites `docs/evidence/fix-004/last-checkin.json` and `runner-state.json`. Every session must run `git checkout -- schemas/v1 docs/evidence/fix-004` before `git add` (included in every prompt).

### 4.4 Security / correctness findings (prioritised per repo review rules)
| ID | Severity | File:line (dev) | Finding | Impact |
|---|---|---|---|---|
| F-01 | P1 cross-tenant | `src/swarm/api/routes_v1.py:2173-2189` | `GET /v1/ops/events` without `project_id` returns events for **all projects**; authorization is only checked when `project_id` is supplied. | Latent cross-project disclosure the moment any emitter is added (V2.3 adds emitters). Fix in SW-W0-S3. |
| F-02 | P1 trust | `src/swarm/capabilities/__init__.py:41-47` | Pack "signature" = `sha256(pack_id|version|digest|caps)` — no key. Anyone can compute a valid signature; `require_signature=False` by default (used by `product/portable_protocol.py:81`). | Signature/trust checks are cosmetic; revocation is the only real control. Fix in SW-W1-S5 (HMAC with publisher key refs). |
| F-03 | P2 secret | `src/swarm/product/portability.py:13-25` | Secret stripping is key-name-only; any value such as `"sk-…"` under a non-secret key (or `"env:"`-prefixed under a secret key) passes. | Possible secret export in bundles. Fix in SW-W1-S6. |
| F-04 | P2 financial | `src/swarm/pursuit/accounting.py:72-260` | `GoalResourceLedger` holds are process-local; restart forgets held budget (V20-E04). | Budget envelopes can be re-spent after restart. Fix in SW-W1-S10. |
| F-05 | P2 recovery | `src/swarm/db/repositories.py:290-464` | Goal/pursuit PG repos have zero call sites (V20-E03). | Postgres is not authoritative for pursuit; file-only durability. Fix in SW-W1-S9 + SW-W3-S2. |
| F-06 | P3 retries | `src/swarm/broker/retry.py:74-75` | `Retry-After` from upstream is used unbounded (`wait = float(retry_after)`); attempt counts are process-local (`_attempt_counts`) so restart resets the retry budget. | A hostile/buggy upstream can park calls indefinitely. Attempts are still bounded (max 3). Fix cap in SW-W0-S3. |
| F-07 | P2 correctness | `src/swarm/controller/scheduler.py:96-104` | Dependency readiness check is a no-op. | Tasks with open dependencies may be selected. Superseded by the WDRR selector (`dependencies_ready` flag) in SW-W1-S1/SW-W2-S1. |
| F-08 | P3 correctness | `src/swarm/controller/resource_allocator.py:37-40` | Fairness ranking computed then ignored. | Fairness has no effect on allocation. Replaced in SW-W2-S1. |
| F-09 | P3 drift | `docs/v2.3/STATUS.md`, `CHANGELOG.md:9`, `docs/v3.0/STATUS.md` | Claim V2.3/V3.0 "implementation-complete". | Unsupported release claim; corrected in SW-W0-S1. |
| F-10 | P3 drift | `docs/agents/*.md`, `context.json` | Tip recorded `dd7726eb`, real tip `8e1c0fde`; `pause: true`. | Resume confusion. Fixed in SW-W0-S1. |
| F-11 | P3 hygiene | `tests/release/test_v1.py`, fix-004 scripts | Tests rewrite tracked files. | Accidental commits. Mitigated in every prompt; optional fix is out of V2.3 scope. |
| F-12 | info | `README.md` "Current label … V0.9 hardening" | Stale label. | Fixed in SW-W4-S1. |
| F-13 | P1 financial | `src/swarm/pursuit/accounting.py` (`_held_totals` / `_settled_totals`) | `_held_totals` counts only `state=="held"`; `_settled_totals` skips `state=="unknown"`. A hold settled with `usage_unknown=True` therefore counts **zero** against `remaining()`, releasing its reservation. `release()` also accepts `unknown` holds (only `settled` is refused). Existing test `tests/pursuit/test_usage_accounting.py::test_unknown_usage_preserved_not_cleared` does not assert remaining amounts, so the fix is compatible. | Unknown usage is treated as zero spend (violates "unknown is never zero"); budget can be over-committed after any unknown-outcome call. Fix in SW-W1-S10 (unknown holds count their reserved amount, conservatively `max(reserved, reported)`). |
| F-14 | P3 drift | `src/swarm/cli.py:580,1078`, `src/swarm/api/routes_v1.py:2205` | Candidate freeze hardcodes `schema_revision="a18tov30schema0001"`; actual head is `a20pursuitpersist0001` (and will be `a23opsplatform0001`). | CandidateManifest names the wrong schema. Fixed in SW-W4-S1 (single constant `CURRENT_SCHEMA_REVISION`). |
| F-15 | P3 hygiene | `src/swarm/api/durable_authority.py:44` (`var/api/idempotency.json`) | Offline tests persist idempotency records into the checkout's gitignored `var/`. A **second** pytest run in the same checkout fails 3 tests (`tests/api/test_api.py::test_idempotent_mutation`, `::test_cancel_blocks_side_effects`, `tests/api/test_fix002_auth_isolation.py::test_idempotency_scoped_and_rejects_body_mismatch`). Reproduced on clean dev 8e1c0fde. | False red on re-runs; CI (fresh checkout) unaffected. Every prompt runs `git clean -fdX -- var/` before pytest. Proper fix (tmp repo_root in those tests) is out of V2.3 scope. |
| F-16 | P2 authz | `src/swarm/api/routes_v1.py:2191-2207` (`freeze_candidate`, dev @ 8e1c0fde) | `POST /v1/release/candidate-freeze` ignores the principal (`_ = principal`): any authenticated operator of any project can run `git rev-parse` and write a CandidateManifest on the control plane. | Release artifacts can be minted by non-admins. Fixed in SW-W4-S1 (admin-only, `forbidden_admin`), test `tests/release/test_schema_revision.py::test_candidate_freeze_requires_admin`. |
| F-17 | P3 observability | `src/swarm/scheduling/service.py::_record` (created by SW-W2-S1) | Non-admit scheduler decisions have no task, so their `scheduler.decision` ops event has `project_id=None` and only appears in the admin (site-wide) view; a project operator cannot see *why* their work is deferred. | Reduced operator visibility, not a leak. Recorded as a follow-up in SW-W3-S4; acceptance probe A09 queries by `kind`. |
| F-18 | P1 integration / zero-spend | `src/swarm/providers/router_client.py` + `contracts/router_capabilities.py` (created by SW-W1-S11 against the legacy personal router @ `96af9d4`) | The inference_server V2.3 plan (D3, §8 X1/X6) makes **SplitSignal** SwarmAI's only inference dependency and retires the legacy router. SplitSignal's key-scoped `GET /v1/models` is the OpenAI list `{object:list, data:[{id, object, created, owned_by}]}` with no billing field. It sends `X-SplitSignal-Served-Route`, not `X-Router-*`, and its errors are `{error:{code,message,request_id,retryable}}`. Through the legacy client every SplitSignal route parses as `billing: unknown` and is refused (`paid_route_forbidden`), and error codes map wrongly (`quota_exhausted` reads as transient). | Without an adapter, SwarmAI cannot use SplitSignal at all (fail-closed, so no spend risk). Fixed by the new gated session **SW-X1-S1** (`SplitSignalClient` subclass, decision D-SS1, 27 offline tests; the fake's bodies were validated against the SplitSignal openapi schemas). Live proof: **SW-X2-S1** (SP4/SP5). |
| F-19 | P3 test hygiene | `tests/pursuit/test_v20_native_loop.py::test_executor_without_loop_records_honest_blocker` (SW-W2-S2) | Once SW-X1-S1 lands, this test fails in any environment that injects `SPLITSIGNAL_BASE_URL` (Cloud Agent secret SEC-14), because the blocker reason changes. Reproduced: 1 failed with the variable set, 8 passed after the fix. | False red in cloud sessions. SW-X1-S1 adds one `monkeypatch.delenv("SPLITSIGNAL_BASE_URL")` line. |
| F-20 | P2 cross-repo contract (inference_server side; report only) | inference_server prompt `IS-W1-S10` step 2/4 vs `docs/api/v1/openapi.yaml` (`cursor/v08-v17-offline-ladder-7ebe`) | IS-W1-S10 has the mock serve `models.list.json` as a **`ModelPage`** (`items[]`) on `GET /v1/models`. The openapi `listV1Models` returns **`V1ModelList`** (`data[]`); `ModelPage` belongs to the cookie-authenticated `GET /api/models`. | The mock and the real server would disagree on the key-scoped model list. SwarmAI's adapter accepts both, so SwarmAI is not blocked. The inference_server coordinator should pick one shape (the openapi says `V1ModelList`). **Resolved by C4 (2026-09-26):** `/v1/models` returns `{"object":"list","data":[...]}`; SwarmAI keeps accepting both. |
| F-21 | P1 financial (SwarmAI side, found in revision) | `providers/splitsignal_client.py::receipt_from_splitsignal` (first X1 draft) | The first draft set `usage_known` from token counts only. A response with tokens but `splitsignal.cost.amount: null` was therefore settled, recording unknown cost as zero spend (the F-13 class). | **Fixed in the X1 reference (C3):** `SplitSignalReceipt.cost_amount/cost_currency/cost_source`; `usage_known` requires tokens **and** a known amount. Tests `test_chat_unknown_cost_never_settles_as_zero` and `test_unknown_cost_keeps_loop_usage_unknown`. |
| F-22 | P3 test hygiene (executor finding) | every prompt's section 6 (before this revision) | Offline and integration pytest used the shared default DB `swarm`. Concurrent sessions on one host dropped each other's tables (`DeadlockDetected`, `relation "missions" does not exist`). | Every prompt and MERGE run now creates and exports `SWARM_DATABASE_URL=.../swarm_<session id>`. |
| — | — | `tests/integration/db/test_action_receipts_durable.py:28` | Hardcodes `NEW_HEAD = "a20pursuitpersist0001"`. | Any new migration must update this constant (assigned to SW-W0-S2). |
| — | — | `rg TODO|FIXME|NotImplementedError src` | 0 hits | Stubs are expressed as thin implementations rather than TODOs. |

### 4.5 Implemented vs stubbed vs docs-only (V2.3 scope)
- **Docs-only:** ART-V23 contracts (status "drafting"), acceptance protocol, pathological list, tolerance proposal, fleet trust classes, trace chain.
- **Stubbed/scaffold:** everything in §4.2; ORM tables `scheduler_policies`, `project_scheduling_state`, `resource_reservation_intents`, `capability_packs` (created by migration `a18tov30schema0001`, unused).
- **Implemented and reusable:** `SiteAuthorityService` (epochs), `WorkerRegistryService` (drain/revoke/generation), `db/lease_fencing.py` (durable task leases), extension registry, `payload_hash`/`new_id`/`StrictModel` helpers, broker `RetryOwner`, `QuotaLedger`, file-atomic-write helpers.
- **Missing entirely:** inference_server HTTP client (planned packet P05: `providers/router_client.py`, `contracts/router_capabilities.py`, fake router fixture) — no `X-Router-*` handling anywhere in `src/`.

---

## 5. Risks
1. **Scope inflation / false claims** — the repo has a history of "implementation-complete" labels ahead of code. Mitigation: every prompt forbids flipping `accepted`, requires deterministic evidence paths, and SW-W4-S1 re-derives status from test output.
2. **Shared-file conflicts** (`db/models.py`, `migrations/`, `api/routes_v1.py`, `api/app.py`, `api/store.py`, `cli.py`) — mitigated by single-owner sessions and new-file-per-session layout (see PLAN.md ownership matrix).
3. **Two alembic heads** if more than one session adds a migration — only SW-W0-S2 may add a migration for V2.3.
4. **Weak-model drift** — prompts include exact signatures, algorithms and test cases; each ends with a "stop and report" rule.
5. **Donor code (codex stack #18–#40) diverges further** — not needed for V2.3 implementation-complete; owner should decide close vs port (blocker B-06).
6. **inference_server contract instability** — no released contract; code lives on unmerged branches. Router client is built against a pinned fixture snapshot; live use stays blocked. The inference_server plan has since switched SwarmAI to the SplitSignal consumer contract (F-18); SW-X1-S1 adapts to it behind gate SP1.
7. **Environment**: CI needs Postgres (provided in CI); local sessions without Postgres can only run offline tests — prompts say how to record that.

---

## 6. Blockers

| ID | Blocker | Type | Owner needed | Unblock action |
|---|---|---|---|---|
| B-01 | `docs/agents/CURRENT.md` says `pause: true`, "do not start E03–E11" | Owner approval | Owner (pri8771) | **RESOLVED 2026-09-26:** the owner's "get to V2.3 for both projects" lifts it (SW-PREAPPROVAL-A1). |
| B-02 | Merging session PRs into `dev` between waves | Process / review | Coordinator (Codex/Claude per AGENTS.md) | **RESOLVED by C1:** `SW-MERGE-<wave>` merges into `cursor/sw-v23-integration-460c` after checks pass (`Codex review pending`); the owner merges integration into `dev`. |
| B-03 | V2.3 "accepted" requires independent review + operator acceptance | Owner/reviewer | Owner + Codex (D2) | After SW-W4-S1/SW-X2-S1, Codex reviews the integration range. |
| B-04 (preflight SW-PREAPPROVAL-A5) | Multi-process/private live evidence (ART acceptance "simulated tests do not replace…") | Owner approval + environment | Owner | Approve a private two-host run (R730 + Mac or 2 containers) with zero-spend profile; blocked R730/CF/DNS remain out of eng scope. |
| B-05 | LiveGrant for any real model call (V20-E07, S12) | Credentials + spending approval | Owner | **Moved into the preflight:** SW-X2-S1 builds a zero-dollar, free-routes-only LiveGrant from `SW-PREAPPROVAL-A3` (PENDING, wording in OWNER_PREFLIGHT); keys per SECRETS_SWARMAI_SECTION. |
| B-06 (preflight R-2) | 26 open draft PRs incl. stacked codex donor PRs #18–#40, #14, #42–#44 → main | Owner housekeeping | Owner | Decide close/supersede; `gh` in sessions is read-only. |
| B-07 | Merge `dev` → `main` and version tag | Owner approval (HL-01) | Owner | Only after B-03. |
| B-08 | inference_server has no merged/versioned HTTP contract; SwarmAI needs context-window/tokenizer/output-limit metadata and idempotency semantics | Cross-repo | inference_server coordinator | Agree on an additive `GET /v1/models` capability fields contract (see PLAN.md §5); SwarmAI keeps a local override file until then. |
| B-09 | Fairness tolerance (±15% after ≥200 decisions) is a proposal | Lead/owner decision | Lead (ChatGPT/Codex/Claude) | SW-W0-S1 freezes the proposed values as `v23-wdrr-1`; lead may amend before counted evidence. |
| B-10 | Docker not available in some agent VMs | Environment | Session operator | V20-E10 compose smoke records `blocked_env_no_docker` if absent. |
| B-11 | Linear MCP needsAuth | Credentials | Owner | Not needed; tracking stays in repo docs. |
| B-12 | SplitSignal consumer contract not yet frozen (sync point SP1: inference_server IS-W1-S10 merged into `cursor/is-v23-integration-460c` (C2); the branch exists at `a685c884`, SP1 not yet reached) | Cross-repo | inference_server coordinator | SW-X1-S1 is fully written and validated but stops at its Step 0 gate until SP1. Live use additionally needs SP3 (key imported), SP4 (hosted smoke) and a LiveGrant (B-05). SW-W4-S1 records the adapter as `pending` if it is not merged. |
| B-13 (**accepted by coordinator C3, 2026-09-26; owner may override**; unknown cost = `null`, never zero, never releases budget) | Decision D-SS1: treat routes listed by SplitSignal's key-scoped `/v1/models` as free (the contract lists only usable routes, and M1 dispatches only `cost_class: free`), refusing a known non-zero cost after the fact | Lead decision | Coordinator | Accept, or ask inference_server to expose `cost_class` on the API-key surface (an additive `swarmai-consumer 1.x` MINOR), after which the adapter already prefers `cost_class`. |

---

## 7. Evidence of cross-repo interface (inference_server, read-only)
- `inference_server` `main` @ `6aeec2d4`: docs only (`docs/STATE.md`: "DISCOVERY / DOCS ONLY").
- Router code exists on branches: `release/v1-build` @ `bb6b6167` (the SHA SwarmAI's plan pinned), `claude/inference-router-implementation-aef2x4` @ `bc7a1d2`, newest `cursor/v08-v17-offline-ladder-7ebe` @ `96af9d4`.
- Observed HTTP surface (`src/inference_router/app.py` on `96af9d4`, lines 539-564): `GET /healthz`, `GET /v1/models` → `{"object":"list","data":[…]}`, `POST /v1/chat/completions` (stream + non-stream), `GET /v1/router/providers`, `GET /v1/router/usage`, `GET /v1/router/analytics`, `GET/POST /v1/mailbox/{channel}`, `/mcp`, `/dashboard`.
- Response headers (`_route_headers`, lines 147-158): `X-Request-Id`, `X-Router-Route`, `X-Router-Provider`, `X-Router-Upstream-Model`, `X-Router-Billing`, `X-Router-Attempts`, `Cache-Control: no-store`; errors add `Retry-After`.
- Error body (`errors.py:27-35`): `{"error": {"type": <openai type>, "code": <stable code>, "message": …}}`.
- Billing policy fail-closed, default `free` only.
- **Superseding direction (inference_server V2.3 plan, `/agent/audit/inference_server/PLAN.md` §8):** SwarmAI calls **SplitSignal** as a plain OpenAI-compatible client with a SplitSignal key (`SPLITSIGNAL_BASE_URL` / `SPLITSIGNAL_API_KEY` / `SPLITSIGNAL_MODEL`). The contract is frozen as `swarmai-consumer 1.x` by IS-W1-S10, with sync points SP1–SP6. The legacy router above is retired (X6). SplitSignal openapi 1.0.0 (read from `cursor/v08-v17-offline-ladder-7ebe`) has `GET /v1/models` → `V1ModelList`, and `POST /v1/chat/completions` → `ChatCompletion` with `usage` (null when unreported) plus `splitsignal` `ResponseMetadata` (served route, `UsageFacts`, `CostFact`). Errors are `ErrorEnvelope`; `retryable` is true only for 7 codes; `X-Should-Retry: false` is always sent. See F-18, F-20, B-12, B-13 and session SW-X1-S1.
- inference_server refs at audit end: `origin/main` `6aeec2d4`, `origin/dev` `804b28bd`, `cursor/v08-v17-offline-ladder-7ebe` `96af9d42`, `cursor/v23-plan-460c` `b8fbf5e2` (the parallel inference_server audit); `cursor/is-v23-integration` absent. At revision (2026-09-26): `cursor/v23-plan-460c` `28232556`, `cursor/is-v23-integration-460c` `a685c884`.

---

## 8. Open PRs (all draft)
To `dev`: #67 (V20-E02 FAST_TRACK docs), #59 (V2 completion plan).
To `main`: #44 (two-host MVP, already in dev), #43 (OpenRouter free canary), #42 (live_local restore), #14 (V1.4 base).
Codex donor stack (bases are other codex branches): #18–#40 (except merged #16 to coordination), #17 → `coordination/swarm-control`.
None are required for V2.3; see B-06.

## 9. Planning branch
The plan branch `cursor/v23-plan-460c` in swarmai (from `origin/dev`) holds these files under `docs/plans/v2.3/`, plus append-only updates to the canonical docs (`docs/agents/CURRENT.md`, `docs/swarm-mvp/DECISIONS.md`, `STATE.md`, `docs/v2.3/STATUS.md`, `docs/handoff/CURRENT.md`, the roadmap, `CONTRIBUTING.md`) and new `docs/PROMPT_LOG.md` and `docs/JIRA_SYNC_PENDING.md`. SW-W0-S1 Step 0 and §3a of every SW-MERGE prompt merge it into the integration branch. It never touches `cursor/sw-v23-integration-460c` itself.
