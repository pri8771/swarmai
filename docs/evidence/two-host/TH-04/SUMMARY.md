# TH-04 evidence summary

**Date:** 2026-09-25T15:38Z  
**Hostname:** `swarm.splitsignal.ai`  
**Server:** `http://127.0.0.1:18766`  
**Content hash:** `a21e29cc4efeb126f2e9192c375e73f7bb25b9c54c6c3850c2df9778b8c8ee99`

## Results

| Check | Result | Evidence |
|---|---|---|
| Publish durable CAS artifact via API | **pass** | step `publish_artifact` |
| List artifacts includes `content_hash` | **pass** | step `list_artifacts_before` |
| Read content before restart | **pass** | step `read_content_before` |
| `docker compose restart api` | **pass** | step `restart_api_container` |
| Mission hydrate after restart | **pass** | step `hydrate_mission_after_restart` |
| List artifacts identical sha256 after restart | **pass** | step `list_artifacts_after_restart` |
| Content reopen identical sha256 | **pass** | step `read_content_after_restart` |
| Volume CAS blob verified in container | **pass** | step `volume_cas_blob_verified` |
| Worker re-enroll leaves artifact intact | **pass** | step `worker_reenroll_artifact_intact` |
| Unit: ArtifactStore + ProductStore cold reopen | **pass** | `tests/workspace/test_artifact_durability.py` |

## Commands

```sh
docker compose -f deploy/compose/server.yml up -d
uv run python scripts/th04_durable_artifacts_restart.py
curl -fsS http://127.0.0.1:18766/health/ready
uv run pytest tests/workspace/test_artifact_durability.py -q
```

## Not run / blocked

R730, `.ai` DNS, Cloudflare Tunnel, Linear MCP (`needsAuth`), paid/live inference, OpenCode/Hermes.
