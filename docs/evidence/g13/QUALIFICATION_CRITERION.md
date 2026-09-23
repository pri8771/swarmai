# G13 / EVAL-131 — preregistered qualification criterion (aligned to LEAD-013)

**Status:** preregistered rule only — **qualification_claimed=false**  
**Recorded (UTC):** 2026-09-20T23:12:00Z  
**Authority:** `docs/coordination/EVAL_131_QUALIFICATION_PROTOCOL.md` (protocol v1.0) + LEAD-20260920-013  
**Prior screening:** ~60 provisional cells (S/M/L/XL × families × local models, n=5) preserved; see `docs/evidence/eval-131/w131a-qualification-gap-map.json`.

## Alignment note

This file previously drafted `n ≥ 30` and Wilson **95%** LB ≥ 0.70. That draft is **superseded**. The frozen lead protocol controls:

- required product families: `coding`, `planning`, `reasoning`, `extraction`
- sizes: S / M / L / XL
- ≥3 exact actual model configurations
- screening n=5/cell (provisional only)
- qualification: batches of 5; **min n=15**; max n=60; **one-sided 90% Wilson LB ≥ 0.80**

## Non-goals

- Do not promote observed 1.0/0.8 rates from n=5 into qualified profiles.
- Do not drop weak/failed cells.
- Do not invent EVAL qualification, n≥30 completion, or lead accept.
- Do not run W-131B qualification volume until this criterion + gap map are committed and a cell is selected.

## Preregistered acceptance / uncertainty rule

A cell `(exact_model_config, family, size)` is **qualified** only if **all** hold:

1. **Sample size:** `n ≥ 15` independent held-out observations (batches of 5; max 60/cell this tranche).
2. **Uncertainty:** one-sided **90%** Wilson lower confidence bound for success rate is `≥ 0.80`.
3. **Integrity:** zero forbidden/unauthorized tool actions; mandatory deterministic safety/format checks pass on every accepted trial; no grader/reference leakage to the worker.
4. **Binding:** evidence bound to exact candidate, dataset, grader, prompt, tool and model/config identities.
5. **Overhead:** planning/worker/review/retry/recombination wall time, attempts, tokens (where available), and charge/usage (or explicit unknown) recorded.
6. **Cost policy:** paid cost must be `0.00` for zero-spend cells; unknown cost remains unknown.

Otherwise the cell remains **provisional / not qualified**.

Reference early-stop thresholds (implementation must compute the bound):

| n | min successes for Wilson lower ≥ 0.80 |
|---:|---:|
| 15 | 14 |
| 20 | 19 |
| 25 | 23 |
| 30 | 27 |
| 60 | 52 |

A perfect 5/5 screening result is still not enough (Wilson LB < 0.80).

## Overhead accounting fields (required per trial)

- `wall_ms`
- `prompt_tokens`, `completion_tokens` (when available)
- `cost_usd` or explicit `unknown` (must be 0 for local/zero-spend lanes)
- `route_id`, `model`, exact config identity
- `accepted` (hidden acceptance + structural checks)
- `candidate_sha`
- planning / worker / review / retry attempt counts when applicable

## Next allowed action

1. Use `w131a-qualification-gap-map.json` to complete only missing required screening (e.g. third-model L/XL) at n=5 if still absent.
2. Select strongest candidate route(s) per required family × size.
3. Run **W-131B** held-out batches of five only on those candidates — not blanket expansion.
4. No qualification claim until the frozen rule is satisfied and independently reviewed.
