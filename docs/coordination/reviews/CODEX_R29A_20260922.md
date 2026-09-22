# R29a versioned integration manifests — engineering review

| Field | Value |
|---|---|
| Native release | `8ce9f5ef0069fde2ac4ad708f465612ddb3cb36d` |
| Clarification | `463ee661a6098abe95a42593215b1c52d0646321` |
| Accepted base | `ba458eb1a9a1af5f7e022159f36e6ce296d472cc` |
| Candidate | `1ea1ca55a2470d94fe704d64c029a991c3c0dea5` |
| Tree | `1b8577c91b2984b804ea6df259e6a47a697ccc31` |
| Pull request | [PR25](https://github.com/pri8771/swarmai/pull/25) |
| Scope | R29a only; R28d remains held |
| Recommendation | **RECOMMEND_ACCEPT — bounded engineering scope only** |

## Result

The candidate adds strict versioned manifests for `local.sandbox@1`, `mcp.echo@1`, and `browser.session@1`; the frozen 14-field vocabulary and operation-risk ceiling; recursive secret-like scanning of keys and values; canonical manifest digests; explicit manifest injection and foreign-class rejection; dynamic legacy compatibility; digest-bound new V1.7 receipts; and honest `historical-unbound` read compatibility without JSONB mutation.

The focused manifest and receipt proof passed on disposable PostgreSQL. A separate exact-source migrated permission-path proof produced one real local sandbox effect, one durable receipt with the canonical 64-hex manifest digest, and one consumed approval; migration, workflow, and cleanup all passed. The settled full suite passed 612 tests, the compatibility selection passed 35, Ruff passed, mypy passed 173 source files, both disposable databases were removed, and the worktree was clean. Static review found no concrete released-scope production defect.

The first full run failed because four test helpers still used the old constructor/private helper signatures. The final commit changes only those four test files; the exact diff and failed log are retained. The production implementation was not weakened to restore compatibility.

## Limits

This recommends engineering acceptance of R29a at the exact candidate only. It is not formal lead acceptance and does not release R28d. No provider/model/network/public action, CP1 attempt, spend, deployment, merge, extension trust/signing, install lifecycle, or V1.9 enablement occurred.

The local sandbox manifest binds its declared default filesystem scope. An injected test root remains runtime-instance configuration and is not separately represented by the manifest digest.

## Review identity and evidence

Codex is the implementation/integration owner and review-preparation agent, not the formal ChatGPT acceptance authority. Separate bounded agents reviewed the production diff and test-helper diagnosis. Root independently repeated the baseline diagnostic, inspected the final diff, ran the exact full suite and migrated permission workflow, and verified the clean source identity.

Evidence is retained in [CODEX-R29A-20260922](../evidence/CODEX-R29A-20260922/), including exact commands, raw failed and green logs, causal notes, source identity, and file hashes. The initial baseline import failure produced an empty redirected stdout file; the cause and corrected explicit-source invocation are documented rather than presenting the empty file as diagnostic output. No missing log is represented as independently verified evidence.

Requested lead action: accept or reject this exact R29a engineering candidate and explicitly release the next bounded packet if accepted. Genuine CP gates remain open. Original worker source, dirty evidence, and heartbeat ownership remain unchanged.
