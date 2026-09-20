# Provider onboarding (P15)

Offline-safe inventory and canary scaffolding. Live probes are opt-in and spend-gated.

## Status layers (keep separate)

| Layer | Meaning |
|---|---|
| Cataloged | Present in `config/provider-catalog.json` |
| Implemented | Adapter exists in core provider set |
| Configured | Secret *reference* present in env (value never logged) |
| Authenticated | Live auth proven — **never** inferred from key presence |

Account / adapter / route statuses are independent.

## Commands

```sh
uv run pytest tests/onboarding
uv run swarm providers list --show-account-status
uv run swarm providers onboarding-report
uv run swarm providers inspect --provider groq --metadata-only
uv run swarm providers canary --route rt_fake_alpha --policy bounded_probe --mode mock
# Local zero-spend (loopback Ollama only):
uv run swarm providers canary --route rt_ollama_default --policy bounded_probe \
  --mode live --billing-known-zero
```

## Live blockers (operator)

1. Open each provider `entry_url`, complete login/MFA/CAPTCHA yourself.
2. Create a least-privilege API credential; store only as env var name (e.g. `GROQ_API_KEY`).
3. Confirm zero-charge eligibility for exact routes — do not attach a payment method via SwarmAI.
4. Re-run `onboarding-report` and only then consider `--mode live` canaries.
5. Under spend=zero without cloud keys, only loopback Ollama (`OLLAMA_BASE_URL=http://127.0.0.1:11434/v1`) is live-canary eligible with `--billing-known-zero`.

Cerebras remains `gated_payment_method` until the owner personally completes provider requirements.
GitHub Models stays retired.
