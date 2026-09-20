"""Broker-aware helpers for the P01 compatibility spike."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel
from pydantic_ai import Agent, RunContext
from pydantic_ai.messages import ModelMessage, ModelResponse, TextPart, ToolCallPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from swarm.contracts.fixtures import sample_quota, sample_route, sample_route_beta
from swarm.contracts.provider import InferenceRequest, RouteSnapshot
from swarm.fakes.broker import FakeInferenceBroker
from swarm.fakes.provider import FakeProviderAdapter


class SpikeAnswer(BaseModel):
    summary: str
    route_id: str
    echo_count: int = 0


@dataclass
class SpikeDeps:
    broker: FakeInferenceBroker
    route_id: str
    # Runtime-only client/secret holder — must never be checkpointed as a secret value.
    runtime_client: object
    secret_ref_name: str = "FAKE_API_KEY"


def _build_function_model(route: RouteSnapshot) -> FunctionModel:
    async def handler(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        tool = next((t for t in info.function_tools if t.name == "echo_count"), None)
        already_used = any(
            isinstance(p, ToolCallPart) and p.tool_name == "echo_count"
            for m in messages
            if isinstance(m, ModelResponse)
            for p in m.parts
        )
        if tool is not None and not already_used:
            return ModelResponse(
                parts=[
                    ToolCallPart(
                        tool_name="echo_count",
                        args={"text": "spike"},
                        tool_call_id="tc1",
                    )
                ]
            )
        user_text = ""
        for message in reversed(messages):
            for part in getattr(message, "parts", []):
                content = getattr(part, "content", None)
                if isinstance(content, str) and content:
                    user_text = content
                    break
            if user_text:
                break
        payload = SpikeAnswer(
            summary=f"handled:{user_text[:40]}",
            route_id=route.route_id,
            echo_count=1,
        )
        return ModelResponse(parts=[TextPart(content=payload.model_dump_json())])

    return FunctionModel(handler, model_name=route.model_id)


def build_spike_agent(route: RouteSnapshot) -> Agent[SpikeDeps, SpikeAnswer]:
    agent: Agent[SpikeDeps, SpikeAnswer] = Agent(
        _build_function_model(route),
        deps_type=SpikeDeps,
        output_type=SpikeAnswer,
        name=f"spike-{route.route_id}",
        instructions="Return structured SpikeAnswer. Use echo_count once.",
    )

    @agent.tool
    async def echo_count(ctx: RunContext[SpikeDeps], text: str) -> int:
        return len(text)

    return agent


async def run_with_broker(
    agent: Agent[SpikeDeps, SpikeAnswer],
    prompt: str,
    deps: SpikeDeps,
) -> SpikeAnswer:
    """Admit one broker ticket per agent model turn before running."""
    assess_req = InferenceRequest(
        project_id="proj_demo",
        attempt_id="att_spike",
        route_id=deps.route_id,
        purpose="spike",
        messages=[{"role": "user", "content": prompt}],
        secret_ref_names=[deps.secret_ref_name],
    )
    routes = await deps.broker.assess(assess_req)
    if not routes:
        raise RuntimeError("no eligible routes")
    route = routes[0]
    ticket = await deps.broker.reserve(assess_req, route)
    await deps.broker.invoke(ticket)
    result = await agent.run(prompt, deps=deps)
    deps.broker.assert_all_calls_accounted()
    if result.output.route_id != deps.route_id:
        raise RuntimeError(
            f"route identity drift: expected {deps.route_id}, got {result.output.route_id}"
        )
    return result.output


def make_default_broker() -> tuple[FakeInferenceBroker, RouteSnapshot, RouteSnapshot]:
    alpha = sample_route()
    beta = sample_route_beta()
    adapter = FakeProviderAdapter([alpha, beta])
    broker = FakeInferenceBroker(adapter, buckets=[sample_quota()])
    return broker, alpha, beta


def serializable_checkpoint(deps: SpikeDeps) -> dict[str, Any]:
    """Only durable refs — never runtime_client or secret values."""
    return {
        "route_id": deps.route_id,
        "secret_ref_name": deps.secret_ref_name,
        "broker_request_count": deps.broker.request_count,
    }
