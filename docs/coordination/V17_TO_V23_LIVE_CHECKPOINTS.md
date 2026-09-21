# V1.7 -> V2.3 live checkpoint definitions

Status: FUTURE PLAN
Date: 2026-09-21

## CP18 Recovery
Real process/state checkpoint:
- create validated backup;
- stop/fail authority;
- restore;
- reconcile in-flight state;
- activate new authority;
- stale old authority cannot dispatch/result/effect;
- record RPO/RTO and duplicate-effect count.

## CP19 Productization
- clean install in fresh state;
- install/enable extension for project A;
- project B denied;
- drain/disable;
- upgrade;
- rollback;
- support bundle secret scan;
- real bounded selfdev PR candidate with no self-merge.

## CP20 Integrated candidate
Bound to one CandidateManifest:
- exact-tip checks;
- clean install;
- upgrade/rollback;
- security negatives;
- performance baseline;
- reliability campaign start/end;
- independent release review.

## CP23 Operational platform
- multiple projects and missions;
- constrained shared capacity;
- fairness observed under frozen workload;
- partial reservation/crash recovery;
- scheduler restart;
- single scheduler authority;
- capability pack project scoping;
- export/import;
- fleet placement/drain;
- explain receipts;
- zero cross-project content/effect leakage.

All live evidence records exact source/candidate/policy versions and preserves failures.
