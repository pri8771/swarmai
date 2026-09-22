# Swarm provider reuse — bounded offline prerequisite

Owner selected reuse of existing Groq, OpenRouter and Ollama on September 22. Codex is the engineering lead and releases this narrow source repair under the existing offline engineering scope. Provider selection does not renew model-call, mission or account-mutation grants.

Base: 4d16fe85188861df6e123b4454c6bdc416e6c639, composed candidate awaiting its separate formal verdict. Isolated branch: codex/swarm-provider-output-bound-20260922. Do not alter that parent candidate or assume it accepted.

Concrete defect: BaseCoreAdapter discards InferenceRequest.max_output_tokens when constructing HTTP requests. A requested bound therefore does not reach providers. Repair request validation and forward the bound using documented API fields; retain omission when absent. Scope: src/swarm/contracts/provider.py, src/swarm/providers/core/base.py, focused request-body/validation regressions and a source-bound return document.

Done means: reproduce the missing wire bound offline; reject nonpositive/noninteger limits; verify payloads at the transport boundary; focused/full checks; independent exact-tree recommendation; candidate commit/push and draft PR. No route enablement, remote canary bypass, credential changes, model calls or claims of live qualification. Do not generalize arbitrary request dictionaries into privileged provider options.

Separate remaining prerequisites: explicit OpenRouter free-route/fallback controls, reviewed remote admission runner, exact account/tier/quota readbacks, observed cost evidence and genuine broker-controlled overlap. The existing g12_local_admission_reconcile_proof.py substitutes a synthetic adapter and is not a fresh live proof command.
