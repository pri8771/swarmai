# Config and secret references

Secrets are **names** (env keys / file refs), never values in manifests, docs, or support bundles.

## Source of truth

| Layer | Location | Notes |
|---|---|---|
| Blank template | `.env.example` | Safe to commit; empty values |
| Portable overlay | `deploy/env/portable.env.example` | Placeholder public URL / ports |
| Worker overlay | `deploy/env/worker-connector.env.example` | `SWARM_SERVER_URL` required |
| Runtime file | `*.env` (gitignored) | Operator-local only |

Copy examples → local files; do not edit application code for install.

## Validated references (doctor)

`uv run swarm deploy doctor --profile <name>` checks:

| Check | Profiles | Failure meaning |
|---|---|---|
| `database_url_configured` | standalone, hybrid, recovery, server | Set `SWARM_DATABASE_URL` before host-side start/migrate tools |
| `server_url_configured` | mac_connector | Set `SWARM_SERVER_URL` before connector start |
| `secret_backend_known` | all | `SWARM_SECRET_BACKEND` empty or one of `environment`, `env_refs_only`, `env_or_file_refs`, `file` |
| `public_url_shape` | when set | `SWARM_API_BASE_URL` / `SWARM_PUBLIC_BASE_URL` / `SWARM_PUBLIC_HOSTNAME` must not look like a secret; URLs http(s); hostname DNS-shaped |
| `compose_artifact` | all | Matching `deploy/compose/*.yml` present |
| Security defaults | all | non-root intent, no public DB, paid-cloud off |

Doctor JSON fields:

- `ok` — security posture checks passed
- `ready_to_start` — all required config/secret **refs** for that profile are present
- `config_errors` — actionable messages (no secret values)

```sh
uv run swarm deploy doctor --profile standalone --require-start
# exit 1 if ready_to_start is false
```

## Secret backend

| Value | Meaning |
|---|---|
| `environment` (default) | Resolve provider/API secrets from process environment by name |
| `env_refs_only` | Profile label: env names only (no file backend) |
| `env_or_file_refs` | Profile allows env or file path refs (file loader productization may lag) |
| `file` | Reserved — point to operator-managed files; do not commit contents |

Provider adapters use `SecretRef` names from contracts. Presence ≠ authentication ≠ free eligibility.

## Never commit

- Filled `.env`, `deploy/env/*.env`, `tunnel.runtime.yml`, credential JSON
- Provider keys, membership tokens, loopback seed tokens
- Database passwords from production

## Useful config errors

| Symptom | Likely cause | Action |
|---|---|---|
| doctor `database_url_configured` false | Missing `SWARM_DATABASE_URL` | Export URL or use compose-injected URL + `--require-start` only on host tools that need it |
| doctor `server_url_configured` false | Missing `SWARM_SERVER_URL` | Set connector base URL |
| `/health/ready` `database: down` | DB unreachable | Check compose health / URL |
| enroll 401 | Missing/invalid bearer | Set `Authorization: Bearer …` from install seed |
| providers report missing keys | Expected on fresh install | Stay on mock until keys are provisioned |
