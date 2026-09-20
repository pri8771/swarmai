"""PydanticAI + DBOS durability compatibility spike."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from dbos import DBOS, DBOSConfig
from pydantic_ai import Agent, RunContext
from pydantic_ai.durable_exec.dbos import DBOSDurability

from swarm.contracts.provider import RouteSnapshot
from swarm.spike.broker_hook import (
    SpikeAnswer,
    SpikeDeps,
    _build_function_model,
    make_default_broker,
    run_with_broker,
    serializable_checkpoint,
)


def _sqlite_url(path: Path) -> str:
    return f"sqlite:///{path.resolve()}"


def _make_durable_agent(route: RouteSnapshot) -> Agent[SpikeDeps, SpikeAnswer]:
    agent: Agent[SpikeDeps, SpikeAnswer] = Agent(
        _build_function_model(route),
        deps_type=SpikeDeps,
        output_type=SpikeAnswer,
        name=f"spike-{route.route_id}",
        instructions="Return structured SpikeAnswer. Use echo_count once.",
        capabilities=[DBOSDurability()],
    )

    @agent.tool
    async def echo_count(ctx: RunContext[SpikeDeps], text: str) -> int:
        return len(text)

    return agent


class DurableSpikeHarness:
    """Owns DBOS lifecycle for the P01 spike with two fake route identities."""

    def __init__(self, db_path: Path, application_version: str = "p01-spike-1") -> None:
        self.db_path = db_path
        self.application_version = application_version
        self.broker, self.route_alpha, self.route_beta = make_default_broker()
        self._launched = False
        self.agent_alpha: Agent[SpikeDeps, SpikeAnswer] | None = None
        self.agent_beta: Agent[SpikeDeps, SpikeAnswer] | None = None
        self.spike_workflow: Any = None
        self.spike_workflow_with_step: Any = None

    def launch(self) -> None:
        if self._launched:
            return
        try:
            DBOS.destroy(destroy_registry=True)
        except Exception:  # noqa: BLE001
            pass

        config: DBOSConfig = {
            "name": "swarm_p01_spike",
            "system_database_url": _sqlite_url(self.db_path),
            "application_version": self.application_version,
        }
        DBOS(config=config)

        # Agents must exist before launch; capabilities register steps.
        self.agent_alpha = _make_durable_agent(self.route_alpha)
        self.agent_beta = _make_durable_agent(self.route_beta)
        self._register_workflows()
        DBOS.launch()
        self._launched = True

    def _register_workflows(self) -> None:
        harness = self

        @DBOS.step()
        async def completed_step_marker(route_id: str) -> str:
            return f"completed:{route_id}"

        @DBOS.workflow()
        async def spike_workflow(route_id: str, prompt: str) -> dict[str, Any]:
            assert harness.agent_alpha is not None and harness.agent_beta is not None
            agent = (
                harness.agent_alpha
                if route_id == harness.route_alpha.route_id
                else harness.agent_beta
            )
            deps = SpikeDeps(
                broker=harness.broker,
                route_id=route_id,
                runtime_client=object(),
                secret_ref_name="FAKE_API_KEY",
            )
            answer = await run_with_broker(agent, prompt, deps)
            checkpoint = serializable_checkpoint(deps)
            if "runtime_client" in checkpoint:
                raise RuntimeError("runtime_client leaked into checkpoint")
            lowered = str(checkpoint).lower()
            if "sk-" in lowered or "secret=" in lowered or "api_key=" in lowered:
                raise RuntimeError("secret material leaked into checkpoint")
            return {
                "answer": answer.model_dump(),
                "checkpoint": checkpoint,
                "broker_requests": harness.broker.request_count,
            }

        @DBOS.workflow()
        async def spike_workflow_with_step(route_id: str, prompt: str) -> dict[str, Any]:
            marker = await completed_step_marker(route_id)
            assert harness.agent_alpha is not None and harness.agent_beta is not None
            agent = (
                harness.agent_alpha
                if route_id == harness.route_alpha.route_id
                else harness.agent_beta
            )
            deps = SpikeDeps(
                broker=harness.broker,
                route_id=route_id,
                runtime_client=object(),
                secret_ref_name="FAKE_API_KEY",
            )
            answer = await run_with_broker(agent, prompt, deps)
            if os.environ.get("SWARM_SPIKE_CRASH") == "1":
                raise RuntimeError("induced_crash_after_completed_step")
            return {
                "marker": marker,
                "answer": answer.model_dump(),
                "checkpoint": serializable_checkpoint(deps),
                "broker_requests": harness.broker.request_count,
            }

        self.spike_workflow = spike_workflow
        self.spike_workflow_with_step = spike_workflow_with_step

    def destroy(self) -> None:
        if self._launched:
            try:
                DBOS.destroy(destroy_registry=True)
            except Exception:  # noqa: BLE001
                pass
            self._launched = False


async def run_dual_route_spike(db_path: Path) -> dict[str, Any]:
    harness = DurableSpikeHarness(db_path)
    harness.launch()
    try:
        assert harness.spike_workflow is not None
        alpha_out = await harness.spike_workflow(harness.route_alpha.route_id, "alpha prompt")
        beta_out = await harness.spike_workflow(harness.route_beta.route_id, "beta prompt")
        harness.broker.assert_all_calls_accounted()
        return {
            "alpha": alpha_out,
            "beta": beta_out,
            "total_broker_requests": harness.broker.request_count,
        }
    finally:
        harness.destroy()
