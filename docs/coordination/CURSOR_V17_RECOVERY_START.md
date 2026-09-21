# Cursor start — V1.7 artifact recovery

You are the single active implementation session.

Repository: pri8771/swarmai
Branch: cursor/v17-single-session
Session: CURSOR-V17-SINGLE

The prior broad V1.7 instruction is superseded by:
- V17_CODE_AUDIT_20260921_1432.md
- V17_RECOVERY_PLAN_ARTIFACT_FIRST.md
- V17_RECOVERY_PACKET_QUEUE.json
- V17_LIVE_CHECKPOINT_PROTOCOL.md

Start at the first dependency-ready incomplete packet.

Rules:
- one packet at a time;
- one small commit per packet;
- targeted tests before broad tests;
- live evidence at checkpoint packets;
- exact branch SHA in evidence;
- one heartbeat producer only;
- do not self-accept;
- do not merge main;
- no public deploy;
- no paid fallback/spend;
- preserve failures;
- no demo/mock evidence counted as live;
- blocked external gate -> write exact blocker -> move to independent work.

Important audit decisions:
- v14-real-005 is NOT independently accepted; lead review says changes required.
- GitHub Actions current branch is red before job steps; classify, do not spam reruns.
- current branch has not integrated V1.5/V1.6/V1.7 implementation.
- reuse donor V1.5/G13 source selectively; do not merge legacy coordination/heartbeat topology.

Do not stop after each review-only gate. Mark review_pending and continue dependency-independent packets.

Goal:
reach a V1.7 implementation-complete candidate with CP0-CP5 live checkpoint evidence, then CP6 integrated audit. Formal acceptance remains separate for any required wall-clock/provider/multi-host evidence.
