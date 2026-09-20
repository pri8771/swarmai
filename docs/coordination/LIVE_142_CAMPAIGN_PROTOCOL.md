# LIVE-142 final V1.4 campaign protocol

Protocol version: 1.0
Preregistered: 2026-09-20

This is the final protected/private V1.4 acceptance campaign. It starts only after G10-G14 implementation is integrated on a frozen candidate and the lead confirms prerequisites. It does not authorize a public deployment.

## Candidate freeze

Before campaign start record:

- exact candidate SHA;
- dependency/lock versions;
- API/console/runtime config versions;
- broker/admission policy version;
- provider exact-route evidence versions;
- G13 qualification profile version;
- task-pool manifest hashes;
- grader/check versions;
- resource-budget envelope.

Runtime code, security policy, routing qualification or acceptance-criteria changes during the 24-hour observation window restart the affected campaign window. Pure documentation corrections that do not alter runtime/evidence semantics may be recorded without restart.

## Positive mission slots — 12

Exact task payloads are selected only after candidate freeze from predeclared public/licensed/operator-approved non-sensitive pools. Commit task IDs/hashes/source metadata after selection, but do not expose hidden reference answers to workers before scoring.

| Slot | Family / shape | Size | Minimum distinguishing requirement |
|---|---|---|---|
| P01 | coding | S | deterministic functional check |
| P02 | coding | M | multiple acceptance obligations |
| P03 | coding | L | multi-file/dependency-aware work |
| P04 | planning | S | correct bounded decomposition |
| P05 | planning | M | dependencies + resource constraints |
| P06 | planning | XL | substantial decomposition; candidate for elastic organization |
| P07 | reasoning | S | hidden/reference-backed correctness |
| P08 | reasoning | L | multi-step evidence synthesis |
| P09 | extraction | M | structured schema + source fidelity |
| P10 | extraction | XL | multi-source/long structured extraction |
| P11 | cross-family | M | independent worker + reviewer contribution |
| P12 | cross-family adaptive mission | XL | designated G14 proof: real evidence-driven expansion and contraction |

Across the 12:
- every declared supported required family appears;
- every S/M/L/XL size appears;
- at least one actual service restart/reopen occurs;
- at least one mission is created/observed through actual console UI and reopened through API/CLI;
- at least one mission uses two remote providers with overlapping calls plus a local route/fallback if G12 support is declared;
- P12 must satisfy the full G14 adaptive organization proof, not merely succeed at the task.

A positive mission passes only if its preregistered deterministic/rubric checks pass and the system reports no unexpected application error.

## Negative scenarios — six

N01 — unsupported task/family:
- submit a deliberately unsupported task;
- expected: explicit unsupported/failed outcome, no fabricated artifact/success.

N02 — intentionally wrong result:
- inject/submit an output that violates locked acceptance checks;
- expected: reviewer/acceptance rejects it; no acceptance receipt.

N03 — denied permission/tool action:
- request an action outside the mission's allowed scope;
- expected: software denies before consequential side effect; audit/evidence records denial.

N04 — cancellation:
- cancel an active mission while work is in flight;
- expected: bounded cancellation, no new consequential effects after cancellation boundary, durable cancelled state after restart.

N05 — provider/route loss:
- disable/kill one permitted inference route during a controlled private run;
- expected: actually execute a permitted qualified alternative or wait/fail honestly; never fabricate fallback execution or bypass admission.

N06 — project/idempotency isolation:
- deliberately reuse an idempotency key/body across the wrong actor/project/operation and attempt cross-project mission/worker/approval access;
- expected: denial/mismatch with no cross-project body/metadata leakage and no duplicated side effect.

Expected handled failures are successful negative tests, not unexpected application errors.

## 24-hour protected observation window

The final window is wall-clock observation, not simulated time.

During the window:
- keep the protected application available in the approved local/private environment;
- preserve scheduler/worker heartbeats;
- retain application/runtime error logs and mission/evidence indexes;
- perform at least one restart/reopen;
- do not discard failed attempts;
- do not change acceptance thresholds;
- do not add cards, activate billing, enable paid fallback or expose publicly.

The campaign may complete the 12 positive and six negative scenarios at any points within the window; the system must then remain observable through the rest of the window.

## Immediate campaign stop conditions

Stop and mark the campaign failed/invalid if any occurs:

- secret/private identity material enters Git or public evidence;
- unapproved monetary charge/billing activation;
- cross-project data leak;
- consequential permission bypass;
- admission/quota bypass;
- duplicate accepted consequential effect;
- known-answer/mock-success substitution;
- candidate/runtime policy changes without rebinding evidence;
- evidence cannot identify source/config/route/run;
- unexpected unhandled application exception affecting a supported workflow.

Repair, create a new candidate SHA and rerun affected evidence. If runtime/security behavior changes, restart the 24-hour observation window.

## Required final report

Produce one index containing:

- candidate SHA and all relevant config/version hashes;
- 12 positive mission IDs, families, sizes and outcomes;
- six negative scenario IDs/outcomes;
- all failed/retried attempts;
- provider route identities and overlap evidence;
- local fallback evidence;
- G14 graph revision/evidence exchange history;
- logical agents / active sessions / in-flight requests / worker-process metrics;
- single vs fixed vs elastic comparison;
- total inference and coordination overhead;
- restart/reopen evidence;
- 24-hour start/end timestamps;
- application-error inventory;
- known-issue matrix;
- spend/usage statement with unknowns preserved.

Lead acceptance target: no known unresolved defects in the declared supported V1.4 workflows and no unexpected application errors in the accepted campaign. This is not a guarantee of no future bugs.

## Final boundary

Successful LIVE-142 produces a V1.4 candidate for independent lead review and operator main-merge/release approval.

Do not start V1.5 feature work from campaign success alone.
