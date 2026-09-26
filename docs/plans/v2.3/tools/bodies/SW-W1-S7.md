**Goal.** Bring the fleet policy up to the ART-V23 fleet section and finding **F-05** (fleet half):
- Use the ART trust classes (`observe_only` < `sandbox_compute` < `model_worker` < `tool_worker` < `integration_worker`) and accept the legacy names through `LEGACY_TRUST_ALIASES`.
- Add a drain state machine (`active → draining → drained`, and `revoked` as terminal from any state).
- Make placement deterministic and least-privilege: take the lowest sufficient trust rank first, then the lowest `worker_id`.
- Enforce a per-project trust ceiling.
- Make locality strict: a worker without a matching locality is never chosen.
- Refuse placement on workers that the registry reports as DRAINING, QUARANTINED or OFFLINE. `registry.operator_drain` sets an idle worker to OFFLINE.

The public API used by existing callers (`FleetPlacementService(registry)`, `annotate_worker`, `place`, `assert_same_tenant`, `audit_log`, `FleetError`) is preserved. The `trust_class` in decisions is now the ART value, such as `tool_worker`.

The code below was compiled and run against `dev @ 8e1c0fde`. The 6 new tests pass, and `tests/workers tests/portability tests/controller` gives 137 passed and 1 skipped. Paste it **exactly**.

### Step 1 — `src/swarm/workers/fleet.py` (replace the whole file, exactly)
```python
{{FILE:src/swarm/workers/fleet.py}}
```

### Step 2 — `tests/workers/test_v23_fleet_policy.py` (create, exactly)
```python
{{FILE:tests/workers/test_v23_fleet_policy.py}}
```

### Step 3 — run
```bash
uv run pytest tests/workers/test_v23_fleet_policy.py -q      # 6 passed
uv run pytest tests/workers tests/portability tests/controller -q   # all pass (1 pre-existing skip)
```
If an existing test asserts a legacy value such as `"code_write"` as the *output* `trust_class`, that is a base change. STOP (S4, section 10); do not edit that test.

### Section-5 acceptance
- [ ] `normalize_trust("code_write") == TrustClass.TOOL_WORKER` and the other 3 legacy aliases map as documented; unknown names raise `FleetError`.
- [ ] With two eligible workers, placement picks the lowest sufficient trust class and then the lowest `worker_id`, and the result is the same on every run.
- [ ] Draining, drained and revoked workers get no new work; `revoked` cannot transition back.
- [ ] A worker drained via `registry.operator_drain` is not placed.
- [ ] A project trust ceiling below the required class denies placement.
- [ ] Locality is strict.
