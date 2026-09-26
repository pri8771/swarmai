# SwarmAI V2.3 Status — implementation-complete candidate (NOT accepted)

Implemented and offline-tested only; not independently reviewed; not live verified.

| Field | Value |
|---|---|
| Tree | `cursor/sw-v23-integration-460c` (campaign re-ran on `1b3f48ad2a1d27cb4d485416502cdd3ba2d12796` after the SW-FIX-* follow-ups; first run `723f6e55`) |
| Schema head | `a23opsplatform0001` (`CURRENT_SCHEMA_REVISION`) |
| Plan | `docs/v2.3/PLAN.md`; session handoffs `docs/v2.3/sessions/` |
| Checklist | [`EXIT_CHECKLIST.md`](EXIT_CHECKLIST.md) |
| Campaign | `docs/evidence/v23/acceptance_campaign.json` (`freeze_id` `v23-acceptance-deterministic-20260926`) |

## Gates (copied from `acceptance_campaign.json`)
- deterministic: `pass` (10/10 probes)
- multi_process_private: `pending_owner_approval`
- live_router_free_route: `blocked:router_not_configured`
- compose_smoke_v20_e10: `pass` (dev VM Docker run after SW-FIX-COMPOSE; not an operator host)
- durable_postgres_flag: `false`

## Not claimed
- V2.3 (or any version) as accepted: never claimed from the harness; not accepted.
- Multi-process / private-infrastructure evidence (V23-A11).
- A live model call through inference_server / SplitSignal (no LiveGrant; SP4 not reached). The SplitSignal adapter (SW-X1-S1) is merged and tested against the fake and the real IS mock only.
- Any spend. `spend_usd` is 0.0 because no provider was called, not because costs were measured as zero.
- V20-E10 on an operator/production host (the `pass` in `docs/evidence/v20/compose-smoke/latest.json` is a dev-VM run with a VM-local bridge sysctl change, recorded in `docs/v2.3/sessions/SW-FIX-COMPOSE.md`).

## Follow-up fixes
SW-FIX-RETRY (`b3162712`), SW-FIX-COMPOSE (`e5fd04c0`), SW-FIX-ALEMBIC (`604f7ace`), SW-FIX-FLAKE (`1b3f48ad`) — implemented / offline-tested; see `EXIT_CHECKLIST.md` §Follow-up fixes. Whole-repo `uv run pytest -q` on the tip: `778 passed, 1 skipped` (private DB).

## SplitSignal sync points (inference_server, JOINT_PLAN §5.2)
| SP | State |
|---|---|
| SP1 consumer contract `docs/api/v1/consumers/swarmai.md` on `cursor/is-v23-integration-460c` | reached (IS `9ca12671`, blob `1a4a31c9`) |
| SP2 `scripts/mock_splitsignal.py` + fixtures on the IS integration branch | reached (IS `9ca12671`); adapter run against it, see `sessions/SW-X1-S1.md` |
| SP3 hosted deploy | pending |
| SP4 live non-streaming call reachable | pending |
| SP5 live streaming | pending |
| SP6 offline contract check (`swarmai-consumer 1.` in IS evidence) | pending |
