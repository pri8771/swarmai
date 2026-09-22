# Provider inventory and blocker corrections — 2026-09-22

Read-only evidence on accepted source `fb58a751d40f1828990d7a0d687ad30de6eb6103`. No provider calls, secret reads, account changes or grants.

## Complete source catalogue

| Class | IDs |
|---|---|
| Core remote | openrouter, groq, gemini, cloudflare_workers_ai, huggingface_inference, nvidia_nim, mistral, cohere, cerebras |
| Extended remote | together, fireworks, deepinfra, replicate, perplexity, openai, anthropic, aws_bedrock, azure_ai_foundry, hyperbolic, sambanova, novita |
| Additional gateways | requesty, vercel_ai_gateway, portkey_cloud, cloudflare_ai_gateway |
| Dedicated endpoint | huggingface_dedicated |
| Local runtimes | ollama, vllm, mlx_lm, llama_cpp, llamafile |
| Disabled/retired in this source | github_models |

32 entries: 26 remote candidates, five local runtimes, one retired entry. Source supplies 30 offline adapters and a Bedrock offline shell. This is not 31 live-qualified or free services. The raw catalogue's `not_implemented` status is stale relative to source; `list_providers` overrides only core statuses, while `changes/provider-catalog-extended.json` holds an unapplied status update.

No subscription-backed provider route exists in this source. ChatGPT/Codex and Claude consumer subscriptions do not establish API-account eligibility.

Sources: `config/provider-catalog.json`, `src/swarm/providers/catalog.py`, `core/registry.py`, `extended/adapters.py`, `capability_registry.py`, `changes/provider-catalog-extended.json`.

## Actual readiness and fastest next facts

The exact-source W-121A ledger records zero admitted remote routes, with no remote inference executed and charge prevention/quota/health unverified. Historical onboarding reports account/auth presence, not present qualification. Historical Groq/OpenRouter canaries are stale; Gemini model listing proves authentication only. Canonical registry corroborates zero admitted remotes.

Historical accepted local evidence covers brokered Ollama `gemma3:4b` and `qwen3.5:4b` with fallback. It is not a fresh runtime check. Do not copy another project's local run receipts or grant into Swarm.

Owner was given the complete catalogue and asked which API accounts have confirmed free quota. Groq and Gemini are candidates for the first account check, not admitted routes:

- Groq publishes Free Plan limits; account-specific limits still need verification: https://console.groq.com/docs/rate-limits
- Gemini publishes free tiers for selected models, with free-tier data used to improve Google's products: https://ai.google.dev/gemini-api/docs/pricing

Use non-private qualification material. No paid upgrade or inference is authorized by this inventory. Two local runtimes do not satisfy a gate requiring two independent remote providers.

## Other corrected blockers

- “No second physical machine exists” is unsupported. No second physical host is qualified in current evidence. The owner mentioned an R730 and a Windows machine; OS, access, physical independence and product prerequisites remain to be verified. Bots' choice of the Mac does not grant Swarm access to other hosts.
- PR28 `11bd4b5276458b2b7adc11528f117e919524f035` is awaiting a verdict; its hosted CI executes and stops on inherited Ruff I001. PR29 `349c732c335d83eaa431d30ea7f2b52b8d4431a3` has green hosted checks on its separate base; PG and live gates are not executed there. Earlier billing failures remain historical facts.
- Proposed composition is accepted `fb58a751` plus P0, lint and selective R02c `1c9ff44ec787508fb874f5ac7fde849f89bdfe42`. R02c touches a rewritten worker: preserve the new worker and integrate the intended guard/prompt semantics, never replace it wholesale. This is a recommendation awaiting release and independent exact-tree review.
- R02a already has bounded guard verdict `ef8a2cc25c9caf8665804a28453c6f81f82d4a11`; R17a has bounded harness verdict `e5bd6350569fb10146517430ca6f7fa097de84a4`. Queue reconciliation must preserve open CP1/CP3/multi-host acceptance.
- R31a's dependencies are accepted, but its contract must align with the newer R30b terminal-request-proof rule and accepted manifest vocabulary before implementation; bare zero submissions cannot establish `not_applied`.

Requested native lead package: target/ownership reconciliation; exact PR28/29 verdicts; bounded composition and R31a release; truthful queue normalization. No self-acceptance, live attempt renewal, new scheduler or main merge.
