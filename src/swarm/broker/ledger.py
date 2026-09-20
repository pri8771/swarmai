"""Atomic multi-bucket quota ledger with deterministic lock ordering."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from swarm.broker.errors import QuotaExhaustedError, UnknownChargeDeniedError
from swarm.contracts.common import utc_now
from swarm.contracts.enums import QuotaDimension, WindowType
from swarm.contracts.provider import BucketAmount, QuotaBucket

Clock = Callable[[], datetime]


@dataclass
class LedgerConfig:
    """Mission envelopes and probe policy."""

    planning_review_reserve: int = 2
    planning_reserve_bucket_id: str = "qb_control_reserve"
    benchmark_envelope: int = 10
    benchmark_bucket_id: str = "qb_benchmark"
    allow_unknown_probe: bool = False
    verified_no_charge_routes: set[str] = field(default_factory=set)
    default_request_amount: int = 1
    token_safety_margin: int = 0


@dataclass
class _LiveBucket:
    model: QuotaBucket
    reserved: int = 0
    settled: int = 0
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


class QuotaLedger:
    """In-memory atomic ledger; locks buckets in sorted bucket_id order."""

    def __init__(
        self,
        buckets: list[QuotaBucket] | None = None,
        *,
        config: LedgerConfig | None = None,
        clock: Clock | None = None,
    ) -> None:
        self.config = config or LedgerConfig()
        self._clock: Clock = clock or utc_now
        self._buckets: dict[str, _LiveBucket] = {}
        self._admission = asyncio.Lock()
        self._settled_keys: set[str] = set()
        for bucket in buckets or []:
            self.register(bucket)

    def register(self, bucket: QuotaBucket) -> None:
        self._buckets[bucket.bucket_id] = _LiveBucket(model=bucket.model_copy(deep=True))

    def get(self, bucket_id: str) -> QuotaBucket | None:
        live = self._buckets.get(bucket_id)
        return None if live is None else live.model.model_copy(deep=True)

    def snapshot(self) -> list[QuotaBucket]:
        return [lb.model.model_copy(deep=True) for lb in self._buckets.values()]

    def _effective_remaining(self, live: _LiveBucket, now: datetime) -> int | None:
        bucket = live.model
        self._maybe_reset(live, now)
        if bucket.remaining is None:
            return None
        return max(0, bucket.remaining - live.reserved)

    def _maybe_reset(self, live: _LiveBucket, now: datetime) -> None:
        bucket = live.model
        if bucket.reset_at is None:
            return
        reset_at = bucket.reset_at
        if reset_at.tzinfo is None:
            reset_at = reset_at.replace(tzinfo=UTC)
        if now < reset_at:
            return
        if bucket.window_type == WindowType.FIXED and bucket.limit is not None:
            bucket.remaining = bucket.limit
            live.reserved = 0
            # Advance fixed window by one period if a previous period length is known.
            period = bucket.reset_at - (bucket.observed_at if bucket.observed_at else now)
            if period.total_seconds() <= 0:
                period = timedelta(days=1)
            bucket.reset_at = reset_at + abs(period)
            bucket.observed_at = now
            bucket.version += 1
        elif bucket.window_type == WindowType.ROLLING and bucket.limit is not None:
            bucket.remaining = bucket.limit
            live.reserved = 0
            bucket.reset_at = now + timedelta(hours=1)
            bucket.observed_at = now
            bucket.version += 1

    def estimate_amounts(
        self,
        *,
        bucket_ids: list[str],
        estimated_input_tokens: int | None,
        max_output_tokens: int | None,
        purpose: str,
    ) -> list[BucketAmount]:
        amounts: list[BucketAmount] = []
        seen: set[str] = set()
        for bucket_id in bucket_ids:
            if bucket_id in seen:
                continue
            seen.add(bucket_id)
            live = self._buckets.get(bucket_id)
            if live is None:
                continue
            dim = live.model.dimension
            if dim == QuotaDimension.REQUESTS or dim == QuotaDimension.CONCURRENCY:
                amounts.append(
                    BucketAmount(
                        bucket_id=bucket_id,
                        dimension=dim,
                        amount=self.config.default_request_amount,
                    )
                )
            elif dim in {
                QuotaDimension.INPUT_TOKENS,
                QuotaDimension.TOTAL_TOKENS,
                QuotaDimension.UNCACHED_TOKENS,
            }:
                base = estimated_input_tokens or 0
                out = max_output_tokens or 0
                need = base + out + self.config.token_safety_margin
                amounts.append(
                    BucketAmount(bucket_id=bucket_id, dimension=dim, amount=max(1, need))
                )
            elif dim == QuotaDimension.OUTPUT_TOKENS:
                need = (max_output_tokens or 0) + self.config.token_safety_margin
                amounts.append(
                    BucketAmount(bucket_id=bucket_id, dimension=dim, amount=max(1, need))
                )
            elif dim in {QuotaDimension.CREDIT, QuotaDimension.NEURONS}:
                amounts.append(BucketAmount(bucket_id=bucket_id, dimension=dim, amount=1))
            else:
                amounts.append(
                    BucketAmount(
                        bucket_id=bucket_id,
                        dimension=dim,
                        amount=self.config.default_request_amount,
                    )
                )
        if purpose == "benchmark" and self.config.benchmark_bucket_id in self._buckets:
            bid = self.config.benchmark_bucket_id
            if bid not in seen:
                amounts.append(
                    BucketAmount(
                        bucket_id=bid,
                        dimension=self._buckets[bid].model.dimension,
                        amount=1,
                    )
                )
        return amounts

    async def reserve(
        self,
        amounts: list[BucketAmount],
        *,
        route_id: str,
        purpose: str,
        probe: bool = False,
    ) -> list[BucketAmount]:
        """Atomically reserve across buckets. Never oversubscribes under contention."""
        if not amounts:
            raise QuotaExhaustedError("no quota buckets to reserve")

        ordered = sorted(amounts, key=lambda a: a.bucket_id)
        # Deduplicate BYOK/direct shared buckets: same bucket_id reserved once.
        merged: dict[str, BucketAmount] = {}
        for amt in ordered:
            if amt.bucket_id in merged:
                prev = merged[amt.bucket_id]
                merged[amt.bucket_id] = BucketAmount(
                    bucket_id=amt.bucket_id,
                    dimension=amt.dimension,
                    amount=prev.amount + amt.amount,
                )
            else:
                merged[amt.bucket_id] = amt
        ordered = sorted(merged.values(), key=lambda a: a.bucket_id)

        async with self._admission:
            now = self._clock()
            # Preflight under admission lock, then take per-bucket locks in order.
            locks: list[asyncio.Lock] = []
            for amt in ordered:
                live = self._buckets.get(amt.bucket_id)
                if live is None:
                    raise QuotaExhaustedError(f"unknown_bucket:{amt.bucket_id}")
                locks.append(live.lock)

            for lock in locks:
                await lock.acquire()
            try:
                # Protected control reserve: mission purposes cannot drain it.
                if purpose not in {"planning", "review", "control"}:
                    control = self._buckets.get(self.config.planning_reserve_bucket_id)
                    if control is not None and control.model.remaining is not None:
                        # Ensure control bucket still has its reserved floor after this admit.
                        # (Only applies when the control bucket is also in the amounts.)
                        pass

                for amt in ordered:
                    live = self._buckets[amt.bucket_id]
                    effective = self._effective_remaining(live, now)
                    if effective is None:
                        # Unknown remaining: only bounded probe on verified no-charge.
                        if not (
                            probe
                            and self.config.allow_unknown_probe
                            and route_id in self.config.verified_no_charge_routes
                        ):
                            raise UnknownChargeDeniedError(
                                f"unknown_quota:{amt.bucket_id}:{amt.dimension.value}"
                            )
                        continue
                    if effective < amt.amount:
                        # Zero remaining vs insufficient — same deny, distinct message.
                        if effective == 0:
                            raise QuotaExhaustedError(
                                f"zero_remaining:{amt.bucket_id}:{amt.dimension.value}"
                            )
                        raise QuotaExhaustedError(
                            f"insufficient:{amt.bucket_id}:{amt.dimension.value}:"
                            f"need={amt.amount}:have={effective}"
                        )
                    # Protect planning/review reserve on the shared control bucket.
                    if (
                        amt.bucket_id == self.config.planning_reserve_bucket_id
                        and purpose not in {"planning", "review", "control"}
                    ):
                        floor = self.config.planning_review_reserve
                        if effective - amt.amount < floor:
                            raise QuotaExhaustedError(
                                f"control_reserve_protected:{amt.bucket_id}:floor={floor}"
                            )

                # Commit reservations
                for amt in ordered:
                    live = self._buckets[amt.bucket_id]
                    if live.model.remaining is not None:
                        live.reserved += amt.amount
                return ordered
            finally:
                for lock in reversed(locks):
                    lock.release()

    async def release(self, amounts: list[BucketAmount]) -> None:
        ordered = sorted(amounts, key=lambda a: a.bucket_id)
        async with self._admission:
            locks = []
            for amt in ordered:
                live = self._buckets.get(amt.bucket_id)
                if live is None:
                    continue
                locks.append(live.lock)
            for lock in locks:
                await lock.acquire()
            try:
                for amt in ordered:
                    live = self._buckets.get(amt.bucket_id)
                    if live is None:
                        continue
                    live.reserved = max(0, live.reserved - amt.amount)
            finally:
                for lock in reversed(locks):
                    lock.release()

    async def settle(
        self,
        amounts: list[BucketAmount],
        *,
        settlement_key: str,
        actual_usage: dict[QuotaDimension, int] | None = None,
    ) -> None:
        if settlement_key in self._settled_keys:
            from swarm.broker.errors import DuplicateSettlementError

            raise DuplicateSettlementError(settlement_key)
        ordered = sorted(amounts, key=lambda a: a.bucket_id)
        async with self._admission:
            locks = []
            for amt in ordered:
                live = self._buckets.get(amt.bucket_id)
                if live is None:
                    continue
                locks.append(live.lock)
            for lock in locks:
                await lock.acquire()
            try:
                for amt in ordered:
                    live = self._buckets.get(amt.bucket_id)
                    if live is None:
                        continue
                    charge = amt.amount
                    if actual_usage and amt.dimension in actual_usage:
                        # Refund over-reservation only; never invent cache credits.
                        observed = actual_usage[amt.dimension]
                        charge = min(amt.amount, max(0, observed))
                    if live.model.remaining is not None:
                        live.model.remaining = max(0, live.model.remaining - charge)
                    live.reserved = max(0, live.reserved - amt.amount)
                    live.settled += charge
                    live.model.version += 1
                    live.model.observed_at = self._clock()
                self._settled_keys.add(settlement_key)
            finally:
                for lock in reversed(locks):
                    lock.release()

    def bottleneck(self, amounts: list[BucketAmount]) -> dict[str, object] | None:
        now = self._clock()
        worst: dict[str, object] | None = None
        worst_ratio = 2.0
        for amt in amounts:
            live = self._buckets.get(amt.bucket_id)
            if live is None:
                return {
                    "bucket_id": amt.bucket_id,
                    "dimension": amt.dimension.value,
                    "reason": "missing_bucket",
                }
            effective = self._effective_remaining(live, now)
            if effective is None:
                return {
                    "bucket_id": amt.bucket_id,
                    "dimension": amt.dimension.value,
                    "reason": "unknown",
                    "remaining": None,
                }
            if amt.amount <= 0:
                continue
            ratio = effective / amt.amount
            if ratio < worst_ratio:
                worst_ratio = ratio
                worst = {
                    "bucket_id": amt.bucket_id,
                    "dimension": amt.dimension.value,
                    "remaining": effective,
                    "requested": amt.amount,
                    "reason": "zero" if effective == 0 else "tight",
                }
        return worst
