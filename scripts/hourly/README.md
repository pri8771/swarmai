# Hourly worker (FIX-004)

Local LaunchAgent check-in for SwarmAI V1.4. No cloud billing.

## Install

```bash
export SWARM_HOURLY_REPO="$(pwd)"
export SWARM_HOURLY_PYTHON=/usr/bin/python3
bash scripts/hourly/install_launchd.sh   # StartInterval=3600
```

Verify (manual + ≥2 scheduler check-ins):

```bash
bash scripts/hourly/verify_fix004.sh
```

State/logs live under:

`~/Library/Application Support/SwarmAI/hourly-runner/`

The LaunchAgent runs a **copy** of `checkin.py` from that directory because macOS TCC often blocks agents from reading `~/Downloads`.

## Notes

- Single-instance lock with stale recovery (`hourly.lock`).
- Scheduler skips repo git + Cursor agent probe (`SWARM_HOURLY_SKIP_REPO=1`, `SWARM_HOURLY_SKIP_CURSOR_PROBE=1`) to avoid TCC hangs.
- Unattended `cursor agent -p` spawn remains blocked until `cursor agent login` / `CURSOR_API_KEY` with verified zero-spend entitlement.
- Uninstall: `bash scripts/hourly/uninstall_launchd.sh`
