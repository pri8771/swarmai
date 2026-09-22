# Existing-provider reuse — source return, 2026-09-22

Owner selected existing Groq + OpenRouter + Ollama. Reuse these accounts/runtime; do not request another broad account inventory. No live-call grant was requested or inferred this turn.

## Completed bounded source repair

Draft PR32: https://github.com/pri8771/swarmai/pull/32

- Candidate: 7aa45a0c436598f5354540476410a0fd1f81bb07.
- Exact tree: d41eb5e67addaea328cabcce1f56b171dfc2d03d.
- Base: 4d16fe85188861df6e123b4454c6bdc416e6c639 (PR30, separate formal verdict pending).
- Branch/worktree: codex/swarm-provider-output-bound-20260922; /tmp/swarm-provider-output-bound-20260922.
- Scope: two production files plus one regression file. InferenceRequest now rejects nonpositive/noninteger output limits. Core adapters serialize the requested limit using their API field; absent limits remain omitted.

Root cause reproduced at the HTTP boundary using MockTransport: before repair 15 failed / 11 passed. No real requests or keys were used. After repair: 66 focused passed; full offline 470 passed / 211 skipped; full owned PostgreSQL 668 passed / 13 live skips; Ruff clean; mypy 174 source files clean; diff check clean. PostgreSQL used only a new disposable database in the owned socket cluster on 56421. public_tables_after_tests=0; cleanup_remaining=0. Jobs database and all product runtime data untouched.

Independent mechanical reviewer /root/jobs_exact_review recommends acceptance for exact tree d41eb5e67addaea328cabcce1f56b171dfc2d03d; independently ran all 26 added regression cases with no sockets. No actionable findings. Source commit and remote readback agree. This is a recommendation, not self-acceptance; formal source verdict requested through draft PR32. Hosted runs 35783041304 and 35783036966 completed successfully for this exact source (offline and console checks, read back after 20:53Z). The live-gated jobs also completed their notices; they do not establish live qualification.

## Remaining engineering before a useful owner grant

1. Freeze and implement explicit OpenRouter request controls for an exact currently eligible free model and backend: forbid paid model/provider fallback and additional billable features; preserve actual resolved backend identity. Do not introduce a generic unchecked extra-payload passthrough.
2. Add a reviewed remote-admission path with durable bounded-call accounting. Current providers canary deliberately refuses remote providers. Keep the refusal until the successor path has exact account/model/quota/cost evidence and authority validation; a caller assertion is insufficient.
3. Preserve provider cost/charge provenance and rate-limit evidence. Core receipts currently keep tokens and model but discard provider cost and HTTP rate-limit headers. A zero local policy budget is not provider billing proof.
4. For the later G12 overlap gate, ensure calls actually overlap under broker control. Current core HTTP is synchronous inside async execute_one; asyncio.gather alone is not overlap evidence. Preserve no automatic transport retries and explicitly limit broker retries to one attempt.

Proposed admission envelope after those prerequisites: one exact approved request each to Groq, OpenRouter and already-installed loopback Ollama, fixed public synthetic prompt, finite output cap/timeout, zero retries and substitutions; a separate later grant for the governed G12 mission. Do not present this as executable or approved until exact source, models, account evidence and command are bound.

## Account evidence without starting over

Historical account inventory remains the reuse source. Existing private receipt timestamps remain September20. This turn checked credential-name presence only in the isolated source .env, main-clone .env and private candidate.env; none of those locations supplied the selected key names. This limited check does not establish that credentials are missing elsewhere. Resolve existing private credential references locally before asking the owner; never export keys into Git, shell arguments, or output.

Current account tier/quota readback is still outstanding. No authenticated provider API call, browser login, account change, inference, model download, schedule, spend or deployment occurred. Public official documentation was read only.

## Evidence correction

The earlier local-admission-reconcile.json is simulated: its script replaces execute_one with _stub. Do not cite it as actual Ollama inference. Separate historical evidence at f393f7f:docs/evidence/g12/a5-current-tip-local-proof.json records real local calls on source 84df040b6ac5981856ab7f32b66966cc0cf38894, September21. This is neither current-source proof nor remote qualification.

## Primary references checked

- Groq completion field: https://console.groq.com/docs/api-reference
- Gemini generationConfig.maxOutputTokens: https://ai.google.dev/api/generate-content
- Cohere max_tokens: https://docs.cohere.com/v2/reference/chat
- Cloudflare compatible endpoint: https://developers.cloudflare.com/workers-ai/configuration/open-ai-compatibility/
- OpenRouter routing restrictions and max_price: https://openrouter.ai/docs/guides/routing/provider-selection
- OpenRouter key metadata: https://openrouter.ai/docs/api/api-reference/api-keys/get-current-key
- Groq account Free tier versus paid Developer tier: https://console.groq.com/docs/billing-faqs
- Groq spend-limit tracking can lag 10–15 minutes; it cannot substitute for verifying the no-charge tier: https://console.groq.com/docs/spend-limits

Public documentation is not account-specific eligibility. Native holds remain in force; owner selection removes no-spend or review boundaries. Next reviewer/Claude should start with these concrete engineering gaps, preserve the exact reviewed repair, and avoid repeating the settled inventory/full tests without drift. If a new gate blocks progress, record exact evidence and switch to another permitted bounded task; do not loop on broad account questions or silently dispatch Fable.
