**Goal.** Implement V20-E03, the write-through half of finding **F-05**.
- Pursuit runtime state (history, satisfied criteria, dedupe, schedule) lives only in `var/pursuit/*.json`. The PostgreSQL tables `pursuit_cycles`, `pursuit_schedules` and `pursuit_dedupe` and the repository `swarm.db.repositories.PursuitStateRepository` exist but nothing writes to them.

**This session adds:**
- `PursuitPgMirror(session_factory)`, which writes the whole snapshot into `pursuit_schedules.payload["snapshot"]`, plus queryable cycle and dedupe rows, in **one transaction per save**.
- An optional `mirror=` argument on `DurablePursuitStateStore`:
  - **DB first** on write. If the DB fails, `PursuitMirrorError` is raised and the file is not written.
  - **DB first** on read, falling back to the file only when the DB has no row (migration from file-only installs).
  - A DB read error raises; it is never silently ignored.

Without `mirror`, behaviour is identical to today. **Do not** wire this into `api/store.py`; SW-W3-S2 owns that.

Design notes:
- Cycles that already exist, matched by `cycle_id`, are skipped, so re-saving is idempotent.
- Dedupe keys longer than 64 characters are stored as their sha256 hex digest; the original key is kept in `payload["key"]`.
- `next_due_at` is `0.0` when there is no schedule.

The code below was compiled and run against `dev @ 8e1c0fde`. `tests/pursuit` gives 36 passed and the integration test gives 1 passed. Paste it **exactly**.

### Step 1 — `src/swarm/pursuit/pg_mirror.py` (create, exactly)
```python
{{FILE:src/swarm/pursuit/pg_mirror.py}}
```

### Step 2 — `src/swarm/pursuit/state_store.py` (replace the whole file, exactly)
```python
{{FILE:src/swarm/pursuit/state_store.py}}
```

### Step 3 — `tests/pursuit/test_v20_writethrough.py` (create, exactly)
```python
{{FILE:tests/pursuit/test_v20_writethrough.py}}
```

### Step 4 — `tests/integration/db/test_v20_pursuit_writethrough_sql.py` (create, exactly)
```python
{{FILE:tests/integration/db/test_v20_pursuit_writethrough_sql.py}}
```

### Step 5 — run
```bash
uv run pytest tests/pursuit -q          # all pass (5 new)
uv run pytest tests/product tests/api -q
```

### Section-5 acceptance
- [ ] With a mirror, a cold engine on an **empty file volume** restores history, satisfied criteria and schedule from PostgreSQL (integration test).
- [ ] A mirror write failure raises `PursuitMirrorError` and leaves no file behind; a read failure raises.
- [ ] Without a mirror, behaviour is unchanged, and `tests/pursuit/test_pursuit_durability.py` passes unchanged.
- [ ] Re-saving does not duplicate cycle rows; long dedupe keys fit the 64-character column.
