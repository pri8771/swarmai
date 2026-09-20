# SwarmAI roadmap: V1 repair -> V2.0 -> V3.0

## Owner decision — 2026-09-20

The operator approved this roadmap direction through V3.0 and authorized immediate implementation through V1.4 inclusive. Read `V1_4_EXECUTION_CONTRACT.md` and `START_CURSOR_TO_V1_4.md` for the executable mandate. Older repair-only/per-increment implementation stops are superseded within that range. Evidence and independent review remain required. Main merge, release/publication, public deployment and additional spending are not authorized by this roadmap.

V1.5-V3 are future direction, not current work. Stop feature development at V1.4 and finish its live acceptance; do not rename incomplete V1 capabilities as future improvements. This document contains goals, not proof that those capabilities exist.

## Product boundary

SwarmAI is a self-hostable elastic problem-solving runtime. Multiple capable planners/reviewers, smaller task-qualified workers and ordinary code/tools can contribute to one mission using approved inference sources concurrently. Agents can propose specialists, split work, compare approaches and challenge evidence; software enforces permissions, budgets, dependencies and resource admission. Team size is dynamic, not permanently small or fixed. There is no mandatory CrewAI dependency.

The operator's copy targets no additional spend, free-cloud coordination when actually available, optional local workers/inference and tested local recovery. Other product deployments can explicitly authorize their own budgets. Business bots, Jobs, Shopify, apps, household assistants and Home Assistant remain separate projects/integrations. Reuse sound libraries rather than recreating queues, databases, model transports or browser engines.

## Universal evidence gate

Every checkpoint needs a pinned code/tree SHA, config/dependency versions, reviewed diff, reproducible commands, actual results, relevant security/CI/backend/frontend coverage, negative cases and resource accounting. Structural/package checks, deterministic unit tests, live local inference, live remote inference and deployment are separate categories. Unknown or missing evidence stays unknown/blocked. No seeded product activity, supplied-answer fallback, fabricated provider readiness or mock-success runtime.

Cursor implements on scoped branches; ChatGPT reviews evidence. Ready independent work can continue within the authorized tranche while a review is pending, but a checkpoint cannot be called accepted without review. Operator approval remains necessary for final main merge/release. The immediate V1.4 contract gives detailed gate criteria and starting validation budgets; it controls any narrower conflict in this roadmap.

## V1.0 — Repair and honest baseline

Fix the audit's incomplete/failing CI, demo-token exposure, cross-project report/history/idempotency defects, false readiness/success claims and operational fixture dependence. Remove known-answer substitutions and force-progress quota bypasses. Set up concise state/messages and platform-session records. Preserve historical evidence and useful code.

Exit: actual checks run on the candidate, security regressions close, unexecuted behavior cannot pass verification, installed runtime has real empty/configured state, and remaining original capability gaps are explicit. This is a repaired development baseline, not proof that the entire swarm already works.

## V1.1 — One generic real mission path

CLI/API/console share authoritative mission state and execution. Task-provided goals, inputs, permitted tools, graph, artifacts, cancellation and acceptance replace parser-specific assumptions. Integrate sound existing execution/persistence components rather than adding a second demo runtime.

Exit: three unfamiliar tasks across at least two families; submit/observe the same mission across interfaces; actual restart/reopen; wrong result rejected; unsupported task reported; review controls acceptance; no reference-answer path or silent primary-worktree overwrite.

## V1.2 — Concurrent inference pool

Every planner/worker/reviewer/evaluation/embedding/memory call uses the governed broker. Exact account/model identity; independently evidenced auth, eligibility, price, quota and health; atomic reservations across shared buckets; bounded retries, resets, cooldowns, unknown-usage reconciliation and planning/review reserves.

Exit: real overlapping calls to two independent remote providers in one mission and an actual local route/fallback; no double allocation; unavailable/uncertain routes wait or use only qualified alternatives; no paid fallback. Metadata access is not inference/task qualification. Simulated concurrency is separate and cannot close the live gate.

## V1.3 — Empirical task-family/size qualification

Build a measured matrix for at least three actual model configurations, four useful task families and S/M/L/XL complexity. Version input/grade/prompt/tool/model settings, keep calibration separate from held-out evidence, preregister quality/confidence rules and report all attempts/uncertainty. Standard task inputs are legitimate; responses and scores must actually be observed.

Exit: every required family/size has at least one qualified route; measured unsuitable/unsupported model cells need not qualify. Inadequate data remains provisional. Selection uses matching profiles; bounded repair/subdivision/escalation works. Compare smaller-worker pipelines with direct execution including planning, retries, recombination and review overhead. A handful of successes is screening, not broad statistical proof.

## V1.4 — Elastic swarm organization

Validated graph revisions for spawn/split/merge/reassign/cancel/review and competing approaches. Allow multiple strong planning/review models and smaller qualified workers. Preserve independent investigation, evidence exchange, duplicate suppression, bounded delegation, permissions and resource admission.

Exit: a real mission expands because useful work is discovered and contracts after convergence; agents do not simply animate a scripted graph. Two planning/review configurations contribute. Measure logical agents, active sessions, requests and worker processes separately. Exercise 10/50/100 logical assignments as scheduler load tests, separately measure available real-model concurrency, and compare elastic/single/fixed approaches fairly. These load points are not fixed product ceilings.

Final tranche acceptance adds a clean installation, all applicable tests, twelve preregistered positive missions, six negative scenarios, actual provider overlap/fallback, actual graph adaptation and a 24-hour protected live observation window. See the execution contract. Target: no known unresolved supported-V1.4 defects and no unexpected application errors, not an impossible guarantee of no future bugs. Report blocked prerequisites honestly. Submit final candidate for independent review and operator merge approval; STOP FEATURE WORK HERE.

## V1.5 — Durable distributed workers

Complete multi-host capabilities, worker registration, leases, heartbeats, timeouts, cancellation, fencing, atomic result acceptance and durable reservations using the chosen proven runtime/storage libraries. Nodes register/drain safely and have explicit code/browser trust boundaries.

Exit: two separate hosts perform eligible work; adding/removing a host changes capacity; kill a real worker and complete the same mission from persisted progress. Duplicate deliveries/stale leases cannot repeat accepted effects. Two missions share quotas safely. Seeded state transitions do not pass. Basic restart integrity is already required earlier; this version adds proven multi-host operation.

## V1.6 — Scoped reusable knowledge

Separate current work, source artifacts, hypotheses, accepted facts and reusable procedures. Permissions apply before retrieval; provenance, expiry, contradictions, correction/deletion, summaries and context budgets remain explicit. Reuse structured/text/vector tooling where measured benefit warrants it, not multiple conflicting memory authorities.

Exit: later missions reuse verified knowledge with measured context savings; cross-project retrieval/summaries/caches/exports/traces cannot leak; superseding/deleting a fact affects future retrieval. Large irrelevant history does not force full reload. Compact development handoffs exist now; this version extends product knowledge reuse.

## V1.7 — Reliable tools and browser sessions

Integrate selected native APIs, workspace tools, sandboxed execution and MCP/browser capabilities through one permission boundary. Bind consequential approvals to exact payload and destination. Finish profile mapping, session validation and safe return destinations; preserve platform/SSO rules.

Exit: three real supported tool integrations; expired-session test restores the correct Apply/dashboard destination after only essential operator authentication, without duplicate submission. Wrong identity/project, unsafe redirects, denied actions and restricted filesystem/network cases pass. Secret-safe evidence is mandatory. Login documentation is an immediate repair obligation, not deferred until V1.7.

## V1.8 — Cloud-first with local recovery

Repeatable deployment on an actually available approved host, protected access, monitoring, consistent backups/artifacts and optional local nodes. Recheck free-host entitlements/capacity; no silent billing. Distinguish provider fallback, worker recovery and whole-site takeover. Prevent split-brain and document recovery limits.

Exit: proposed 72-hour trial on the approved host with actual resource/cost observations. Cloud-eligible missions continue with the home worker off. Exercise outages, restore real control/database/artifact state locally and finish recoverable work. Record recovery time/data-loss window. Unavailable free capacity remains a constraint. V1.4 live acceptance does not authorize or prove this rollout.

## V1.9 — Independent beta and controlled self-development

Stabilize supported SDK/extension interfaces, installation/upgrades/backups, dependencies/licenses/security and complete UI behavior. Swarm develops a selected real improvement in an isolated workspace with independent testing/review and prepares a PR; it cannot approve its own security, credentials or deployment.

Exit: two clean external installations without personal identity/default credentials; held-out mission set against declared baselines; actual browser/API journeys; a non-demo repository PR candidate accepted by independent review. An available hourly runner has observed consecutive invocations with no overlap, not just configuration. Public launch requires separate authorization.

## V2.0 — Accepted elastic product

Integrate and independently review all preceding requirements. Freeze public interfaces/migrations, accurately publish support limits and close release-blocking defects. Proposed final reliability gate: seven observed days on the intended deployment, not an estimate of development duration.

Exit: coding, research/synthesis and tool/automation missions use the same product path with heterogeneous concurrent models, task-size-qualified routing, dynamic organization, distributed recovery, scoped memory, authorized tools, charge admission and repeatable installation. Actual model/host performance is separate from simulations. Operator authorizes stable release/tag/launch.

User experience: install, connect permitted resources, submit a problem and limits, observe the work adapt, review artifacts/evidence and handle only necessary approvals. Outages or missing capacity do not produce fake success. The system can report failure or an honest limit. Unlimited inference, perpetual free hosting and optimal answers to every problem are not promised.

## V3.0 — Persistent, learning multi-mission operations

Approved direction, to be refined from actual V2 use; not current implementation permission or a reason to defer V2 defects.

1. Persistent objectives: authorized schedules/events create bounded missions over time with stop conditions and human control.
2. Cross-project resource allocation: fair priorities across deadlines, shared quotas and local/cloud workers without pooling private data or evading provider rules.
3. Governed operational learning: versioned improvements to prompts, routing, decomposition and procedures; held-out evaluation, drift checks and rollback. Self-generated memory is not automatically accepted truth.
4. Controlled self-development: use Swarm to prepare useful code/adapter improvements and tested PRs through independent review. No self-granted permission or automatic production release.
5. Reusable capability ecosystem: versioned/signed packs and adapters with contracts, permissions, tests and compatibility; no unrestricted arbitrary-code marketplace.
6. Fleet/team operations: stronger identity, tenancy, policy, audit and portability for larger heterogeneous installations where justified.

Example: an authorized application-maintenance objective detects a failing test, opens a bounded mission, investigates with appropriate models, compares fixes, prepares evidence and a reviewed change, and learns a useful procedure without silently deploying or spending.

**V2.0 completes individual missions reliably. V3.0 pursues continuing objectives through many reliable missions and improves its procedures under review.**
