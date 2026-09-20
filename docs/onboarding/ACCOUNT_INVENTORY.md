# SwarmAI account inventory (sanitized)

**Generated:** 2026-09-20T16:35:30.202014+00:00
**Chrome profile:** Default / **Priyansh** (`priyansh.chordia@gmail.com`)
**Spend:** zero · `SWARM_ALLOW_PAID=false` · **V0.2:** not started · **PR #2:** not merged

## Live status

| Provider | Signed in | Key in `.env` | Auth/canary | Notes |
|---|---|---|---|---|
| OpenRouter | yes | yes | yes | free route canary OK |
| Groq | yes | yes | yes | free canary OK |
| Gemini | yes | yes | yes | models.list OK |
| Cloudflare | yes | yes | yes | Workers AI models.search OK |
| HF | yes | yes | yes | whoami-v2 OK |
| NVIDIA (primandir) | yes | yes | yes | models.list OK |
| Mistral | yes | yes | yes | models.list OK |
| Cohere | yes | yes | yes | models.list OK |
| OpenAI | yes | no | blocked | Create disabled — Add credits |
| Anthropic | yes | yes | yes | models.list OK |
| Together | yes | no | blocked | $5 deposit required |
| Fireworks | yes | no | blocked | Create no-op at $0 credits |
| DeepInfra | yes | yes | yes | models.list OK |
| Replicate | yes | yes | no | key present; API 403 |
| Ollama | yes (local) | yes | yes | local zero-cost |

## NVIDIA
- **Workspace:** `primandir`
- **Signed in:** yes
- **`.env`:** NVIDIA_API_KEY present + auth canary OK

## Blocked (zero-spend)
- **Together:** deposit $5 to create key
- **OpenAI:** Create secret key disabled (credits/billing)
- **Fireworks:** Create API Key does not mint at Credits $0.00
- **Replicate:** token in `.env` but API returns 403 — may need regenerate/scopes

## Operator action
none — keep working
