# CP3 run cp3-20260922T020141Z — rerun after MISSION-CANCEL-01

- Source SHA (pushed, clean tree): `e53da7305d138658edfb9bd8f47ebbd140a40a63`
- Result: **pass** — all nine requirements demonstrated; the cancellation step's durable bump now goes through `DurableWorkerService.revoke_mission_work` (product code) with `notify_leases=False` first, then the advisory lease cancel.
- Same mode as run cp3-20260922T013226Z (separate OS processes, real PostgreSQL, real SIGKILL, 20 concurrent duplicate-accept iterations). Spend $0. Self-accept: false. Independent review: pending.
- Multi-host evidence remains external (EXT-V15-SECOND-HOST); "CP3 on a real operational mission" still needs R17b.
