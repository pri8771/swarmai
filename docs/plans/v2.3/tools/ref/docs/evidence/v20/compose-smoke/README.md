# V20-E10 compose full-path smoke

`scripts/v20_compose_smoke.sh` brings up `deploy/compose/product.yml` (api, console, worker, postgres) on loopback, probes it, restarts the api, probes again, and tears everything down, volumes included.

| Exit code | `status` in `latest.json` | Meaning |
|---|---|---|
| 0 | `pass` | every probe returned the expected HTTP status, before and after the api restart |
| 1 | `fail` | compose did not become healthy, or a probe returned an unexpected status (see `steps`) |
| 3 | `blocked_env_no_docker` / `blocked_existing_env` | the environment cannot run the smoke; nothing was started |

Probes, each run on first boot and again after the api restart:
- `/health/live` and `/health/ready`;
- an unauthenticated scheduler read gives 401;
- an authenticated `/v1/scheduler/queues` and `/v1/ops/events` give 200;
- registering a foreign project gives 403;
- the console `/healthz` and its same-origin `/health/live` proxy.

Secrets are handled like this:
- The token and database password are generated for each run with `secrets.token_hex`.
- They are written only to a `mktemp` directory outside the repository, which the compose file reaches through a temporary `deploy/env/product.env` symlink that is removed on exit.
- They are never printed or recorded.

There is no spend: `SWARM_ALLOW_PAID=false` and there is no provider network.

A `blocked_*` result is honest evidence that the smoke did **not** run. It does not satisfy V20-E10. Only a `pass` run by an operator with Docker does.
