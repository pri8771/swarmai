"""Transport-independent worker protocol boundary (V2A-004).

HTTP / queue / DBOS adapters implement :class:`WorkerTransport`. Tests and local
loops use :class:`InProcessWorkerTransport`.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from swarm.db.lease_fencing import AcceptedResult
from swarm.db.models import WorkerLeaseRow
from swarm.workers.envelopes import (
    CancelLeaseRequest,
    CancelLeaseResponse,
    CapabilityAdvertisement,
    ClaimDispatchRequest,
    ClaimDispatchResponse,
    DrainRequest,
    DrainResponse,
    EnrollmentRequest,
    EnrollmentResponse,
    ReconnectRequest,
    ReconnectResponse,
    RenewLeaseRequest,
    RenewLeaseResponse,
    ResultSubmitRequest,
    ResultSubmitResponse,
    WorkerHeartbeatRequest,
    WorkerHeartbeatResponse,
)
from swarm.workers.service import DurableWorkerService


@runtime_checkable
class WorkerTransport(Protocol):
    def enroll(self, request: EnrollmentRequest) -> EnrollmentResponse: ...

    def heartbeat(self, request: WorkerHeartbeatRequest) -> WorkerHeartbeatResponse: ...

    def advertise(self, request: CapabilityAdvertisement) -> WorkerLeaseRow: ...

    def claim(self, request: ClaimDispatchRequest) -> ClaimDispatchResponse: ...

    def renew(self, request: RenewLeaseRequest) -> RenewLeaseResponse: ...

    def submit_result(self, request: ResultSubmitRequest) -> ResultSubmitResponse: ...

    def drain(self, request: DrainRequest) -> DrainResponse: ...

    def cancel_lease(self, request: CancelLeaseRequest) -> CancelLeaseResponse: ...

    def reconnect(self, request: ReconnectRequest) -> ReconnectResponse: ...

    def accept_result(self, *, result_id: str) -> AcceptedResult: ...


class InProcessWorkerTransport:
    """Direct in-process adapter — no network; PostgreSQL still authoritative."""

    def __init__(self, service: DurableWorkerService) -> None:
        self.service = service

    def enroll(self, request: EnrollmentRequest) -> EnrollmentResponse:
        return self.service.enroll(request)

    def heartbeat(self, request: WorkerHeartbeatRequest) -> WorkerHeartbeatResponse:
        return self.service.heartbeat(request)

    def advertise(self, request: CapabilityAdvertisement) -> WorkerLeaseRow:
        return self.service.advertise(request)

    def claim(self, request: ClaimDispatchRequest) -> ClaimDispatchResponse:
        return self.service.claim(request)

    def renew(self, request: RenewLeaseRequest) -> RenewLeaseResponse:
        return self.service.renew(request)

    def submit_result(self, request: ResultSubmitRequest) -> ResultSubmitResponse:
        return self.service.submit_result(request)

    def drain(self, request: DrainRequest) -> DrainResponse:
        return self.service.drain(request)

    def cancel_lease(self, request: CancelLeaseRequest) -> CancelLeaseResponse:
        return self.service.cancel_lease(request)

    def reconnect(self, request: ReconnectRequest) -> ReconnectResponse:
        return self.service.reconnect(request)

    def accept_result(self, *, result_id: str) -> AcceptedResult:
        return self.service.accept_result(result_id=result_id)
