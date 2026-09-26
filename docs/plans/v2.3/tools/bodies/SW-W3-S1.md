**Goal.** Expose the Wave-1/Wave-2 V2.3 services over HTTP in one new router module, `src/swarm/api/routes_v23.py`, and wire it into `create_app`.

**Security rules** (tests enforce each one):
- Every route resolves a `Principal` through `get_principal`.
- Project-level routes call `auth.require_project(principal, project_id)` **before** reading or writing.
- Admin-only: pack install, drain, disable, uninstall, revoke and history; fleet audit; scheduler receipts without a `project_id`.
- `GET /v1/scheduler/queues` shows a non-admin only their own projects.
- `GET /v1/ops/trace/{id}` returns **404, not 403**, when any node belongs to a foreign project, so a foreign trace's existence is never confirmed.
- Portability import checks the **target** and **source** projects, and rejects any `bundle_id` that does not match `^port_[A-Za-z0-9_-]{1,64}$`. This blocks path traversal.
- Worker drain/revoke: a worker with no `project_id` (fleet-level) is admin-only. This is stricter than the legacy `/v1/workers/drain`, which stays unchanged.
- The pack registry is built with `require_signature=True, trusted_keys=trusted_keys_from_env()`, so unsigned or untrusted packs are refused.
- The API runtime **never dispatches**. Its scheduler's reserve function raises `api_runtime_has_no_broker`, so a stray `schedule_once` defers and reserves nothing.
- Every mutation emits an `operator.action` ops event containing the actor subject; the sink redacts secrets.
- Durable state (`SqlSchedulingStore`, `SqlSchedulerEpochService`, `SqlPackInstallStore`, `SqlOpsSink`) is used **only** when `SWARM_V23_DURABLE=1` **and** the database is reachable. Otherwise everything is in memory, as today.

**API shapes** (the SW-W1-S12 console codes against these; do not change them):

| Method and path | Response |
|---|---|
| `GET /v1/scheduler/queues` | `{"projects":[{project_id, tenant_id, weight, credit, running, max_concurrency, paused, version}]}` |
| `GET /v1/scheduler/receipts?project_id=&limit=` | `{"receipts":[...]}` |
| `POST /v1/scheduler/projects/{pid}` body `{weight?, max_concurrency?}` | project state |
| `POST /v1/scheduler/projects/{pid}/weight` body `{weight>0}` | project state |
| `POST /v1/scheduler/projects/{pid}/pause` or `/resume` | project state |
| `GET /v1/ops/trace/{trace_id}` | `TraceGraph.to_dict()` |
| `POST /v1/packs/install` body `{manifest}` | install record (admin) |
| `POST /v1/projects/{pid}/packs/{pack}/{ver}/enable` body `{capabilities:[...]}` | project install record |
| `POST /v1/packs/{pack}/{ver}/drain` (or `disable`, `uninstall`, `revoke`) | install record (admin) |
| `GET /v1/packs/{pack}/{ver}/history` | `{"history":[...]}` (admin) |
| `POST /v1/projects/{pid}/export` | `{bundle_id, project_id, integrity_digest, schema_version}` |
| `POST /v1/projects/{pid}/import` body `{bundle_id}` | `{bundle_id, project_id, imported:true}` |
| `POST /v1/fleet/place` body `{project_id, preferred_locality?, min_trust?}` | placement decision |
| `GET /v1/fleet/audit` | `{"events":[...]}` (admin) |
| `POST /v1/workers/{worker_id}/drain` or `/revoke` body `{reason}` | `{"worker_id","drain_state"}` |

The code below was compiled and run against `dev @ 8e1c0fde` plus every Wave-1/Wave-2 change. `tests/api/test_v23_routes.py` gives 7 passed, the durable integration test gives 1 passed, `tests/api tests/product` all pass, and ruff and mypy are clean. Paste it **exactly**.

### Step 1 — `src/swarm/api/routes_v23.py` (create, exactly)
```python
{{FILE:src/swarm/api/routes_v23.py}}
```

### Step 2 — `src/swarm/api/app.py` (replace the whole file, exactly)
First run `git diff 8e1c0fdec24c131e7612d88076220945230f4c3b -- src/swarm/api/app.py`; it must print nothing. The change against that baseline is only:
- two new import lines for `routes_v23`;
- `OpsEventLog, SqlOpsSink` in the local import;
- the `v23_factory` / `app.state.v23` block right after the `ops_events` line;
- `app.include_router(v23_router)` after `app.include_router(v1_router)`.

If `app.py` on your base differs from what this file implies, apply just those four edits by hand instead; if any of the four anchor lines is missing, STOP (S4, section 10).
```python
{{FILE:src/swarm/api/app.py}}
```

### Step 3 — `tests/api/test_v23_routes.py` (create, exactly)
```python
{{FILE:tests/api/test_v23_routes.py}}
```

### Step 4 — `tests/integration/db/test_v23_routes_durable_sql.py` (create, exactly)
```python
{{FILE:tests/integration/db/test_v23_routes_durable_sql.py}}
```

### Step 5 — run
```bash
git clean -fdX -- var/
uv run pytest tests/api/test_v23_routes.py -q                               # 7 passed
uv run pytest tests/integration/db/test_v23_routes_durable_sql.py -q        # 1 passed (skips if no Postgres)
uv run pytest tests/api tests/product -q
```
If an import fails (for example `swarm.scheduling.service`, `swarm.capabilities.lifecycle` or `swarm.observability.build_trace`), a dependency session has not been merged. STOP (S2, section 10); do **not** write stand-in modules.
