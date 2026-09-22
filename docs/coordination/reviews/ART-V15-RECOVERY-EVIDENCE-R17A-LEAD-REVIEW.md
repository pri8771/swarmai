# ART-V15-RECOVERY-EVIDENCE — R17a lead review

Decision: **LOCAL HARNESS CHECKPOINT ACCEPTED; artifact lifecycle unchanged**
Reviewed source/evidence: `cursor/v17-single-session@e5bd6350569fb10146517430ca6f7fa097de84a4`
Evidence: `docs/evidence/v17-checkpoints/CP3/cp3-20260922T013226Z/`

## Accepted evidence

R17a is credible local recovery evidence on a real PostgreSQL database using separate spawned OS processes. The preserved receipt demonstrates:

- victim worker claim followed by real `SIGKILL`;
- lease expiry and reassignment to a survivor process;
- stale victim/zombie result rejection;
- exactly one accepted result for the task;
- cancellation-generation rejection for both result acceptance and lease renewal after the control-plane generation is advanced;
- 20/20 genuinely concurrent duplicate-result races resolving to exactly one accepted result.

The evidence is useful and should remain part of the eventual V1.5/CP3 evidence chain.

## What is NOT accepted

This does not satisfy the final CP3 or `ART-V15-RECOVERY-EVIDENCE` acceptance contract because the harness seeds/operates durable worker tasks directly rather than exercising the same operational product mission path. The harness also had to bump the durable mission `cancellation_generation` directly; `LeaseLifecycleService.cancel_active_lease` does not itself advance mission cancellation authority and no product mission-cancel service method is present.

Physical multi-host proof remains separately blocked by `EXT-V15-SECOND-HOST`; aliases or extra local processes do not substitute for it.

## Required follow-up

- add the bounded mission-cancel/control-plane method that atomically advances durable mission cancellation generation before advisory lease cancellation;
- wire durable worker dispatch/results into an actual operational mission (`R17b`/`R17c` lineage) and repeat kill/expiry/reassign/cancel/duplicate-result evidence on that path;
- preserve the 20-way concurrency and stale-result negatives;
- keep `ART-V15-MULTIHOST-EVIDENCE` blocked until a second physical host is actually exercised.

No artifact lifecycle promotion is justified by this review.
