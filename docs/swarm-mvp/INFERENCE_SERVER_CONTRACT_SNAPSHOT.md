# inference_server HTTP contract snapshot (client view)

Status: **observed, not released**. inference_server `main` is docs-only; the router code lives on
unmerged branches. This snapshot pins what SwarmAI's `RouterClient` (packet P05) expects. Source:
`inference_server` branch `cursor/v08-v17-offline-ladder-7ebe` @ `96af9d4`,
`src/inference_router/app.py`, `errors.py`, `router.py`, `config.py`. SwarmAI never edits inference_server.

## Endpoints used
| Method | Path | Used by |
|---|---|---|
| GET | `/v1/models` | `RouterClient.list_models()` |
| POST | `/v1/chat/completions` (`stream=false`) | `RouterClient.chat()` |
| POST | `/v1/chat/completions` (`stream=true`, SSE, `data: [DONE]`) | `RouterClient.chat_stream()` |

## `/v1/models` entry
`{"id", "object": "model", "created", "owned_by", "router": {...}}`.
- Route: `router.type="route"`, `billing` ∈ `free|trial|paid|unknown`, `capabilities` (list or null), `admission` (`"admitted"` or a reason).
- Alias: `router.type="alias"`, `routes`, `admitted_routes`; **no billing** → SwarmAI treats it as `unknown` (never free).
- Missing today: `context_window`, `max_output_tokens`, `tokenizer`. SwarmAI reads them from the router if present, else from `config/router_context_overrides.example.json` (overrides can **never** set billing).

## Response headers → `RouterCallReceipt`
`X-Request-Id`, `X-Router-Route`, `X-Router-Provider`, `X-Router-Upstream-Model`, `X-Router-Billing`,
`X-Router-Attempts` (comma list `route=outcome`), `Retry-After` on errors.

## Errors
Body `{"error": {"message", "type", "code"}}`. Mapping in `swarm.contracts.router_capabilities.classify_error`:
401→authentication, 403→policy_denied, 429→rate_limit, `upstream_payment_required`→quota_exhausted,
`unknown_model`→unsupported_capability, other 4xx→invalid_request, 504/`upstream_timeout`/`deadline_exceeded`→unknown_outcome, else transient.

## SwarmAI rules
- No client-side HTTP retries (router owns retry/fallback). One request per call.
- Zero spend: a response whose `X-Router-Billing` is not `free` is refused as `paid_route_forbidden`.
- Missing `usage` → `usage_known=false` (never zero). Timeouts → `unknown_outcome`.
- Stream without `[DONE]` or with an error event → `partial_stream` (partial text kept, never treated as success).

## Asks for the inference_server coordinator (non-blocking)
1. Additive capability fields on `/v1/models`: `context_window`, `max_output_tokens`, `tokenizer`, `supports_tools`, `supports_json`; `billing` on aliases (resolved worst-case).
2. Freeze the header set with a version header (e.g. `X-Router-Contract: 1`).
3. Document the max router-side attempts per request, and `Idempotency-Key` support (or its absence).
