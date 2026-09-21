# V2.0 clean install/operator journey acceptance protocol

Artifact: `ART-V20-INSTALL-JOURNEY`
Status: preregistered lead acceptance contract; no install evidence claimed
Owner: Cursor Session B executes evidence; ChatGPT lead independently reviews
Target: exact V2.0 implementation/artifact-complete candidate

## Purpose

Prove that a supported operator can install and start the exact V2.0 candidate from a genuinely clean environment without hidden workstation state, fixture/demo identities, mock-success paths, secret leakage, manual database surgery, or undocumented repository knowledge.

This protocol is evidence design only. It does not promote the artifact and does not start any reliability/live observation window.

## Candidate binding

Every counted install journey must bind, before execution, to:

- exact source commit and branch/ref;
- exact dependency lockfile digest;
- exact container/image or package identities used;
- exact database migration head(s);
- exact supported OS/runtime tuple from `ART-V20-SUPPORT-MATRIX`;
- exact install command path and configuration template version;
- route/model configuration identities used for the smoke mission;
- zero-spend declaration and observed cost/accounting evidence for any inference used.

If any candidate-bound identity changes after a counted run, that run remains historical evidence and does not silently transfer to the new candidate.

## Clean-environment rule

A counted journey starts from a fresh supported environment that does not already contain SwarmAI application state. The evidence must identify how cleanliness was established, for example a newly provisioned VM/container/host profile or an equivalent disposable environment.

The following may not be preseeded merely to make the journey pass:

- application database rows;
- projects, users, workers, missions or approvals;
- generated `.env` secrets copied from a previous deployment;
- local caches or worktrees containing required runtime state;
- mock/demo provider responses;
- known-answer task outputs;
- manually edited migration tables.

Normal operating-system/package-manager caches are allowed only when they do not contain SwarmAI application state and are disclosed in the evidence.

## Required journey

A counted clean-install run must demonstrate, in order:

1. **Prerequisite verification** — supported OS/runtime/container/database prerequisites are checked and unsupported versions fail clearly rather than proceeding ambiguously.
2. **Secret-safe bootstrap** — required local credentials/configuration are generated or supplied without repository commits or plaintext log exposure; generated secret-bearing files have restrictive platform-appropriate permissions.
3. **Dependency/install step** — documented install command succeeds from the exact candidate without ad-hoc source edits.
4. **Database initialization** — an empty database reaches the expected Alembic/schema heads using the documented path only.
5. **Service startup** — control plane and required supporting services start with explicit health/readiness truth. Missing mandatory dependencies fail closed.
6. **First project/operator setup** — create the minimum real operator/project state using supported product/API/CLI surfaces, not direct database insertion.
7. **Broker-governed smoke mission** — execute one unfamiliar, preregistered, non-known-answer mission through the governed broker path. For the zero-spend candidate this must use an already admitted `$0` route; no unknown-cost remote canary is allowed.
8. **Material result check** — the mission must produce a material, inspectable result rather than a synthetic success flag or empty diff.
9. **Restart/reopen** — stop the application process/services through the documented operator path, restart them, and reopen the same durable project/mission/result state.
10. **Evidence export** — emit the install-journey manifest described below without secrets.

A run that reaches startup but cannot complete the brokered smoke mission is installation evidence only, not an accepted end-to-end install journey.

## Negative/failure-path requirements

At least one reproducible negative check is required for each relevant supported environment:

- missing mandatory database/config secret fails closed;
- unsafe/default known credential is rejected;
- unsupported dependency/runtime version is rejected or clearly unsupported;
- failed migration prevents false readiness;
- unavailable inference route does not fall back around broker admission;
- no route/admission produces an explicit blocked/failure state rather than mock success;
- secret values do not appear in committed evidence, stdout/stderr excerpts, support bundle, or generated manifest;
- rerunning bootstrap against an already initialized database does not falsely imply safe credential rotation or destructive reinitialization.

Negative checks may use isolated test fixtures where appropriate, but isolated tests do not substitute for the counted clean-install journey.

## Evidence manifest

Each counted journey must create an immutable/versioned evidence directory containing at minimum:

- `manifest.json` with source/config/dependency/migration identities;
- environment/support-matrix tuple;
- commands actually executed and exit outcomes;
- timestamps for major steps (not fabricated durations);
- health/readiness observations;
- sanitized service/container inventory;
- migration before/after state;
- project/mission/result identifiers safe to disclose in repository evidence;
- broker route identity and admission/accounting receipt for the smoke mission;
- material-result assertion and restart/reopen assertion;
- negative-check outcomes;
- explicit `additional_spend_usd` or equivalent accounting result, which must be zero under the current owner boundary;
- failure/partial-run status when the journey does not complete.

Failed attempts are retained; a successful retry never overwrites them.

## Platform coverage

`ART-V20-SUPPORT-MATRIX` defines which environment tuples must be counted. This protocol does not invent support claims. A platform not present in the frozen support matrix is not required for acceptance and may not be advertised as supported from an incidental developer run.

Where Windows/macOS/Linux host behavior differs, evidence must identify whether SwarmAI runs natively, through Docker/containers, or through another explicitly supported execution path. Platform-specific installer behavior must be reviewed on the actual supported path.

## Review and acceptance

`ART-V20-INSTALL-JOURNEY` may move to `reviewable` only when Session B provides exact candidate-bound evidence for every required support-matrix tuple and all mandatory negative checks.

Independent lead review must confirm:

- evidence comes from the exact candidate claimed;
- environment cleanliness is credible and documented;
- no demo/mock/known-answer/admission bypass was used;
- database initialization and restart/reopen are real;
- smoke inference is broker-governed and zero-spend under the current boundary;
- failures are preserved and not rewritten;
- no secrets are present in repository evidence;
- all required support-matrix tuples are covered.

The artifact is not `accepted` merely because installation commands exit zero or CI is green. Acceptance requires the full clean operator journey above and consistency with the V2.0 integrated candidate, support matrix, security review, and release review.
