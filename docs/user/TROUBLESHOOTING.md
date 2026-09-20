# Troubleshooting

| Symptom | Likely cause | Action |
|---|---|---|
| `release verify` fails on docs | Missing V0.9 user/security docs | Ensure `docs/user/*` and `docs/security/HARDENING.md` exist |
| `secret_untracked:.env` TRACKED | `.env` committed | Remove from git; keep gitignored |
| Provider probe blocked | Zero-spend / network flags | Keep mock mode or use Ollama local |
| Empty model content (qwen) | OpenAI-compat `/v1` think mode | Runtime uses native Ollama chat with `think=false` |
| Console blank / error | Fixture load failure | Use “Recover with mock fixtures” |
| Permission write denied | Approval required | Run `swarm tools permission-proof` or resolve `/v1/approvals` |
| Mission cost > 0 unexpectedly | Paid path opened | Set `SWARM_ALLOW_PAID=false` and re-run |
| `uv sync` fails | Python version | Need 3.12 (and <3.14) |
| DB ready = down | No Postgres | Mock profile / API `db_reachable` dry-run is fine for local product proofs |

## Upgrade notes (0.8 → 0.9)

- New commands: `swarm release install-check`, `harden`, `demo-suite`
- Release verify now checks **git-tracked** secrets (local `.env` OK if ignored)
- User docs under `docs/user/` are required for RC verify
