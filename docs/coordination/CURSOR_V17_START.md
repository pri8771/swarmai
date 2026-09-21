# Cursor bootstrap — single session to V1.7

You are the ONLY active SwarmAI implementation session.

Repository: `pri8771/swarmai`
Implementation branch: `cursor/v17-single-session`
Canonical coordination: `coordination/swarm-control`
Session ID: `CURSOR-V17-SINGLE`

Read, in this order:

1. `docs/coordination/ARTIFACT_REGISTRY.json` from coordination branch
2. `docs/coordination/STATE.json`
3. `docs/coordination/SINGLE_SESSION_V17_EXECUTION.md`
4. `docs/coordination/SINGLE_SESSION_HEARTBEAT.md`
5. `docs/coordination/VERSION_ARTIFACT_MATRIX.md`
6. `docs/coordination/WORK_QUEUE.md`
7. relevant artifact contracts/reviews/messages

Then execute the single-session contract continuously through a V1.7 implementation-complete/reviewable candidate.

Important:
- exactly one heartbeat scheduler/producer for this session;
- publish heartbeat every 5 minutes while active, including "still working on X" updates;
- stop/disable legacy A/B local heartbeat/autonomous processes;
- no parallel implementation sessions;
- old runtime/product branches are donor/evidence branches only;
- inspect/cherry-pick selectively; never blindly merge them;
- do not self-accept;
- do not merge main;
- no public deploy;
- no additional spend;
- `SWARM_ALLOW_PAID=false`;
- preserve honest BLOCKED/UNKNOWN/WAITING states;
- never count mocks as live proof.

Continue without routine permission questions. Ask only for genuinely human-only actions such as login/MFA/consent/credential availability, or when a destructive/paid/public action would be required.

At the end, push the branch and publish a final artifact-by-artifact V1.0-repair -> V1.7 implementation/evidence/blocker report.
