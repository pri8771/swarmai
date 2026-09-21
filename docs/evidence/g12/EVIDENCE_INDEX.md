# G12 / INF-121 evidence index

**Tip binding:** `a17ae17e430831eb23d2fafc871244c096ca275d`  
**Lead accepted:** no · **Remote dual-provider:** live-blocked

| Artifact | Claim | Not claimed |
|----------|-------|-------------|
| `inf-121/concurrent-local-pool.json` | Overlapping local brokered routes; quota accounting; $0 | Two independent remote providers |
| `inf-121/kill-route-local-fallback.json` | Kill one local route → permitted fallback/wait | Remote failover |
| `inf-121/local-admission-reconcile.json` | Dual local routes admit+settle then honest deny on exhaust (`QuotaExhaustedError` via `InferenceResult.error`); $0 | Remote dual overlap |

**Script:** `scripts/g12_local_admission_reconcile_proof.py` (exit 0 locally).

**Post–LEAD-009 #5:** provider registry fail-closed; `_ollama_routable` requires healthy free-eligible probe. Remote overlap waits on verified zero-charge remote auth+capacity (no spend).

**LEAD-012:** [`DUAL_REMOTE_TEST_PLAN.md`](./DUAL_REMOTE_TEST_PLAN.md) prepared; remote dual **not** executed/claimed.

**W-121A:** [`../inf-121/w121a-remote-eligibility-ledger.json`](../inf-121/w121a-remote-eligibility-ledger.json) — metadata-only inspect + stale historical canary review; **0 admissible remote routes**; local Ollama leg ready; W-121B dual-remote overlap remains blocked. No spend / no invented eligibility.

## V12-REMOTE-ADMIT-01 (2026-09-21)

Packet status: **blocked_user_action_account_tier_canary** — **0 admissible remote routes** (no invented admission).

| Evidence | Path | Result |
|---|---|---|
| Credential presence (sibling `.env` consulted; secrets not printed) | `v12-remote-admit-01-credential-probe.json` | openrouter/groq/gemini keys present when sibling env loaded; runtime process alone was UNSET |
| Live capability-report (auth probes; no paid inference) | `v12-remote-admit-01-capability-report.json` | auth_ok for openrouter/groq/gemini; cost_policy `price_unverified`; only ollama `available`/`zero_spend_ok` |
| Metadata-only models/pricing + canary denies | `v12-remote-admit-01-admission.json` | OpenRouter lists exact `:free` zero API-price models; account Free-plan / Groq Free-tier / Gemini Free project **not** dashboard-verified; cloud canaries fail-closed; USER_ACTION recorded |
| Local Ollama canary (known-zero loopback) | `v12-remote-admit-01-ollama-canary.json` | `rt_ollama_gemma3:4b` canaried/settled; local only — not a remote admit |

USER_ACTION required before remote admit: operator confirms Free-plan/tier in OpenRouter, Groq, and Gemini dashboards and authorizes one bounded zero-charge canary per exact route. Public docs / API price metadata alone never admit.

## A5 — current-tip local G12 proof (2026-09-21)

Packet: **A5-LOCAL-G12-CURRENT-TIP** / live Ollama only — **not** remote dual claim.

| Evidence | Path | Result |
|---|---|---|
| Live inventory + brokered inference + kill/fallback + quota deny | `a5-current-tip-local-proof.json` | `ok=true`; models `gemma3:4b` + `qwen3.5:4b`; adapter **not** stubbed; kill → `route_unavailable`; fourth call → `QuotaExhaustedError`; spend `$0`; `live_dual_remote_claimed=false` |
| Script | `scripts/g12_current_tip_local_proof.py` | exit 0 |

Historical stubbed `scripts/g12_local_admission_reconcile_proof.py` remains regression prep only.
