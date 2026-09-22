# Remote source attestation, 2026-09-22

The durable remote gate now derives its tree SHA from a clean Git worktree
root. It checks that same worktree again before reservation and immediately
before SENDING. A dirty checkout, missing Git metadata, subdirectory input,
or changed committed tree fails before provider execution. The grant hash now
includes the exact attempt ID as well as route, account, model, backend,
messages, output bound, tool names, and secret reference names.

Owned isolated-schema PostgreSQL: 13 passed, including dirty before reserve,
dirty before send, changed committed tree, and changed attempt denial. Full
offline: 485 passed, 4 skipped, 220 deselected. Ruff and mypy clean.

This does not issue a grant or prove that account, quota, route, or price
observations are genuine. Source attestation is checked at these software
boundaries; an independently reviewed launch must still bind the checkout
to its released artifact. No authenticated provider access or model request
occurred.
