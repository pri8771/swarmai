# Provider progress and category clarification — 2026-09-22

Read-only source/record audit of clean candidate 4d16fe85188861df6e123b4454c6bdc416e6c639. No provider auth request, inference, account change, secret value readback or runtime enablement. Historical onboarding evidence is dated September 20; inspecting it today does not make its auth/quota fresh.

## Work already done

| Group | Provider(s) | Recorded completed work | Remaining distinction |
|---|---|---|---|
| Core remote | OpenRouter, Groq | Adapter code, account/key setup, historical completion-call receipts (HTTP 200, four completion tokens each) | OpenRouter returned no visible text, finish length; these small canaries are not useful-task qualification. Exact current model/free eligibility, remaining quota, charge prevention and product-path mission qualification remain open |
| Core remote | Gemini, Cloudflare Workers AI, Hugging Face Inference, NVIDIA NIM, Mistral, Cohere | Adapter code and account/key/auth-metadata checks | Model/account metadata success does not establish generation or zero-charge eligibility |
| Core remote | Cerebras | Adapter code exists | No completed onboarding record found in inspected inventory |
| Extended remote | Anthropic, Together, Fireworks, DeepInfra, Replicate | Adapter code and account/key/auth checks recorded | No current zero-charge inference qualification. Together/Fireworks historically held under no-spend |
| Extended remote | OpenAI | Adapter code and account sign-in recorded | API setup deferred at payment gate; no key recorded in that inventory |
| Other extended remote | Perplexity, AWS Bedrock, Azure AI Foundry, Hyperbolic, SambaNova, Novita | Connector implementation/configuration exists; Bedrock is explicitly an offline shell | No completed account onboarding found. Endpoint-specific entries still need real operator configuration |
| Additional gateways | Requesty, Vercel AI Gateway, Portkey Cloud, Cloudflare AI Gateway | Connector code exists | No completed onboarding or live route qualification found |
| Dedicated endpoint | Hugging Face Dedicated | Connector supports an existing operator-configured endpoint | A general HF account/token is not a provisioned dedicated model endpoint; none proved here |
| Local runtimes | Ollama | Installed local route; actual historical brokered calls to gemma3:4b and qwen3.5:4b recorded | Fresh run/current-source evidence remains separate from historical local receipts |
| Other local runtimes | vLLM, MLX-LM, llama.cpp, llamafile | Connector code exists | No Swarm-qualified runtime installation/run established in this audit |
| Retired | GitHub Models | Explicitly blocked from adapter registration | Official service retired July 30, 2026; do not count as a current candidate |

Onboarding total: 13 remote services with credentials/auth recorded plus local Ollama = 14 reported entries. This comprises eight of nine core remotes and five extended remotes. Do not describe this as “nothing set up” or ask the owner to inventory all accounts again.

A separate read-only review of whitelisted private receipt metadata confirmed OpenRouter's completion response at 2026-09-20T15:36:08Z (usage cost 0) and Groq's at 15:46:13Z (zero-spend recorded, no cost field). No response previews, credential values, probes or new inference were used. The scoped canonical registry at 34e10a60e255161829d0dce3c384eec10ca014e5 still admits zero remote routes.

## What the categories mean

Core and extended are this project's implementation-wave labels, not official industry tiers or quality/cost rankings. Core is the initial priority group; extended adds more providers. OpenRouter is technically a gateway but belongs to the core rollout wave.

A remote provider runs the model outside the owner's machine and exposes an API. An additional gateway sits between Swarm and one or more model providers, adding routing/observability/control; adding it does not automatically add free quota or an independent inference backend. Cloudflare Workers AI (model hosting) and Cloudflare AI Gateway (request intermediary) are separate entries.

A dedicated endpoint is a managed deployment for a selected model on configured infrastructure, rather than merely an account on a shared provider service. Local runtimes are the software that executes models on owned/self-hosted hardware: the runtime and model are distinct (for example, Ollama runs a Qwen model). Disabled is a current configuration/policy state; retired denotes a discontinued/excluded route. Not every disabled provider is retired.

## Real remaining blocker

W-121A admitted zero remote routes for its current G12 proof. That is a routing/evidence boundary, not zero completed setup. The old Groq/OpenRouter canaries were not accepted as current route/quota/charge-prevention evidence; Gemini only established metadata access. The next route-qualification packet should reuse the known accounts and existing credential references, starting with the historically tested pair if current eligibility supports it. Ask the owner only for a concrete missing login/consent or a bounded live-call grant once the exact scope is ready; do not repeat the generic “which accounts do you have?” question.

The first dual-remote gate needs at least two independently authorized remotes plus a local route, not activation of every catalog entry. Do not run inference to answer this status question.

## Source/display discrepancy

config/provider-catalog.json still labels many implemented adapters not_implemented and all entries disabled. list_providers overrides implementation status only for core providers. Actual code contains ten core adapters including Ollama, plus 21 extended entries; Bedrock remains an offline-only shell. Therefore neither the raw catalog nor connector presence alone is a truthful live-readiness dashboard. This is an engineering status-reporting issue; this documentation correction does not enable routes or silently change production code.

## Sources

- docs/onboarding/ACCOUNT_INVENTORY.md, account-inventory.json and PLATFORM_ACCESS.md (historical onboarding).
- docs/evidence/inf-121/w121a-remote-eligibility-ledger.json; local-admission-reconcile.json; docs/evidence/g12/DUAL_REMOTE_TEST_PLAN.md.
- src/swarm/providers/catalog.py, core/adapters.py, core/registry.py, extended/adapters.py, capability_registry.py.
- Official category references checked September 22: https://developers.cloudflare.com/ai-gateway/ ; https://huggingface.co/docs/inference-endpoints/about ; https://docs.ollama.com/quickstart .
- Official GitHub retirement notice: https://docs.github.com/en/github-models . GitHub Models is separate from GitHub Copilot.
