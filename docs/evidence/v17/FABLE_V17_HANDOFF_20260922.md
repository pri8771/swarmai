# Fable V1.7 delivery handoff — 2026-09-22 (session 1)

Worker: Claude Fable 5.1 (engine `fable`, heartbeat epoch `fable-v17-20260922-01`, same stream `CURSOR-V17-SINGLE`).
Scope: `OWNER_V17_LIVE_ONLY` (`EXECUTION_CONTROL.json`). No V1.8+ work was done or planned.
Verdict: **BLOCKED_FRONTIER** — every dependency-ready, non-held V1.7 packet has been executed; the remaining V1.7 chain waits on the lead's independent review hold **REV-R27C** and on external gates. Nothing here is self-accepted.

## 1. Branch and source

- Implementation branch: `cursor/v17-single-session`.
- Takeover base (Cursor's last tip): `f2b8d5f7dfd65530e73c63438c229b9fa428f922`.
- **Exact pushed tip at handoff: see the commit that adds this file** (`git log -1 -- docs/evidence/v17/FABLE_V17_HANDOFF_20260922.md`); the last source-changing commit is `e46f5b6` (R30a). All pushes are fast-forward; the Cursor checkout `~/Downloads/swarm-ai-v2-runtime` and its idle agent processes were not touched.
- Coordination branch was read-only for this worker except the heartbeat/status/state stream published through the existing producer.

## 2. Running private/local candidate

| Item | Value |
|---|---|
| URL | `http://127.0.0.1:18771` — loopback only; **not** reachable from other hosts by design (no owner-side remote reachability was tested or promised) |
| Service | launchd `com.swarmai.v17-candidate` (pid changes on restart; `scripts/v17_candidate.sh status` prints it), RunAtLoad + KeepAlive |
| Commands | `scripts/v17_candidate.sh start | restart | stop | status | logs` (runbook: `docs/runbooks/V17_CANDIDATE.md`) |
| Source | `/Users/pchordia/swarmai-v17` (moved out of `~/Downloads` because launchd cannot read TCC-protected folders); serving the tip current at restart time (last restart at `7e5ac70`; restart after pulling this tip) |
| Config | `~/Library/Application Support/SwarmAI/v17-candidate/candidate.env` (mode 600; DSN, loopback bootstrap token, `SWARM_ALLOW_PAID=false`, Ollama URL) — never in Git |
| DB | PostgreSQL 16 `swarmai_v17_live` at Alembic head `a17effect004b0001` (single head) |
| Reachability evidence (from the execution host) | `GET /health/live` → 200 `{"status":"ok"}`; `GET /health/ready` → `{"status":"ready","execution_mode":"operational","database":"up","allow_paid":false,...}`; `GET /v1/missions` unauthenticated → 401; with the loopback token → 200 |
| Logs | `~/Library/Application Support/SwarmAI/v17-candidate/{stdout,stderr}.log` |

Honest limit: a running API is **not** working V1.7. The V1.5/V1.6/V1.7 subsystems are still not on this service's mission path (see §5).

## 3. Heartbeat

Single producer `com.swarmai.coord-heartbeat-v17` (5-minute launchd timer), engine `fable`, epoch `fable-v17-20260922-01`, takeover record published at `2026-09-22T00:33:34Z`. All heartbeat commits carry `[skip ci]`. At session end the context is set to `review_requested` with the real last-meaningful-activity time; timer ticks after that are publication only, not work.

## 4. Packets executed this session (meaningful source change unless noted)

| Packet | Status | Tested SHA | Evidence |
|---|---|---|---|
| OPS-CI-01 | impl_complete + live (77 min run counts) | `ab958d7` | `docs/evidence/ops/OPS-CI-01/` (+ coordination-branch patch for the lead) |
| R27a durable receipts | impl_complete | `0505c24` | `docs/evidence/v17-recovery/R27a/` |
| R27b atomic reserve / CAS | impl_complete (5 consecutive green runs) | `d3a7b56` | `.../R27b/` |
| R27c repository-owned transactions, committed admission, exact-once approval use | **review_pending (REV-R27C)** | `8dbe5d8` | `.../R27c/` incl. `diff-tracked.patch` |
| R27d approval integrity | impl_complete | `1b9afc5` | `.../R27d/` |
| R17a CP3 gaps | **live_checkpointed** (CP3 9/9, 20/20 concurrent accepts) | `e5bd635` | `docs/evidence/v17-checkpoints/CP3/cp3-20260922T013226Z/` |
| R02a red→green defect-proof gate | impl_complete | `ef8a2cc` | `.../R02a/` |
| R02b v14-real-008 attempt 1 | **failed, preserved** (verbatim echo, no material diff) | `ffa3317` (candidate) | `docs/evidence/v14-real-e2e/v14-real-008/` |
| R30a live fixture service + markers | impl_complete (11 live_local tests) | `e46f5b6` | `.../R30a/` |
| R33c preflight | read-only probe only (no mutation) | — | `docs/evidence/v17-checkpoints/CP5-REALWORLD/preflight-probe-20260922.json` |
| Candidate service + runbook | ops | `ffa3317` | `docs/runbooks/V17_CANDIDATE.md` |

Test counts at the last full run (real Postgres, `SWARM_LIVE_LOCAL` unset): **433 passed, 13 skipped, 0 failed** (11 `live_local` skips by design + 2 pre-existing `tests/ui` node_modules skips; `live_local` = 11 passed when enabled). `ruff check .` clean; `mypy src/swarm` clean. Hosted CI: **blocked** (account billing) — every hosted run is `failure` with zero steps; local results are the only test evidence.

## 5. Checkpoint matrix

| Checkpoint | Result | Evidence | Tested SHA | Independent review | Open gates |
|---|---|---|---|---|---|
| CP0 exact-tip health | local pass (ruff/mypy/433 tests); hosted CI **blocked** | this file §4; per-packet receipts | `e46f5b6` | pending | EXT-ACTIONS-BILLING (apply `docs/evidence/ops/OPS-CI-01/coordination-ci.patch` first) |
| CP1 real mission | **not passed**: attempt 008/1 failed honestly (no material diff); 005/007 CHANGES REQUIRED | `v14-real-e2e/v14-real-008/` | `ffa3317` | n/a for a failed attempt | R02c repair packet, then attempt 2; EXT-V14-LEAD-REVIEW |
| CP2 qualification/provider | **not run** | — | — | — | EXT-G13-WIN-VERIFY, EXT-G13-SEALED-DIGEST, EXT-G12-REMOTE-ROUTES |
| CP3 durable worker path | **live_checkpointed** 9/9 incl. cancellation fence + concurrent duplicate accept; on harness-seeded tasks, not a product mission | `v17-checkpoints/CP3/cp3-20260922T013226Z/` | `e5bd635` | pending | EXT-V15-SECOND-HOST; "on a real operational mission" needs R17b |
| CP4 scoped knowledge | **not run** (retrieval not on mission path) | — | — | — | R25a/R25b behind R28d |
| CP5 unified boundary | **not run**; adapters still echo/simulator; fixture ready | R30a evidence | — | — | R27e→R28a…R28d→R30b/R31a/R31b→R32a→R33a/b, all behind REV-R27C |
| CP5-REALWORLD (R33c) | **not run**; read-only preflight recorded (identity `pri8771`, private repo readable) | `CP5-REALWORLD/preflight-probe-20260922.json` | — | — | EXT-V17-REALWORLD-GITHUB (exact operator approval) + R33b |
| CP6 integrated | **not run** | — | — | — | all of the above + R17b/R17c + R34a/b |

Claim ladder position: durable effects/approvals are now `implementation` (with R27c awaiting review); durable workers are `implementation` + `live_checkpoint` (harness); knowledge and the action boundary are **not wired** to the mission path. **V1.7 is not live.**

## 6. Findings recorded (not fixed here)

1. `LeaseLifecycleService.cancel_active_lease` does not bump the durable mission `cancellation_generation`, and no mission-cancel service method exists (CP3 harness performed the durable bump as control plane). Proposed packet: mission-cancel method that bumps the generation before advisory lease cancellation.
2. v14-real-008: the local model echoes the target file verbatim as a full-file rewrite. Proposed packet **R02c**: detect verbatim/near-verbatim echo before write and re-prompt for a diff-shaped targeted change + regression test.
3. The full test suite mutates tracked files (`tests/release/test_v1.py` re-freezes `schemas/v1/*`; a fix-004 runner test rewrites `docs/evidence/fix-004/*`). Reverted before every commit; needs a small hygiene packet (write to `tmp_path`).
4. CLI-run missions (`swarm mission run`) persist with `project_id: null` and never enter `var/history/index.json`, so the project-scoped API (`/v1/missions`, `/v1/history`) does not surface them. Mission identity/project scoping is not unified across CLI and API (relevant to R17b/R34a).
5. `scripts/coordination/heartbeat.py` has 8 pre-existing mypy `type-arg` notes; outside the configured mypy target; untouched.

## 7. Blockers (exact)

| Gate | Owner | Needed action | Blocks |
|---|---|---|---|
| REV-R27C | lead | Independent review of `8dbe5d8` (bundle in `docs/evidence/v17-recovery/R27c/`) | R27e → R28a → R28b–d → R29a → R30b/R31a/R31b → R32a → R33a/b/c → R25a/b, R17b/c, R34a/b |
| EXT-ACTIONS-BILLING | operator | Apply `coordination-ci.patch` to `coordination/swarm-control`, **then** restore Actions billing | exact-tip hosted CI |
| EXT-V14-LEAD-REVIEW | lead | review after a passing real mission (none yet) | ART-V14-REAL-E2E |
| EXT-G13-WIN-VERIFY / EXT-G13-SEALED-DIGEST | operator / lead | Windows run or governance decision; sealed digest | CP2, R06–R08, R11 |
| EXT-G12-REMOTE-ROUTES | operator | ≥2 zero-charge providers confirmed | R09–R12, LIVE-142 |
| EXT-V15-SECOND-HOST | operator | second physical host | R18 |
| EXT-V17-REALWORLD-GITHUB | operator | exact approval for one `[SwarmAI LIVE TEST] <run-id>` issue create/comment/close through SwarmAI | R33c |

## 8. Next executable packets after the hold clears

R27e → R28a → R28b → R28c → R29a → R28d (wires the boundary into the mission path) → R30b → R31a → R31b → R32a → R33a → R33b → R33c (with approval) → R25a → R25b → R17b → R17c → R34a → R34b. Independent of the hold: R02c (new), the mission-cancel packet (new), the test-hygiene packet (new).
