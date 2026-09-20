# SwarmAI — Release Candidate Status

**Date:** 2026-09-20  
**Branch:** `main` (+ live zero-spend follow-up branch)  
**Label:** `offline-verified-release-candidate` with **partial local live verification**  
**Not:** fully live-verified across cloud providers, cloud-operating, or production-launched

## Links

| Item | URL |
|---|---|
| Repo | https://github.com/pri8771/swarmai |
| PR (merged) | https://github.com/pri8771/swarmai/pull/1 |
| Pre-release | https://github.com/pri8771/swarmai/releases/tag/v0.1.0-rc.1 |
| Merge commit | `827cb82c9aebc5f83741b215d025fcedf8ab16bd` |

## Status

| Dimension | Result |
|---|---|
| Kit packets P01–P21 (offline) | complete |
| `swarm release verify` | pass (prior) |
| Live P15 canary | **partial pass** — loopback Ollama only (`gemma3:4b`) |
| Live P16 qualification | **partial** — provisional cells on Ollama route; `wilson_lower` remains null |
| Live P18 comparisons | **skipped** — optional; mock evidence retained |
| Spend policy | **zero** (`SWARM_ALLOW_PAID=false`; no payment methods; no cloud credits) |
| Cloud provider keys | **none found** (shell / known env files / `.env` empty for API keys) |
| Cloud production infra | **not** provisioned |

## Live setup (2026-09-20)

| Check | Result |
|---|---|
| `.env` present | **yes** (from `.env.example`; gitignored) |
| Cloud API keys populated | **no** |
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434/v1` (loopback) |
| `MLX_LM_BASE_URL` | unset — `:8080` serves Open WebUI HTML, not OpenAI API |
| `SWARM_ALLOW_PAID` | `false` |
| `SWARM_ALLOW_PROVIDER_NETWORK` | `false` |

### Provider matrix (honest)

| Provider | Cataloged | Configured | Authenticated | Inference-tested | Notes |
|---|---|---|---|---|---|
| ollama | yes | yes (`OLLAMA_BASE_URL`) | yes (live canary) | **pass** `rt_ollama_gemma3:4b` | local zero-cost |
| groq / openrouter / gemini / others | yes | no | no | **blocked** | no keys; live canary denied |
| mlx_lm | yes | no | no | **blocked** | endpoint not chat API |
| cerebras | yes | no | no | **blocked** | payment-gated; not pursued |

## Evidence paths (local `var/`, gitignored)

- P15 canary: `var/onboarding/canaries/rt_ollama_gemma3_4b.json`
- P15 alias: `var/onboarding/canaries/rt_ollama_default.json`
- P16 live run: `var/reports/qualification/run_897bfae7212644acb51c8e1666ae5074.json`
- Onboarding report: `var/onboarding/onboarding-report.json`

## Commands run (zero-spend)

```sh
cp .env.example .env   # already present; spend flags set false
# OLLAMA_BASE_URL=http://127.0.0.1:11434/v1 only — no invented cloud keys

uv run swarm providers inspect --provider ollama --metadata-only
uv run swarm providers onboarding-report
uv run swarm providers canary --route rt_ollama_default --policy bounded_probe \
  --mode live --billing-known-zero
uv run swarm providers canary --route 'rt_ollama_gemma3:4b' --policy bounded_probe \
  --mode live --billing-known-zero
uv run swarm eval plan --suite starter --mode live --max-cases 4 --purpose evaluation
uv run swarm eval run --plan <plan_id> --mode live --route 'rt_ollama_gemma3:4b'
```

## Pending / remaining blockers

- [ ] Cloud zero-charge-eligible API keys (operator MFA/CAPTCHA/signup) — **paused for user**
- [ ] Multi-provider live canaries beyond Ollama
- [ ] P16 statistical qualification rankings (`wilson_lower`) — intentionally null until larger live samples
- [ ] Optional P18 live soak under verified capacity
- [ ] No cloud production hosting from this pass

## Claim

**Partially live-verified RC** (local Ollama only). Still **not** fully live-verified across catalog providers.
