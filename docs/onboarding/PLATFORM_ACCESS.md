# Platform logins, browser sessions and protected links

Operator request, 2026-09-20: document how to access each platform and avoid abandoning an Apply/dashboard link simply because the browser is logged out.

**Status:** this is the required operating procedure and inventory format. It does not establish a new login, browser-session fix or completed application. Existing ACCOUNT_INVENTORY entries are historical onboarding reports; recheck actual sessions when needed.

## Two records, not passwords in Git

The repository stores a sanitized per-platform access index. The private local account inventory/password manager stores the actual identity and credentials. Use the existing private location under `~/Library/Application Support/SwarmAI/account-inventory/` where appropriate; retain OS/password-manager protection and restrictive permissions. A gitignored file alone is not equivalent to a secure secret store.

Repository-safe fields for each platform:

| Field | Meaning |
|---|---|
| platform_id / purpose | Stable service identifier and why Swarm uses it |
| official_entry_url / login_url / dashboard_url | Canonical non-token URLs, verified against the actual service |
| account_alias / identity_ref | Opaque reference, e.g. `primary-personal`; no real email/password |
| login_method | Google SSO, GitHub SSO, passkey or email/password; `unknown` until confirmed |
| workspace_alias / project_alias | Required account context; actual sensitive IDs stay private |
| browser_profile_ref | The authorized user profile/session; not exported cookies |
| credential_ref_names | Secret-store/env reference names only; no values |
| browser_session_status | `unknown`, `verified`, `expired`, `needs_operator`, `wrong_account` |
| api_auth_status / inference_status | Separate from browser login and from each other |
| last_verified_at / evidence_ref | When/how each layer was checked, without sensitive artifacts |
| recovery_action / next_human_step | Precise sign-in/resume instruction, not a generic checklist |

Keep actual username/email, password-manager item location, private browser profile paths, recovery details and credential values in the protected local record. Never commit cookies, auth-state JSON, MFA seeds/codes, recovery codes, browser profiles, screenshots with secrets, signed magic/reset links or OAuth tokens. Platform session data is secret material even in a private repo. Playwright's official guidance also warns that authenticated state can impersonate the user and should not be committed: https://playwright.dev/docs/auth .

## Initial index to populate from the existing setup

These are historical platform references, not newly verified live accounts. Fill login methods and current session evidence in the authorized local browser; do not infer SSO from the fact that Chrome is signed into Google.

| Platform | Private record alias | Current check required |
|---|---|---|
| OpenRouter | `openrouter-primary` | Browser identity, free-route access and quota independently |
| Groq | `groq-primary` | Browser identity and organization-scoped API access |
| Google AI Studio / Gemini | `google-ai-primary` | SSO identity, correct project and API/free eligibility |
| Cloudflare | `cloudflare-primary` | Identity, correct account and scoped Workers AI token |
| Hugging Face | `huggingface-primary` | Identity and token permission versus inference credit |
| NVIDIA | `nvidia-primary` | Correct identity/workspace and endpoint eligibility |
| Mistral | `mistral-primary` | Identity, project and actual free API mode |
| Cohere | `cohere-primary` | Identity and evaluation versus production permissions |
| Anthropic | `anthropic-primary` | Console/API identity; consumer subscription is separate |
| OpenAI | `openai-primary` | Existing account; historical API payment gate is not fresh proof |
| Together | `together-primary` | Account auth versus no-spend inference restriction |
| Fireworks | `fireworks-primary` | Account auth versus no-spend inference restriction |
| DeepInfra | `deepinfra-primary` | Identity and exact-route billing eligibility |
| Replicate | `replicate-primary` | Identity and approved zero-charge usage only |
| GitHub | `github-project-access` | Correct repo/org identity and allowed operations |
| Cursor | `cursor-operator` | Browser/CLI auth and actual unattended execution entitlement |
| Local Ollama | `local-ollama` | Endpoint/service availability; no hosted account assumed |

Add other catalog/roadmap platforms only when selected. Do not create duplicate accounts. The index is not permission to set up unrelated jobs/social/commerce projects.

## Browser operating rule

Preserve the repo's current local rule: use normal **Priyansh / Default Chrome** for provider login/setup. The abandoned blank SwarmAI profile is not the active account profile. Do not use Playwright, Selenium or CDP automation for Google SSO under that rule. Use supported visible browser interactions and hand over the precise verification step when required. Never extract cookies from unrelated profiles, disable security or expose a debugging port publicly.

A link opened in a fresh automated/incognito/embedded browser may not share the user's ordinary session. Check the actual browser/profile before describing the site as inaccessible. A signed-in API token does not sign a human browser in, and a browser session does not prove API authentication.

## Protected Apply/dashboard link workflow

1. **Capture intent.** Record the intended destination, platform, relevant job/application/project identifier and task status. Store any sensitive URL privately; put only a safe canonical identifier/reference in Git. Do not persist magic-link/reset/OAuth secrets or guess away signed URL parameters.
2. **Use the right session.** Open the destination in the authorized browser profile. Inspect for a login redirect, wrong identity/workspace, access denial, expired link or a genuinely missing resource. Do not treat every failure as logout.
3. **Restore login with minimum handoff.** Navigate official login, select the documented account/SSO where verified, and perform supported setup. Ask the operator only for the actual password/passkey/MFA/CAPTCHA/consent step. Do not ask them to redo the entire platform setup or paste secrets into chat.
4. **Resume the original destination.** After login, return to the saved allowed destination. Use a platform-supported return URL or direct navigation, with a domain allowlist to avoid arbitrary redirect targets. Confirm the correct account and resource/form—not merely the dashboard homepage.
5. **Verify the outcome.** Mark `destination_opened` only after the intended page is present. Opening an application form does not authorize or prove submission. Reauthenticate/resume must not repeat any previous consequential click or submit a duplicate application.
6. **Handle non-session failures honestly.** For 403/wrong-project access, expired signed links, missing resources or IDE-local `vscode-file://`/`cursor://` links, provide the correct access/context or a normal HTTPS repository/file destination when one exists. Authentication alone cannot repair a machine-specific deep link.
7. **Record and stop loops.** Save a concise check timestamp, verified identity alias, final status and exact remaining action. Bound retries; do not repeatedly log in or cycle accounts. Keep raw network traces/screenshots private/redacted.

## Acceptance tests for Cursor

- Signed-out controlled session: operator completes only the necessary auth step, then the original page opens in the right account.
- Wrong profile/account: no sensitive content loaded or submitted to the wrong identity; switch only to the authorized profile.
- MFA/consent required: workflow pauses at the precise step and resumes without redoing completed setup.
- Expired/signed/IDE-local link: diagnose the actual link problem without inventing a replacement or exposing its token.
- Previously submitted action: reauthentication cannot cause a duplicate submission.
- Secrets scan: tracked documents, logs and summaries contain no real credentials, auth state or private identity mapping.

The lead cannot validate these browser tests from GitHub alone. Cursor must return observed evidence from the authorized local environment. User report: an Apply link failed while logged out; exact platform/session reproduction is still pending.
