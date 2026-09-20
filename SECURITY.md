# Security Policy

## Reporting a vulnerability

Email the maintainer privately (see repository owner profile). Do **not** open a
public issue with exploit details or secrets.

Include:
- Affected version / commit
- Reproduction steps
- Impact assessment
- Whether secrets were exposed

## Supported versions

| Version | Supported |
|---|---|
| 1.0.0-rc.x | yes (pre-launch RC) |
| < 1.0 | best-effort |

## Hardening baseline

- `SWARM_ALLOW_PAID=false` by default
- `.env` gitignored; never commit keys
- `swarm release harden` scans git-tracked files
- Tool writes require approval receipts
- API auth + project isolation on `/v1`

See `docs/security/HARDENING.md`.
