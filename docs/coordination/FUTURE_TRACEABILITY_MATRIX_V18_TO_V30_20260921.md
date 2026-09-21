# SwarmAI future traceability matrix — V1.8 through V3.0

Date: 2026-09-21
Status: PLANNING ONLY

Purpose: connect artifact -> packet -> code surface -> acceptance cases -> evidence type.

| Artifact | Packets | Primary code surface | Acceptance case families | Evidence |
|---|---|---|---|---|
| ART-V18-SITE-EPOCH | V18-01 | db, controller scheduler, workers, tools, recovery | V18-AUTH-* | U/I + live stale-epoch proof |
| ART-V18-DEPLOYMENT-MANIFEST | V18-02 | deploy, recovery | V18-BACKUP-* | deterministic manifest/redaction |
| ART-V18-BACKUP-RESTORE | V18-02 | recovery, deploy, db | V18-BACKUP-*, V18-RESTORE-* | I/L |
| ART-V18-SPLIT-BRAIN-SAFETY | V18-01/03 | scheduler/workers/tools/recovery | V18-SPLIT-* | U/I/L |
| ART-V18-OUTAGE-DRILL | V18-03 | recovery test harness | V18-DRILL-* | L/W/R |
| ART-V19-EXTENSION-CONTRACT | V19-01 | extensions, tools registry/gateway | V19-EXT-* | U/I/L/R |
| ART-V19-INSTALL-UPGRADE | V19-02 | deploy, migrations, release/product | V19-INSTALL-*, V19-UPGRADE-*, V19-ROLLBACK-* | I/L/R |
| ART-V19-EXTERNAL-INSTALLS | V19-03 | install journey | V19-INSTALL-* | real fresh environment |
| ART-V19-SELFDEV-PR-EVIDENCE | V19-04 | selfdev, workspace, review | V19-SELFDEV-* | L/R |
| ART-V20-FOUNDATION-HARDENING | V20-01 | cross-cutting | existing hardening + candidate cases | U/I |
| ART-V20-INTEGRATED-CANDIDATE | V20-01 | integration/release | V20-CAND-* | U/I/R |
| ART-V20-SUPPORT-MATRIX | V20-02 | product/release docs | V20-SUPPORT-* | evidence linkage |
| ART-V20-INSTALL-JOURNEY | V20-02 | deploy/product | V20-INSTALL-* | L/R |
| ART-V20-UPGRADE-ROLLBACK | V20-02 | deploy/migrations | V20-UPGRADE-*, V20-ROLLBACK-* | L/R |
| ART-V20-SECURITY-REVIEW | V20-03 | cross-cutting | V20-SEC-* | U/I/L/R |
| ART-V20-PERFORMANCE-BASELINE | V20-03 | observability/benchmarks | V20-PERF-* | benchmark/L/R |
| ART-V20-RELIABILITY-PROTOCOL | V20-04 | observability/reliability | V20-REL-* | W/L/R |
| ART-V20-RELEASE-REVIEW | V20-04 | review/release | V20-REVIEW-* | R |
| ART-V23-MULTIMISSION-OPS | V23-01 | controller scheduler, db, workers, broker/tools | V23-SCHED-*, V23-RES-*, V23-BP-*, V23-CANCEL-*, V23-DRAIN-*, V23-EPOCH-*, V23-RECEIPT-* | U/I/L/R |
| ART-V23-CAPABILITY-PACKS | V23-02 | extensions/capabilities | V23-PACK-* | U/I/L/R |
| ART-V23-PORTABILITY | V23-03 | product portability, export schemas | V23-PORT-* | U/I/L |
| ART-V23-OBSERVABILITY | V23-04 | observability, API/console | V23-OBS-* | U/I/L |
| ART-V23-FLEET-POLICY | V23-05 | workers, scheduler placement | V23-FLEET-* | U/I/L/R |
| ART-V30-OBJECTIVE-CONTRACT | V30-01 | objectives, mission admission, scheduler | V30-OBJ-* | U/I/L/W/R |
| ART-V30-LEARNING-GOVERNANCE | V30-02 | learning, evals, review, observability | V30-LEARN-* | U/I/L/R |
| ART-V30-RESOURCE-ALLOCATOR | V30-03 | controller allocator/scheduler | V30-ALLOC-* | U/I/L/R |
| ART-V30-CONTROLLED-SELFDEV | V30-04 | learning + selfdev | V30-LEARN-011/012 + selfdev cases | I/L/R |
| ART-V30-CAPABILITY-ECOSYSTEM | V30-05 | capability packs/extensions | V30-CAP-* | U/I/L/R |
| ART-V30-FLEET-TENANCY-AUDIT | V30-06 | workers/fleet/observability/audit | V30-TENANT-*, V30-AUDIT-* | U/I/L/R |

## Worker traceability rule

Each future implementation PR/commit packet should state:
- artifact IDs;
- packet ID;
- acceptance case IDs implemented/tested;
- exact source paths changed;
- test commands/results;
- evidence paths;
- remaining live/time-bound/independent gates.

## Review traceability rule

Reviewer should never infer readiness from code volume.

Review artifact-by-artifact:
1. contract implemented;
2. mandatory negative cases exist;
3. deterministic checks run;
4. live/wall-clock evidence present when required;
5. exact candidate/source bound;
6. blockers honestly retained.
