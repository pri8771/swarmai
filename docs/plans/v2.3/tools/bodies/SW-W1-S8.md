**Goal.** Complete ART-V23-OPS observability and the observability half of finding **F-04**.
- Ops events live only in a process-local list, redaction is one level deep (a secret nested inside `detail.request.headers` leaks), and there is no trace graph from operator action to acceptance.

**This session adds:**
- A pluggable sink: `InMemoryOpsSink`, the default, which behaves exactly like today, and `SqlOpsSink`, which writes to the `v23_ops_events` table created by SW-W0-S2.
- Recursive redaction of dicts and lists.
- `trace_id` / `parent_event_id` on events.
- `trace_graph.build_trace(log, trace_id)`, which reports missing stages and orphans instead of inventing links.
- A hard `MAX_LIST_LIMIT = 1000` cap on `list_events`.

**Compatibility.** Existing behaviour is kept:
- `OpsEventLog()` with no arguments.
- `emit(...)` with the old keywords.
- `list_events(project_id=, kind=, limit=)` returning dicts.
- `detail["api_key"] == "[redacted]"`.

`to_dict()` gains two keys, `trace_id` and `parent_event_id`. **Do not** wire `SqlOpsSink` into `app.py`; SW-W3-S1 owns that file.

The code below was compiled and run against `dev @ 8e1c0fde` plus SW-W0-S2. The offline tests give 17 passed with the existing gap tests, and the integration test gives 1 passed. Paste it **exactly**.

### Step 1 — `src/swarm/observability/ops_events.py` (replace the whole file, exactly)
```python
{{FILE:src/swarm/observability/ops_events.py}}
```

### Step 2 — `src/swarm/observability/trace_graph.py` (create, exactly)
```python
{{FILE:src/swarm/observability/trace_graph.py}}
```

### Step 3 — `src/swarm/observability/__init__.py` (replace the whole file, exactly)
```python
{{FILE:src/swarm/observability/__init__.py}}
```

### Step 4 — `tests/controller/test_v23_ops_trace.py` (create, exactly)
```python
{{FILE:tests/controller/test_v23_ops_trace.py}}
```

### Step 5 — `tests/integration/db/test_v23_ops_events_sql.py` (create, exactly)
```python
{{FILE:tests/integration/db/test_v23_ops_events_sql.py}}
```

### Step 6 — run
```bash
uv run pytest tests/controller/test_v23_ops_trace.py tests/controller/test_v18_v30_gaps.py -q   # all pass
uv run pytest tests/api -q                                                                     # unchanged
```

### Section-5 acceptance
- [ ] Nested secret keys at any depth, inside dicts and lists, are stored as `[redacted]`; the raw secret never reaches the SQL `payload`.
- [ ] `OpsEventLog()` with no arguments behaves as before, and the existing `test_ops_events_and_dashboard_boundary` passes unchanged.
- [ ] `SqlOpsSink` events survive a new `OpsEventLog` instance, and filters by project, kind and trace work.
- [ ] `build_trace` returns ordered nodes; `complete` is true only when every `TRACE_CHAIN` stage is present and there are no orphans; gaps are listed, never filled.
- [ ] `list_events(limit=…)` never returns more than 1000 rows.
