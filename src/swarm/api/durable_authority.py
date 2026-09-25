"""Durable on-disk snapshots for API authority that must survive process restart.

Workers and scoped idempotency entries are mirrored under ``var/`` so a cold
API reconstruction against the same repo_root restores membership and replay
keys. PostgreSQL remains the preferred transactional authority when configured;
this file-backed mirror closes the in-memory-only reconstruction hole (R2/R3).
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

from swarm.contracts.enums import WorkerStatus
from swarm.contracts.mission import TaskSpec
from swarm.contracts.workspace import WorkerLease
from swarm.workers.registry import DispatchLease, WorkerRecord, WorkerRegistryService


def _atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True, default=str)
            handle.write("\n")
        os.replace(tmp_name, path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def worker_registry_path(repo_root: Path) -> Path:
    return repo_root / "var" / "workers" / "registry.json"


def idempotency_path(repo_root: Path) -> Path:
    return repo_root / "var" / "api" / "idempotency.json"


def _parse_dt(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    text = str(value)
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


def save_worker_registry(repo_root: Path, registry: WorkerRegistryService) -> None:
    rows: list[dict[str, Any]] = []
    for rec in registry._workers.values():
        rows.append(
            {
                "lease": rec.lease.model_dump(mode="json"),
                "token": rec.token,
                "project_id": rec.project_id,
                "revoked": rec.revoked,
                "privacy_classes": sorted(rec.privacy_classes),
                "named_inference_urls": list(rec.named_inference_urls),
                "measured_capacity": rec.measured_capacity,
                "claimed_task_id": rec.claimed_task_id,
                "active_lease_ids": list(rec.active_lease_ids),
                "last_heartbeat": (
                    rec.last_heartbeat.isoformat()
                    if hasattr(rec.last_heartbeat, "isoformat")
                    else str(rec.last_heartbeat)
                ),
            }
        )
    lease_rows: list[dict[str, Any]] = []
    for lease in registry._leases.values():
        lease_rows.append(
            {
                "lease_id": lease.lease_id,
                "task": lease.task.model_dump(mode="json"),
                "worker_id": lease.worker_id,
                "worker_generation": lease.worker_generation,
                "expires_at": lease.expires_at.isoformat(),
                "state": lease.state,
                "cancel_requested": lease.cancel_requested,
                "cancel_reason": lease.cancel_reason,
                "result_id": lease.result_id,
                "result_payload": lease.result_payload,
                "submitted_at": (
                    lease.submitted_at.isoformat() if lease.submitted_at else None
                ),
                "acceptance_state": lease.acceptance_state,
            }
        )
    _atomic_write(
        worker_registry_path(repo_root),
        {
            "schema_version": "1.1",
            "workers": rows,
            "quarantine": sorted(registry._quarantine),
            "dispatch_queue": [t.model_dump(mode="json") for t in registry._dispatch_queue],
            "leases": lease_rows,
            "results": dict(registry._results),
        },
    )


def load_worker_registry(repo_root: Path, registry: WorkerRegistryService) -> None:
    path = worker_registry_path(repo_root)
    if not path.is_file():
        return
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError):
        return
    registry._workers.clear()
    registry._tokens.clear()
    registry._quarantine.clear()
    registry._dispatch_queue.clear()
    registry._leases.clear()
    registry._results.clear()
    for row in raw.get("workers") or []:
        if not isinstance(row, dict):
            continue
        try:
            lease = WorkerLease.model_validate(row.get("lease") or {})
            token = str(row.get("token") or "")
            if not token:
                continue
            # Rehydrate status enum if stored as string inside lease already.
            if isinstance(lease.status, str):
                lease = lease.model_copy(update={"status": WorkerStatus(lease.status)})
            rec = WorkerRecord(
                lease=lease,
                token=token,
                project_id=row.get("project_id"),
                revoked=bool(row.get("revoked")),
                privacy_classes=set(row.get("privacy_classes") or ["local"]),
                named_inference_urls=list(row.get("named_inference_urls") or []),
                measured_capacity=float(row.get("measured_capacity") or 1.0),
                claimed_task_id=row.get("claimed_task_id"),
                active_lease_ids=list(row.get("active_lease_ids") or []),
            )
            registry._workers[lease.worker_id] = rec
            registry._tokens[token] = lease.worker_id
        except (TypeError, ValueError, KeyError):
            continue
    for wid in raw.get("quarantine") or []:
        registry._quarantine.add(str(wid))
    for task_row in raw.get("dispatch_queue") or []:
        try:
            registry._dispatch_queue.append(TaskSpec.model_validate(task_row))
        except (TypeError, ValueError):
            continue
    for lease_row in raw.get("leases") or []:
        if not isinstance(lease_row, dict):
            continue
        try:
            expires = _parse_dt(lease_row.get("expires_at"))
            if expires is None:
                continue
            dispatch_lease = DispatchLease(
                lease_id=str(lease_row["lease_id"]),
                task=TaskSpec.model_validate(lease_row.get("task") or {}),
                worker_id=str(lease_row["worker_id"]),
                worker_generation=int(lease_row.get("worker_generation") or 1),
                expires_at=expires,
                state=str(lease_row.get("state") or "claimed"),
                cancel_requested=bool(lease_row.get("cancel_requested")),
                cancel_reason=lease_row.get("cancel_reason"),
                result_id=lease_row.get("result_id"),
                result_payload=lease_row.get("result_payload"),
                submitted_at=_parse_dt(lease_row.get("submitted_at")),
                acceptance_state=str(lease_row.get("acceptance_state") or "pending"),
            )
            registry._leases[dispatch_lease.lease_id] = dispatch_lease
        except (TypeError, ValueError, KeyError):
            continue
    results = raw.get("results") or {}
    if isinstance(results, dict):
        registry._results.update(results)


def save_idempotency(repo_root: Path, table: dict[str, dict[str, Any]]) -> None:
    _atomic_write(
        idempotency_path(repo_root),
        {"schema_version": "1.0", "entries": table},
    )


def load_idempotency(repo_root: Path) -> dict[str, dict[str, Any]]:
    path = idempotency_path(repo_root)
    if not path.is_file():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError):
        return {}
    entries = raw.get("entries") or {}
    return entries if isinstance(entries, dict) else {}
