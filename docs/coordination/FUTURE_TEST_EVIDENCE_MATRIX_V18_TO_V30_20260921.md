# SwarmAI future test/evidence matrix — V1.8 through V3.0

Date: 2026-09-21
Status: PLANNING ONLY

Legend:
- U = unit/deterministic
- I = integration
- L = real/private live
- W = real wall-clock
- R = independent review

Mocks/simulators may satisfy U/I development tests but never substitute for required L/W evidence.

## V1.7 remainder (Fable planning pass; case IDs in `packets/R32a.md`)

Levels: **U** unit/in-memory · **I** `integration` (real Postgres, real threads/processes) · **L** `live_local` (real HTTP fixture process, real Postgres) · **CP** live checkpoint run on the pushed tip. A skipped test is *not run*, never a pass.

| Packet | Deterministic / negative tests | Live evidence | Exit rung |
|---|---|---|---|
| OPS-CI-01 | U: skip-ci suffix, workflow filters | run-count before/after, 20 observed minutes | ops |
| R27a | I: receipt durability, replay identity, cross-project, single head | — | implementation |
| R27b | I: 8-thread reserve/CAS single winner, binding mismatch ×3 (5 consecutive green runs) | — | implementation |
| R27c | I: second-process visibility, one-shot approval concurrency, no row on denial, fence reader | — | implementation |
| R27d | I: insert-only, monotonic revoke, legacy NULL rows, cross-project | — | implementation |
| R27e | I: real child-process kills (before/after side effect), no takeover of live executor, irreversible re-arm | — | implementation |
| R28a | U+I: unknown-by-default, exception→unknown, not-sent retry, timeout, durable store required | — | implementation |
| R28b | U+I: under-classification, undeclared op, missing fence, provider-sourced fences, policy version, actor/project | — | implementation |
| R28c | U+I: AST single-path guards, legacy delegation exactly-once across instances | — | implementation |
| R29a | U: strict manifest, secret guard, digest, vocabulary subset | — | implementation |
| R28d | U: path/command denials, AST no-direct-effects, receipts per effect | one real `$0` mission with receipts (not counted for V14) | wired |
| R30a | L: fixture semantics (idempotency, faults, session TTL, no dedupe on submit) | — | infra |
| R30b | L+I: response loss → one note, fail-before-commit → one retry, redirect denied, scope denial | — | implementation |
| R31a | L+I: expiry, submit-unknown, reconcile while signed out never posts, cookies never persisted | — | implementation |
| R31b | L+I: login issues zero submits, exactly one submission after recovery, unsafe `next`, restart survival | — | implementation |
| R32a | matrix: every N17 case mapped to a collected test at the required level | full-suite run, zero skips | implementation |
| R33a/R33b | harness guards | **CP5** three integrations through one gateway object + live negatives | live_checkpoint |
| R17a | harness self-checks (steps can fail) | **CP3** 9/9 incl. cancellation fence, 20× concurrent accept | live_checkpoint |
| R02a | U: temp-repo red→green cases incl. collection-error ≠ red | — | implementation |
| R02b | — | **CP1** `v14-real-008`, lead review required | live_checkpoint → review |
| R25a | I: indistinguishable not-found, no accepted_fact from missions, prompt isolation, AST guard | — | wired |
| R25b | — | **CP4** real missions A/B, existence-inference negative, strict token savings | live_checkpoint |
| R17b/R17c | I: expiry/cancel/duplicate through the mission path | CP3 rerun with a real mission task | wired |
| R34a/R34b | — | **CP6** one mission with all four receipt families; audit package | live_checkpoint |

## V1.8

| Scenario | U | I | L | W | R |
|---|---:|---:|---:|---:|---:|
| stale SiteEpoch cannot dispatch | yes | yes | desirable | no | yes |
| stale SiteEpoch result rejected | yes | yes | yes | no | yes |
| stale SiteEpoch effect rejected | yes | yes | yes | no | yes |
| backup integrity detects corruption | yes | yes | no | no | yes |
| restore reconciles leases | yes | yes | yes | no | yes |
| unknown external effects remain unknown/fenced | yes | yes | yes | no | yes |
| outage -> new epoch -> old site fenced | yes | yes | yes | elapsed drill | yes |
| measured RPO/RTO | no | yes | yes | yes | yes |

## V1.9

| Scenario | U | I | L | R |
|---|---:|---:|---:|---:|
| extension cannot exceed manifest scopes | yes | yes | no | yes |
| project grant cannot exceed manifest/global policy | yes | yes | no | yes |
| extension cannot bypass broker/ToolGateway | yes | yes | yes when adapter exists | yes |
| disabled/draining extension receives no new work | yes | yes | desirable | yes |
| clean install from documented prerequisites | no | yes | yes | yes |
| upgrade preserves state | yes | yes | yes | yes |
| rollback returns to usable prior state | yes | yes | yes | yes |
| support bundle redacts secrets | yes | yes | no | yes |
| selfdev prepares bounded PR candidate | yes | yes | yes | yes |
| selfdev cannot merge/release itself | yes | yes | yes | yes |

## V2.0

| Scenario | I | L | W | R |
|---|---:|---:|---:|---:|
| clean candidate install | yes | yes | no | yes |
| upgrade/migration | yes | yes | no | yes |
| rollback | yes | yes | no | yes |
| supported capability journeys | yes | yes | no | yes |
| security negative matrix | yes | some live | no | yes |
| performance/resource baseline | yes | yes | benchmark duration | yes |
| reliability campaign | yes | yes | REQUIRED by frozen protocol | yes |
| evidence binds exact CandidateManifest | yes | yes | yes where applicable | yes |

Candidate invalidation:
Any source/config/schema/policy change covered by the freeze must either create a new candidate or be explicitly proven non-invalidating by the frozen protocol.

## V2.3 scheduler

Mandatory deterministic/pathological tests:
- one project cannot starve all others indefinitely;
- low-priority eligible work receives aging floor;
- many missions in one project do not multiply fair share;
- incompatible worker at queue head does not block later eligible work;
- denied provider/tool/privacy route is not silently replaced outside policy;
- partial resource reservation failure compensates/releases;
- crash during preparing intent reconciles before redispatch;
- unknown provider/effect outcome prevents unsafe fresh retry;
- duplicate scheduler process/site epoch cannot both authorize dispatch;
- cancellation/drain fences future dispatch;
- backpressure is bounded and explainable;
- deterministic tie-break is stable for same persisted input/policy.

Live/private evidence:
- multiple processes;
- heterogeneous worker capabilities;
- multiple projects;
- constrained provider/resource pools;
- real restart/recovery;
- no private content in decision receipts.

## V2.3 capability packs
- install;
- enable for project A;
- deny project B;
- verify declared permissions only;
- drain;
- disable;
- uninstall;
- failed/invalid signature/digest rejected;
- incompatible version rejected;
- enabling pack does not modify model qualification state.

## V2.3 portability
- export project;
- confirm no secret values;
- import into clean environment;
- reconcile versions;
- run a supported mission;
- deleted/superseded knowledge remains semantically correct;
- unauthorized project data absent.

## V2.3 observability/fleet
- read dashboard cannot mutate state;
- UI mutation goes through action approval;
- drained worker gets no new work;
- stale generation/epoch gets no work;
- locality/privacy placement respected;
- capacity exhaustion yields defer/backpressure, not scope relaxation.

## V3 objectives

Required:
- duplicate event -> one authoritative TriggerReceipt/proposal;
- real scheduled occurrence survives process restart;
- missed-run policy is deterministic;
- burst obeys rate/max-active;
- pause blocks new proposals immediately;
- revoke is irreversible for objective version;
- edit creates new immutable version;
- authority revoked after trigger but before mission admission fences proposal;
- cross-project event reference leaks no content/count/existence;
- many objectives do not multiply project fairness entitlement;
- stale objective version trigger rejected;
- actual wall-clock schedule evidence remains actual.

## V3 learning

Required governance scenarios:
1. candidate improves quality but violates frozen cost guardrail -> rejected;
2. held-out contamination -> contaminated, never promotable on that evidence;
3. two proposals use frozen selection rule and retain loser;
4. canary forced regression triggers deterministic rollback;
5. authority-expanding proposal blocked before held-out;
6. dependency drift expires accepted procedure;
7. selfdev proposal cannot merge itself;
8. stale workers/schedulers cannot continue rolled-back version;
9. all failed attempts retained;
10. thresholds/scorer/sample rule cannot change after held-out begins.

## V3 resource allocator
- fairness invariants retained;
- budget/provider quota retained;
- privacy/locality retained;
- no hidden starvation;
- no cost shifting outside recorded envelope;
- denied route remains denied;
- scheduler decision receipt explains allocation.

## V3 fleet tenancy/audit
- project A cannot inspect B queue/capability/data metadata beyond authorized aggregate;
- cross-tenant effect rejected;
- export audit contains refs/digests, no secrets;
- stale epoch/worker rejected;
- operator can reconstruct trigger -> proposal -> mission -> scheduler -> worker/provider/tool -> result/effect chain.

## Evidence file convention recommendation

For future live campaigns use:
`docs/evidence/<artifact-or-campaign-id>/<timestamp-or-run-id>/`

Include:
- manifest.json
- environment.json (redacted)
- candidate.json
- events/receipts
- test/check output refs
- final summary

Do not include:
- credentials;
- cookies;
- hidden held-out answers on worker-visible paths;
- private chain-of-thought.
