**Goal.** Build packet P05, SwarmAI's client for the `inference_server` router. Today `src/` has **no** router client and no `X-Router-*` handling.

**This session adds:**
- `swarm.contracts.router_capabilities`: `RouteBilling`, `RouteCapabilities.admissible()` (free-only), `RouterCallReceipt` built from headers, and `classify_error`, which maps router errors to `ErrorClass`.
- `swarm.providers.router_client.RouterClient` on `httpx`:
  - `list_models`, `chat` and `chat_stream`.
  - **No retries**.
  - Refuses routes that are not free.
  - Treats timeouts as `unknown_outcome`, missing usage as unknown (not 0), and an incomplete stream as `partial_stream`.
- An offline `FakeRouter` built on `httpx.MockTransport`, with 10 scenarios, used here and by SW-W2-S2.
- An overrides example file and a contract snapshot doc.

**Live calls stay blocked** (owner LiveGrant, blocker B-05). Nothing in this session may contact a real network address; the tests use `http://router.invalid` with the mock transport.

The code below was compiled and run against `dev @ 8e1c0fde`. `tests/providers` gives 48 passed, including 12 new tests, and ruff and mypy are clean. Paste it **exactly**.

### Step 1 — `src/swarm/contracts/router_capabilities.py` (create, exactly)
```python
{{FILE:src/swarm/contracts/router_capabilities.py}}
```

### Step 2 — `src/swarm/providers/router_client.py` (create, exactly)
```python
{{FILE:src/swarm/providers/router_client.py}}
```

### Step 3 — test fixtures (create, exactly)
Create `tests/fixtures/__init__.py` and `tests/fixtures/router_http/__init__.py` as **empty** files. Then create `tests/fixtures/router_http/fake_router.py`:
```python
{{FILE:tests/fixtures/router_http/fake_router.py}}
```

### Step 4 — `tests/providers/test_router_client.py` (create, exactly)
```python
{{FILE:tests/providers/test_router_client.py}}
```

### Step 5 — `config/router_context_overrides.example.json` (create, exactly)
```json
{{FILE:config/router_context_overrides.example.json}}
```

### Step 6 — `docs/swarm-mvp/INFERENCE_SERVER_CONTRACT_SNAPSHOT.md` (create, exactly)
````markdown
{{FILE:docs/swarm-mvp/INFERENCE_SERVER_CONTRACT_SNAPSHOT.md}}
````

### Step 7 — run
```bash
uv run pytest tests/providers/test_router_client.py -q    # 12 passed
uv run pytest tests/providers -q
```
If `from tests.fixtures.router_http.fake_router import FakeRouter` fails with `ModuleNotFoundError`, check that both `__init__.py` files exist. `tests/__init__.py` already exists on the base branch.

### Section-5 acceptance
- [ ] `list_models` parses route and alias entries; only `billing == "free"` with `admission` of `admitted` or absent is admissible, and aliases are unknown and therefore not admissible.
- [ ] Overrides fill missing context and tool metadata but can never change billing.
- [ ] `chat` returns a `RouterCallReceipt` from `X-Router-*` headers; missing `usage` gives `usage_known=False`.
- [ ] A paid response raises `paid_route_forbidden`; each error scenario sends exactly one request (no retries) and maps to the documented `ErrorClass`.
- [ ] A complete stream returns the text and usage; a stream without `[DONE]` raises `partial_stream` with the partial text.
- [ ] No real network, no API key in code (the test key is a fake literal via `monkeypatch`).
