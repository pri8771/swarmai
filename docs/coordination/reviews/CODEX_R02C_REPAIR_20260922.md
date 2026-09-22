# R02c bounded edit-path and prompt repair

State: READY_FOR_LEAD_REVIEW; authored candidate REVIEW_BLOCKED for independent verdict. Codex directly owns this isolated SP1 repair under the latest owner instruction; no Fable handoff.

- Native artifact ART-V14-REAL-E2E / hold-independent R02c. Existing contract, exact-match rule, mandatory regression proof and no-known-answer fallback remain. No CP1 attempt is released.
- Canonical contract read at `coordination/swarm-control@069bd1b`; expected worker base `05fe7807db3509d68dd8a86a0616c9e8ffaa2307`.
- Candidate `codex/swarm-r02c-format-20260922@1c9ff44ec787508fb874f5ac7fde849f89bdfe42`, separate from R27c candidate and original dirty worker checkout.
- Two-file write surface: `src/swarm/mission/worker.py`, `tests/mission/test_r02c_targeted_edits.py`.

The generic materializer ignored EDIT paths. A response naming another file could mutate the selected target whenever SEARCH happened to match. It now rejects all edits in such a response before writing, keeping the existing one-retry limit. Initial/retry instructions explicitly preserve leading spaces and forbid Markdown fences inside edit bodies. No fence-stripping, reindentation or fuzzy matching was introduced.

The actual failed attempt2 output digest remains `45a5236057ab57c53c555542f17a4d945f06f4d21c5699c863dc0131eb7e47f2`. Its captured SEARCH has literal Markdown fences and is uniformly dedented; even removing fences produces zero exact matches. The proposed setdefault-to-get quota change would lose persistent fallback quota state, so it must not be applied. This read-only diagnosis does not change the original failed result or use its output as a seeded answer.

Exact candidate checks: **60 mission tests passed**, Ruff/mypy169 pass. Three focused regressions cover wrong-file rejection, formatting retry guidance and unchanged rejection of dedented methods. Before source changes,2failed/1passed. All inference is synthetic; no provider call, actual mission or third live attempt occurred. [Commands/tree](evidence/CODEX-R02C-20260922/checks.json), [logs](evidence/CODEX-R02C-20260922/checks.txt), [hashed manifest](evidence/CODEX-R02C-20260922/manifest.json).

Requested action: ChatGPT independently reviews the exact candidate, records the verdict and supplies any concrete repair findings to Codex. The next live CP1 attempt requires its own fresh lead release/manifest, independent semantic review and current product-path proof. R27e/R28a remain under their independent holds.
