# Provider receipt fields — offline candidate

The core OpenAI-compatible transport now retains only `x-ratelimit-*` and `retry-after` response headers, with secret redaction, on success and HTTP errors. The adapter records those headers in `AttemptReceipt.normalized_usage.extras`. It records a nonnegative finite `usage.cost` as an exact decimal string with `response.usage.cost` provenance. Missing or invalid cost remains `unknown`; it is never filled with zero.

OpenRouter requests opt into `X-OpenRouter-Metadata: enabled`. The receipt keeps only the reported attempt count, BYOK flags, selected backend and selected model. The requested backend in a route snapshot is not proof of the backend that served a request. Missing routing metadata remains unknown. A reported cost of zero and reported backend still require authenticated account and generation readback before a live zero-charge claim.

Official references checked September 22: [OpenRouter chat response and metadata](https://openrouter.ai/docs/api/api-reference/chat/create-a-chat-completion), [OpenRouter generation metadata](https://openrouter.ai/docs/api/api-reference/generations/get-generation), [Groq rate-limit headers](https://console.groq.com/docs/rate-limits).

The tests use `httpx.MockTransport` only. No provider call, authenticated metadata request, key readback, charge verification or live grant was used. Durable broker accounting remains a separate prerequisite.
