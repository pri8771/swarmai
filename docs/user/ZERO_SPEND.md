# Zero-spend policy

SwarmAI defaults to **zero paid spend**.

## Rules

1. `SWARM_ALLOW_PAID=false` (see `.env.example`)
2. Local providers (Ollama) are preferred for live demos
3. Cloud free-tier **auth probes** may run; **paid generation** must be blocked
4. Cost ledger must report `$0.00` for dogfood proofs unless explicitly authorized

## Commands that must stay free by default

```sh
uv run swarm product journey
uv run swarm reliability proof
uv run swarm tools permission-proof
uv run swarm release demo-suite
uv run swarm demo parser-issue --mode mock
```

## If a command asks to spend

Refuse unless the operator sets `SWARM_ALLOW_PAID=true` **and** explicitly
authorizes the spend in the session. Record the authorization in the proof JSON.
