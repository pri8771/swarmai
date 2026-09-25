# REFERENCE ONLY — Mac connector worker

> **Label:** Reference guide for macOS as an outbound worker/connector host.  
> **Not** the generic worker contract.  
> Primary path: [`docs/install/SERVER_WORKER_STARTUP.md`](../install/SERVER_WORKER_STARTUP.md).

## Intent

macOS may run an outbound connector that reaches a server API (`SWARM_SERVER_URL`). Bounded task workspaces and scoped worker identity apply — do not mount whole-home directories or share operator production credentials on the normal path.

## Portable vs Mac-specific

| Portable | Mac reference |
|---|---|
| `deploy/env/worker-connector.env.example` | Historical `deploy/env/mac-connector.env.example` |
| Generic worker client / enroll HTTP | `deploy/compose/mac-connector.yml` (`host.docker.internal`) |
| Doctor profile name `mac_connector` | Name is historical; means outbound connector |

## Local verify pattern (engineering)

```sh
cp deploy/env/worker-connector.env.example deploy/env/worker-connector.env
# SWARM_SERVER_URL=http://127.0.0.1:<server-host-port>
# Same loopback token as server — never commit

uv run swarm deploy doctor --profile mac_connector --require-start
```

Optional compose one-shot (Docker Desktop):

```sh
docker compose -f deploy/compose/mac-connector.yml up --abort-on-container-exit
```

Historical TH-03 scripted evidence: `scripts/th03_mac_connector.py` and `docs/evidence/two-host/TH-03/` — labelled evidence, not fresh-install.

## Private console token path (optional)

Operators may store a loopback seed token outside git, for example under an OS application-support directory. That path is **operator-local** and must not appear as a required install root in portable docs. See also `docs/operator/PRIVATE_CONSOLE.md`.

## Blockers

Mac-only native extraction fixtures belong in optional adapters / explicit demo modes (Lane P1/P2). Unsupported platforms must fail closed with clear errors — never succeed from mere message processing.
