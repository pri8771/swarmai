# Changelog

All notable changes to SwarmAI are documented here.

## [Unreleased] — V1.4→V3.0 implementation-complete + accept/launch track (2026-09-23)

### Added
- V1.5–V3.0 implementation packages: leases/workers, knowledge, V17 gateway, SiteEpoch recovery,
  extensions/install, CandidateManifest, V2.3 scheduler/reservations/packs/portability/ops/fleet,
  V3.0 objectives + learning governance
- Lead-accept packages and launch-track evidence under `docs/evidence/v20/`, `v30/`, `launch/`

### Fixed
- CLI mypy type conflicts that failed GitHub Actions offline CI

### Evidence (zero-spend)
- Ollama loopback live canary `cost_usd: 0.0`
- Local recovery drill; release harden/verify/demo-suite/first-run/freeze
- Offline pytest suites green; CI offline green on tip after mypy fix

### Notes
- **Not lead-accepted.** ART lead sign remains USER_ACTION.
- **Not a completed public launch claim.** Operator authorized the accept/launch track;
  merge/tag/publish still require remaining human clicks if tooling blocks the agent.
- `SWARM_ALLOW_PAID=false` remains in force.

## [1.0.0-rc.1] — 2026-09-20

### Added
- V1 public contract freeze (`swarm release freeze`)
- First-run guided setup (`swarm release first-run`)
- V1 validation matrix (`swarm release validate`)
- V0.9 install-check / harden / demo-suite
- V0.8 product experience (projects, history, console tabs, journey proof)
- V0.2–V0.7 routing, scale, memory, tools, self-dev, reliability

### Security
- Git-tracked secret scan; local `.env` allowed when gitignored
- Zero-spend default (`SWARM_ALLOW_PAID=false`)

### Notes
- **Not a public launch.** V1 RC awaits explicit launch approval.
- Draft PR only at V1.0 stop gate — no merge/tag/publish without authorization.

## Earlier

See `docs/v0.*/STATUS.md` for version dogfood evidence.
