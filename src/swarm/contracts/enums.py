"""Shared enumerations for SwarmAI contracts."""

from enum import StrEnum


class MissionStatus(StrEnum):
    DRAFT = "draft"
    PLANNING = "planning"
    RUNNING = "running"
    WAITING_CAPACITY = "waiting_capacity"
    WAITING_INPUT = "waiting_input"
    WAITING_APPROVAL = "waiting_approval"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskStatus(StrEnum):
    PROPOSED = "proposed"
    READY = "ready"
    LEASED = "leased"
    RUNNING = "running"
    WAITING_CHILDREN = "waiting_children"
    WAITING_CAPACITY = "waiting_capacity"
    WAITING_APPROVAL = "waiting_approval"
    VERIFYING = "verifying"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SUPERSEDED = "superseded"


class AttemptStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    UNKNOWN = "unknown"


class GraphOperation(StrEnum):
    SPAWN = "spawn"
    SPLIT = "split"
    REASSIGN = "reassign"
    MERGE = "merge"
    CHALLENGE = "challenge"
    REVISE = "revise"
    STOP = "stop"
    REQUEST_HELP = "request_help"
    SUBMIT_RESULT = "submit_result"
    REVISE_DEPENDENCY = "revise_dependency"


class AccountStatus(StrEnum):
    UNKNOWN = "unknown"
    CATALOGED = "cataloged"
    CONFIGURED = "configured"
    AUTHENTICATED = "authenticated"
    DISABLED = "disabled"
    RETIRED = "retired"


class PurposeEligibility(StrEnum):
    PROTOTYPE = "prototype"
    INTERNAL = "internal"
    PRODUCTION = "production"
    UNKNOWN = "unknown"


class BillingMode(StrEnum):
    FREE = "free"
    TRIAL = "trial"
    PAID = "paid"
    UNKNOWN = "unknown"
    NONE = "none"


class AvailabilityStatus(StrEnum):
    UNKNOWN = "unknown"
    AVAILABLE = "available"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    DISABLED = "disabled"
    RETIRED = "retired"


class QuotaDimension(StrEnum):
    REQUESTS = "requests"
    INPUT_TOKENS = "input_tokens"
    OUTPUT_TOKENS = "output_tokens"
    TOTAL_TOKENS = "total_tokens"
    UNCACHED_TOKENS = "uncached_tokens"
    NEURONS = "neurons"
    CREDIT = "credit"
    CONCURRENCY = "concurrency"


class WindowType(StrEnum):
    ROLLING = "rolling"
    FIXED = "fixed"
    LIFETIME = "lifetime"
    UNKNOWN = "unknown"


class ReservationState(StrEnum):
    OPEN = "open"
    COMMITTED = "committed"
    RELEASED = "released"
    EXPIRED = "expired"
    UNKNOWN = "unknown"


class ReservationPhase(StrEnum):
    RESERVED = "reserved"
    SENDING = "sending"
    SENT = "sent"
    UNKNOWN = "unknown"
    SETTLED = "settled"


class ErrorClass(StrEnum):
    RATE_LIMIT = "rate_limit"
    AUTHENTICATION = "authentication"
    QUOTA_EXHAUSTED = "quota_exhausted"
    TRANSIENT = "transient"
    UNSUPPORTED_CAPABILITY = "unsupported_capability"
    INVALID_REQUEST = "invalid_request"
    POLICY_DENIED = "policy_denied"
    PARTIAL_STREAM = "partial_stream"
    UNKNOWN_OUTCOME = "unknown_outcome"


class SettlementState(StrEnum):
    PENDING = "pending"
    SETTLED = "settled"
    UNKNOWN = "unknown"
    VOID = "void"


class RoutingState(StrEnum):
    UNASSESSED = "unassessed"
    PROVISIONAL = "provisional"
    QUALIFIED = "qualified"
    REVIEW_ONLY = "review_only"
    QUARANTINED = "quarantined"
    STALE = "stale"


class FindingStatus(StrEnum):
    HYPOTHESIS = "hypothesis"
    CORROBORATED = "corroborated"
    DISPUTED = "disputed"
    ACCEPTED = "accepted"
    SUPERSEDED = "superseded"


class WorkerStatus(StrEnum):
    ONLINE = "online"
    DRAINING = "draining"
    OFFLINE = "offline"
    QUARANTINED = "quarantined"


class ActionOutcome(StrEnum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    UNKNOWN = "unknown"


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Modality(StrEnum):
    TEXT = "text"
    CODE = "code"
    IMAGE = "image"
    AUDIO = "audio"
    MULTIMODAL = "multimodal"
    OTHER = "other"
