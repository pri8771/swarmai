# SwarmAI account inventory (sanitized)

**Generated:** 2026-09-20T15:49:41.153707+00:00
**Spend policy:** zero (`SWARM_ALLOW_PAID=false`)
**Standing rule:** Agent uses SwarmAI Chrome to create/copy keys into gitignored `.env`. Escalate only MFA/CAPTCHA/password/consent.
**V0.1:** `cursor/v0.1-real-mission-runtime` @ `0a0c7e4` (**not merged**)
**Onboarding branch:** `cursor/v0.1-provider-onboarding`
**Browser:** system Google Chrome + Playwright persistent profile  
`~/Library/Application Support/SwarmAI/browser-profile`

## Operator claim vs verified

Operator believed all accounts logged in. **Verified browser signed-in:** `groq` only.  
**API keys working:** `openrouter`, `groq`. Remaining core providers require login/SSO.

## Identity
Observed login hint: `priyansh.chordia@gmail.com` (Cloudflare → Google OAuth). Confirm if this is the preferred SwarmAI identity.

## Browser verification (Playwright, this pass)

| Provider | Browser status | Key in `.env` | Auth / canary |
|---|---|---|---|
| `openrouter` | Google SSO required again | yes | auth OK; free canary `liquid/lfm-2.5-2.6b:free` cost=0 |
| `groq` | **signed in** (keys UI) | yes (clipboard ingest) | models OK; canary `openai/gpt-oss-20b` OK (no payment error) |
| `gemini` | Google SSO required | no | blocked |
| `cloudflare_workers_ai` | Google SSO / password gate | no | blocked |
| `huggingface_inference` | login required | no | blocked |
| `nvidia_nim` | login required (not signed in) | no | blocked |
| `mistral` | login required | no | blocked |
| `cohere` | login required | no | blocked |
| `ollama` | n/a | n/a | local zero-spend canaried |
| `cerebras` | n/a | n/a | payment_gated — leave disabled |

## Open handoff (one precise step)

**Complete Google sign-in** (password/MFA) in the SwarmAI Chrome window for `priyansh.chordia@gmail.com`.  
When finished, reply **`google signed in`**. Agent will then create/copy remaining free keys itself — do not paste secrets in chat.

## Constraints
- No V0.2
- Do not merge PR #2
- Draft PR #3 updates OK
- Zero spend

## Private evidence
`~/Library/Application Support/SwarmAI/account-inventory/` (outside git)
