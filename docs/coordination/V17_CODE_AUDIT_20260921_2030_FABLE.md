# SwarmAI code/evidence audit — V1.5–V1.7 depth audit (Fable planning pass)

Audit time: 2026-09-21T20:30Z
Auditor: Claude/Fable 5.1 (planning worker; **not** an acceptance authority)
Audited implementation tip: `cursor/v17-single-session` @ `f2b8d5f7dfd65530e73c63438c229b9fa428f922`
Coordination truth read at: `coordination/swarm-control` @ `eebd59a`
Supersedes for routing purposes: `V17_CODE_AUDIT_20260921_1432.md` (kept unchanged as the historical record at `fe6acbf`).

This file records findings only. It changes no artifact state. Finding IDs (`W*`, `E*`, `A*`, `I*`, `V*`, `O*`) are referenced by packet specs in `packets/`.

## Verdict

1. The 14:32 audit said V1.5/V1.6/V1.7 source was absent. That is no longer true: source landed in six broad commits between 14:39 and 15:02 EDT (`ddd96a6`, `a26f21a`, `ab6cd8d`, `7f86981`, `198df7f`, `1b1050d`).
2. Recovery packets R13–R16 and R19–R27 did **not** implement anything. Their commits touch only `docs/evidence/**`; the last commit touching `src/` or `migrations/` is `7687753` (R05, 15:50 EDT). They re-ran existing suites against that broad code and wrote receipts. R21/R22/R23 share one byte-identical pytest output; R26 ran no test.
3. The V1.5, V1.6 and V1.7 subsystems are **standalone libraries**. The operational mission path (`MissionRuntime.run` → `RepoWorker.run_task`) calls none of them. Only the inference broker is on-path.
4. The V1.7 effect boundary has fail-open defects in exactly the properties V1.7 exists to provide (restart-safe exactly-once, atomic approval use, fail-closed classification).
5. Therefore: **"V1.7 implementation-complete" is not supported by source.** Truthful position is below.

## Audited version position

| Layer | Position | Basis |
|---|---|---|
| Formally accepted version | none ≥ 1.0 | registry: no version has its full required set `accepted` |
| Highest fully `verified` required set | V1.1 (5/5) | registry |
| Operational product path | V1.4-in-repair | real brokered $0 missions run; `v14-real-005` and `-007` both CHANGES REQUIRED |
| V1.5 durable workers | library + CP3 partial (7/9) | `db/lease_fencing.py`, `workers/service.py`; not used by mission runtime |
| V1.6 scoped knowledge | library; CP4 not live | `knowledge/*`; not used by mission runtime; no real mission in CP4 |
| V1.7 action boundary | library with contract gaps; CP5 absent | `tools/v17_gateway.py`, `tools/effects.py`; zero callers outside `tools/` |
| Live checkpoints | CP0 local-only (CI blocked); CP1 failed review; CP3 partial; CP2/CP4/CP5/CP6 absent | `docs/evidence/v17-checkpoints/`, `v17-recovery/` |

## W — wiring findings (library vs operational path)

- **W1** Mission path bypasses the action boundary. Effect sites: `src/swarm/mission/worker.py:66` (`_run_cmd` → `subprocess.run`), `:593` and `:599` (`target.write_text`). No envelope, scope check, fence or receipt.
- **W2** Two gateways. Legacy `ToolGateway` (`src/swarm/tools/gateway.py:26`) keeps process-local `_seen_ops` (`:42`, `:89`, `:124`) and is still imported by `src/swarm/runtime/session.py:34,74` and `src/swarm/tools/permission_mission.py`. `ConsequentialToolGateway` (`tools/v17_gateway.py:52`) has no caller outside `tools/` and tests. Violates cemented decision 3 (one consequential path).
- **W3** `PermissionFirstRetriever` (`knowledge/retrieval.py:35`) has no caller outside `knowledge/` and tests. `swarm memory retrieve` (`cli.py:897-902`) still calls legacy `retrieve_context` (`memory/store.py:132-171`, iterates `store.list_all()` with no ACL).
- **W4** `MissionController.reconcile_leases` (`controller/mission.py:142`) is a no-op placeholder. `api/store.py:53` holds in-memory `WorkerRegistryService`. `DurableWorkerService` (`workers/service.py:52`) has no caller outside `workers/` and tests. Two authorities for worker state = violation of ART-V20-INTEGRATION-CONTRACT ("no duplicate persistence authorities").

## E — effect-boundary findings (`tools/effects.py`, `tools/v17_gateway.py`)

- **E1** Receipts are not durable. `DurableEffectRepository.receipts` is a dict (`effects.py:167`, `:314-319`); no `action_receipts` table exists. R27 required persisted receipts.
- **E2** `reserve` is SELECT-then-INSERT (`effects.py:225-255`). Concurrent reservers hit a raw `IntegrityError` and a poisoned session instead of "one logical effect".
- **E3** `mark_executing` is read-modify-write with no compare-and-swap or row lock (`effects.py:257-270`). Two processes can both move `reserved → executing` and both execute.
- **E4** Transactions are caller-owned; the repository only flushes and the gateway never commits. The reservation is neither visible to other processes nor crash-durable before `adapter.execute` (`v17_gateway.py:127-161`). A crash mid-execute rolls the reservation back and a retry re-executes.
- **E5** A crashed `executing` row has no recovery path; retries raise `effect_already_executing` forever.
- **E6** Adapter exceptions map to `failed` (`v17_gateway.py:162-178`) and `failed` is re-executable (`effects.py:259-266` does not block it). Timeout-after-send ⇒ duplicate consequential effect.
- **E7** `_outcome_from_result` returns `"succeeded"` on every path, including an empty result (`v17_gateway.py:377-383`).
- **E8** `reserve` returns an existing row without comparing `payload_hash`/`destination_digest`/`operation`/integration (`effects.py:233-234`). A different payload can ride an old effect identity and inherit its receipt.
- **E9** Replay of a succeeded effect re-mints a receipt with fresh `finished_at` and `attempt_refs` (`v17_gateway.py:128-132`, `:436-448`). Replays must return the original immutable receipt.
- **E10** `_reconcile_unknown` reads `self.store.receipts.values()` (`:273-277`). After restart it is empty, `ApiMcpAdapter.reconcile` returns `failed: no_prior_success`, and with E6 the retry duplicates the effect.
- **E11** The gateway silently defaults to `InMemoryEffectStore` for every side-effect class (`v17_gateway.py:71`) — `_seen_ops` again under a new name.

## A — authorization findings

- **A1** The envelope's self-declared `side_effect_class`/`risk_class` is trusted; defaults are `none`/`low` (`contracts/actions.py:44-45`). A caller can label a consequential write `none` and skip approval (`v17_gateway.py:332-346`). The adapter manifest is never consulted for classification.
- **A2** Fences default to plausible-valid values (`lease_generation=1`, `cancellation_generation=0`, `actions.py:48-49`) and the gateway compares against constructor constants (`v17_gateway.py:61-70`, `:371-375`), never current durable state.
- **A3** Approval use is recorded after success and non-atomically (`v17_gateway.py:247-248`; `effects.py:219-223`). With `grant.effect_key = None`, a one-shot approval authorizes N concurrent effects.
- **A4** `put_approval` uses `session.merge` (`effects.py:191`): re-putting an `approval_id` can reset `used_count` or clear `revoked_at`.
- **A5** Legacy approval rows with NULL V1.7 columns are given defaults (`policy_version or "v17-policy-1"`, `integration_id or ""`, `effects.py:204-214`) instead of staying non-operational as the accepted schema requires.
- **A6** `policy_version` is only compared envelope↔grant, never to a current policy. Scopes are a static constructor set with no actor dimension (`v17_gateway.py:320-330`).
- **A7** Denials raise exceptions and leave no durable audit event; nothing in `tools/` writes to the outbox.

## I — integration findings

- **I1** No adapter registry; one gateway instance is bound to one adapter instance.
- **I2** `ApiMcpAdapter` is an in-process echo and `BrowserSessionAdapter` a simulator. Neither performs IO. Simulations never count as live evidence, so CP5's three integrations do not exist yet.
- **I3** Manifests are built inline in adapter constructors: no versioned manifest file, digest, or per-operation classification. Not yet a forward-compatible subset of the V1.9 `ExtensionManifest`.
- **I4** Adapter calls are synchronous inside `async def execute_envelope`; real network IO will block the event loop.

## V — evidence findings

- **V1** See Verdict 2. Evidence for R13–R16, R19–R27 is re-verification, not packet implementation.
- **V2** CP3 (`scripts/r17_cp3_separate_process_recovery.py`) is genuinely live (spawned processes, SIGKILL, real Postgres) and shows 7 of 9 requirements. Missing: cancellation-generation rejection. Partial: duplicate-result race is sequential, not concurrent.
- **V3** CP4 evidence is in-process repository calls on five hand-written strings. No real mission, no later-mission reuse, no existence-inference negative, and the savings assertion is `tokens_avoided_estimate >= 0`.
- **V4** No CP2, CP5 or CP6 evidence exists.
- **V5** R01 has source and tests but no evidence folder.

## O — operations findings

- **O1** `.github/workflows/ci.yml` triggers on every push with no branch or path filter, and `scripts/coordination/heartbeat.py` writes three files through the contents API = three commits = three workflow runs every five minutes. GitHub reports 1,023 workflow runs in the 24h before this audit on a private repository. This is the probable root cause of the Actions billing/spending-limit block recorded in CP0. **Restoring billing without fixing the trigger will exhaust the quota again within about a day.**
- **O2** `V17_RECOVERY_PACKET_QUEUE.json` still marks all 35 packets `planned`; `ARTIFACT_REGISTRY.json` `updated_at` (17:08Z) predates every V1.5–V1.7 source commit. Status lives only in heartbeat prose.
- **O3** Only one pytest marker (`integration`) exists and there is no `conftest.py`; live checks cannot be selected or excluded mechanically.

## What is genuinely good (reuse, do not rewrite)

- Broker admission/reservation/settlement is wired on the live mission path with DB uniqueness constraints.
- `db/lease_fencing.py` fencing (worker/lease/cancellation generations, `_assert_accept_fence`) plus the CP3 harness are real and reusable.
- `KnowledgeRepository` and `PermissionFirstRetriever` implement the correct authorize → filter → rank order.
- `action_effects` already has `UNIQUE(project_id, effect_key)`; migrations are one linear chain with head `a17effect004a0001`.
- The R01 grounding guard and the empty-diff fail-closed rule are sound.

The remediation path is packets `OPS-CI-01`, `R27a`–`R27d`, `R28a`–`R28d`, `R29a`, `R30a`–`R30b`, `R31a`–`R31b`, `R32a`, `R33a`–`R33b`, `R25a`–`R25b`, `R17a`–`R17c`, `R02a`–`R02b`, `R34a`–`R34b` in `V17_RECOVERY_PACKET_QUEUE.json`.
