# CP1 attempt 2 — honest failed-run preservation

**REWORK_FOUND / FAILED, not accepted and not a live checkpoint pass.** This packages already-existing failed execution; no rerun or new model call. Original worker checkout/branch and untracked attempt2 files remain untouched.

Run v14-real-008, attempt2, mission ec5bf495ed3d4318b97af2ea2840b5be ended failed/repair_required at2026-09-22T02:11:59.854522+00:00, accepted=false, changed_files=[], independent review=null. Retained raw cost record reports three requests and $0. The no-known-answer implementation path failed; no patch/review/product proof was delivered. No third attempt is authorized.

The apparent source-binding discrepancy is reconciled from Git: freeze candidate32ddb91164b236740eb6dfa561470de2ce67485d versus mission inspection head05fe7807db3509d68dd8a86a0616c9e8ffaa2307. The latter has exactly one additional commit adding only pre-run-freeze-attempt2.json; every implementation path is identical. Both SHAs remain recorded; the raw result is never rewritten. This resolves provenance of the failed run, not its failure.

The byte-identical raw stdout (SHA25645a5236057ab57c53c555542f17a4d945f06f4d21c5699c863dc0131eb7e47f2), empty stderr and original freeze are preserved in this native coordination evidence package. [Manifest](evidence/CODEX-CP1-ATTEMPT2-20260922/manifest.json), [Git/readback facts](evidence/CODEX-CP1-ATTEMPT2-20260922/provenance-readback.json), [raw outcome](evidence/CODEX-CP1-ATTEMPT2-20260922/mission-run.stdout.json). Secret-pattern scan returned zero candidate matches before preservation. Existing top-level worker attempt1 manifest is not overwritten.

Recommendation: lead acknowledge durable failed-attempt packaging and preserve CP1 failure/no-third-attempt boundary. The existing timer's repeated RUNNING text is stale; no worker ACK, crash or new execution is inferred. R02c repair PR19 remains a separate engineering review and cannot retroactively turn this attempt into a pass. No Fable handoff, provider/model invocation, scheduler change, source reset, main merge, spend or deployment occurred.
