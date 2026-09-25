# Worker enrollment and revocation

Workers enroll with the control plane, receive a membership token + generation, then heartbeat/claim/submit under that fence. Personal machine names are not authority.

## Enrollment (HTTP)

Authenticated:

```http
POST /v1/workers/enroll
Authorization: Bearer <install-or-project-token>
Idempotency-Key: <optional>
Content-Type: application/json
```

Body (shape): project id, capabilities, capacity, privacy classes, optional named inference URLs, optional platform/architecture. Response includes `worker_id`, `generation`, and a **one-time** `membership_token` — store it like a secret; it is not re-shown.

Qualification rules:

- Self-reported capabilities are **claims**; scheduling uses authorized grants.
- `capabilities_verified=true` only when an explicit project policy authorized the grants **and** the host platform/architecture is supported.
- Unsupported hosts may enroll for inventory but receive an empty scheduling grant set (unschedulable).
- Omitted platform/architecture defaults to the detected host; explicit unsupported values stay unqualified.

Related worker routes:

| Method | Path | Purpose |
|---|---|---|
| POST | `/v1/workers/enroll` | Enroll / re-enroll (generation bump) |
| POST | `/v1/workers/heartbeat` | Keep lease alive; receive cancel notices |
| POST | `/v1/workers/claim` | Claim assigned work |
| POST | `/v1/workers/renew` | Renew task lease |
| POST | `/v1/workers/submit-result` | Submit result under generation fence |
| POST | `/v1/workers/cancel-lease` | Cancel lease (stale submit rejected) |
| POST | `/v1/workers/reconnect` | Reconnect + reconcile active/cancelled leases |
| POST | `/v1/workers/drain` | Worker self-drain (token) or operator drain |
| POST | `/v1/workers/revoke` | Operator revoke by worker_id (generation fence) |
| POST | `/v1/workers/rotate-token` | Rotate membership token + bump generation |
| GET | `/v1/workers` | Inspect workers (`project_id` required unless admin) |
| POST | `/v1/workers/enqueue` | Enqueue task for eligible workers |

Offline self-test (mock only):

```sh
uv run swarm worker self-test --mode mock
```

## Drain (graceful)

- Worker self-drain: `POST /v1/workers/drain` with `worker_id`, `generation`, and membership `token`.
- Operator drain: same route with `worker_id` only (project-scoped principal).
- CLI (local durable store): `uv run swarm worker drain --worker-id <id>`

In-flight claims may finish; no new claims while draining. Prefer drain before host shutdown.

## Revocation (operator)

`POST /v1/workers/revoke` (project-scoped principal):

1. Marks worker revoked / quarantined
2. Bumps generation
3. Invalidates membership tokens
4. Cancels active leases so reconnect reports them cancelled
5. Causes stale-generation / revoked rejection on subsequent heartbeats/results

CLI (local durable store): `uv run swarm worker revoke --worker-id <id>`

Revoke by **worker_id** and generation fence — never by hostname.

## Rotate

`POST /v1/workers/rotate-token` with current membership token returns a new one-time token and bumped generation. Prior token is invalid immediately.

## After revoke / cancel

- Stale results with old generation or cancelled lease → rejected (`stale_generation` / `lease_cancelled`)
- Reconnect returns `active_leases`, `cancelled_leases`, and `cancel_notices`
- Re-enrollment under a new membership issues a new token and generation
- Do not copy membership tokens between hosts

## CLI

```sh
uv run swarm worker self-test --mode mock
uv run swarm worker inspect --project-id <project>
uv run swarm worker drain --worker-id <id>
uv run swarm worker revoke --worker-id <id>
```
