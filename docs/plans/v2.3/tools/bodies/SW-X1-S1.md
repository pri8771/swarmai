**Goal.** Make SwarmAI a standard API client of **SplitSignal** (the product in the `inference_server` repo), per the frozen consumer contract `swarmai-consumer 1.x` (inference_server `docs/api/v1/consumers/swarmai.md`, session IS-W1-S10). Add a `SplitSignalClient` adapter that subclasses `RouterClient` (SW-W1-S11) and reuses its types, and make `native_loop_from_env` (SW-W2-S2) prefer `SPLITSIGNAL_*` over the legacy `SWARM_ROUTER_*` personal-router variables. Everything is tested offline against a fake. **No real SplitSignal call is made in this session.**

**Why.** The legacy router client reads `router.billing` from `/v1/models` and `X-Router-*` headers. SplitSignal sends neither. Its `/v1/models` returns the OpenAI list shape `{"object":"list","data":[{"id","object","created","owned_by"}]}`; cost comes from the `splitsignal` metadata on the settled response, and errors are `{"error":{code,message,request_id,retryable}}`. With the legacy client, every SplitSignal route would read as `billing: unknown` and be refused as `paid_route_forbidden`. The inference_server plan also retires the personal router (its X6), so SplitSignal becomes SwarmAI's only inference dependency.

**Decision D-SS1 — coordinator-accepted 2026-09-26 (C3); the owner may override it.** Copy this paragraph into the handoff under "Decisions".
- A route listed by SplitSignal's `/v1/models` under SwarmAI's key is admitted as `billing: free`. The contract says `/v1/models` lists only routes usable now, and in M1 only `cost_class: free` is dispatchable.
- A response whose `splitsignal.cost.amount` is a **known non-zero** decimal is refused after the fact with `policy_denied / paid_route_forbidden`; the receipt keeps `billing: paid`.
- An unknown cost (`amount: null`) is recorded as unknown: `cost_amount = None`, `cost_source = "unknown"`, never `0`. The receipt then has `usage_known = False`, so accounting keeps the budget hold committed and never releases it as zero (F-13 semantics).
- If the body is a `ModelPage` (`items[]` with `cost_class`), `cost_class` is authoritative. The coordinator is getting inference_server fixed so `/v1/models` returns `{"object":"list","data":[...]}` (C4); the adapter accepts both shapes.

### Step 0 — external gate SP1 (the contract is frozen)
SP1 means inference_server session IS-W1-S10 is merged into `cursor/is-v23-integration-460c`. Check it read-only:
```bash
gh api "repos/pri8771/inference_server/contents/docs/api/v1/consumers/swarmai.md?ref=cursor/is-v23-integration-460c" --jq .path \
  && echo "SP1 OK" || echo "SP1 MISSING"
```
- `SP1 OK`: read that file (`gh api ... --jq .content | base64 -d`). Compare it with the facts in this prompt: env var names `SPLITSIGNAL_BASE_URL` / `SPLITSIGNAL_API_KEY` / `SPLITSIGNAL_MODEL`, route ids like `mock/ok`, error codes, and the `/v1/models` shape. If the doc's `/v1/models` example is a `ModelPage` (`items`) instead of `{"object":"list","data":[...]}`, that is fine: the adapter accepts both. Write the difference in the handoff under "Decisions". If the doc changes something else this prompt relies on (env var names, auth header, error envelope field names), STOP (S7) and name the difference.
- `SP1 MISSING`: STOP (S7, section 10) with reason `external gate SP1 not reached`. Do not guess the contract. Exception: if the coordinator explicitly asks for the adapter before SP1, implement it against the offline fake, title the PR `[AWAITING SP1]`, write `awaiting SP1` in the handoff Status, and do not merge it.
- These contract facts are expected and are **not** differences (joint consistency check, `docs/plans/v2.3/JOINT_PLAN.md`): the version line `Consumer contract version: swarmai-consumer 1.0.0` (any `1.x` is compatible); the six `x-ratelimit-*` headers are optional and informational (the real server sends none; the mock and the fake send demo values; the adapter ignores them); a client may strip the trailing `/v1` from `SPLITSIGNAL_BASE_URL` and append `/v1/...` itself; the usage chunk arrives only with `stream_options.include_usage` (the base client sends it).
- Retry rule in the contract: never retry before `Retry-After` has elapsed; a client whose maximum wait is shorter gives up instead. Since SW-FIX-RETRY (`b3162712`), `RetryOwner.decide` returns a give-up with reason `retry_after_exceeds_cap` when `Retry-After` exceeds `max_retry_after_seconds` (30 s) or is not finite. Confirm with `grep -n retry_after_exceeds_cap src/swarm/broker/retry.py` and record the result under "Decisions". If the grep prints nothing, add under "Needs other owner": `src/swarm/broker/retry.py: when retry_after exceeds max_retry_after_seconds, give up instead of retrying at the cap (SplitSignal contract)`. Do not edit that file in this session.
- If `gh api repos/pri8771/inference_server --jq .full_name` does not print `pri8771/inference_server`, this session cannot read the private repo: STOP (S7) with reason `inference_server not readable from this environment`.

### Step 1 — `src/swarm/providers/splitsignal_client.py` (create, exactly)
```python
{{FILE:src/swarm/providers/splitsignal_client.py}}
```

### Step 2 — `tests/fixtures/splitsignal_http/__init__.py` (create, empty file) and `tests/fixtures/splitsignal_http/fake_splitsignal.py` (create, exactly)
Every body in this fake was validated against inference_server `docs/api/v1/openapi.yaml` (`V1ModelList`, `ChatCompletion`, `ChatCompletionChunk`, `ErrorEnvelope`, `OfferCapabilities`, `OfferLimits`). The key is the contract's synthetic test key, not a secret.
```python
{{FILE:tests/fixtures/splitsignal_http/fake_splitsignal.py}}
```

### Step 3 — `tests/providers/test_splitsignal_client.py` (create, exactly)
```python
{{FILE:tests/providers/test_splitsignal_client.py}}
```

### Step 4 — `src/swarm/pursuit/native_loop.py` (two edits, nothing else)
Edit 4a: directly **below** the line `from swarm.providers.router_client import RouterClient, RouterClientError`, add:
```python
from swarm.providers.splitsignal_client import DEFAULT_SPLITSIGNAL_MODEL, SplitSignalClient
```
Edit 4b: replace the whole function `native_loop_from_env` (it is the last function in the file). It currently reads exactly:
```python
{{FILE:snippets/SW-X1-native_loop_before.py}}
```
Replace it with exactly:
```python
{{FILE:snippets/SW-X1-native_loop_from_env.py}}
```
If the current text differs from the "currently reads" block, STOP (S4, section 10).

### Step 5 — `tests/pursuit/test_v20_native_loop.py` (one added line)
In `test_executor_without_loop_records_honest_blocker`, directly below `monkeypatch.delenv("SWARM_ROUTER_BASE_URL", raising=False)`, add:
```python
    monkeypatch.delenv("SPLITSIGNAL_BASE_URL", raising=False)
```
Reason: Cloud Agent environments may inject `SPLITSIGNAL_BASE_URL` as a secret. Without this line the test then fails, because the blocker reason changes. This failure was reproduced.

### Step 6 — `tests/pursuit/test_v20_native_loop_splitsignal.py` (create, exactly)
```python
{{FILE:tests/pursuit/test_v20_native_loop_splitsignal.py}}
```

### Step 7 — `docs/swarm-mvp/INFERENCE_SERVER_CONTRACT_SNAPSHOT.md` (append at the end)
```markdown
## SplitSignal consumer contract (`swarmai-consumer 1.x`) — SW-X1-S1

- Source: inference_server `docs/api/v1/consumers/swarmai.md` on `cursor/is-v23-integration-460c` (read <DATE>, blob <git sha from gh api --jq .sha>).
- Env: `SPLITSIGNAL_BASE_URL` (ends in `/v1`; the client strips it), `SPLITSIGNAL_API_KEY` (bearer; never logged), `SPLITSIGNAL_MODEL` (route id `<provider>/<model>`; default `gemini/gemini-3.5-flash-lite` when unset). These win over the legacy `SWARM_ROUTER_*`.
- `GET /v1/models`: OpenAI list shape; listed routes are admitted as free (decision D-SS1, coordinator-accepted 2026-09-26, owner may override). A `ModelPage` body's `cost_class` is authoritative.
- Chat: served route = body `model` = `X-SplitSignal-Served-Route`; usage `null` stays unknown; a known non-zero `splitsignal.cost.amount` is refused as `paid_route_forbidden`; an unknown cost is `cost_amount: null` and the receipt does not settle (`usage_known: false`), so no budget is released as zero (C3, F-13).
- Errors: `ErrorEnvelope`. A non-retryable 5xx is `unknown_outcome` (SplitSignal sets `retryable` only when no provider execution can still be running). SwarmAI never auto-retries after a 200 header; the stream `event: error` is `partial_stream`.
- Offline fake: `tests/fixtures/splitsignal_http/fake_splitsignal.py`. Live use still needs a LiveGrant (V20-E07) and sync point SP4 (non-streaming) / SP5 (streaming).
```
Fill `<DATE>` and the blob SHA from Step 0.

### Step 8 — optional: run against the real mock (only if SP2 is reached)
SP2 means `scripts/mock_splitsignal.py` is on `cursor/is-v23-integration-460c`. This step is optional. Its result goes into the handoff only; do not commit the mock. The mock loads `docs/api/v1/consumers/fixtures` relative to its repo root, so export that tree read-only and run the mock from there (a lone `/tmp/mock_splitsignal.py` dies with `FileNotFoundError` and the client then reports `transient:connect_error`, which is not a contract mismatch). Without a clone, fetch `scripts/mock_splitsignal.py` **and** every file under `docs/api/v1/consumers/fixtures/` with `gh api`, keeping the same relative paths under `/tmp/is-mock`.
```bash
mkdir -p /tmp/is-mock && git -C <inference_server clone> archive origin/cursor/is-v23-integration-460c scripts docs/api/v1 | tar -x -C /tmp/is-mock \
  && (cd /tmp/is-mock && python3 scripts/mock_splitsignal.py --port 8089 & echo $! > /tmp/mock.pid; sleep 2) \
  && SPLITSIGNAL_API_KEY="ss_live_00000000000000000000000000000000_AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA" uv run python -c "
from swarm.providers.splitsignal_client import SplitSignalClient
c = SplitSignalClient('http://127.0.0.1:8089/v1')
print([m.model_id for m in c.list_models()])
r = c.chat({'model': 'mock/ok', 'messages': [{'role': 'user', 'content': 'hi'}]})
print(r.receipt.route_id, r.receipt.billing, r.receipt.usage_known)
"; kill "$(cat /tmp/mock.pid)" 2>/dev/null; true
```
Expected output (observed with the IS-W1-S10 mock: `['mock/ok', 'mock/quota', 'mock/unavailable']` then `mock/ok free False`): a list containing `mock/ok`, then `mock/ok free <True or False>` (`False` is correct when the mock's fixture reports no cost). If it differs, record the exact output under "Needs other owner" (a contract/mock mismatch for the inference_server coordinator). Do **not** change the adapter to fit the mock.

### Acceptance (this session)
- [ ] Step 0 printed `SP1 OK`, and the contract facts match (or the differences are recorded).
- [ ] `uv run pytest tests/providers/test_splitsignal_client.py tests/pursuit -q` passes (27 new tests in the two new files, plus the existing ones).
- [ ] `SPLITSIGNAL_BASE_URL=http://x.test/v1 uv run pytest tests/pursuit/test_v20_native_loop.py -q` passes.
- [ ] `tests/providers/test_router_client.py` is unchanged and still passes (the legacy path works).
- [ ] No real network call: every test uses `FakeSplitSignal().transport()` or an explicit `env` dict.
- [ ] `grep -rn "ss_live_" src/` prints nothing (the synthetic key lives only in tests).
- [ ] `test_chat_unknown_cost_never_settles_as_zero` and `test_unknown_cost_keeps_loop_usage_unknown` pass.
- [ ] The handoff records D-SS1, the contract blob SHA and the Step 8 result (or `SP2 not reached`).
