# Later V1.7 packets — medium detail

These six packets are not dependency-ready yet. Each gets a full spec (same template as `R27a.md`) from the lead or a planning pass **before** it becomes `ready`; the constraints below are already binding. Shared conventions: `README.md`.

## R02b — new preregistered real mission `v14-real-008`

- Artifact ART-V14-REAL-E2E · SP1 · live · depends R02a · gate `EXT-V14-LEAD-REVIEW` for the result.
- Preregister per `REAL_V14_E2E_PROTOCOL.md` before running: candidate SHA, entrypoint, model routes, limits, zero-spend, no-known-answer declaration.
- Target: one bounded operational subsystem that **no audit or packet has described a defect in**. `src/swarm/tools/**`, `src/swarm/knowledge/**`, `src/swarm/workers/**`, `src/swarm/db/lease_fencing.py`, `src/swarm/workspace/artifacts.py` and `src/swarm/workspace/context.py` are excluded (audited, or used by 006/007). Candidates: `src/swarm/runtime/backpressure.py`, `src/swarm/controller/graph.py`, `src/swarm/cost/`. The worker records why the chosen target leaks no known answer.
- Pass needs `defect_proof.proven == true` (R02a) plus every existing CP1 criterion. At most two attempts; each attempt is preserved whatever its outcome. A run whose gate reports `no_defect_demonstrated` is an honest negative result, not a failure to hide.
- Exit: evidence under `docs/evidence/v14-real-e2e/v14-real-008/`; status `review_pending`. Only the lead can move the artifact.

## R17b — leased execution mode for `MissionRuntime`

- Artifact ART-V15-WORKER-PROTOCOL · SP3 (split into service-loop and runtime-mode packets when specified) · depends R17a, R28d.
- Fixes W4 (first half). `MissionRuntime(execution_mode="direct" | "leased")`. In `leased` mode each task attempt is persisted, then claimed through `DurableWorkerService.claim` by an in-process worker loop built on `WorkerClient`; `RepoWorker.run_task` runs under that lease; the result goes through `submit_result`; the controller accepts through `accept_result` and its existing fence. `MissionController.reconcile_leases` (`controller/mission.py:142`) stops being a no-op: it calls `expire_leases` and re-queues expired attempts.
- The gateway's `StaticFenceProvider` is replaced by `LeaseFenceProvider` in leased mode (R28b), which makes tool effects cancellable by the same generation that fences results.
- Operational entrypoints (API `POST /missions/{id}/execute`, CLI `swarm mission run`) default to `leased` when `SWARM_DATABASE_URL` is set. `direct` stays for database-less local runs and is labeled in the mission record.
- Negatives: lease expiry mid-task → attempt re-queued and late result rejected; cancel mid-task → tool effect denied by `fence_changed_before_execute` and result rejected; duplicate accept → one accepted.
- No second scheduler: `controller/scheduler.py` remains the only place that decides what runs next.

## R17c — separate-process worker + single worker-state authority

- Artifacts ART-V15-WORKER-PROTOCOL, ART-V15-RECOVERY-EVIDENCE · SP2 · depends R17b.
- `swarm worker run --project <id>`: a separate OS process that enrolls, heartbeats, claims, runs and submits through `WorkerClient`. No provider secrets on the worker: inference still goes through the control plane's broker.
- Fixes W4 (second half): `api/store.py:53` stops owning an in-memory `WorkerRegistryService` for operational routes; `/workers`, `/workers/enroll`, `/workers/heartbeat` read and write through `DurableWorkerService`. The in-memory class remains only for `load/` and `chaos/` simulations and is named as such in its docstring.
- Live gate: rerun CP3 with a real mission task instead of a synthetic one (kill the worker process mid-task; a second worker finishes it; exactly one accepted result).

## R25b — CP4 live knowledge checkpoint through real missions

- Artifact ART-V16-CONTEXT-BUDGET-EVIDENCE · SP2 · live · depends R25a.
- Fixes V3. Harness `scripts/r25_cp4_knowledge_missions.py`, zero spend, real brokered local inference, real Postgres, projects A and B:
  1. mission A1 appends an observation; the harness, acting as `operator` with scope `knowledge.accept`, promotes it to `accepted_fact`;
  2. mission A2's prompt contains that fact and its receipt lists the item id and version;
  3. mission B1 with the same query: the prompt contains no A text; the actor-visible receipt has no A ids and no count that changes when A's corpus size changes (run B1 twice with A holding 1 and then 50 items; receipts must be identical except ids and timestamps) — this is the existence-inference negative;
  4. supersede → mission A3 sees the new version only; tombstone → A4 sees neither, and the dependent summary is `disputed`;
  5. token evidence: on the frozen mission set, bounded context tokens **strictly less than** the whole-history baseline for every mission, otherwise the run reports `fail`. `tokens_avoided_estimate >= 0` is not acceptance evidence.
- `task_quality` stays `UNKNOWN` unless a frozen scorer measures it. Do not invent a quality number.

## R34a — integrated operational mission (CP6 precondition)

- Artifact V1.7-integrated-audit · SP2 · live · depends R33b, R25a, R17b.
- One real `$0` mission whose record proves every V1.5–V1.7 subsystem was **on the path**: broker reservation and settlement receipts, a lease id with claim/accept receipts, a knowledge retrieval receipt id, action receipt ids for every file write and command. The harness fails if any of the four receipt families is empty.
- Negatives run inside the same harness: cancel mid-mission (no further effects, result rejected) and kill + restart the control process (mission resumes; no duplicate effect).

## R34b — exact-tip V1.7 audit package (CP6)

- Artifact V1.7-integrated-audit · SP2 · audit · depends R34a, R02b, R25b, R17a and every open gate listed as open, not hidden.
- Deliverable: `docs/evidence/v17-checkpoints/CP6/<run-id>/` binding source SHA, single migration head, complete configured deterministic checks (every skipped test listed by name), CP0–CP5 run ids, artifact-by-artifact status V1.0-repair → V1.7 on the claim ladder (`implementation`, `wired`, `live_checkpoint`, `independent_review`, `external_gate`, `wall_clock_gate`), and the open external and wall-clock gates.
- The only label this packet may assert is **V1.7 IMPLEMENTATION-COMPLETE / LIVE-CHECKPOINTED / FORMAL-ACCEPTANCE-PENDING**. "Accepted V1.7" is reserved for the registry.
