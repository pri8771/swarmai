"""V20-E05: bounded native model/tool loop over RouterClient.

Hard bounds on turns, model calls and tool calls. Tools must be allowlisted; an
unknown or disallowed tool call stops the loop (fail closed) without executing.
The loop never decides goal success: callers keep outcomes pending until
protected verification. Only a transcript digest is kept, never raw content.

Live use (V20-E07) needs a usable LiveGrant; ``native_loop_from_env`` returns an
honest blocker instead of constructing a live client without one.
"""

from __future__ import annotations

import json
import os
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any, Literal

from swarm.contracts.common import payload_hash
from swarm.contracts.router_capabilities import RouterCallReceipt
from swarm.evals.synthetic_harness import LiveGrant
from swarm.providers.router_client import RouterClient, RouterClientError
from swarm.pursuit.live_grant import preflight_live_grant

ToolFn = Callable[[dict[str, Any]], str]
LoopStatus = Literal["completed", "budget_exhausted", "tool_denied", "router_error"]


@dataclass
class LoopResult:
    status: LoopStatus
    final_text: str = ""
    turns: int = 0
    model_calls: int = 0
    tool_calls: int = 0
    receipts: list[RouterCallReceipt] = field(default_factory=list)
    error_class: str | None = None
    error_code: str | None = None
    transcript_digest: str = ""

    @property
    def usage_known(self) -> bool:
        return bool(self.receipts) and all(r.usage_known for r in self.receipts)

    def summary(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "turns": self.turns,
            "model_calls": self.model_calls,
            "tool_calls": self.tool_calls,
            "usage_known": self.usage_known,
            "error_class": self.error_class,
            "error_code": self.error_code,
            "transcript_digest": self.transcript_digest,
            "routes": sorted({r.route_id for r in self.receipts if r.route_id}),
        }


class BoundedNativeLoop:
    def __init__(
        self,
        router: RouterClient,
        tools: Mapping[str, ToolFn],
        *,
        model: str,
        max_turns: int = 4,
        max_model_calls: int = 8,
        max_tool_calls: int = 8,
    ) -> None:
        self.router = router
        self.tools = dict(tools)
        self.model = model
        self.max_turns = max_turns
        self.max_model_calls = max_model_calls
        self.max_tool_calls = max_tool_calls

    def _tool_specs(self) -> list[dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {"name": name, "parameters": {"type": "object"}},
            }
            for name in sorted(self.tools)
        ]

    def run(self, objective: str, *, system: str | None = None) -> LoopResult:
        messages: list[dict[str, Any]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": objective})
        result = LoopResult(status="budget_exhausted")

        def done(status: LoopStatus, **kw: Any) -> LoopResult:
            result.status = status
            for k, v in kw.items():
                setattr(result, k, v)
            result.transcript_digest = payload_hash({"messages": messages})
            return result

        for _ in range(self.max_turns):
            if result.model_calls >= self.max_model_calls:
                return done("budget_exhausted", error_code="max_model_calls")
            result.turns += 1
            body: dict[str, Any] = {"model": self.model, "messages": messages}
            if self.tools:
                body["tools"] = self._tool_specs()
            try:
                chat = self.router.chat(body)
            except RouterClientError as exc:
                result.model_calls += 1
                if exc.receipt is not None:
                    result.receipts.append(exc.receipt)
                return done("router_error", error_class=exc.error_class.value, error_code=exc.code)
            result.model_calls += 1
            result.receipts.append(chat.receipt)
            msg = chat.message
            messages.append(msg)
            calls = msg.get("tool_calls") or []
            if not calls:
                return done("completed", final_text=str(msg.get("content") or ""))
            for call in calls:
                fn = (call.get("function") or {}) if isinstance(call, dict) else {}
                name = str(fn.get("name") or "")
                if name not in self.tools:
                    return done("tool_denied", error_code=f"tool_not_allowed:{name}")
                if result.tool_calls >= self.max_tool_calls:
                    return done("budget_exhausted", error_code="max_tool_calls")
                try:
                    args = json.loads(fn.get("arguments") or "{}")
                except ValueError:
                    return done("tool_denied", error_code=f"tool_args_invalid:{name}")
                if not isinstance(args, dict):
                    return done("tool_denied", error_code=f"tool_args_invalid:{name}")
                result.tool_calls += 1
                output = self.tools[name](args)
                messages.append(
                    {"role": "tool", "tool_call_id": str(call.get("id") or ""), "content": output}
                )
        return done("budget_exhausted", error_code="max_turns")


def native_loop_from_env(
    tools: Mapping[str, ToolFn],
    *,
    grant: LiveGrant | None,
    env: Mapping[str, str] | None = None,
) -> tuple[BoundedNativeLoop | None, str]:
    """Build a live loop only with a router URL, a model and a usable LiveGrant."""
    e = os.environ if env is None else env
    base_url = e.get("SWARM_ROUTER_BASE_URL", "").strip()
    if not base_url:
        return None, "router_not_configured"
    model = e.get("SWARM_ROUTER_MODEL", "").strip()
    if not model:
        return None, "router_model_not_configured"
    pre = preflight_live_grant(grant, purpose="pursuit_native_loop", required_route=model)
    if not pre.ready:
        return None, pre.blocked_reason or "live_grant_not_ready"
    return BoundedNativeLoop(RouterClient(base_url), tools, model=model), "ready"
