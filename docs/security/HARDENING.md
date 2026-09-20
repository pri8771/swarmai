# Security hardening

## Defaults

- `SWARM_ALLOW_PAID=false`
- API auth required for `/v1`
- Project isolation on missions
- Tool path allowlists; writes require approval
- Log/event payloads scrub secret-shaped keys

## Checks

```sh
uv run swarm release harden
uv run swarm release verify
```

`harden` scans **git-tracked** files for secret patterns and refuses tracked
`.env` / `secrets.json` / `credentials.json`.

## Never commit

- `.env` (gitignored)
- API keys, tokens, private keys
- Filled provider credentials

`.env.example` may list **variable names** only.

## Tool / path boundaries

- Allowlisted roots for repo tools (`sandbox/`, `var/`)
- Side-effecting tools require approval receipts
- Cancelled missions block new side effects

## Reporting

Evidence: `var/reports/security/latest_harden.json` (gitignored under `var/`).
