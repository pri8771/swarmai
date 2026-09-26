**Goal.** Fix finding **F-02**. Today a pack "signature" is `sha256(pack_id|version|digest|caps)` with no key, so anyone can forge it. This session adds:
1. **Keyed signatures**: HMAC-SHA256 (`hmac-sha256-v1:<hex>`) per publisher, with keys read from the environment and never stored in the repo.
2. **Lifecycle**: `installed → enabled_for_project → draining → disabled → uninstalled`, plus immediate `revoke`, persisted in memory or in `v23_pack_installs`.

**Compatibility.** Existing tests (`tests/controller/test_v18_v30_gaps.py::test_pack_signature_and_revoke`, `tests/controller/test_v23_v20.py`, `tests/portability/test_portable_protocol.py`) and `product/portable_protocol.py:81` use the legacy digest without keys. They keep working: legacy mode applies when `trusted_keys=None`. Keyed mode (production; SW-W3-S1 wires it) refuses unkeyed digests.

The code below was compiled and run against `dev + SW-W0-S2` (9 new passed, 50 existing pack/portability tests still pass, 1 PostgreSQL passed). Paste it **exactly**.

### Step 1 — `src/swarm/capabilities/signing.py` (create, exactly)
```python
{{FILE:src/swarm/capabilities/signing.py}}
```

### Step 2 — `src/swarm/capabilities/__init__.py` (replace the whole file, exactly)
```python
{{FILE:src/swarm/capabilities/__init__.py}}
```

### Step 3 — `src/swarm/capabilities/lifecycle.py` (create, exactly)
```python
{{FILE:src/swarm/capabilities/lifecycle.py}}
```

### Step 4 — tests (create, exactly)
`tests/extensions/test_v23_pack_lifecycle.py`:
```python
{{FILE:tests/extensions/test_v23_pack_lifecycle.py}}
```
`tests/integration/db/test_v23_pack_installs_sql.py`:
```python
{{FILE:tests/integration/db/test_v23_pack_installs_sql.py}}
```

### Step 5 — run
```bash
uv run pytest tests/extensions/test_v23_pack_lifecycle.py -q            # 9 passed
uv run pytest tests/controller/test_v18_v30_gaps.py tests/controller/test_v23_v20.py tests/portability -q   # unchanged, all pass
sudo -u postgres psql -c "CREATE DATABASE swarm_sw_w1_s5 OWNER swarm;" || true
SWARM_DATABASE_URL=postgresql+psycopg://swarm:swarm@127.0.0.1:5432/swarm_sw_w1_s5 uv run pytest tests/integration/db/test_v23_pack_installs_sql.py -q -m integration   # 1 passed
```

### Section-5 acceptance
- [ ] Keyed mode: forged, tampered, wrong-key, untrusted-publisher and unsigned packs are refused.
- [ ] Lifecycle: enable is per project; other projects are denied; capabilities are never widened; draining blocks new use and new enables; disable and uninstall follow the transition table; revoke disables immediately.
- [ ] Legacy fixture tests pass unchanged.
- [ ] Handoff "Needs other owner": "SW-W3-S1 must build the operational registry as `CapabilityPackRegistry(require_signature=True, trusted_keys=trusted_keys_from_env())`."
