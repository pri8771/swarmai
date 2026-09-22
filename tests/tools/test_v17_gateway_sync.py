"""R28d-2 synchronous ToolGateway entrypoint boundaries."""

from __future__ import annotations

import asyncio
from unittest.mock import patch

import pytest

from swarm.tools.v17_gateway import ConsequentialToolGateway


def _subject(result: object) -> ConsequentialToolGateway:
    gateway = object.__new__(ConsequentialToolGateway)

    async def execute_envelope(envelope: object, *, context: object) -> object:
        assert envelope == "envelope"
        assert context == "context"
        return result

    gateway.execute_envelope = execute_envelope  # type: ignore[method-assign]
    return gateway


def test_execute_envelope_sync_runs_async_gateway_without_running_loop():
    expected = object()
    gateway = _subject(expected)
    real_run = asyncio.run

    with patch("swarm.tools.v17_gateway.asyncio.run", wraps=real_run) as run:
        assert gateway.execute_envelope_sync("envelope", context="context") is expected

    run.assert_called_once()


@pytest.mark.asyncio
async def test_execute_envelope_sync_rejects_running_event_loop():
    gateway = _subject(object())

    with pytest.raises(RuntimeError, match="^sync_call_inside_running_loop$"):
        gateway.execute_envelope_sync("envelope", context="context")
