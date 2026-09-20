# SwarmAI account inventory (sanitized)

**Generated:** 2026-09-20T16:11:00+00:00
**Chrome profile:** Default / **Priyansh** (`priyansh.chordia@gmail.com`) — SwarmAI blank profile abandoned
**Spend:** zero · `SWARM_ALLOW_PAID=false` · **V0.2:** not started · **PR #2:** not merged

## Live tab verification (Priyansh Chrome)

| Provider | Signed in | Key in `.env` | Evidence |
|---|---|---|---|
| `openrouter` | True | True | API Keys \| Settings \| OpenRouter |
| `groq` | True | True | API Keys - GroqCloud |
| `gemini` | True | False | API keys \| Google AI Studio |
| `cloudflare` | True | False; ACCOUNT_ID=yes | dash.cloudflare.com/\<account\>/home |
| `huggingface` | True | False | huggingface.co/settings/tokens |
| `nvidia` | True | False | workspace **primandir** (operator-confirmed); keys URL `build.nvidia.com/settings/api-keys` |
| `mistral` | True | False | Your API keys - AI Studio - Mistral AI |
| `cohere` | True | False | API Keys \| Cohere |
| `openai` | True | False | API keys - OpenAI API |
| `anthropic` | True | False | API keys \| Claude Platform |
| `together` | True | False | together.ai .../api-keys project URL |
| `fireworks` | partial | False | app.fireworks.ai (onboarding / account) |
| `deepinfra` | True | False | Dashboard - DeepInfra |
| `replicate` | True | False | Account settings api-tokens |

## NVIDIA
- **Workspace:** `primandir`
- **Signed in:** yes (operator-confirmed; do **not** redo Google SSO)
- **Keys URL:** https://build.nvidia.com/settings/api-keys
- **`.env`:** `NVIDIA_API_KEY` not yet present (agent self-copy blocked until Chrome JS Apple Events)

## Notes
- `CLOUDFLARE_ACCOUNT_ID` ingested from dashboard URL (not a secret token).
- OpenRouter + Groq keys already present from earlier clipboard ingest + canaries.
- Key Create/Copy in live tabs blocked: Chrome **Allow JavaScript from Apple Events** is OFF and Accessibility is denied.
- Normal Chrome only for Google-blocked logins (no Playwright/Selenium/CDP attach for Google SSO).

## Open handoff (one)
Enable Chrome **View → Developer → Allow JavaScript from Apple Events**, then reply **`js apple events on`**. Agent will Generate/Copy remaining free keys (including NVIDIA under **primandir**) into gitignored `.env` without closing tabs and without redoing NVIDIA Google SSO.

## MCP (Cursor `~/.cursor/mcp.json`)
**Added:** openrouter, huggingface, cloudflare-api, cloudflare-docs, groq-compound (launcher).  
**Preserved:** atlassian, clickup.  
**Unavailable official:** Mistral/Cohere/NVIDIA/Gemini AI Studio dedicated MCPs.  
**OAuth still needs operator approval** (OpenRouter may mint spend-capped MCP key — set $0 if prompted).
