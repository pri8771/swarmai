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

Body (shape): project id, capabilities, capacity, privacy classes, optional named inference URLs. Response includes `worker_id`, `generation`, and a **one-time** `membership_token` — store it like a secret; it is not re-shown.

Related worker routes:

| Method | Path | Purpose |
|---|---|---|
| POST | `/v1/workers/enroll` | Enroll / re-enroll (generation bump) |
| POST | `/v1/workers/heartbeat` | Keep lease alive |
| POST | `/v1/workers/claim` | Claim assigned work |
| POST | `/v1/workers/renew` | Renew task lease |
| POST | `/v1/workers/submit-result` | Submit result under generation fence |
| POST | `/v1/workers/cancel-lease` | Cancel lease |
| POST | `/v1/workers/reconnect` | Reconnect + reconcile |
| POST | `/v1/workers/enqueue` | Enqueue task for eligible workers |

Offline self-test (mock only):

```sh
uv run swarm worker self-test --mode mock
```

## Drain (graceful)

Workers may drain themselves via the worker client (`DrainRequest`) so in-flight claims finish then go offline. Prefer drain before host shutdown.

## Revocation (operator)

In-process control plane (`WorkerRegistry.revoke_generation`):

1. Marks worker revoked / quarantined
2. Bumps generation
3. Invalidates membership tokens
4. Causes stale-generation rejection on subsequent heartbeats/results

**Operator HTTP revoke/drain admin routes are not yet exposed** as first-class `/v1/admin/workers/...` endpoints. Until they are (Lane P2/product API work), revocation is:

- Process-local via registry/service APIs used by tests and harnesses, or
- Re-enroll denial + token invalidation after controlled restart with durable worker state cleared for that id

Documented requirement for portable ops: never rely on “forget the hostname” — revoke by **worker_id** and generation fence.

## After revoke

- Stale results with old generation → rejected (`stale_generation` / quarantine)
- Re-enrollment under same id (when permitted) issues a new token and generation
- Do not copy membership tokens between hosts

## CLI gap (honest)

There is no `swarm worker enroll|revoke|drain` operator CLI yet — use HTTP enroll + documented registry semantics. Track CLI as a follow-up; do not invent shell wrappers that embed personal tokens in scripts committed to git.
