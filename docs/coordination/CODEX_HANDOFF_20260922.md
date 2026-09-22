# Codex checkpoint for Claude — 2026-09-22

Engineering is ready for the next native verdict. No independent recommendation is formal acceptance.

## Submitted exact candidates

| Candidate | Source / tree | Settled checks |
|---|---|---|
| PR30 composition | 4d16fe85188861df6e123b4454c6bdc416e6c639 / 05d97987e006853da51a4b7df12b7e80506bc7c0 | Offline 444 passed / 211 skipped; owned PG 642 passed / 13 live skips; focused PG 70 passed; mypy 174 files, Ruff/format/diff clean; cleanup 0; exact hosted checks green. |
| PR31 R31a offline adapter | 3c79a880e7ad7ec2373290aa20f876a5b368d6e1 / bc690d6c86fc95db1df307745c101b2fd383f291 | Offline 494 passed / 213 skipped; owned PG 694 passed / 13 live skips; 50 adapter tests and 111 focused PG tests; mypy 175 files, Ruff/format/diff clean; cleanup 0; hosted 35777255861/35777260132 green. |

Both received independent exact-tree engineering recommendations. Formal PR30 then PR31 verdicts were requested in the native lead task and are not yet observed. Main and dirty checkout were untouched.

R31a uses in-process MockTransport only. It does not claim a live server, login, session, R31b recovery or full live R31a artifact. Cookie reflection and intermediate rotation defects were reproduced and repaired before final review. The exact evidence and contract are in CODEX_R31A_OFFLINE_RETURN_20260922.md and R31A_CONTRACT_DISPOSITION_20260922.md.

## Cleared versus still blocked

Canonical 93d4e6e accepted P0/lint, normalized bounded R02a/R17a records and released composition plus R31a offline work. Earlier billing-start failures are historical; current hosted offline checks execute. Gated live CI is not live proof. Windows is not mandatory for the platform-neutral G13 verifier, but actual sealed-bundle proof still needs disposition.

Still needed: exact candidate verdicts; fresh grants for exhausted/failed missions; two independently qualified remote providers with verified no-spend quota; a qualified second physical host; actual CP/live/recovery receipts and R33c per-action authority. Owner mentioned R730/Windows, so “none exists” must not be repeated. No route or host is qualified by that mention. Full 32-entry source catalogue and account-inventory question are in PROVIDER_INVENTORY_20260922.md; owner answer pending.

## Next bounded action

Refresh native Git and PR verdicts first. If accepted, request/obey one precise next release; do not infer R31b or live authorization from offline acceptance. Preserve attempt identity, terminal-request proof, exact origin and unknown-result safety. Do not rerun settled tests without source drift or a specific new finding.

No spend, inference, mailbox, public action, scheduler change, deployment or main merge is authorized. Keep this repository's runtime, receipts and grants separate. If blocked, record the exact decision/access dependency and move to another permitted project task. When none remain, return a compact HANDOFF_FOR_CODEX with SHAs, failures, checks and next step rather than repeated exploratory work.
