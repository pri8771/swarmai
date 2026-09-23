# ART-V20-ACCEPTANCE — V2.0 integrated product candidate contract

Status: drafting
Target: V2.0
Owner: ChatGPT lead

## V2.0 candidate definition

A V2.0 implementation-complete candidate integrates:
- accepted/reviewable V1.4 elastic mission path;
- durable distributed worker implementation;
- scoped reusable knowledge;
- unified tool/approval boundary;
- recovery/backup primitives;
- stable extension/install path;
- controlled non-demo self-development candidate;
- operator console/API/CLI paths on one current tree.

## Required V2.0 artifacts

- ART-V20-INTEGRATED-CANDIDATE
- ART-V20-SUPPORT-MATRIX
- ART-V20-INSTALL-JOURNEY
- ART-V20-UPGRADE-ROLLBACK
- ART-V20-RELIABILITY-PROTOCOL
- ART-V20-SECURITY-REVIEW
- ART-V20-PERFORMANCE-BASELINE
- ART-V20-RELEASE-REVIEW

## Candidate vs accepted

Implementation-complete/reviewable can occur before wall-clock reliability windows finish.

Accepted V2.0 additionally requires:
- all required lower-version acceptance artifacts;
- final time-bound observation windows;
- no known unresolved supported-workflow defects;
- declared support limits;
- operator approval for release/merge.

Never use today's date target to bypass elapsed-time evidence.

## User journeys

At minimum:
1. clean install -> create project -> configure permitted routes -> submit mission -> observe -> review artifacts;
2. distributed worker joins/drains/restarts;
3. knowledge reused with provenance and project isolation;
4. consequential tool request requires exact approval;
5. provider/worker outage handled honestly;
6. backup -> restore -> reopen mission;
7. extension installed/disabled safely;
8. controlled self-development prepares isolated change but cannot self-release.

## Support matrix

Each capability is:
- supported;
- experimental;
- local-only;
- external-prerequisite-blocked;
- unsupported.

No feature is marked supported solely because code exists.

## Reliability protocol

Freeze candidate and config. Track:
- mission success by supported family;
- unexpected application exceptions;
- worker/provider outages;
- duplicate effects;
- resource/cost usage;
- restart/recovery;
- knowledge/tool permission violations;
- latency/overhead.

Observation windows remain real wall-clock evidence.
