# Owner decisions and handoff lessons

This is a curated carry-forward of the relevant conversation plus current native project instructions. It is not a verbatim export of private history, a new architecture plan or live acceptance. Exact short owner quotations below are from the conversation; unknown dates/times are not invented.

## Preserve these owner instructions

- "nothing is working without a real life test"
- "1 session 1 heartbeat"
- "tasks must be broken up smaller and made easier. it should be artifact oriented"
- "organize the repo efficiently for claude. no point in giving it a 10000word prompt"
- "put the instructions in the repo itself, and then give me the prompt to start it off"
- "Lets focus on getting to 1.7 live and thats it."
- Current request: "Put all of these notes in the repo, and then give me a prompt that tells codex what to do" because Codex will manage "bots, jobs, and swarm, in one".

The specific native heartbeat semantics take precedence over interpreting the earlier shorthand identically everywhere: Swarm/Jobs periodic owned watchers, Bots SESSION_ONCE. The new portfolio request changes coordination convenience; it does not silently reopen scope or grant new external actions.

## Scope chronology to avoid stale instructions

Earlier SwarmAI directions progressed from V1.4 repair through a proposed V1.7 run and broad V3 source planning/implementation. Several chats alternated lead versus worker prompts and model choices. The latest instruction narrowed work to V1.7 live and stopped both implementation and planning beyond it. EXECUTION_CONTROL is the current scope source; old STATE fields, future queues, release labels and branch names are historical.

The same latest V1.7 stop is now independently recorded in Bots LEAD-048/V17_SCOPE and Jobs main AGENTS/FABLE_V17_LIVE. Bots' v23 integrator name and Jobs' PR #10 V2.3 program do not conflict once treated as history. Jobs' earlier STOP AT V1.5 is superseded only for scope, not technical safety tests.

Do not delete already-existing future code or planning just to simplify the handoff. Preserve it; keep unsafe future paths unreachable and don't spend this run finishing them. Do not create a fourth project or shared production orchestrator as a prerequisite for three working V1.7 products.

## Role corrections

ChatGPT led requirements, architecture, small artifact decomposition and independent review. Cursor and later Claude/Fable were implementation workers. Fable first received an architecture-only branch to harden the plan, then a delivery assignment. Planning-only prompts are no longer the active implementation assignment.

Codex is now requested as the combined project coordinator. It can inspect actual state and manage ready work, but does not automatically replace already-active worker ownership or become ChatGPT's acceptance authority. If Codex writes an artifact, its own second summary is not independent approval. Do not label a commit `lead: approved` or fabricate review receipts on behalf of another agent.

## Failure lessons that must survive context loss

1. A giant instruction to finish several versions led to loops rather than small deliveries. Keep exact inputs, behavior, surfaces, negative tests, live gate and exit condition per packet. Split cross-cutting work; do not avoid it by claiming a library is enough.
2. Source existing on another branch is not integrated source. Conversely, repeated tests of already-integrated source are not new implementation. Inspect before importing or rebuilding.
3. Real inference, a nonempty diff and unrelated passing tests can still yield a semantically wrong fix. Swarm's ledger example demonstrates this. Require relevant pre/post behavior and independent review.
4. A SQL-backed repository class can still have process-local receipts, non-atomic approvals or no runtime callers. Follow the actual product path end to end.
5. Fresh timer commits can mask an idle/stopped model; excessive heartbeat commits can waste CI. Track actual activity and publish without triggering unrelated application CI. A heartbeat never proves product correctness.
6. A local service/fixture is valuable engineering evidence, not proof of real source/account/public/recruiter behavior. Manual actions outside the application also do not prove application execution.
7. Permission to create/use a necessary owned test account is not spend, public social activity, employer application, Gmail ingestion or blanket OAuth authority. Preserve the exact grant and raw evidence privately.
8. A planning worker once self-authored/promoted lead approval. Preserve the corrective independent-review boundary, not the misleading earlier filename/commit prefix.
9. The structural packet validator originally treated some progress states too generously and missed certain execution gaps. Use the native execution guard AND source-bound prerequisites. A ready list is never a permission token.
10. A local transaction cannot retract an external request already sent. Be explicit about admission ordering, uncertain outcome reconciliation, idempotency and provider capabilities; do not promise universal exactly-once effects.
11. Hosted CI not starting is distinct from a failing test. No blind rerun storm, hidden skipped checks, paid-limit changes or claims of CI green from a local-only test.
12. All previous test totals are attributed to their original run/source. Do not repeat them as a new successful run in a handoff.

## Portable memory policy

Use this context and repo PROJECT_MEMORY/decision/review files when past chats are unavailable. Retrieve actual past conversation memory only if the environment exposes it. Do not claim that Codex/Claude has automatic access to ChatGPT's private history.

Keep project-relevant preferences and decisions here, not unrelated health, household, finance or family memories. Never store secret values, raw private candidate identity/resumes, browser cookies, mailbox bodies, hidden held-out answers, or an invented alias mechanism. Record safe references and uncertainty.

Model names/effort suggestions in old assistant text are not governance. Fable 5.1 is the owner's worker label; Codex is the requested coordinator. Use actually available models/settings under the account's permissions. Do not install a new provider or pay for a model just because an old handoff named it.
