**Goal.** Complete ART-V23-PORTABILITY and fix finding **F-03**.
- Today secret stripping only checks key names; a value like `"sk-…"` under a harmless key passes, and any `"env:…"` string passes under a secret key.
- Bundles also carry no history, receipts or approvals.

**Schema 2 adds:**
- Sections `history`, `receipts`, `approvals`, `leases` and `artifact_digests`, each with its own digest.
- Approvals and leases are **tombstoned** (`executable: false`, `state: "tombstoned"`), so imported authority can never run.
- A compatibility check (`min_reader`) and a namespace remap on import (`target_project_id`).
- A value-based secret scan over every string, with strict `env:NAME` references.

Schema-1 bundles still import, and existing callers (`product/portable_protocol.py`, `tests/controller/test_v23_v20.py`, `tests/portability/test_portable_protocol.py`) are unchanged.

The code below was compiled and run against `dev @ 8e1c0fde` (7 new tests pass; the existing portability tests pass unchanged). Paste it **exactly**.

### Step 1 — `src/swarm/product/portability.py` (replace the whole file, exactly)
```python
{{FILE:src/swarm/product/portability.py}}
```

### Step 2 — `tests/portability/test_v23_bundle.py` (create, exactly)
```python
{{FILE:tests/portability/test_v23_bundle.py}}
```

### Step 3 — run
```bash
uv run pytest tests/portability/test_v23_bundle.py -q          # 7 passed
uv run pytest tests/portability tests/controller/test_v23_v20.py -q   # all pass
```

### Section-5 acceptance
- [ ] Secret values are caught anywhere (config, history, receipts); `env:` references must match `^env:[A-Z_][A-Z0-9_]*$`.
- [ ] Round-trip into a clean directory verifies the integrity and section digests; imported approvals and leases are non-executable tombstones.
- [ ] Tampered sections, injected `executable: true` and incompatible `min_reader` are rejected.
- [ ] Remap rewrites `project_id` in sections and records `remapped_from`.
- [ ] Schema-1 bundles still import.
