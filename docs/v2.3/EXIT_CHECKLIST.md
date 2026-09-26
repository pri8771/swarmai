# V2.3 implementation-complete — exit checklist

Source checklist: `docs/coordination/FUTURE_VERSION_EXIT_CHECKLISTS_20260921.md` §"V2.3 implementation-complete".
Contracts: `src/swarm/contracts/v23.py` (artifact `docs/artifacts/future/ART-V23-MULTIMISSION_SCHEDULER.md`), policy `config/v23/scheduler_policy.v1.json` (`v23-wdrr-1`).

| Field | Value |
|---|---|
| Tree | `origin/cursor/sw-v23-integration-460c` @ `1b3f48ad2a1d27cb4d485416502cdd3ba2d12796` (campaign `source_sha`, re-run after the follow-up fixes SW-FIX-RETRY (`b3162712`), SW-FIX-COMPOSE (`e5fd04c0`), SW-FIX-ALEMBIC (`604f7ace`), SW-FIX-FLAKE (`1b3f48ad`); first run was on `723f6e55`, SW-W4-S1) |
| Schema head | `a23opsplatform0001` (`CURRENT_SCHEMA_REVISION`) |
| Campaign | `docs/evidence/v23/acceptance_campaign.json` (`freeze_id` `v23-acceptance-deterministic-20260926`) |
| Deterministic probes | `10/10` pass |
| Version claim | **implementation-complete candidate only. NOT accepted.** Acceptance needs Codex review (D2), owner sign-off, the owner's merge into `dev`, and the multi-process/private gate. |

Legend: **done**, meaning implemented with a deterministic test and, where it says "PG", a PostgreSQL integration test. **pending** means an external gate, honestly not run.

| # | Checklist item | Status | Evidence (test or artifact) |
|---|---|---|---|
| 1 | scheduler state durable | done (PG) | `tests/integration/db/test_v23_store_sql.py`, `test_v23_service_restart_sql.py`, `test_v23_routes_durable_sql.py` |
| 2 | project-level fairness defined | done | `tests/controller/test_v23_wdrr.py`; probe V23-A01 |
| 3 | aging/priority deterministic | done | `tests/controller/test_v23_wdrr.py`; `test_v23_pathological.py::test_03` |
| 4 | reservation intent transactional / fail-closed | done | `tests/controller/test_v23_dispatch_intent.py`; `test_v23_pathological.py::test_05,test_06` |
| 5 | provider/worker/tool capacity integrated | done | `SchedulerService(reserve=, release=)`; `test_v23_pathological.py::test_09`; probe V23-A09 |
| 6 | backpressure bounded | done | WDRR caps + `test_v23_pathological.py::test_01,test_10` |
| 7 | cancellation/drain fenced | done | `test_v23_pathological.py::test_07`; `tests/workers/test_v23_fleet_policy.py`; probe V23-A05 |
| 8 | scheduler bound to SiteEpoch | done | `tests/controller/test_v23_epoch.py`; `test_v23_pathological.py::test_07,test_11` |
| 9 | decision receipts emitted | done (PG) | `SqlSchedulingStore.append_receipt`; `GET /v1/scheduler/receipts` (`tests/api/test_v23_routes.py`) |
| 10 | capability packs lifecycle complete | done (PG) | `tests/extensions/test_v23_pack_lifecycle.py`; `test_v23_pack_installs_sql.py`; probe V23-A06 |
| 11 | portability export/import complete | done | `tests/portability/test_v23_bundle.py`; probe V23-A07 |
| 12 | observability read surface complete | done | `tests/api/test_v23_ops_events_scope.py`; `tests/controller/test_v23_ops_trace.py`; `GET /v1/ops/trace/{id}`; console Ops tab (`apps/console/src/ops.test.tsx`) |
| 13 | dashboard mutation uses action boundary | done | console `WorkerControls` → `POST /v1/workers/{id}/drain|revoke` (audited `operator.action`) |
| 14 | fleet placement/trust/locality complete | done | `tests/workers/test_v23_fleet_policy.py`; probe V23-A03 |
| 15 | pathological deterministic suite passes | done | `tests/controller/test_v23_pathological.py` (11 cases); `tests/acceptance/test_v23_acceptance.py` |
| 16 | multi-process/private evidence complete or honestly pending | **pending_owner_approval** | scenario V23-A11; blocker B-04 |

## V2.0 depth prerequisites

| Item | Status | Evidence |
|---|---|---|
| V20-E03 pursuit PostgreSQL write-through | done (PG), behind `SWARM_V23_DURABLE=1` | `tests/integration/db/test_v20_pursuit_writethrough_sql.py`, `test_v20_durable_wiring_sql.py` |
| V20-E04 durable holds/lessons (+ F-13 unknown ≠ zero) | done (PG) | `tests/pursuit/test_v20_durable_holds.py`, `test_v20_unknown_usage_budget.py`, `test_v20_holds_sql.py` |
| V20-E05 inference_server router client | done (fake router) | `tests/providers/test_router_client.py` |
| SplitSignal consumer adapter (contract `swarmai-consumer 1.x`, sync point SP1/SP2) | done (fake SplitSignal + real IS mock); live pending SW-X2-S1 (SP4) — SW-X1-S1 merged at `2b27bc20` after SP1/SP2 were reached (IS integration `9ca12671`; contract blob `1a4a31c9` unchanged); SP3–SP6 pending | `tests/providers/test_splitsignal_client.py`, `tests/pursuit/test_v20_native_loop_splitsignal.py`, `docs/v2.3/sessions/SW-X1-S1.md` (real-mock run) |
| V20-E06 singleton pursuit ticker | done | `tests/product/test_v20_durable_wiring.py::test_only_one_ticker_runs_per_site` |
| V20-E07 native model/tool loop | implemented; **live run blocked** (`blocked:router_not_configured`) | `tests/pursuit/test_v20_native_loop.py` |
| V20-E08 sandbox cancel kill-bound | done | `tests/tools/test_v20_cancel_killbound.py` |
| V20-E09 console ops surface | done | `apps/console/src/ops.test.tsx` |
| V20-E10 compose full-path smoke | implemented; smoke `pass` (17/17 steps, incl. after api restart) on the dev VM (Docker 29.1.3, compose v2.40.3) at `6f85edc7` after SW-FIX-COMPOSE gave `worker` a connector process healthcheck (it inherited the API HTTP HEALTHCHECK and was always unhealthy). VM-local env change for the run: `net.bridge.bridge-nf-call-iptables=0` (leftover `iptables-legacy` FORWARD DROP), reverted after; not an operator/production host; not independently reviewed | `docs/evidence/v20/compose-smoke/latest.json`, `tests/deployment/test_product_compose.py` |
| V20-E11 | deferred (out of scope) | — |

## Not claimed

- V2.3 (or any version) as accepted: never claimed from the harness; not accepted.
- Multi-process / private-infrastructure evidence (V23-A11).
- A live model call through inference_server, unless the owner granted a LiveGrant **and** it is recorded in the campaign.
- Any spend. `spend_usd` is 0.0 because no provider was called, not because costs were measured as zero.

## Follow-up fixes (after SW-W4-S1)
Each merged into `cursor/sw-v23-integration-460c` with `--no-ff` after ruff, mypy, one Alembic head, the offline CI list and the Postgres integration run passed on the tip. Status: implemented / offline-tested; not independently reviewed.
| Fix | Merge | What changed |
|---|---|---|
| SW-FIX-RETRY | `b3162712` | `RetryOwner.decide`: `Retry-After` above `max_retry_after_seconds` (or non-finite) → give-up `retry_after_exceeds_cap`, never a retry at the cap (SplitSignal rule) |
| SW-FIX-COMPOSE | `e5fd04c0` | compose `worker` has a connector process healthcheck; V20-E10 smoke `pass` (17/17) on the dev VM |
| SW-FIX-ALEMBIC | `604f7ace` | V20-S11 probe restores `SWARM_*`; Alembic tests pinned to their DB; whole-repo `uv run pytest -q` → `778 passed, 1 skipped` (was 4 failed) |
| SW-FIX-FLAKE | `1b3f48ad` | V20-E08 kill-bound tests deterministic (reaped-zombie race in the helper; cancel after the grandchild exists) |
| SW-X1-S1 | `2b27bc20` | SplitSignal consumer adapter merged after SP1/SP2 (Codex review pending) |
