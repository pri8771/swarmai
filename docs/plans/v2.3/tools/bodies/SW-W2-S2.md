**Goal.** Replace the "native dispatch records a plan and stops" behaviour with a **bounded native model/tool loop** that calls inference_server through `RouterClient` (SW-W1-S11).

Rules:
- The loop is hard-bounded by turns, model calls and tool calls. Only allow-listed tools ever execute.
- Any router error stops the loop and is recorded; it is never retried here.
- Missing `usage` is reported as `usage_known=False`, never as zero.
- The live path needs a ready `LiveGrant` plus `SWARM_ROUTER_BASE_URL` and `SWARM_ROUTER_MODEL`. Without them the executor records an honest blocker: `router_not_configured`, `router_model_not_configured` or the preflight reason (for example `missing_live_grant`).
- The executor **never invents success**. The mission outcome stays `submitted_pending` until acceptance, and `plan["native_loop"]` holds the loop summary plus a `native_loop.<status>` timeline entry.

The code below was compiled and run against `dev @ 8e1c0fde` plus the Wave-1 changes. `tests/pursuit tests/product tests/api` gives 82 passed (8 new), and ruff and mypy are clean. Paste it **exactly**.

### Step 1 — `src/swarm/pursuit/native_loop.py` (create, exactly)
```python
{{FILE:src/swarm/pursuit/native_loop.py}}
```

### Step 2 — `src/swarm/pursuit/native_dispatch.py` (replace the whole file, exactly)
Your base file must be the `dev @ 8e1c0fde` version. If `git diff 8e1c0fdec24c131e7612d88076220945230f4c3b -- src/swarm/pursuit/native_dispatch.py` prints anything before you start, someone else changed it: STOP (S4, section 10).
```python
{{FILE:src/swarm/pursuit/native_dispatch.py}}
```

### Step 3 — `tests/pursuit/test_v20_native_loop.py` (create, exactly)
It uses `tests/fixtures/router_http/fake_router.py` from SW-W1-S11, so no network is involved.
```python
{{FILE:tests/pursuit/test_v20_native_loop.py}}
```

### Step 4 — run
```bash
uv run pytest tests/pursuit/test_v20_native_loop.py -q        # 8 passed
uv run pytest tests/pursuit tests/product tests/api -q        # all pass
```
If `RouterClient`, `ChatResult`, `RouterClientError` or `FakeRouter` are missing, SW-W1-S11 has not been merged into your base yet. STOP (S2, section 10) with reason `blocked_on SW-W1-S11`.

**Never** point the tests or a local run at a real inference_server or at any paid route. Live runs belong to SW-W4-S1, under an explicit owner grant.
