**Goal.** Bind the frozen V2.3 acceptance manifest (`benchmarks/v23_acceptance/scenarios.freeze.json`, created by SW-W0-S1) to **ten deterministic probes**, V23-A01 through V23-A10.
- Each probe drives the *real* V2.3 services in-process, with fake brokers and injected clocks: `SchedulerService`, `FleetPlacementService`, `PackLifecycleService`, `PortabilityService`, `OpsEventLog` / `build_trace`, `RouteCapabilities.admissible`, and the `AuthRegistry.require_project` path used by the routes.
- V23-A11 (multi-process, private infrastructure) has no probe. It is reported as `pending_owner_approval`.

**Truth rules** (tests enforce each one):
- `run_v23_probes` always returns `"version_claim": "not_accepted_by_harness"`. The harness never marks V2.3 accepted.
- A probe that raises counts as a **failure** (`error:<Type>`), never as a pass.
- `load_v23_freeze` fails closed in four cases:
  - the schema is not `2.3.0`;
  - the manifest's `policy_version` differs from `config/v23/scheduler_policy.v1.json`;
  - `version_claim_policy` is missing;
  - a scenario names an unknown probe, or scenario ids are duplicated.
- There is no network, no provider and no spend. The only key is a probe-local literal, `b"probe-only-key"`, used to sign a throwaway manifest.
- Probes read the manifest and policy relative to the **repository root**, so run them from there.

**Probe → ART item:**

| Scenario | Probe | What it proves |
|---|---|---|
| A01 | `fairness_three_projects` | weights 1:2:3 over 600 decisions; every share within 15% relative error |
| A02 | `anti_amplification` | 60 child missions do not beat the one-mission project (share stays about 0.5) |
| A03 | `isolation_negatives` | cross-project read 403; cross-tenant placement rejected **and** audited; pack isolation; forged task/mission project never admitted |
| A04 | `restart_recovery` | reload equals pre-restart state; credit clamped to the restart cap; expired intent compensated exactly once; stale epoch cannot write |
| A05 | `drain_active` | a draining worker gets no placement; a cancelled mission gets no admission; a duplicate result gives `already_terminal` |
| A06 | `pack_lifecycle` | unsigned or wrongly signed packs refused; enable → deny other project → no widening → drain → disable → uninstall |
| A07 | `portability_roundtrip` | secret values refused; digests verify in a clean root; tampering refused; approvals and leases tombstoned |
| A08 | `trace_chain` | the full `TRACE_CHAIN` is linked through `parent_event_id`; a gap is reported, not invented |
| A09 | `failure_truth` | provider unavailable gives DEFER `deferred_resource_unavailable` with nothing reserved; the site-scoped ops event records it; a lost or drained worker gets no work |
| A10 | `zero_spend` | billing `paid`, `unknown`, `trial` or missing is denied (`paid_route_forbidden`); `free` is admitted |

**Known limitation (do not fix here).** A non-admit decision has no task, so its `scheduler.decision` event carries `project_id=None` and appears only in the admin (site-wide) view. That is why A09 queries by `kind`. Record it in the PR body under "Follow-ups".

The code below was compiled and run against `dev @ 8e1c0fde` plus every Wave-1/Wave-2 change and the SW-W0-S1 manifest:
- `tests/acceptance`: 39 passed (15 new).
- All ten probes: `pass`.
- ruff and mypy: clean.

### Step 1 — `src/swarm/acceptance/v23_probes.py` (create, exactly)
```python
{{FILE:src/swarm/acceptance/v23_probes.py}}
```

### Step 2 — `tests/acceptance/test_v23_acceptance.py` (create, exactly)
```python
{{FILE:tests/acceptance/test_v23_acceptance.py}}
```

### Step 3 — run (from the repository root)
```bash
uv run pytest tests/acceptance/test_v23_acceptance.py -q      # 15 passed
uv run pytest tests/acceptance -q
uv run python -c "import tempfile,pathlib,json; from swarm.acceptance.v23_probes import run_v23_probes as r; x=r(pathlib.Path(tempfile.mkdtemp())); print(x['deterministic_passed'], x['deterministic_total'], x['version_claim'])"
# expect: 10 10 not_accepted_by_harness
```
If a probe fails, **do not loosen its check**. Print its `detail["checks"]`: the failing key names the broken behaviour in a dependency session. STOP (S3, section 10) and name that key in the handoff.
