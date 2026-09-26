**Goal.** Create the shared V2.3 data contracts, the `swarm.scheduling` package with an in-memory reference store, the ORM rows, and the **only** V2.3 Alembic migration. Every later session imports these; nobody else edits them.

The code below was compiled, type-checked, and tested against `dev @ 8e1c0fde` (ruff, mypy, 548 offline tests, 70 integration tests). Paste it **exactly**.

### Step 1 — `src/swarm/contracts/v23.py` (create, exactly)
```python
{{FILE:src/swarm/contracts/v23.py}}
```

### Step 2 — `src/swarm/scheduling/__init__.py` (create, exactly one line)
```python
"""V2.3 scheduler package (ART-V23-SCHEDULER)."""
```

### Step 3 — `src/swarm/scheduling/memory_store.py` (create, exactly)
```python
{{FILE:src/swarm/scheduling/memory_store.py}}
```

### Step 4 — append ORM rows to `src/swarm/db/models.py`
Open the file, go to the **very end** (after `class PursuitDedupeRow`), and append this block. Do not change anything above it. No new imports are needed (`BigInteger, DateTime, Index, Integer, String, UniqueConstraint, func, JSONB, Mapped, mapped_column, Any, datetime` are already imported).
```python
{{FILE:models_append.py}}
```

### Step 5 — migration `migrations/versions/a23opsplatform0001_v23_ops_platform.py` (create, exactly)
```python
{{FILE:migrations/versions/a23opsplatform0001_v23_ops_platform.py}}
```
Then check there is exactly one head:
```bash
uv run alembic heads      # expected output: a23opsplatform0001 (head)
```

### Step 6 — update the pinned head in an existing test
In `tests/integration/db/test_action_receipts_durable.py`, change **only** this line (around line 28):
```python
NEW_HEAD = "a20pursuitpersist0001"
```
to
```python
NEW_HEAD = "a23opsplatform0001"
```
(Without this, `test_single_alembic_head_after_upgrade` fails because it asserts the head name.)

### Step 7 — tests (create, exactly)
`tests/contracts/test_v23_contracts.py`:
```python
{{FILE:tests/contracts/test_v23_contracts.py}}
```
`tests/controller/test_v23_store_memory.py`:
```python
{{FILE:tests/controller/test_v23_store_memory.py}}
```
`tests/integration/db/test_v23_schema.py`:
```python
{{FILE:tests/integration/db/test_v23_schema.py}}
```

### Step 8 — run the new tests first
```bash
uv run pytest tests/contracts/test_v23_contracts.py tests/controller/test_v23_store_memory.py -q    # 7 passed
sudo -u postgres psql -c "CREATE DATABASE swarm_sw_w0_s2 OWNER swarm;" || true
SWARM_DATABASE_URL=postgresql+psycopg://swarm:swarm@127.0.0.1:5432/swarm_sw_w0_s2 uv run pytest tests/integration/db/test_v23_schema.py tests/integration/db/test_action_receipts_durable.py -q -m integration
```

### Section-5 acceptance
- [ ] `uv run alembic heads` prints exactly `a23opsplatform0001 (head)`.
- [ ] `uv run python -c "import swarm.contracts.v23, swarm.scheduling.memory_store"` succeeds.
- [ ] The 7 new offline tests pass; `test_v23_schema.py` passes (upgrade → downgrade to `a20pursuitpersist0001` → upgrade).
- [ ] `models.py` diff is append-only (`git diff src/swarm/db/models.py` shows only `+` lines at the end).
- [ ] Handoff lists the 9 new table names and says: "Contracts frozen; later sessions import only. Field changes need a follow-up PR from the coordinator."
