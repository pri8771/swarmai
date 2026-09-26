**Goal.** Fix finding **F-13** (financial) and implement V20-E04.

**F-13.**
- In `GoalResourceLedger`, `_held_totals` counts only `held` holds and `_settled_totals` skips `unknown` holds, so a hold settled with `usage_unknown=True` **frees its budget**.
- `release()` also accepts unknown holds.
- After this session:
  - An unknown hold keeps `max(reserved, reported)` committed.
  - `release` refuses unknown holds.
  - The only way out is `reconcile_unknown(..., evidence_ref=...)`.

**V20-E04.**
- Holds and lessons are process memory only today.
- This session adds `durable_accounting.py`, which provides:
  - `HoldStore` with in-memory and SQL implementations over `v20_goal_usage_holds`.
  - `bind_durable_ledger`, which restores holds and then persists each change **before** it becomes visible in memory. A failure rolls memory back.
  - `LessonPersistence` with in-memory and SQL implementations over `v20_pursuit_lessons`.
- `PursuitLessonStore(persistence=None)` keeps today's behaviour when no argument is given.

**Do not** wire these into `api/store.py` or `pursuit/loop.py`; SW-W3-S2 owns them.

The code below was compiled and run against `dev @ 8e1c0fde` plus SW-W0-S2. `tests/pursuit tests/goals tests/product` gives 54 passed and the integration tests give 2 passed. Paste it **exactly**.

### Step 1 — `src/swarm/pursuit/accounting.py` (replace the whole file, exactly)
```python
{{FILE:src/swarm/pursuit/accounting.py}}
```

### Step 2 — `src/swarm/pursuit/durable_accounting.py` (create, exactly)
```python
{{FILE:src/swarm/pursuit/durable_accounting.py}}
```

### Step 3 — `src/swarm/pursuit/learning.py` (replace the whole file, exactly)
```python
{{FILE:src/swarm/pursuit/learning.py}}
```

### Step 4 — `tests/pursuit/test_v20_unknown_usage_budget.py` (create, exactly)
```python
{{FILE:tests/pursuit/test_v20_unknown_usage_budget.py}}
```

### Step 5 — `tests/pursuit/test_v20_durable_holds.py` (create, exactly)
```python
{{FILE:tests/pursuit/test_v20_durable_holds.py}}
```

### Step 6 — `tests/integration/db/test_v20_holds_sql.py` (create, exactly)
```python
{{FILE:tests/integration/db/test_v20_holds_sql.py}}
```

### Step 7 — run
```bash
uv run pytest tests/pursuit -q                      # all pass (existing tests/pursuit/test_usage_accounting.py unchanged)
uv run pytest tests/goals tests/product tests/api -q
```
If an existing test expects `release()` of an unknown hold to succeed, or expects remaining budget to grow after an unknown settle, **stop**. That test encodes F-13; STOP (S4, section 10) and name the test. Do not edit it.

### Section-5 acceptance
- [ ] After an unknown settle, `remaining()` still subtracts `max(reserved, reported)`, and a reserve that needs the freed amount fails with `insufficient_spend_budget`.
- [ ] `release()` of an unknown hold raises `unknown_hold_requires_reconciliation`; `reconcile_unknown` requires a non-empty `evidence_ref`.
- [ ] Holds, including unknown holds, and lessons survive a cold restart through the store (both in-memory and PostgreSQL).
- [ ] A persistence failure leaves in-memory ledger and lesson state unchanged, and the error propagates.
- [ ] With no store or persistence, behaviour is unchanged apart from the F-13 fix.
