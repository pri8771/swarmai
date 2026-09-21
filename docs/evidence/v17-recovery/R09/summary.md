# R09 — account-specific remote admission

## Result

**Blocked / not admitted** — `0` remote routes admitted.

Keys may be present in operator env, but recovery protocol forbids admitting from key presence or stale canaries alone. No live remote inference was attempted this packet (avoid spend / invent-accept).

## USER_ACTION

Confirm zero-charge entitlement + fresh `$0` canary for ≥2 distinct remote providers with `SWARM_ALLOW_PAID=false`, then re-run admission.

No invent-accept of `ART-V12-REMOTE-OVERLAP`.

Evidence tip: `d6e033c5202d4404364ac5a766e20dbf24778c9a`.
