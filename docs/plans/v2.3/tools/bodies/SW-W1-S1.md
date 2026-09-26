**Goal.** Implement the V2.3 fairness selector: weighted deficit round robin (WDRR), project level first, then mission level, then task order. It is a **pure function**: no I/O, no clock reads (`now` is passed in), no mutation of inputs. SW-W2-S1 wraps it with persistence.

**Rules it implements** (from `docs/artifacts/future/ART-V23-MULTIMISSION_SCHEDULER.md` and `config/v23/scheduler_policy.v1.json`):
- For each decision, every *eligible* project accrues `base_quantum * weight`, capped at `max_credit_cap_multiplier * weight * base_quantum`. The chosen project pays `service_cost * base_quantum * total_eligible_weight`. Long-run share is therefore proportional to weight.
- Ineligible projects (paused, at the concurrency cap, or with only blocked work) neither accrue nor pay. Blocked work never earns credit.
- Urgent, aging and deadline bonuses add to the **score only**, never to credit, and are capped at `urgent_borrow_cap * base_quantum`.
- Tie-break: `(-score, last_served_seq, id)`. Tasks inside a mission are ordered by `(-priority, enqueued_at, task_id)`.
- On restart, only positive credit is clamped (to `restart_credit_cap_multiplier * weight * base_quantum`); debt is kept.

The code and tests below were compiled and run against `dev + SW-W0-S1 + SW-W0-S2` (15 passed; ruff and mypy clean). Paste them **exactly**.

### Step 1 — `src/swarm/scheduling/wdrr.py` (create, exactly)
```python
{{FILE:src/swarm/scheduling/wdrr.py}}
```

### Step 2 — `tests/controller/test_v23_wdrr.py` (create, exactly)
```python
{{FILE:tests/controller/test_v23_wdrr.py}}
```

### Step 3 — run
```bash
uv run pytest tests/controller/test_v23_wdrr.py -q     # 15 passed
```
If `test_policy_file_loads` fails with FileNotFoundError, SW-W0-S1 has not merged into the integration branch. STOP (S2, section 10).

### Section-5 acceptance
- [ ] 15 tests pass, covering: weight-proportional share within ±15% over 600 decisions; no amplification from more missions; low weight not starved; blocked work earns no credit; stale cancellation generation never selected; paused, draining and capped work excluded with reason codes; resource-unavailable gives DEFER; deterministic output with inputs unchanged; urgent bonus bounded; deadline tie-break; task order; restart clamp.
- [ ] `wdrr.py` imports nothing from `swarm.db`, `swarm.api` or any I/O module.
