"""Durable project/workspace configuration (no secrets on disk)."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from swarm.contracts.common import new_id, utc_now

_SECRET_KEY_RE = re.compile(
    r"(api[_-]?key|secret|password|token|authorization|credential)", re.I
)
_SECRET_VAL_RE = re.compile(r"(sk-[A-Za-z0-9]{8,}|api_key\s*=)", re.I)


def scrub_config(obj: Any) -> Any:
    """Strip secret-shaped keys/values before persistence or API export."""
    if isinstance(obj, dict):
        out: dict[str, Any] = {}
        for k, v in obj.items():
            if _SECRET_KEY_RE.search(str(k)) and str(k).lower() not in {
                "secret_ref_names",
                "env_refs",
                "token_budget",
            }:
                continue
            if isinstance(v, str) and _SECRET_VAL_RE.search(v):
                out[k] = "[redacted]"
            else:
                out[k] = scrub_config(v)
        return out
    if isinstance(obj, list):
        return [scrub_config(x) for x in obj]
    if isinstance(obj, str) and _SECRET_VAL_RE.search(obj):
        return "[redacted]"
    return obj


@dataclass
class ProjectConfig:
    """Workspace settings — durable, secret-free."""

    project_id: str
    name: str
    repo_path: str
    allowed_tools: list[str] = field(
        default_factory=lambda: ["repo.read", "tests.run", "calc"]
    )
    provider_policy: dict[str, Any] = field(
        default_factory=lambda: {
            "allow_paid": False,
            "prefer_local": True,
            "blocked_providers": ["together", "fireworks"],
        }
    )
    budgets: dict[str, Any] = field(
        default_factory=lambda: {
            "max_cost_usd": 0.0,
            "max_requests": 50,
            "max_wall_ms": 300_000,
        }
    )
    defaults: dict[str, Any] = field(
        default_factory=lambda: {
            "model": "gemma3:4b",
            "max_agents": 8,
            "use_evidence_router": True,
        }
    )
    env_refs: list[str] = field(default_factory=lambda: ["SWARM_ALLOW_PAID"])
    safety: dict[str, Any] = field(
        default_factory=lambda: {
            "require_approval_for_writes": True,
            "deny_secret_paths": True,
            "path_allowlist": ["sandbox/", "var/"],
        }
    )
    created_at: str = field(default_factory=lambda: utc_now().isoformat())
    updated_at: str = field(default_factory=lambda: utc_now().isoformat())
    schema_version: str = "0.8.0"

    def to_dict(self) -> dict[str, Any]:
        result = scrub_config(asdict(self))
        assert isinstance(result, dict)
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProjectConfig:
        known = set(cls.__dataclass_fields__.keys())
        clean = scrub_config({k: v for k, v in data.items() if k in known})
        return cls(**clean)


class ProjectStore:
    """File-backed project registry under var/projects/."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, project_id: str) -> Path:
        return self.root / f"{project_id}.json"

    def create(
        self,
        *,
        name: str,
        repo_path: str | Path,
        project_id: str | None = None,
        **overrides: Any,
    ) -> ProjectConfig:
        cfg = ProjectConfig(
            project_id=project_id or new_id("proj_"),
            name=name,
            repo_path=str(Path(repo_path).resolve()),
            **{k: v for k, v in overrides.items() if k in ProjectConfig.__dataclass_fields__},
        )
        self.save(cfg)
        return cfg

    def save(self, cfg: ProjectConfig) -> Path:
        cfg.updated_at = utc_now().isoformat()
        path = self._path(cfg.project_id)
        payload = cfg.to_dict()
        blob = json.dumps(payload, indent=2, default=str)
        if _SECRET_VAL_RE.search(blob):
            raise ValueError("refusing_to_persist_secret_shaped_project_config")
        path.write_text(blob + "\n", encoding="utf-8")
        return path

    def get(self, project_id: str) -> ProjectConfig:
        path = self._path(project_id)
        if not path.exists():
            raise KeyError(f"project_not_found:{project_id}")
        return ProjectConfig.from_dict(json.loads(path.read_text(encoding="utf-8")))

    def list_projects(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for path in sorted(self.root.glob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            rows.append(
                {
                    "project_id": data.get("project_id"),
                    "name": data.get("name"),
                    "repo_path": data.get("repo_path"),
                    "updated_at": data.get("updated_at"),
                    "allow_paid": (data.get("provider_policy") or {}).get("allow_paid"),
                }
            )
        return rows

    def update(self, project_id: str, **patch: Any) -> ProjectConfig:
        cfg = self.get(project_id)
        data = cfg.to_dict()
        data.update(patch)
        data["project_id"] = project_id
        updated = ProjectConfig.from_dict(data)
        self.save(updated)
        return updated
