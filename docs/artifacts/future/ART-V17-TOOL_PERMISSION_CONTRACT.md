# ART-V17-TOOL-CONTRACT — Unified tool and browser permission contract

Status: drafting
Target: V1.7
Owner: ChatGPT lead

## Goal

Expose APIs, MCP/apps, local commands, sandboxes and browser/session actions through one auditable permission boundary.

## Action envelope

Every consequential tool request should resolve to:
- mission/task/actor;
- tool/integration ID and version;
- operation;
- exact destination/resource;
- normalized payload hash;
- project/tenant scope;
- requested capabilities;
- risk class;
- side-effect class;
- approval requirement;
- idempotency key/scope;
- timeout/retry policy;
- evidence policy.

## Approval binding

Approval must bind to the exact:
- actor/project;
- tool + operation;
- destination;
- payload or constrained payload template;
- expiry;
- maximum repetitions/side effects.

A generic "browser approved" or "email approved" token must not authorize arbitrary future actions.

## Execution boundary

Sequence:
1. normalize request;
2. authorize project/resource;
3. evaluate policy/risk;
4. require exact approval if needed;
5. reserve side-effect/idempotency record;
6. execute tool;
7. capture result/evidence;
8. reconcile reservation;
9. expose only authorized artifacts.

Retries cannot duplicate accepted consequential effects.

## Browser/session model

Separate:
- browser profile/session identity;
- site/app authorization;
- destination URL;
- intended operation;
- current login/session health.

Session recovery:
- detect signed-out/expired state;
- preserve intended safe destination;
- request only essential human authentication;
- restore approved destination;
- do not submit merely because login succeeded.

## Integration trust

Each integration declares:
- data classes it may read/write;
- scopes;
- secrets needed;
- network/filesystem boundaries;
- whether user interaction can be consequential;
- sandbox/host requirements.

## V1.7 acceptance

At least three actual supported integrations using the same envelope:
- one read-heavy API/MCP integration;
- one local/sandbox tool;
- one browser/session-aware workflow.

Negative evidence:
- wrong project/identity;
- altered payload after approval;
- unsafe redirect;
- denied filesystem/network scope;
- expired approval;
- duplicate retry;
- signed-out session restored to correct destination without duplicate submission.


## Implementation status (CURSOR-V17-SINGLE)

- Branch: `cursor/v17-single-session`
- Packets: V2B-004a–e / Phase D1–D5
- Status: **reviewable candidate** — local implementation-complete; **no self-accept**; independent review required
- Evidence: `docs/evidence/v17/v2b004a-e-action-gateway.json`
- Frozen gates unchanged: ART-V14 drafting, G13 HOST-WIN-DEV blocked, B3 live multi-host UNKNOWN, spend \$0, SWARM_ALLOW_PAID=false
