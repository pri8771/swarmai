**Goal.** Only one scheduler (and one pursuit ticker) may act per site at a time. Implement a **scheduler epoch lease**: a fencing token stored in `v23_scheduler_epochs`. Acquiring bumps the epoch, so a stale scheduler (paused or partitioned) is rejected by `require_current`. Add `SingletonTicker`, which runs a callback only while holding the lease. SW-W2-S1 uses the lease for scheduler writes; SW-W3-S2 uses the ticker for the pursuit loop (V20-E06).

Unlike `SiteAuthorityService` (`src/swarm/recovery/authority.py`), which fences a whole *site*, this lease fences the *scheduler process* inside a site. SW-W2-S1 checks both.

The code below was compiled and run against `dev + SW-W0-S2` (4 offline passed and 1 PostgreSQL passed; ruff and mypy clean). Paste it **exactly**.

### Step 1 — `src/swarm/scheduling/epoch.py` (create, exactly)
```python
{{FILE:src/swarm/scheduling/epoch.py}}
```

### Step 2 — `src/swarm/scheduling/singleton.py` (create, exactly)
```python
{{FILE:src/swarm/scheduling/singleton.py}}
```

### Step 3 — tests (create, exactly)
`tests/controller/test_v23_epoch.py`:
```python
{{FILE:tests/controller/test_v23_epoch.py}}
```
`tests/integration/db/test_v23_epoch_sql.py`:
```python
{{FILE:tests/integration/db/test_v23_epoch_sql.py}}
```

### Step 4 — run
```bash
uv run pytest tests/controller/test_v23_epoch.py -q     # 4 passed
sudo -u postgres psql -c "CREATE DATABASE swarm_sw_w1_s4 OWNER swarm;" || true
SWARM_DATABASE_URL=postgresql+psycopg://swarm:swarm@127.0.0.1:5432/swarm_sw_w1_s4 uv run pytest tests/integration/db/test_v23_epoch_sql.py -q -m integration   # 1 passed
```

### Section-5 acceptance
- [ ] A second holder cannot acquire while the lease is valid; after expiry the epoch increments; the old holder is fenced (`StaleSchedulerEpochError`) on renew and `require_current`.
- [ ] `SingletonTicker` runs the tick in only one holder; fencing during a tick is reported as `fenced_after_tick`.
- [ ] The SQL service gives the same results across two service instances sharing one database.
