# SwarmAI handoff — CURRENT

**Updated:** 2026-09-20T13:50:00Z  
**Packets complete (offline):** P01–P21  
**Live follow-up:** P15/P16 **partial** (loopback Ollama, spend=zero)  
**Label:** `offline-verified-release-candidate` + partial local live  
**Branch:** `cursor/p15-p16-live-zero-spend-11e2` (sync to `main` after review)  
**Remote:** https://github.com/pri8771/swarmai  
**PR:** https://github.com/pri8771/swarmai/pull/1 (**merged**)  
**Pre-release:** https://github.com/pri8771/swarmai/releases/tag/v0.1.0-rc.1  
**RC status doc:** `docs/RELEASE_CANDIDATE_STATUS.md`

## Live status (honest)

| Packet | Live | Reason |
|---|---|---|
| P15 | **partial pass** | Ollama `gemma3:4b` canaried; all cloud providers denied (no keys) |
| P16 | **partial** | live provisional cells on `rt_ollama_gemma3:4b`; `wilson_lower` null |
| P18 | skipped | optional; mock evidence retained; no cloud capacity |

**Spend:** zero. **Payment methods:** none added. **Cloud keys:** none found/invented.

## Exact commands (this pass)

```sh
cd /path/to/swarm-ai
export OLLAMA_BASE_URL=http://127.0.0.1:11434/v1
export SWARM_ALLOW_PAID=false

uv run swarm providers canary --route rt_ollama_default --policy bounded_probe \
  --mode live --billing-known-zero
uv run swarm eval plan --suite starter --mode live --max-cases 4 --purpose evaluation
uv run swarm eval run --plan <plan_id> --mode live --route 'rt_ollama_gemma3:4b'
```

## Evidence

- `var/onboarding/canaries/rt_ollama_gemma3_4b.json`
- `var/reports/qualification/run_897bfae7212644acb51c8e1666ae5074.json`

## Remaining user actions (cloud free tiers only)

1. Complete provider MFA/CAPTCHA/signup yourself for any zero-charge cloud route.
2. Put least-privilege keys in local `.env` only (never commit); keep `SWARM_ALLOW_PAID=false`.
3. Re-run live canary per route with `--billing-known-zero` only after confirming billing=0.

## Mock vs live

Offline kit remains verified. This pass adds **local live** Ollama canary + partial P16 only.
