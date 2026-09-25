"""Durable authenticated mission mailbox (file-backed; PG wiring is L1).

Messages require an authenticated session token bound to logical agent + generation.
Message body cannot expand authority. Delivery cursors support succession catch-up.
"""

from __future__ import annotations

import hashlib
import json
import secrets
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from swarm.contracts.common import new_id, utc_now
from swarm.contracts.communication import AuthenticatedMessage, DeliveryCursor, MessageKind

_FORBIDDEN_TOKENS = (
    "expand_budget",
    "grant_admin",
    "bypass_kernel",
    "self_accept",
    "grant_permission",
)


class MailboxAuthError(PermissionError):
    pass


class MailboxError(ValueError):
    pass


@dataclass
class AgentSessionCredential:
    """Server-issued session credential — bearer secret is not stored in messages."""

    session_id: str
    logical_agent_id: str
    generation: int
    mission_id: str
    secret_hash: str
    created_at: str = field(default_factory=lambda: utc_now().isoformat())


@dataclass
class DurableMissionMailbox:
    """Append-only JSONL mailbox with per-agent delivery cursors."""

    mission_id: str
    project_id: str
    root: Path | None = None
    _sessions: dict[str, AgentSessionCredential] = field(default_factory=dict)
    _secrets: dict[str, str] = field(default_factory=dict)  # session_id -> plaintext (process)
    _agents: set[str] = field(default_factory=set)
    _messages: list[AuthenticatedMessage] = field(default_factory=list)
    _cursors: dict[str, DeliveryCursor] = field(default_factory=dict)
    _event_order: int = 0

    def __post_init__(self) -> None:
        if self.root is not None:
            self.root.mkdir(parents=True, exist_ok=True)
            self._load()

    def _path(self) -> Path | None:
        return None if self.root is None else self.root / f"{self.mission_id}.jsonl"

    def _meta_path(self) -> Path | None:
        return None if self.root is None else self.root / f"{self.mission_id}.meta.json"

    def join(self, logical_agent_id: str, *, generation: int = 1) -> tuple[str, str]:
        """Register agent and issue (session_id, secret). Secret shown once."""
        self._agents.add(logical_agent_id)
        session_id = new_id("as_")
        secret = secrets.token_urlsafe(24)
        secret_hash = hashlib.sha256(secret.encode("utf-8")).hexdigest()
        cred = AgentSessionCredential(
            session_id=session_id,
            logical_agent_id=logical_agent_id,
            generation=generation,
            mission_id=self.mission_id,
            secret_hash=secret_hash,
        )
        self._sessions[session_id] = cred
        self._secrets[session_id] = secret
        self._cursors.setdefault(
            logical_agent_id,
            DeliveryCursor(mission_id=self.mission_id, logical_agent_id=logical_agent_id),
        )
        self._persist_meta()
        return session_id, secret

    def rotate_session(self, logical_agent_id: str, *, generation: int) -> tuple[str, str]:
        """Issue a new session for a promoted generation; old sessions stay for audit."""
        if logical_agent_id not in self._agents:
            raise MailboxAuthError("agent_not_on_mission")
        return self.join(logical_agent_id, generation=generation)

    def _authenticate(self, *, session_id: str, secret: str) -> AgentSessionCredential:
        cred = self._sessions.get(session_id)
        if cred is None:
            raise MailboxAuthError("session_unknown")
        expected = hashlib.sha256(secret.encode("utf-8")).hexdigest()
        if not secrets.compare_digest(expected, cred.secret_hash):
            raise MailboxAuthError("session_auth_failed")
        return cred

    def post(
        self,
        *,
        session_id: str,
        secret: str,
        kind: MessageKind,
        body: str,
        to_logical_agent_id: str | None = None,
        evidence_refs: list[str] | None = None,
        artifact_refs: list[str] | None = None,
        correlation_id: str | None = None,
        reply_to: str | None = None,
    ) -> AuthenticatedMessage:
        cred = self._authenticate(session_id=session_id, secret=secret)
        if cred.mission_id != self.mission_id:
            raise MailboxAuthError("mission_mismatch")
        if to_logical_agent_id is not None and to_logical_agent_id not in self._agents:
            raise MailboxAuthError("recipient_not_on_mission")
        lowered = body.lower()
        if any(tok in lowered for tok in _FORBIDDEN_TOKENS):
            raise MailboxAuthError("message_authority_expansion_forbidden")
        self._event_order += 1
        msg = AuthenticatedMessage(
            project_id=self.project_id,
            mission_id=self.mission_id,
            kind=kind,
            body=body,
            sender_logical_agent_id=cred.logical_agent_id,
            sender_session_id=cred.session_id,
            sender_generation=cred.generation,
            recipient_logical_agent_id=to_logical_agent_id,
            correlation_id=correlation_id,
            reply_to=reply_to,
            event_order=self._event_order,
            evidence_refs=list(evidence_refs or []),
            artifact_refs=list(artifact_refs or []),
        )
        self._messages.append(msg)
        self._append(msg)
        return msg

    def inbox(
        self,
        logical_agent_id: str,
        *,
        after_cursor: int | None = None,
        limit: int = 50,
    ) -> list[AuthenticatedMessage]:
        if logical_agent_id not in self._agents:
            raise MailboxAuthError("agent_not_on_mission")
        cursor = (
            after_cursor
            if after_cursor is not None
            else self._cursors.get(
                logical_agent_id,
                DeliveryCursor(mission_id=self.mission_id, logical_agent_id=logical_agent_id),
            ).cursor
        )
        out: list[AuthenticatedMessage] = []
        for msg in self._messages:
            if msg.event_order <= cursor:
                continue
            if (
                msg.recipient_logical_agent_id is not None
                and msg.recipient_logical_agent_id != logical_agent_id
                and msg.sender_logical_agent_id != logical_agent_id
            ):
                continue
            # Deliver broadcast + addressed-to-self + own sends for audit continuity.
            if (
                msg.recipient_logical_agent_id in (None, logical_agent_id)
                or msg.sender_logical_agent_id == logical_agent_id
            ):
                out.append(msg)
            if len(out) >= limit:
                break
        return out

    def advance_cursor(
        self, logical_agent_id: str, *, to_event_order: int, last_message_id: str | None = None
    ) -> DeliveryCursor:
        if logical_agent_id not in self._agents:
            raise MailboxAuthError("agent_not_on_mission")
        cur = self._cursors.get(logical_agent_id) or DeliveryCursor(
            mission_id=self.mission_id, logical_agent_id=logical_agent_id
        )
        if to_event_order < cur.cursor:
            raise MailboxError("cursor_regression_forbidden")
        updated = cur.model_copy(
            update={
                "cursor": to_event_order,
                "last_message_id": last_message_id or cur.last_message_id,
                "updated_at": utc_now(),
            }
        )
        self._cursors[logical_agent_id] = updated
        self._persist_meta()
        return updated

    def cursor(self, logical_agent_id: str) -> DeliveryCursor:
        return self._cursors.get(logical_agent_id) or DeliveryCursor(
            mission_id=self.mission_id, logical_agent_id=logical_agent_id
        )

    def evidence(self) -> dict[str, Any]:
        return {
            "mission_id": self.mission_id,
            "project_id": self.project_id,
            "agents": sorted(self._agents),
            "message_count": len(self._messages),
            "messages": [m.model_dump(mode="json") for m in self._messages],
            "cursors": {k: v.model_dump(mode="json") for k, v in self._cursors.items()},
            "sessions": {
                sid: {
                    "session_id": c.session_id,
                    "logical_agent_id": c.logical_agent_id,
                    "generation": c.generation,
                    "mission_id": c.mission_id,
                    "created_at": c.created_at,
                    # never export secret or secret_hash
                }
                for sid, c in self._sessions.items()
            },
            "authority_via_message_text": False,
            "spend_usd": 0,
        }

    def _append(self, msg: AuthenticatedMessage) -> None:
        path = self._path()
        if path is None:
            return
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(msg.model_dump(mode="json"), default=str) + "\n")

    def _persist_meta(self) -> None:
        path = self._meta_path()
        if path is None:
            return
        payload = {
            "mission_id": self.mission_id,
            "project_id": self.project_id,
            "agents": sorted(self._agents),
            "event_order": self._event_order,
            "cursors": {k: v.model_dump(mode="json") for k, v in self._cursors.items()},
            "sessions": [
                {
                    "session_id": c.session_id,
                    "logical_agent_id": c.logical_agent_id,
                    "generation": c.generation,
                    "mission_id": c.mission_id,
                    "secret_hash": c.secret_hash,
                    "created_at": c.created_at,
                }
                for c in self._sessions.values()
            ],
        }
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    def _load(self) -> None:
        meta = self._meta_path()
        if meta is not None and meta.exists():
            data = json.loads(meta.read_text(encoding="utf-8"))
            self._agents = set(data.get("agents") or [])
            self._event_order = int(data.get("event_order") or 0)
            self._cursors = {
                k: DeliveryCursor.model_validate(v) for k, v in (data.get("cursors") or {}).items()
            }
            for row in data.get("sessions") or []:
                cred = AgentSessionCredential(
                    session_id=row["session_id"],
                    logical_agent_id=row["logical_agent_id"],
                    generation=int(row["generation"]),
                    mission_id=row["mission_id"],
                    secret_hash=row["secret_hash"],
                    created_at=row.get("created_at") or utc_now().isoformat(),
                )
                self._sessions[cred.session_id] = cred
        path = self._path()
        if path is not None and path.exists():
            rows: list[AuthenticatedMessage] = []
            for line in path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                rows.append(AuthenticatedMessage.model_validate(json.loads(line)))
            self._messages = rows
