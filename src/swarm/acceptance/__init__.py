"""V2.0 acceptance campaign — freeze, harness, matrices.

Lane F: freeze scenarios and pass criteria before relying on them.
Never mark versions accepted from harness output. Never invent LiveGrant.
"""

from swarm.acceptance.freeze import (
    FREEZE_PATH,
    AcceptanceFreeze,
    FreezeIntegrityError,
    load_freeze,
    verify_freeze_integrity,
)
from swarm.acceptance.harness import (
    CampaignReport,
    ScenarioResult,
    run_acceptance_campaign,
)
from swarm.acceptance.matrix import build_version_matrices

__all__ = [
    "FREEZE_PATH",
    "AcceptanceFreeze",
    "CampaignReport",
    "FreezeIntegrityError",
    "ScenarioResult",
    "build_version_matrices",
    "load_freeze",
    "run_acceptance_campaign",
    "verify_freeze_integrity",
]
