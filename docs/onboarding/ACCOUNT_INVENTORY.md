# SwarmAI account inventory (sanitized)

**Generated:** 2026-09-20T15:19:24Z
**Spend policy:** zero — no cards, purchases, or paid endpoints
**V0.1 remote:** `cursor/v0.1-real-mission-runtime` @ `0a0c7e4` (push complete)
**Onboarding branch:** `cursor/v0.1-provider-onboarding`
**Browser:** local visible Google Chrome, dedicated SwarmAI profile (Browserless abandoned)

## Identity
Preferred SwarmAI account email/SSO: **pending operator answer (asked once)** — not inferred from git.

## Honest outcomes (catalog providers)

| Provider | Priority | Outcome | API / inference | Next action |
|---|---|---|---|---|
| `openrouter` | core | waiting_operator_signin | account_unverified_browser_open | Sign in on OpenRouter tab in SwarmAI Chrome profile; do not paste secrets in cha |
| `groq` | core | waiting_operator_or_browser | unknown | Browser tab queued or pending after identity choice; verify free eligibility bef |
| `gemini` | core | waiting_operator_or_browser | unknown | Browser tab queued or pending after identity choice; verify free eligibility bef |
| `cloudflare_workers_ai` | core | waiting_operator_or_browser | unknown | Browser tab queued or pending after identity choice; verify free eligibility bef |
| `huggingface_inference` | core | waiting_operator_or_browser | unknown | Browser tab queued or pending after identity choice; verify free eligibility bef |
| `nvidia_nim` | core | waiting_operator_or_browser | unknown | Browser tab queued or pending after identity choice; verify free eligibility bef |
| `mistral` | core | waiting_operator_or_browser | unknown | Browser tab queued or pending after identity choice; verify free eligibility bef |
| `cohere` | core | waiting_operator_or_browser | unknown | Browser tab queued or pending after identity choice; verify free eligibility bef |
| `cerebras` | catalog | payment_gated | blocked_no_spend | Do not attach payment method; leave disabled under no-spend |
| `github_models` | catalog | unavailable_retired | n/a | Unavailable — retired |
| `together` | catalog | cataloged_unverified_offer | not_yet_attempted | Browser tab queued or pending after identity choice; verify free eligibility bef |
| `fireworks` | catalog | cataloged_unverified_offer | not_yet_attempted | Browser tab queued or pending after identity choice; verify free eligibility bef |
| `deepinfra` | catalog | cataloged_unverified_offer | not_yet_attempted | Browser tab queued or pending after identity choice; verify free eligibility bef |
| `replicate` | catalog | cataloged_unverified_offer | not_yet_attempted | Browser tab queued or pending after identity choice; verify free eligibility bef |
| `perplexity` | catalog | cataloged_unverified_offer | not_yet_attempted | Browser tab queued or pending after identity choice; verify free eligibility bef |
| `openai` | catalog | cataloged_unverified_offer | not_yet_attempted | Browser tab queued or pending after identity choice; verify free eligibility bef |
| `anthropic` | catalog | cataloged_unverified_offer | not_yet_attempted | Browser tab queued or pending after identity choice; verify free eligibility bef |
| `aws_bedrock` | catalog | cataloged_unverified_offer | not_yet_attempted | Browser tab queued or pending after identity choice; verify free eligibility bef |
| `azure_ai_foundry` | catalog | cataloged_unverified_offer | not_yet_attempted | Browser tab queued or pending after identity choice; verify free eligibility bef |
| `hyperbolic` | catalog | cataloged_unverified_offer | not_yet_attempted | Browser tab queued or pending after identity choice; verify free eligibility bef |
| `sambanova` | catalog | cataloged_unverified_offer | not_yet_attempted | Browser tab queued or pending after identity choice; verify free eligibility bef |
| `novita` | catalog | cataloged_unverified_offer | not_yet_attempted | Browser tab queued or pending after identity choice; verify free eligibility bef |
| `requesty` | catalog | cataloged_unverified_offer | not_yet_attempted | Browser tab queued or pending after identity choice; verify free eligibility bef |
| `vercel_ai_gateway` | catalog | cataloged_unverified_offer | not_yet_attempted | Browser tab queued or pending after identity choice; verify free eligibility bef |
| `portkey_cloud` | catalog | cataloged_unverified_offer | not_yet_attempted | Browser tab queued or pending after identity choice; verify free eligibility bef |
| `cloudflare_ai_gateway` | catalog | cataloged_unverified_offer | not_yet_attempted | Browser tab queued or pending after identity choice; verify free eligibility bef |
| `huggingface_dedicated` | catalog | not_selected_dedicated_compute | blocked_no_spend | Do not attach payment method; leave disabled under no-spend |
| `ollama` | local | no_account_needed | inference_tested_local | No account required; keep OLLAMA_BASE_URL loopback |
| `vllm` | local | no_account_needed | endpoint_not_configured | Configure endpoint only if operator runs local server |
| `mlx_lm` | local | no_account_needed | endpoint_not_configured | Configure endpoint only if operator runs local server |
| `llama_cpp` | local | no_account_needed | endpoint_not_configured | Configure endpoint only if operator runs local server |
| `llamafile` | local | no_account_needed | endpoint_not_configured | Configure endpoint only if operator runs local server |

## Infra / forge

| Service | Outcome | Notes |
|---|---|---|
| `github` | account_ok_repo_verified | Remote origin already authenticated for push/PR; no new account |
| `local_ollama_runtime` | no_account_needed | V0.1 dogfood + P15 canary already inference-tested on gemma3:4b |

## Layers (keep separate)
cataloged ≠ configured ≠ authenticated ≠ zero-charge-eligible ≠ inference-tested ≠ task-qualified

## Open handoffs
1. **OpenRouter** — SwarmAI Chrome is on sign-in. One action: sign in (or create free account) with the SwarmAI identity. Do not paste password/API key into chat. Say “OpenRouter signed in” when the keys page is visible.

## Private local inventory
Credential refs and identity live under `~/Library/Application Support/SwarmAI/account-inventory/` (outside git).

## V0.2
**Not started.**

