"""
Data models for Trust Center audit system.

Provides data structures for tracking AWS API calls,
audit sessions, and compliance reports.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class APICategory(Enum):
    """
    AWS API operation categories.

    Used to classify operations as read-only, write, delete, or admin.
    """

    READ = "read"  # Describe*, Get*, List*, Head*
    WRITE = "write"  # Create*, Put*, Update*, Modify*
    DELETE = "delete"  # Delete*, Remove*, Terminate*
    ADMIN = "admin"  # IAM policy changes, Organizations
    UNKNOWN = "unknown"  # Unclassified operations

    def __str__(self) -> str:
        return self.value


class AuditEventType(Enum):
    """Types of audit events."""

    API_CALL = "api_call"
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    ERROR = "error"

    def __str__(self) -> str:
        return self.value


@dataclass
class APICallRecord:
    """
    Record of a single AWS API call.

    Captures all relevant information about an API operation
    for audit and compliance purposes.
    """

    # Timing
    timestamp: datetime
    duration_ms: int

    # AWS API details
    service: str  # e.g., "ec2", "rds", "iam"
    operation: str  # e.g., "DescribeInstances"
    region: str  # e.g., "ap-southeast-2"

    # Request tracking
    request_id: str  # AWS request ID or generated UUID

    # Classification
    category: APICategory

    # Response info
    http_status: int = 200
    error_code: str | None = None
    error_message: str | None = None

    # Request parameters (sanitized - sensitive data redacted)
    parameters: dict[str, Any] = field(default_factory=dict)

    # Additional context
    user_agent: str | None = None
    account_id: str | None = None

    @property
    def is_read_only(self) -> bool:
        """Check if this was a read-only operation."""
        return self.category == APICategory.READ

    @property
    def is_success(self) -> bool:
        """Check if the API call succeeded."""
        return 200 <= self.http_status < 300 and self.error_code is None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "duration_ms": self.duration_ms,
            "service": self.service,
            "operation": self.operation,
            "region": self.region,
            "request_id": self.request_id,
            "category": self.category.value,
            "http_status": self.http_status,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "is_read_only": self.is_read_only,
            "is_success": self.is_success,
            "account_id": self.account_id,
            "parameters": self.parameters if self.parameters else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> APICallRecord:
        """Create from dictionary."""
        return cls(
            timestamp=datetime.fromisoformat(data["timestamp"]),
            duration_ms=data["duration_ms"],
            service=data["service"],
            operation=data["operation"],
            region=data["region"],
            request_id=data["request_id"],
            category=APICategory(data["category"]),
            http_status=data.get("http_status", 200),
            error_code=data.get("error_code"),
            error_message=data.get("error_message"),
            parameters=data.get("parameters", {}),
            account_id=data.get("account_id"),
        )


@dataclass
class AuditSession:
    """
    An audit session representing a unit of work.

    A session groups related API calls together, such as
    all calls made during a single scan operation.
    """

    session_id: str
    session_name: str | None = None

    # Timing
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: datetime | None = None

    # Statistics (updated incrementally)
    total_calls: int = 0
    read_calls: int = 0
    write_calls: int = 0
    delete_calls: int = 0
    admin_calls: int = 0
    unknown_calls: int = 0
    error_calls: int = 0

    # API call records
    records: list[APICallRecord] = field(default_factory=list)

    # Session metadata (e.g., environment, user, scan type)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_read_only(self) -> bool:
        """Check if all operations in this session were read-only."""
        return (
            self.write_calls == 0 and self.delete_calls == 0 and self.admin_calls == 0
        )

    @property
    def duration_seconds(self) -> float | None:
        """Get session duration in seconds."""
        if self.end_time is None:
            return None
        return (self.end_time - self.start_time).total_seconds()

    @property
    def read_only_percentage(self) -> float:
        """Get percentage of read-only calls."""
        if self.total_calls == 0:
            return 100.0
        return (self.read_calls / self.total_calls) * 100

    def add_record(self, record: APICallRecord) -> None:
        """Add an API call record and update statistics."""
        self.records.append(record)
        self.total_calls += 1

        if record.category == APICategory.READ:
            self.read_calls += 1
        elif record.category == APICategory.WRITE:
            self.write_calls += 1
        elif record.category == APICategory.DELETE:
            self.delete_calls += 1
        elif record.category == APICategory.ADMIN:
            self.admin_calls += 1
        else:
            self.unknown_calls += 1

        if not record.is_success:
            self.error_calls += 1

    def close(self) -> None:
        """Mark session as complete."""
        self.end_time = datetime.utcnow()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "session_id": self.session_id,
            "session_name": self.session_name,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration_seconds,
            "total_calls": self.total_calls,
            "read_calls": self.read_calls,
            "write_calls": self.write_calls,
            "delete_calls": self.delete_calls,
            "admin_calls": self.admin_calls,
            "unknown_calls": self.unknown_calls,
            "error_calls": self.error_calls,
            "is_read_only": self.is_read_only,
            "read_only_percentage": round(self.read_only_percentage, 2),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AuditSession:
        """Create from dictionary."""
        session = cls(
            session_id=data["session_id"],
            session_name=data.get("session_name"),
            start_time=datetime.fromisoformat(data["start_time"]),
            end_time=(
                datetime.fromisoformat(data["end_time"])
                if data.get("end_time")
                else None
            ),
            total_calls=data.get("total_calls", 0),
            read_calls=data.get("read_calls", 0),
            write_calls=data.get("write_calls", 0),
            delete_calls=data.get("delete_calls", 0),
            admin_calls=data.get("admin_calls", 0),
            unknown_calls=data.get("unknown_calls", 0),
            error_calls=data.get("error_calls", 0),
            metadata=data.get("metadata", {}),
        )
        return session


@dataclass
class TrustCenterReport:
    """
    Comprehensive Trust Center audit report.

    Aggregates data from multiple sessions for compliance reporting.
    """

    # Report metadata
    report_id: str
    generated_at: datetime
    report_period_start: datetime
    report_period_end: datetime

    # Tool information
    tool_name: str
    tool_version: str

    # Aggregate statistics
    total_sessions: int
    total_api_calls: int
    total_duration_seconds: float

    # Read-only analysis
    read_only_percentage: float
    is_fully_read_only: bool

    # Breakdown by category
    calls_by_category: dict[str, int]

    # Service usage
    unique_services: list[str]
    calls_by_service: dict[str, int]

    # Operation details
    unique_operations: list[str]
    write_operations: list[str]  # Non-empty if not fully read-only

    # Error summary
    total_errors: int
    error_rate_percentage: float

    # Compliance statement
    compliance_statement: str

    # Sessions included
    session_summaries: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "report_id": self.report_id,
            "generated_at": self.generated_at.isoformat(),
            "report_period": {
                "start": self.report_period_start.isoformat(),
                "end": self.report_period_end.isoformat(),
            },
            "tool": {
                "name": self.tool_name,
                "version": self.tool_version,
            },
            "summary": {
                "total_sessions": self.total_sessions,
                "total_api_calls": self.total_api_calls,
                "total_duration_seconds": round(self.total_duration_seconds, 2),
                "read_only_percentage": round(self.read_only_percentage, 2),
                "is_fully_read_only": self.is_fully_read_only,
                "total_errors": self.total_errors,
                "error_rate_percentage": round(self.error_rate_percentage, 2),
            },
            "calls_by_category": self.calls_by_category,
            "calls_by_service": self.calls_by_service,
            "unique_services": self.unique_services,
            "unique_operations": self.unique_operations,
            "write_operations": self.write_operations,
            "compliance_statement": self.compliance_statement,
            "sessions": self.session_summaries,
        }
