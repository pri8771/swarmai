# SwarmAI account inventory (sanitized)

**Generated:** 2026-09-20T15:37:12.837284+00:00
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
| OpenRouter keys | keys UI reachable | **Signed in** + key now configured locally |
| Groq | keys UI reachable | **Likely signed in** — next free key |
| Google AI Studio | keys UI reachable | **Likely signed in** — after Groq |
| Hugging Face | login redirect | Needs sign-in |
| NVIDIA NIM | settings/api-keys | Unverified / may need account |
| Mistral | login | Needs sign-in |
| Cohere | welcome | Needs signup/onboarding |
| Cloudflare | login | Needs sign-in |

Operator Create → Copy keys; agent ingests via clipboard helper (never paste secrets in chat).

## Honest outcomes (catalog providers)

| Provider | Priority | Outcome | API / inference | Next action |
|---|---|---|---|---|
| `openrouter` | core | authenticated_zero_spend_canary_ok | authenticated; canary `liquid/lfm-2.5-2.6b:free` cost=0 | Prefer `:free` only; paid routes disabled |
| `groq` | core | browser_keys_ui_reachable | key_not_configured | **NEXT:** Create free key → Copy → reply `key copied GROQ_API_KEY` |
| `gemini` | core | browser_keys_ui_reachable | key_not_configured | After Groq: Create free key → Copy → reply `key copied GEMINI_API_KEY` |
| `cloudflare_workers_ai` | core | browser_login_required | unknown | Sign-in then Workers AI token; zero-spend only |
| `huggingface_inference` | core | browser_login_required | unknown | Sign-in then free token |
| `nvidia_nim` | core | browser_unverified | unknown | Confirm free NIM access before any key use |
| `mistral` | core | browser_login_required | unknown | Sign-in; verify free tier before canary |
| `cohere` | core | browser_signup_incomplete | unknown | Complete welcome only if free; no paid |
| `cerebras` | catalog | payment_gated | blocked_no_spend | Do not attach payment method |
| `github_models` | catalog | unavailable_retired | n/a | Retired |
| `ollama` | local | no_account_needed | inference_tested_local | Re-canaried live `$0` |

Other catalog providers remain deferred until core free keys are done.

## Infra / forge

| Service | Outcome | Notes |
|---|---|---|
| `github` | account_ok_repo_verified | Draft PRs #2 / #3 — **do not merge** |
| `local_ollama_runtime` | inference_tested | `rt_ollama_gemma3:4b` canaried live, `billing_known_zero=true` |

## Verification this pass

- `SWARM_ALLOW_PAID=false`
- Ollama canary: **canaried** / `live_local_zero_cost`
- OpenRouter: key in gitignored `.env` (not committed); `GET /api/v1/key` 200; tiny canary on `liquid/lfm-2.5-2.6b:free` → **cost=0**, **usage_delta=0**
- Other cloud keys: not present yet
- Local ingest helpers (outside git):  
  `~/Library/Application Support/SwarmAI/secret-drop/ingest-openrouter-from-clipboard.sh`  
  `~/Library/Application Support/SwarmAI/secret-drop/ingest-env-from-clipboard.sh`

## Layers (keep separate)
cataloged ≠ configured ≠ authenticated ≠ zero-charge-eligible ≠ inference-tested ≠ task-qualified

## Open handoffs (operator)

1. **NEXT — Groq free key:** SwarmAI Chrome → https://console.groq.com/keys → Create free key → **Copy** → reply **`key copied GROQ_API_KEY`**. Do not paste the key in chat.
2. **Then Gemini:** same pattern → reply **`key copied GEMINI_API_KEY`**.
3. **Login-required:** HF, Mistral, Cloudflare, Cohere, NVIDIA — operator SSO in SwarmAI Chrome (free/eval only).
4. **OpenRouter:** DONE (auth + zero-spend canary).

## Private local inventory
Credential refs and evidence live under `~/Library/Application Support/SwarmAI/account-inventory/` (outside git).

## V0.2
**Not started.**
