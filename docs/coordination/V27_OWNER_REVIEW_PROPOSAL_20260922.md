# SwarmAI V2.7 — OWNER-REVIEW PROPOSAL ONLY

Date: 2026-09-22
Status: **PROPOSED / NOT ACCEPTED / NOT IMPLEMENTATION AUTHORITY**

Owner direction sets V2.3 as the minimum desired milestone and V2.7 as the target. SwarmAI already has a cemented V1.7 -> V2.3 plan; no canonical V2.7 contract existed when this proposal was written.

## Position in the ladder

- V2.3 remains the existing operational-platform baseline and must be satisfied first.
- V2.7 should be a production-autonomy hardening milestone between V2.3 and V3.0.
- V2.7 must **not** introduce V3.0 controlled self-development/self-release authority.
- Existing PostgreSQL authority, scheduler, ToolGateway, broker, fences, extension contracts and project policy remain the control planes; V2.7 hardens/scales them rather than creating replacements.

## Proposed V2.7 definition

Call V2.7 **Distributed Production Beta**.

A V2.7 candidate should prove all of the following on one exact candidate manifest:

1. **Independent self-hosted CI**
   - GitHub Actions is non-authoritative.
   - At least one owned CI control plane/runner validates exact SHAs independently.
   - Linux is required; platform-specific Mac/Windows lanes are included where the support matrix claims them.

2. **Multi-node operational fleet**
   - at least three enrolled worker nodes across at least two physical hosts;
   - project-scoped capability/privacy labels;
   - worker loss/rejoin, stale result rejection and no duplicate consequential effect;
   - no second scheduler.

3. **Recovery + upgrade at fleet scope**
   - V2.3 backup/restore/site-authority guarantees retained;
   - rolling or bounded-drain upgrade/rollback of the supported fleet;
   - stale pre-upgrade worker/result/effect authority fails closed.

4. **Integration maturity**
   - the V2.3 accepted integration classes remain through the single ToolGateway boundary;
   - at least one API-style and one session/browser-style real integration proof plus local sandbox;
   - response loss, session expiry, redirect/destination confinement and reconciliation evidence retained.

5. **Operational SLO evidence**
   - candidate-bound soak/load campaign with frozen protocol;
   - scheduler fairness, queue latency, worker utilization, retry/reconciliation rates and effect ambiguity are measured;
   - thresholds must be frozen before counted evidence rather than invented after the run.

6. **Observability and incident reconstruction**
   - read-only operational dashboard/query surfaces can reconstruct mission -> dispatch -> worker -> inference -> effect -> receipt;
   - alerts for stuck leases, unknown effects, exhausted approvals, provider unavailability and recovery mode;
   - observability cannot mutate authority directly.

7. **Project isolation / policy**
   - cross-project negatives for workers, knowledge, extensions, integrations, approvals and receipts;
   - extension/capability grants remain project scoped;
   - no secret values in portability/support bundles.

8. **Portability**
   - export/import of authorized project configuration, manifests/digests and knowledge references;
   - restore onto a second owned host from documented bundle;
   - secret references must be rebound, never exported as secret values.

9. **Operator experience**
   - documented install/upgrade/recovery/worker-enrollment paths;
   - diagnostics/support bundle with secret scan;
   - explicit degraded states instead of silent fallback.

10. **Autonomy boundary**
    - Swarm may plan, schedule, route, recover and operate missions within existing grants;
    - no self-merge, self-release, autonomous public action, autonomous spend expansion or policy/grant creation;
    - V3.0 remains the milestone for any separately governed controlled self-development expansion.

## Proposed acceptance gate

V2.7 is accepted only when:
- V2.3 is accepted first;
- one exact CandidateManifest binds source/schema/dependencies/policies/integrations;
- deterministic + owned PostgreSQL + independent self-hosted CI are green;
- the frozen V2.7 operational campaign passes;
- required multi-host/recovery/integration evidence is genuine;
- an independent lead review accepts the candidate.

## Not authorized by this proposal

This document does not authorize V2.7 implementation, live tests, model/provider calls, scheduler runtime changes, spend, deployment, public actions or merge. Owner/lead approval must first freeze the V2.7 definition and packet DAG.
