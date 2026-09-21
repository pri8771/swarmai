# SwarmAI heartbeat protocol

Status: SUPERSEDED FOR CURRENT EXECUTION
Date: 2026-09-21

The former A/B multi-lane stress/soak heartbeat protocol is historical evidence only.

Current owner directive:
- exactly ONE active Cursor implementation session;
- exactly ONE scheduled heartbeat producer;
- current session: `CURSOR-V17-SINGLE`;
- current implementation branch: `cursor/v17-single-session`;
- current heartbeat protocol: `docs/coordination/SINGLE_SESSION_HEARTBEAT.md`.

Old HOST-MAC-DEV / HOST-WIN-DEV heartbeat histories must not be treated as current liveness.

Heartbeat remains liveness/progress evidence only and never constitutes artifact acceptance.
