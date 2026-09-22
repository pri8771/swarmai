# R28d R730 execution-host preflight — BLOCKED

Date: 2026-09-22.
Purpose: verify whether the owner-authorized R730 can run the one released
`R28d live_local` mission without changing host state.

## Observed facts

- SSH to the R730 succeeded using its existing host authentication.
- `git` is installed.
- No `python3` or `uv` executable is installed on the host shell path.
- No existing SwarmAI checkout was found in the bounded shared-storage search.
- A read-only `git ls-remote` for `pri8771/swarmai` could not authenticate;
  no repository credential is configured for this host.
- The host-local Ollama service is running and exposes the existing
  `qwen3.5:4b` model. No inference request was made.

## Consequence

The source's zero-spend route accepts only a loopback Ollama endpoint. Running
the mission from the coordinator machine against the R730 LAN endpoint would
be denied by that source guard. A tunnel/proxy would defeat the intended
co-location boundary and was not attempted.

No mission was started, no model was invoked, no checkout was created, no
runtime was installed, and no credential was created or entered.

## Next permitted action

Await a separately authorized R730 execution environment with an existing
Python/uv runtime and authenticated isolated SwarmAI checkout, then repeat the
read-only loopback preflight before the single released mission. Continue
offline/reviewable V1.7 work in the meantime.
