# Platform access index (sanitized)

**Status:** operating inventory for FIX-004. No passwords, tokens, cookies, or private emails.
**Private records:** `~/Library/Application Support/SwarmAI/account-inventory/`
**Browser rule:** Priyansh / Default Chrome only. No Playwright/Selenium/CDP for Google SSO.
**Updated:** 2026-09-20 (worker session; historical onboarding + local private status cross-check)

## Fields

| Field | Meaning |
|---|---|
| platform_id | Stable service id |
| account_alias | Opaque alias only |
| login_method | Observed or `unknown` |
| browser_profile_ref | `chrome-default-priyansh` |
| credential_ref_names | Env/secret-store names only |
| browser_session_status | `unknown` / `verified` / `expired` / `needs_operator` / `wrong_account` |
| api_auth_status | Separate from browser |
| inference_status | Separate from API auth |
| last_verified_at | ISO UTC when checked |
| recovery_action | Precise next human step if blocked |

## Index

| platform_id | account_alias | login_method | credential_ref_names | browser_session_status | api_auth_status | inference_status | last_verified_at | recovery_action |
|---|---|---|---|---|---|---|---|---|
| openrouter | openrouter-primary | Google SSO | OPENROUTER_API_KEY | needs_operator (SSO again historically) | authenticated | free-route canary historically OK | 2026-09-20T17:04:46Z | Re-auth Google SSO in Default Chrome; resume OpenRouter keys/settings |
| groq | groq-primary | unknown | GROQ_API_KEY | unknown | authenticated | free-tier canary historically OK | 2026-09-20T17:04:46Z | Open console in Default Chrome; verify org |
| google-ai-studio | google-ai-primary | Google SSO | GEMINI_API_KEY | unknown | authenticated_ui | models.list historically OK | 2026-09-20T17:04:46Z | Confirm correct Google project in Default Chrome |
| cloudflare | cloudflare-primary | unknown | CLOUDFLARE_API_TOKEN, CLOUDFLARE_ACCOUNT_ID | unknown | authenticated_ui | Workers AI historically OK | 2026-09-20T17:04:46Z | Confirm account scope |
| huggingface | huggingface-primary | unknown | HF_TOKEN | unknown | authenticated_ui | whoami historically OK | 2026-09-20T17:04:46Z | Confirm token permissions vs inference credit |
| nvidia | nvidia-primary | unknown | NVIDIA_API_KEY | unknown | authenticated_ui | workspace `primandir` historically OK | 2026-09-20T17:04:46Z | Confirm workspace primandir |
| mistral | mistral-primary | unknown | MISTRAL_API_KEY | unknown | authenticated_ui | models.list historically OK | 2026-09-20T17:04:46Z | Confirm free API mode |
| cohere | cohere-primary | unknown | COHERE_API_KEY | unknown | authenticated_ui | models.list historically OK | 2026-09-20T17:04:46Z | Confirm eval vs production |
| anthropic | anthropic-primary | unknown | ANTHROPIC_API_KEY | unknown | authenticated_ui | models.list historically OK | 2026-09-20T17:04:46Z | Console identity ≠ consumer subscription |
| openai | openai-primary | unknown | OPENAI_API_KEY | unknown | deferred | payment-gated | 2026-09-20T17:04:46Z | Do not spend; leave deferred |
| together | together-primary | unknown | TOGETHER_API_KEY | unknown | authenticated | inference live-blocked no-spend | 2026-09-20T17:04:46Z | Auth only; no paid inference |
| fireworks | fireworks-primary | unknown | FIREWORKS_API_KEY | unknown | authenticated | no paid inference | 2026-09-20T17:04:46Z | Auth only; no paid inference |
| deepinfra | deepinfra-primary | unknown | DEEPINFRA_API_KEY | unknown | authenticated_ui | models.list historically OK | 2026-09-20T17:04:46Z | Confirm zero-charge eligibility before call |
| replicate | replicate-primary | unknown | REPLICATE_API_TOKEN | unknown | authenticated_ui | account auth historically OK | 2026-09-20T17:04:46Z | Zero-charge only |
| github | github-project-access | unknown | gh auth / SSH | unknown | repo write observed via pushes | n/a | 2026-09-20 | Confirm correct org/user before privileged ops |
| cursor | cursor-operator | IDE/CLI | CURSOR_API_KEY / agent login | IDE present | CLI agent **Not logged in** (re-verified) | unattended agent blocked | 2026-09-20T20:48:00Z | Open loginDeepControl URL from `cursor agent login`; then re-run `cursor agent status` |
| local-ollama | local-ollama | n/a | OLLAMA_BASE_URL | n/a | local endpoint | zero-cost canary historically OK | 2026-09-20T17:04:46Z | Ensure Ollama daemon running |

## Destination recovery procedure

1. Capture intended HTTPS destination + platform_id privately (`~/Library/Application Support/SwarmAI/platform-access/destinations.json`).
2. Open in Default Chrome / Priyansh profile.
3. If login redirect: hand off only password/passkey/MFA/CAPTCHA/consent.
4. Resume saved destination (domain allowlist); do not resubmit consequential actions.
5. Record check timestamp + status locally; update this index with sanitized status only.

Machine helper: `scripts/hourly/destination_recover.py` (sanitized paths only; no secrets).

## Explicit non-claims

- Fresh browser SSO verification was **not** completed in this FIX-004 pass for every provider.
- Cursor unattended `cursor agent` spawn is **blocked** until operator login/API key entitlement is confirmed (zero-spend).
- Apply-URL incident reproduction remains pending (URL unavailable to workers).

## Local database (FIX / V1.4 optional)

| field | value |
|---|---|
| engine | PostgreSQL 16 (Homebrew local) |
| host | 127.0.0.1:5432 |
| database | swarm |
| role | swarm |
| dsn_secret_ref | `~/Library/Application Support/SwarmAI/secret-drop/database-url.txt` (+ gitignored `.env` `SWARM_DATABASE_URL`) |
| migration | alembic head `9eb193b10f4e` |
| health_ready.database | `up` (API started with DSN) |
| integration_tests | `tests/integration/db` 8 passed |
| last_verified_at | 2026-09-20T20:37:48Z |
| spend | 0 (local only; no cloud DB) |

