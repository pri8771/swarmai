# G13 / EVAL-131 — preregistered qualification criterion (screening preserved)

**Status:** preregistered rule only — **qualification_claimed=false**  
**Recorded (UTC):** 2026-09-20T23:04:00Z  
**Prior screening:** ~60 provisional cells (S/M/L/XL × families × local models, n=5) preserved; no additional volume until this rule is in force.

## Non-goals

- Do not promote observed 1.0/0.8 rates from n=5 into qualified profiles.
- Do not drop weak/failed cells.
- Do not invent EVAL qualification or lead accept.

## Preregistered acceptance / uncertainty rule

A cell `(model, family, size)` is **qualified** only if **all** hold:

1. **Sample size:** `n ≥ 30` independent trials on the preregistered holdout set for that cell.
2. **Point estimate:** empirical success rate `p̂ ≥ 0.80` under the cell’s task-defined hidden acceptance checks (worker never sees grader answers).
3. **Uncertainty:** Wilson score 95% lower bound for `p̂` is `≥ 0.70`.
4. **Overhead accounting:** total wall time, token usage, and $ cost recorded per trial; cell mean overhead published; paid cost must be `0.00` for zero-spend cells.
5. **Integrity:** every trial retains raw output excerpt + review reasons; failed/weak trials kept.

Otherwise the cell remains **provisional / not qualified**.

## Overhead accounting fields (required per trial)

- `wall_ms`
- `prompt_tokens`, `completion_tokens`
- `cost_usd` (must be 0 for local/zero-spend lanes)
- `route_id`, `model`
- `accepted` (hidden acceptance + structural checks)
- `candidate_sha`

## Next allowed action

Only after this file is committed: resume additional trials toward n≥30 **per cell**, preserving all prior weak cells. No qualification claim until the rule above is satisfied and independently reviewed.
