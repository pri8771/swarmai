# Health, readiness, and config errors

## Endpoints

| Path | Meaning |
|---|---|
| `GET /health/live` | Process up — always `{"status":"ok",...}` when the app responds |
| `GET /health/ready` | Safe to send traffic? Includes DB/runtime/mode flags |

```sh
curl -fsS http://127.0.0.1:8765/health/live
curl -fsS http://127.0.0.1:8765/health/ready
```

Replace host/port with your configured bind (`SWARM_HOST_PORT`, `SWARM_BIND_HOST`, `SWARM_PORT`).

## Ready payload fields

| Field | Notes |
|---|---|
| `status` | `ready` or `not_ready` |
| `database` | `up` / `down` / `unprobed` |
| `runtime` | `ok` if controller+workers wired |
| `execution_mode` | e.g. mock / standalone / operational |
| `fixture_mode` | Whether fixtures were seeded |
| `providers_network` | Network permission flag |
| `allow_paid` | Must stay false unless spend authorized |
| `configured_accounts` / `configured_routes` | Counts only — not proof of live auth |

Compose healthchecks currently probe **live** only; operators should still gate traffic on **ready**.

## Pre-start config errors (doctor)

Prefer doctor before curl:

```sh
uv run swarm deploy doctor --profile standalone --require-start
```

| `config_errors` example | Fix |
|---|---|
| `missing_env:SWARM_DATABASE_URL` | Export DB URL for host tools / non-compose start |
| `missing_env:SWARM_SERVER_URL` | Set connector base URL |
| `invalid_secret_backend:...` | Use a known backend name |
| `invalid_public_hostname:...` | DNS-shaped hostname; no spaces/secrets |
| `invalid_api_base_url:...` | Absolute `http(s)://` URL without credentials |
| `invalid_public_base_url:...` | Absolute `http(s)://` URL without credentials |

Doctor never prints secret values.

## Runtime vs install failures

| Class | Example | Not the same as |
|---|---|---|
| Product correctness | Wrong ready semantics | Missing R730 |
| Supported-platform qualification | Arch not in smoke list | Your LAN DNS |
| Particular deployment | Tunnel cert missing | Generic eng blocker |
| Config/install | Missing `SWARM_DATABASE_URL` | Live inference grant |

See portable product mandate §5 for reporting vocabulary.
