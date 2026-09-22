"""V2B-004c — integration adapter interface + manifests."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from swarm.contracts.actions import ActionEnvelope, ActionReceiptV17, AdapterManifest

ADAPTER_OUTCOMES = frozenset({"succeeded", "not_applied", "denied", "cancelled", "unknown"})


class AdapterNotSentError(Exception):
    """The request provably never left this process."""


class AdapterDeniedError(PermissionError):
    """The adapter explicitly denied the operation."""


@runtime_checkable
class IntegrationAdapter(Protocol):
    """Adapter never decides project authorization or approval validity."""

    manifest: AdapterManifest

    def normalize(self, request: dict[str, Any]) -> ActionEnvelope: ...

    def validate(self, envelope: ActionEnvelope) -> None: ...

    def observe_pre_state(self, envelope: ActionEnvelope) -> dict[str, Any]: ...

    def execute(self, envelope: ActionEnvelope) -> dict[str, Any]:
        """Return an explicit outcome in ADAPTER_OUTCOMES; never infer success."""
        ...

    def observe_post_state(
        self, envelope: ActionEnvelope, execution_result: dict[str, Any]
    ) -> dict[str, Any]: ...

    def reconcile(
        self, envelope: ActionEnvelope, prior_receipts: list[ActionReceiptV17]
    ) -> dict[str, Any]: ...
