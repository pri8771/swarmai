# SwarmAI real-world acceptance policy

Status: LEAD POLICY
Date: 2026-09-21
Owner: ChatGPT engineering lead
Operator direction: "nothing is working without a real life test"

## Rule

A deterministic test, integration test, simulator, local fixture, mock server, or in-process proof can establish implementation correctness. It cannot by itself justify the word **working** for a milestone.

A milestone may be described as working only after:
1. its deterministic/integration contract is green;
2. its live checkpoint runs through the operational product path;
3. at least one milestone-relevant interaction crosses a real non-test boundary:
   - an actual external service/account,
   - a physically distinct worker/host,
   - a real outage/restore of the candidate deployment,
   - a real fresh install environment,
   - or another lead-approved real environment appropriate to the artifact;
4. evidence is bound to the exact pushed source/config identity;
5. failures are preserved and independently reviewed.

A local HTTP fixture is useful **live-local** evidence, not real-world acceptance evidence.

## V1.7 reality checkpoint

After CP5 local-fixture semantics pass, execute `R33c`:
- use the existing authenticated GitHub identity on the development host when available;
- through SwarmAI's V1.7 action boundary, create one uniquely named test issue in the private `pri8771/swarmai` repository, observe it, add one test comment, and close it;
- every mutation must be approval/effect-key bound and receipt-backed;
- retry of the same effect key must not create duplicate external state;
- an unknown outcome is reconciled before any retry;
- no GitHub token value appears in SwarmAI input, logs, receipts, or committed evidence.

This is a reversible test artifact, not product activity.

If GitHub authentication is unavailable, record an exact external blocker. Do not substitute a local fixture and call it real-world evidence.

The operator has also authorized using an existing test identity or a dedicated email/account alias when a later checkpoint genuinely requires identity/session testing. Do not create an account merely to satisfy a checkbox; use the minimum real external identity needed by the active artifact.

## Later milestones

### V1.8
CP18 uses an actual candidate deployment process/data store and performs a real stop/outage -> restore -> authority-fence drill. A pure unit simulation is insufficient.

### V1.9
A fresh install must run in a genuinely fresh environment. Supported OS rows require evidence on that OS.

### V2.0
Reliability evidence runs on the frozen integrated candidate for the real elapsed protocol duration.

### V2.3
CP23 must include:
- at least two physically distinct worker hosts or independently hosted execution nodes;
- constrained real resource capacity;
- at least one non-fixture external provider/tool interaction through normal authority;
- real scheduler restart/drain/reassignment;
- no cross-project leakage.

If the second host or external route is unavailable, V2.3 may be implementation-complete but is not called working.

### V3.0
CP30 must include a real elapsed persistent objective whose scheduled/event trigger creates a normal mission and performs at least one reversible real external action through the V1.7 boundary. Restart/replay must not duplicate the external effect. Canary/rollback evidence must use actual elapsed time.

## Language

Allowed before real-world proof:
- implemented
- deterministic tests green
- integration-tested
- live-local checkpointed
- reviewable

Reserved until this policy is satisfied:
- working
- operationally proven
- real-world verified

Formal artifact `accepted` remains governed by ARTIFACT_REGISTRY and may require additional gates beyond this policy.
