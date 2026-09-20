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
