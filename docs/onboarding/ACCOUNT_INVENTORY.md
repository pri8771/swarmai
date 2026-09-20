# SwarmAI account inventory (sanitized)

**Generated:** 2026-09-20T17:15:00+00:00  
**Pass:** V0.1 provider onboarding wrap-up · branch `cursor/v0.1-provider-onboarding` · draft **PR #3**  
**Chrome:** Default / **Priyansh** (`priyansh.chordia@gmail.com`) — SwarmAI blank profile abandoned  
**Spend:** zero · `SWARM_ALLOW_PAID=false` · **V0.2:** not started · **PR #2 / #3:** not merged

## Wrap-up summary

| Metric | Result |
|---|---|
| Providers keyed + auth-verified | **14** (OpenRouter, Groq, Gemini, Cloudflare, HF, NVIDIA primandir, Mistral, Cohere, Anthropic, Together, Fireworks, DeepInfra, Replicate, Ollama) |
| Deferred | **OpenAI** — payment-gated |
| Inference live-blocked (no-spend) | Together (and other paid-only routes); Fireworks auth-only (no paid inference run) |
| NVIDIA workspace | **primandir** (operator-confirmed) |

## Live status

| Provider | Signed in | Key in `.env` | Auth/canary | Notes |
|---|---|---|---|---|
| OpenRouter | yes | yes | yes | free route canary OK |
| Groq | yes | yes | yes | free canary OK |
| Gemini | yes | yes | yes | models.list OK |
| Cloudflare | yes | yes | yes | Workers AI token + models.search OK |
| HF | yes | yes | yes | whoami-v2 OK |
| NVIDIA (primandir) | yes | yes | yes | models.list OK |
| Mistral | yes | yes | yes | models.list OK |
| Cohere | yes | yes | yes | models.list OK |
| OpenAI | yes | no | deferred | payment-gated; not pursued this pass |
| Anthropic | yes | yes | yes | models.list OK |
| Together | yes | yes | yes | auth OK; **inference live-blocked** under no-spend |
| Fireworks | yes | yes | yes | clipboard ingest; models.list auth OK; no paid inference |
| DeepInfra | yes | yes | yes | models.list OK |
| Replicate | yes | yes | yes | account auth OK |
| Ollama | yes (local) | yes | yes | local zero-cost |

## Browser operating rule

- Use **normal Priyansh / Default Chrome** only (no Playwright/Selenium/CDP for Google SSO).
- Agent Create/Copy into gitignored `.env` via AppleScript JS when enabled; escalate only for MFA/CAPTCHA/password/consent.
- Never paste secrets into chat; prefer drop-file ingest; clear clipboard after ingest.
- Abandoned: SwarmAI isolated blank Chrome profile.

## Deferred / blocked

- **OpenAI:** DEFERRED — payment-gated (Add credits / Create secret key disabled).
- **Together inference:** key + auth OK; paid inference live-blocked under `SWARM_ALLOW_PAID=false`.
- **Fireworks inference:** key + auth OK; no paid inference run this pass.

## Operator action

none — onboarding pass wrap-up complete
