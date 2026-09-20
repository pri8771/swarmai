# Provider onboarding

Browser-first, zero-spend, truthful verification. Catalog presence is **not** access proof.

## Status layers (keep separate)

| Layer | Meaning |
|---|---|
| Cataloged | Present in `config/provider-catalog.json` |
| Configured | Secret *reference* present locally (value never logged) |
| Authenticated | Live auth proven — **never** inferred from key presence |
| Zero-charge eligible | Exact route confirmed free under current terms |
| Inference-tested | Bounded synthetic canary succeeded |
| Task-qualified | Eval/mission evidence (separate from canary) |

Account / adapter / route statuses are independent. Dashboard login ≠ API access.

## Agent / operator rule (authorized setup)

**Standing rule (2026-09-20):** After initial OpenRouter/Groq setup, the agent uses SwarmAI Chrome to open provider consoles and create/copy API keys into gitignored `.env` itself. Do **not** ask the operator to copy/paste keys into chat. Escalate only for MFA, CAPTCHA, password, or consent the browser cannot complete.


For authorized account or integration setup:

1. Use a **local visible browser** with a dedicated SwarmAI profile (`~/Library/Application Support/SwarmAI/browser-profile`).
2. Navigate official provider URLs from the catalog; reuse existing accounts before creating new ones.
3. Escalate to the operator **only** for a precise identity/verification/consent/security step (password, passkey, MFA, CAPTCHA, phone/IDV, or secure secret transfer).
4. Do **not** return a generic “go sign up and send me the key” checklist without attempting the browser path first.
5. Never ask the operator to paste passwords, MFA codes, recovery codes, or API keys into chat.

Paid browser services (e.g. Browserless) are **not** used under the no-spend policy.

## Commands

```sh
uv run pytest tests/onboarding
uv run swarm providers list --show-account-status
uv run swarm providers onboarding-report
uv run swarm providers inspect --provider groq --metadata-only
uv run swarm providers canary --route rt_fake_alpha --policy bounded_probe --mode mock
# Local zero-spend (loopback Ollama only) after eligibility is known:
uv run swarm providers canary --route rt_ollama_default --policy bounded_probe \
  --mode live --billing-known-zero
```

## Spend / safety

- No payment methods, purchases, card-gated trials, auto top-ups, or paid model calls.
- Free signup is OK; payment-required API stays **disabled** and marked `payment_gated`.
- Prefer password manager / OS secret store; store only env **names** in gitignored `.env`.
- Cerebras remains `gated_payment_method` until the owner personally decides otherwise.
- GitHub Models stays retired.

## Inventory

Sanitized readiness report: [`ACCOUNT_INVENTORY.md`](ACCOUNT_INVENTORY.md).  
Private credential refs: outside the repo under `~/Library/Application Support/SwarmAI/account-inventory/`.
