# SwarmAI account inventory (sanitized)

**Generated:** 2026-09-20T15:36:00Z
**Spend policy:** zero — no cards, purchases, or paid endpoints (`SWARM_ALLOW_PAID=false`)
**V0.1 remote:** `cursor/v0.1-real-mission-runtime` @ `0a0c7e4` (push complete; **not merged**)
**Onboarding branch:** `cursor/v0.1-provider-onboarding`
**Browser:** system Google Chrome, dedicated SwarmAI profile  
`~/Library/Application Support/SwarmAI/browser-profile` (not Cursor in-app browser)

## Identity
Preferred SwarmAI account email/SSO: **still unset in private inventory** — not re-asked while OpenRouter session works. Provide once if a later provider needs a different identity.

## Browser session snapshot (SwarmAI Chrome profile)

| Tab | Observed title / URL state | Interpretation |
|---|---|---|
| OpenRouter keys | `API Keys \| Settings \| OpenRouter` → `/workspaces/default/keys` | **Signed in** (keys UI reachable) |
| OpenRouter sign-in | leftover `/sign-in?...` tab | Ignore; keys tab is authoritative |
| Groq | `API Keys - GroqCloud` → `/keys` | **Likely signed in** (keys UI reachable) |
| Google AI Studio | `API keys` with project query | **Likely signed in** |
| Hugging Face | redirected to `/login?next=/settings/tokens` | Needs sign-in |
| NVIDIA NIM | `Try NVIDIA NIM APIs` / settings/api-keys | Unverified / may need account |
| Mistral | `Login - Mistral AI` | Needs sign-in |
| Cohere | `About You` welcome redirect | Needs signup/onboarding |
| Cloudflare | `/login` | Needs sign-in |

Accessibility UI automation and AppleScript JS are **unavailable** in this environment (no button click / page DOM probe). Operator must Create → Copy keys; agent ingests via local clipboard helper (never paste secrets in chat).

## Honest outcomes (catalog providers)

| Provider | Priority | Outcome | API / inference | Next action |
|---|---|---|---|---|
| `openrouter` | core | signed_in_awaiting_free_key | account_signed_in_key_not_configured | **STOP:** Create free key on focused keys tab → Copy → reply `key copied` |
| `groq` | core | browser_keys_ui_reachable | key_not_configured | After OpenRouter: Create free key → Copy → reply `groq key copied` |
| `gemini` | core | browser_keys_ui_reachable | key_not_configured | After OpenRouter: Create free key → Copy → reply `gemini key copied` |
| `cloudflare_workers_ai` | core | browser_login_required | unknown | Sign-in then Workers AI token; zero-spend only |
| `huggingface_inference` | core | browser_login_required | unknown | Sign-in then free token |
| `nvidia_nim` | core | browser_unverified | unknown | Confirm free NIM access before any key use |
| `mistral` | core | browser_login_required | unknown | Sign-in; verify free tier before canary |
| `cohere` | core | browser_signup_incomplete | unknown | Complete welcome only if free; no paid |
| `cerebras` | catalog | payment_gated | blocked_no_spend | Do not attach payment method |
| `github_models` | catalog | unavailable_retired | n/a | Retired |
| `together` | catalog | cataloged_unverified_offer | not_yet_attempted | Defer until core free keys done |
| `fireworks` | catalog | cataloged_unverified_offer | not_yet_attempted | Defer |
| `deepinfra` | catalog | cataloged_unverified_offer | not_yet_attempted | Defer |
| `replicate` | catalog | cataloged_unverified_offer | not_yet_attempted | Defer |
| `perplexity` | catalog | cataloged_unverified_offer | not_yet_attempted | Defer |
| `openai` | catalog | cataloged_unverified_offer | not_yet_attempted | Defer (likely paid) |
| `anthropic` | catalog | cataloged_unverified_offer | not_yet_attempted | Defer (likely paid) |
| `aws_bedrock` | catalog | cataloged_unverified_offer | not_yet_attempted | Defer |
| `azure_ai_foundry` | catalog | cataloged_unverified_offer | not_yet_attempted | Defer |
| `hyperbolic` | catalog | cataloged_unverified_offer | not_yet_attempted | Defer |
| `sambanova` | catalog | cataloged_unverified_offer | not_yet_attempted | Defer |
| `novita` | catalog | cataloged_unverified_offer | not_yet_attempted | Defer |
| `requesty` | catalog | cataloged_unverified_offer | not_yet_attempted | Defer |
| `vercel_ai_gateway` | catalog | cataloged_unverified_offer | not_yet_attempted | Defer |
| `portkey_cloud` | catalog | cataloged_unverified_offer | not_yet_attempted | Defer |
| `cloudflare_ai_gateway` | catalog | cataloged_unverified_offer | not_yet_attempted | Defer |
| `huggingface_dedicated` | catalog | not_selected_dedicated_compute | blocked_no_spend | No paid compute |
| `ollama` | local | no_account_needed | inference_tested_local | Re-canaried live `$0` |
| `vllm` | local | no_account_needed | endpoint_not_configured | Optional local server |
| `mlx_lm` | local | no_account_needed | endpoint_not_configured | Optional local server |
| `llama_cpp` | local | no_account_needed | endpoint_not_configured | Optional local server |
| `llamafile` | local | no_account_needed | endpoint_not_configured | Optional local server |

## Infra / forge

| Service | Outcome | Notes |
|---|---|---|
| `github` | account_ok_repo_verified | Draft PRs #2 / #3 — **do not merge** |
| `local_ollama_runtime` | inference_tested | `rt_ollama_gemma3:4b` canaried live, `billing_known_zero=true` |

## Verification this pass

- `SWARM_ALLOW_PAID=false`
- Ollama canary: **canaried** / `live_local_zero_cost`
- Cloud keys in gitignored `.env`: **all empty** (presence ≠ auth)
- `uv run pytest tests/onboarding`: **10 passed**
- Local ingest helpers (outside git):  
  `~/Library/Application Support/SwarmAI/secret-drop/ingest-openrouter-from-clipboard.sh`  
  `~/Library/Application Support/SwarmAI/secret-drop/ingest-env-from-clipboard.sh`

## Layers (keep separate)
cataloged ≠ configured ≠ authenticated ≠ zero-charge-eligible ≠ inference-tested ≠ task-qualified

## Open handoffs (operator)

1. **STOP — OpenRouter free key (primary):** SwarmAI Chrome is focused on OpenRouter API Keys. Create a free API key → **Copy** → reply **`key copied`**. Do **not** paste the key in chat. Agent will ingest to gitignored `.env` and clear the clipboard, then run a zero-spend auth canary if a free route is confirmed.
2. **Next (optional, same profile):** Groq and Google AI Studio keys UIs already open — same Create → Copy → `groq key copied` / `gemini key copied`.
3. **Login-required:** HF, Mistral, Cloudflare, Cohere — need operator identity/SSO in the SwarmAI Chrome window (not chat secrets).
4. **Identity email/SSO:** still unset privately; only needed if you want a single documented identity for remaining logins.

## Private local inventory
Credential refs and identity live under `~/Library/Application Support/SwarmAI/account-inventory/` (outside git).

## V0.2
**Not started.**
