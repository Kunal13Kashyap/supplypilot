from datetime import datetime
from enum import StrEnum


class UserRole(StrEnum):
    BUYER = "buyer"
    APPROVER = "approver"
    ADMIN = "admin"


class CaseStatus(StrEnum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTING = "executing"
    VALIDATED = "validated"
    RECOVERY = "recovery"
    ESCALATED = "escalated"
    FAILED = "failed"
    CLOSED = "closed"


class AgentRunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    AWAITING_APPROVAL = "awaiting_approval"
    EXECUTING = "executing"
    VALIDATING = "validating"
    RECOVERY = "recovery"
    COMPLETED = "completed"
    FAILED = "failed"
    ESCALATED = "escalated"


class DecisionType(StrEnum):
    ACCEPT = "ACCEPT"
    MODIFY = "MODIFY"
    REJECT = "REJECT"
    INVESTIGATE = "INVESTIGATE"


class RiskLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ActionType(StrEnum):
    NONE = "NONE"
    CREATE_PO = "CREATE_PO"
    MODIFY_PO = "MODIFY_PO"
    ACCEPT_PARTIAL = "ACCEPT_PARTIAL"
    CREATE_ALTERNATE_PO = "CREATE_ALTERNATE_PO"
    WAIT = "WAIT"
    ESCALATE = "ESCALATE"


class ApprovalStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    REANALYZE = "reanalyze"


class POStatus(StrEnum):
    DRAFT = "draft"
    OPEN = "open"
    PARTIAL = "partial"
    RECEIVED = "received"
    CANCELLED = "cancelled"


class ToolCallStatus(StrEnum):
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class ActionStatus(StrEnum):
    PENDING = "pending"
    EXECUTED = "executed"
    FAILED = "failed"


def utcnow() -> datetime:
    from datetime import UTC

    return datetime.now(UTC)
