"""Tools package."""

from swarm.tools.adapters import (
    ApiMcpAdapter,
    BrowserSessionAdapter,
    IntegrationAdapter,
    LocalSandboxAdapter,
)
from swarm.tools.effects import DurableEffectRepository, InMemoryEffectStore
from swarm.tools.gateway import (
    ApprovalInvalidError as LegacyApprovalInvalidError,
)
from swarm.tools.gateway import (
    StaleLeaseError as LegacyStaleLeaseError,
)
from swarm.tools.gateway import (
    ToolAuthorizationError as LegacyToolAuthorizationError,
)
from swarm.tools.gateway import (
    ToolGateway,
    make_approval,
)
from swarm.tools.registry import CapabilityRegistry, ToolSpec, hash_operation
from swarm.tools.sandbox_runner import IsolatedCodeRunner, SandboxPolicyError, self_test
from swarm.tools.session_recovery import SessionRecoveryService
from swarm.tools.v17_gateway import (
    ApprovalInvalidError,
    CancellationFenceError,
    ConsequentialToolGateway,
    PolicyDeniedError,
    ReconciliationRequiredError,
    StaleLeaseError,
    ToolAuthorizationError,
)

__all__ = [
    "ApiMcpAdapter",
    "ApprovalInvalidError",
    "BrowserSessionAdapter",
    "CancellationFenceError",
    "CapabilityRegistry",
    "ConsequentialToolGateway",
    "DurableEffectRepository",
    "InMemoryEffectStore",
    "IntegrationAdapter",
    "IsolatedCodeRunner",
    "LegacyApprovalInvalidError",
    "LegacyStaleLeaseError",
    "LegacyToolAuthorizationError",
    "LocalSandboxAdapter",
    "PolicyDeniedError",
    "ReconciliationRequiredError",
    "SandboxPolicyError",
    "SessionRecoveryService",
    "StaleLeaseError",
    "ToolAuthorizationError",
    "ToolGateway",
    "ToolSpec",
    "hash_operation",
    "make_approval",
    "self_test",
]
