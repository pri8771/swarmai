"""Capability profiles with provisional / qualified / stale / quarantine states."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from swarm.contracts.enums import RoutingState
from swarm.contracts.mission import SizeFeatures
from swarm.contracts.workspace import CapabilityProfile, EvalResult
from swarm.evals.wilson import wilson_lower_bound


@dataclass
class QualificationPolicy:
    """Versioned thresholds — not hardcoded model labels."""

    policy_version: str = "qual-policy-v1"
    provisional_min_distinct: int = 2
    qualified_low_risk_min_distinct: int = 30
    qualified_low_risk_wilson: float = 0.85
    qualified_medium_risk_min_distinct: int = 60
    qualified_medium_risk_wilson: float = 0.90
    # Starter archive is not statistically sufficient for qualified promotion.
    allow_qualified_on_starter_archive: bool = False


@dataclass
class ProfileStore:
    policy: QualificationPolicy = field(default_factory=QualificationPolicy)
    profiles: dict[str, CapabilityProfile] = field(default_factory=dict)
    results: list[EvalResult] = field(default_factory=list)
    # Track distinct cases separately from repeated runs.
    _distinct_cases: dict[str, set[str]] = field(default_factory=dict)
    _repeat_counts: dict[str, int] = field(default_factory=dict)
    _pass_distinct: dict[str, set[str]] = field(default_factory=dict)
    _policy_failures: dict[str, int] = field(default_factory=dict)
    _simulated: set[str] = field(default_factory=set)

    def profile_key(
        self,
        *,
        route_fingerprint: str,
        task_family: str,
        size_band: str,
        harness_version: str,
        prompt_version: str,
        tool_protocol: str,
        dataset_version: str,
        model_revision: str,
    ) -> str:
        return "|".join(
            [
                route_fingerprint,
                task_family,
                size_band,
                model_revision,
                harness_version,
                prompt_version,
                tool_protocol,
                dataset_version,
            ]
        )

    def record_result(
        self,
        result: EvalResult,
        *,
        task_family: str,
        size_band: str,
        size_features: SizeFeatures | None = None,
        harness_version: str = "1",
        prompt_version: str = "1",
        tool_protocol: str = "none",
        dataset_version: str = "starter-v1",
        model_revision: str = "unknown",
        simulated: bool = False,
    ) -> CapabilityProfile:
        key = self.profile_key(
            route_fingerprint=result.route_fingerprint,
            task_family=task_family,
            size_band=size_band,
            harness_version=harness_version,
            prompt_version=prompt_version,
            tool_protocol=tool_protocol,
            dataset_version=dataset_version,
            model_revision=model_revision,
        )
        if simulated:
            self._simulated.add(key)
            # Simulated scores never enter live profile tables.
            return CapabilityProfile(
                profile_key=key,
                route_fingerprint=result.route_fingerprint,
                task_family=task_family,
                size_features=size_features or SizeFeatures(),
                harness_version=harness_version,
                prompt_version=prompt_version,
                tool_protocol=tool_protocol,
                dataset_version=dataset_version,
                routing_state=RoutingState.UNASSESSED,
            )

        self.results.append(result)
        cases = self._distinct_cases.setdefault(key, set())
        if result.distinct_case_id in cases:
            self._repeat_counts[key] = self._repeat_counts.get(key, 0) + 1
        else:
            cases.add(result.distinct_case_id)
        if result.correctness:
            self._pass_distinct.setdefault(key, set()).add(result.distinct_case_id)
        if result.policy_violation:
            self._policy_failures[key] = self._policy_failures.get(key, 0) + 1

        distinct_n = len(cases)
        # Sample counts exclude repeat pseudo-replication for Wilson.
        pass_n = len(self._pass_distinct.get(key, set()))
        lower = wilson_lower_bound(pass_n, distinct_n)
        state = self._derive_state(key, distinct_n, lower)

        profile = CapabilityProfile(
            profile_key=key,
            route_fingerprint=result.route_fingerprint,
            task_family=task_family,
            size_features=size_features or SizeFeatures(),
            harness_version=harness_version,
            prompt_version=prompt_version,
            tool_protocol=tool_protocol,
            dataset_version=dataset_version,
            distinct_case_count=distinct_n,
            repeated_run_count=self._repeat_counts.get(key, 0),
            pass_count=pass_n,
            confidence_method="wilson",
            lower_bound=lower,
            routing_state=state,
            decoding_settings={"model_revision": model_revision},
        )
        self.profiles[key] = profile
        return profile

    def _derive_state(
        self, key: str, distinct_n: int, lower: float | None
    ) -> RoutingState:
        if self._policy_failures.get(key, 0) > 0:
            return RoutingState.QUARANTINED
        pol = self.policy
        if distinct_n < pol.provisional_min_distinct:
            return RoutingState.UNASSESSED
        # Starter archive cannot grant qualified without explicit policy override.
        if not pol.allow_qualified_on_starter_archive:
            if distinct_n >= pol.provisional_min_distinct:
                return RoutingState.PROVISIONAL
            return RoutingState.UNASSESSED
        if (
            lower is not None
            and distinct_n >= pol.qualified_medium_risk_min_distinct
            and lower >= pol.qualified_medium_risk_wilson
        ):
            return RoutingState.QUALIFIED
        if (
            lower is not None
            and distinct_n >= pol.qualified_low_risk_min_distinct
            and lower >= pol.qualified_low_risk_wilson
        ):
            return RoutingState.QUALIFIED
        return RoutingState.PROVISIONAL

    def mark_alias_stale(self, route_fingerprint: str) -> list[str]:
        stale: list[str] = []
        for key, profile in list(self.profiles.items()):
            if profile.route_fingerprint == route_fingerprint:
                updated = profile.model_copy(update={"routing_state": RoutingState.STALE})
                self.profiles[key] = updated
                stale.append(key)
        return stale

    def query(
        self,
        *,
        task_family: str | None = None,
        min_state: RoutingState | None = None,
    ) -> list[CapabilityProfile]:
        order = {
            RoutingState.UNASSESSED: 0,
            RoutingState.PROVISIONAL: 1,
            RoutingState.REVIEW_ONLY: 2,
            RoutingState.QUALIFIED: 3,
            RoutingState.STALE: -1,
            RoutingState.QUARANTINED: -2,
        }
        out: list[CapabilityProfile] = []
        for p in self.profiles.values():
            if task_family and p.task_family != task_family:
                continue
            if min_state and order.get(p.routing_state, 0) < order.get(min_state, 0):
                continue
            if p.routing_state in {RoutingState.QUARANTINED, RoutingState.STALE}:
                if min_state in {RoutingState.QUALIFIED, RoutingState.PROVISIONAL}:
                    continue
            out.append(p)
        return out

    def summary(self) -> dict[str, Any]:
        return {
            "policy_version": self.policy.policy_version,
            "profile_count": len(self.profiles),
            "result_count": len(self.results),
            "simulated_excluded": len(self._simulated),
            "by_state": {
                s.value: sum(1 for p in self.profiles.values() if p.routing_state == s)
                for s in RoutingState
            },
        }
