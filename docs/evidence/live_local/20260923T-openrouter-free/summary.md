# OpenRouter free-route live canary attempt

## Allowlisted route

- `rt_openrouter_qwen/qwen3.8-27b:free` → model `qwen/qwen3.8-27b:free`, backend `modelrun`
- Why: public OpenRouter metadata lists prompt+completion price `0` for this exact `:free` model on ModelRun (`modelrun`); transplanted from PR #33 prerequisite pin. Not derived from provider-level `paid=false`.

## Command

```bash
SWARM_ALLOW_PAID=false uv run swarm providers canary \
  --route rt_openrouter_qwen/qwen3.8-27b:free \
  --policy bounded_probe --mode live --billing-known-zero
```

## Result

- **denied** — `missing_OPENROUTER_API_KEY`
- `cost_usd`: 0.0 (no request sent)
- `secret_ref_names`: `OPENROUTER_API_KEY` (value never present in this environment)

## USER_ACTION

Set `OPENROUTER_API_KEY` in gitignored `.env` or Cloud Agent environment secrets (do not paste into chat), then re-run the command on `cursor/openrouter-free-live-de09`.
