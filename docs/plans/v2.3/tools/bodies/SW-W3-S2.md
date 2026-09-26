**Goal.** Wire the Wave-1 durability building blocks into the production path, `ProductStore.pursuit_engine()`, and give pursuit a site-wide singleton tick.
- **V20-E03:** `DurablePursuitStateStore(root, mirror=PursuitPgMirror(factory))` writes and reads PostgreSQL first (SW-W1-S9).
- **V20-E04:** `PursuitEngine(hold_store=SqlHoldStore(factory))` restores every goal ledger's holds through `bind_durable_ledger`, and `PursuitLessonStore(persistence=SqlLessonPersistence(factory))` restores lessons (SW-W1-S10).
- **V20-E06:**
  - `PursuitEngine.tick_all_due()` ticks every ACTIVE/WAITING goal that is due, in goal-id order.
  - `PursuitEngine.singleton_tick(ticker)` runs it only while holding the epoch (SW-W1-S4 `SingletonTicker`).
  - `ProductStore.run_pursuit_tick()` is the production entry point. It uses the epoch row `site_id="pursuit-ticker"`, separate from the scheduler's `local` row.

**Gating** (unchanged default behaviour): PostgreSQL is used only when `SWARM_V23_DURABLE=1` **and** `db_reachable is True`. Otherwise `pg_session_factory()` returns `None`, and file-backed state under `var/` stays authoritative exactly as today. This is the same flag SW-W3-S1 uses in `routes_v23.v23_session_factory`.

The change was compiled and run against `dev @ 8e1c0fde` plus SW-W1-S4, SW-W1-S9 and SW-W1-S10:
- `tests/product/test_v20_durable_wiring.py`: 6 passed.
- The integration test: 1 passed.
- `tests/product tests/pursuit tests/api`: 95 passed.
- ruff and mypy: clean.

### Step 1 — apply the source patch (exact)
Save the block below as `/tmp/SW-W3-S2.patch`, **byte for byte** (keep the leading spaces on context lines). Then run:
```bash
git apply --check /tmp/SW-W3-S2.patch && git apply /tmp/SW-W3-S2.patch
git diff --stat   # expect: src/swarm/api/store.py and src/swarm/pursuit/loop.py only
```
```diff
{{FILE:patches/SW-W3-S2.patch}}
```
If `git apply --check` fails, `store.py` or `loop.py` moved on the integration branch. Apply the same hunks by hand; each hunk is small:
- **`loop.py`:**
  - `TYPE_CHECKING` import;
  - `from swarm.pursuit.durable_accounting import HoldStore, bind_durable_ledger`;
  - the `hold_store` kwarg and `self.hold_store`;
  - `bind_durable_ledger` inside `resource_ledger`;
  - the new methods `tick_all_due` and `singleton_tick`.
- **`store.py`:**
  - two new dataclass fields, `_pg_factory` and `_pursuit_ticker`;
  - the durable block inside `pursuit_engine`;
  - the new methods `pg_session_factory`, `pursuit_ticker` and `run_pursuit_tick`.

### Step 2 — `tests/product/test_v20_durable_wiring.py` (create, exactly)
```python
{{FILE:tests/product/test_v20_durable_wiring.py}}
```

### Step 3 — `tests/integration/db/test_v20_durable_wiring_sql.py` (create, exactly)
```python
{{FILE:tests/integration/db/test_v20_durable_wiring_sql.py}}
```

### Step 4 — run
```bash
git clean -fdX -- var/
uv run pytest tests/product/test_v20_durable_wiring.py -q                   # 6 passed
uv run pytest tests/integration/db/test_v20_durable_wiring_sql.py -q        # 1 passed (skips without Postgres)
uv run pytest tests/product tests/pursuit tests/api -q
```
Do **not** turn `SWARM_V23_DURABLE` on by default, and do not change `.env.example` or compose files. Enabling it in an environment is an operator decision recorded by SW-W4-S1.
