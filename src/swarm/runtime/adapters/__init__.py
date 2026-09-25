"""Optional agent runtime adapters (Native / OpenCode / Hermes)."""

from swarm.runtime.adapters.base import (
    REQUIRED_CAPABILITIES,
    CapabilityStatus,
    RuntimeAvailability,
    RuntimeQualification,
)
from swarm.runtime.adapters.hermes import HermesRuntimeAdapter
from swarm.runtime.adapters.native import NativeRuntimeAdapter
from swarm.runtime.adapters.opencode import OpenCodeRuntimeAdapter
from swarm.runtime.adapters.qualify import default_adapters, qualification_report, qualify_runtimes

__all__ = [
    "REQUIRED_CAPABILITIES",
    "CapabilityStatus",
    "RuntimeAvailability",
    "RuntimeQualification",
    "NativeRuntimeAdapter",
    "OpenCodeRuntimeAdapter",
    "HermesRuntimeAdapter",
    "default_adapters",
    "qualify_runtimes",
    "qualification_report",
]
