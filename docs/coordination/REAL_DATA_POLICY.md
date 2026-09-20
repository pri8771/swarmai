# Real runtime data and acceptance policy

Effective 2026-09-20. Owner direction: "no more demo data, no more mock data. lets just finish this".

## Product behavior

The installed application, normal console, API, CLI, onboarding, routing and release-acceptance path must use actual configuration and actual observations. Remove seeded projects, fake provider accounts, synthetic activity, default demonstration tokens and canned-success responses from those paths. Do not merely hide or relabel them while continuing to use them underneath.

An empty installation shows a genuine empty/unconfigured state. An unavailable provider shows unavailable or unknown. A failed call remains failed. A blocked account remains blocked. A missing observation is not zero remaining capacity, unlimited capacity, authenticated access, or a successful run.

No fallback may substitute a known answer, prewritten patch, recorded successful response, or test fixture for failed inference and call it an agent result. Delete the normal-runtime dependency on `GOOD_FIX` and the hard-coded parser target. A legitimate deterministic tool must be declared as a deterministic step and evaluated for that purpose.

No production `demo` switch, seeded startup credential, auto-mock-on-error behavior, or browser control that falsely reports success. Report authenticated destinations and persisted actions, not just button clicks.

## Testing without fabricating product evidence

Do not replace valuable isolated unit/security regression tests with uncontrolled paid calls. Existing test doubles and fault injection may remain strictly under test-only boundaries to verify deterministic logic, permission denial and failure handling. They must never ship as normal runtime dependencies or satisfy a live-product gate. Do not add more showcase demos or mock-driven feature implementations.

Run real database, filesystem, process, browser and model integration checks where authorized. Use sanitized real issues/source material or independently specified unseen tasks. Keep expected answers and hidden tests inaccessible to the solving worker. A controlled task dataset is not user activity and must never populate the operational dashboard as such.

The first repair pass must inventory runtime imports and routes reaching fake adapters, fixture stores, seeded tokens, sample missions and success fallbacks. Remove or isolate those dependencies, then verify a clean installation starts without fabricated records. Do not delete failing tests merely to obtain a passing count.

## Evidence contract

Each acceptance item records source commit, command, environment/dependency versions, start/end timestamps, exit status, actual outcome, artifact reference, and evidence mode. Relevant inference evidence adds the real provider/model/route, account alias, request identifiers when available, usage, reservations and actual failure state. Never log secrets or raw sensitive inputs.

Allowed evidence distinctions: source inspection; isolated unit/regression test; real local integration; real local inference; real remote inference; real browser interaction; real deployment/recovery. Historical results remain historical and retain their original labels. Missing, failed, stale and blocked results cannot be converted to passes by editing a status file.

A release checker must run required tests or validate fresh attestations tied to the exact source/configuration. File existence is packaging evidence only. Show that deliberately broken behavior fails acceptance even when all documentation exists.

## Cost and safety

This policy does not authorize paid inference, paid CI, additional subscriptions, cloud provisioning, production exposure, destructive changes or credential disclosure. Use verified included/free routes and local resources within approved bounds. Unknown billing must fail closed. Remove safety bypasses added to make demonstrations finish. Keep the API loopback-only until authentication and project isolation fixes are reviewed.

## Completion

A task is implemented when its code exists, verified when its evidence is valid, and accepted when independently reviewed. A checkpoint is promoted only after the operator's approval. A version number, model call, merged PR, screenshot or passing file-presence check is not a substitute for the requested behavior.
