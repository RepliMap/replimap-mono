"""
Trust Center - Core audit and compliance system for RepliMap.

Provides centralized audit logging for all AWS API calls,
enabling compliance reporting and enterprise security reviews.

Features:
- Automatic API call capture via boto3 hooks
- Session-based grouping of operations
- Real-time statistics
- Multi-format export (JSON, CSV)
- Thread-safe operations
- Compliance statement generation

Usage:
    from replimap.audit import TrustCenter

    tc = TrustCenter.get_instance()
    tc.enable(boto3_session)

    with tc.session("scan_production"):
        scanner.scan()

    report = tc.generate_report()
    print(report.compliance_statement)
"""

from __future__ import annotations

import json
import logging
import threading
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any, Generator

from .classifier import classifier
from .hooks import AuditHooks
from .models import APICallRecord, APICategory, AuditSession, TrustCenterReport

if TYPE_CHECKING:
    import boto3

logger = logging.getLogger(__name__)


class TrustCenter:
    """
    Centralized audit and compliance system for RepliMap.

    Thread-safe singleton that manages audit sessions, records API calls,
    and generates compliance reports.

    Designed to satisfy enterprise security requirements, particularly
    for Australian banks (CBA, Westpac, NAB, ANZ) that require:
    - Agentless operation proof
    - Read-Only operations verification
    - API call transparency
    """

    # Singleton instance
    _instance: TrustCenter | None = None
    _lock = threading.Lock()

    # Version info
    VERSION = "1.0.0"
    TOOL_NAME = "RepliMap"

    # Default storage location
    DEFAULT_STORAGE_DIR = Path(".replimap/audit")

    @classmethod
    def get_instance(cls) -> TrustCenter:
        """Get or create the singleton instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton instance (for testing)."""
        with cls._lock:
            if cls._instance is not None:
                cls._instance.disable()
            cls._instance = None

    def __init__(self) -> None:
        """Initialize Trust Center (use get_instance() instead)."""
        self._sessions: dict[str, AuditSession] = {}
        self._current_session_id: str | None = None
        self._enabled = False
        self._hooks: AuditHooks | None = None
        self._registered_boto_sessions: list[Any] = []

        # Thread safety
        self._session_lock = threading.Lock()

        # Storage
        self._storage_dir = self.DEFAULT_STORAGE_DIR
        self._storage_dir.mkdir(parents=True, exist_ok=True)

        # Global statistics
        self._total_calls = 0
        self._total_read_calls = 0
        self._total_write_calls = 0
        self._total_delete_calls = 0
        self._total_admin_calls = 0

    # =========================================================================
    # Enable/Disable
    # =========================================================================

    def enable(
        self,
        boto3_session: boto3.Session,
        capture_params: bool = False,
    ) -> None:
        """
        Enable audit logging for a boto3 session.

        Args:
            boto3_session: boto3 Session to audit
            capture_params: If True, capture sanitized request parameters
        """
        if self._enabled and boto3_session in self._registered_boto_sessions:
            return

        # Create hooks if needed
        if self._hooks is None:
            self._hooks = AuditHooks(
                on_call=self._on_api_call,
                capture_params=capture_params,
            )

        # Register hooks
        self._hooks.register(boto3_session)
        self._registered_boto_sessions.append(boto3_session)
        self._enabled = True

        logger.info("Trust Center audit enabled")

    def disable(self) -> None:
        """Disable audit logging and unregister all hooks."""
        if self._hooks:
            for session in self._registered_boto_sessions:
                self._hooks.unregister(session)

        self._registered_boto_sessions.clear()
        self._enabled = False

        logger.info("Trust Center audit disabled")

    @property
    def is_enabled(self) -> bool:
        """Check if auditing is enabled."""
        return self._enabled

    # =========================================================================
    # Session Management
    # =========================================================================

    @contextmanager
    def session(
        self,
        name: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Generator[str, None, None]:
        """
        Create an audit session context.

        Args:
            name: Human-readable session name
            metadata: Additional metadata to attach

        Yields:
            Session ID

        Example:
            with trust_center.session("production_scan") as session_id:
                scanner.scan_all()
        """
        session_id = str(uuid.uuid4())[:8]

        audit_session = AuditSession(
            session_id=session_id,
            session_name=name,
            start_time=datetime.utcnow(),
            metadata=metadata or {},
        )

        with self._session_lock:
            self._sessions[session_id] = audit_session
            previous_session = self._current_session_id
            self._current_session_id = session_id

        logger.debug(f"Started audit session: {session_id} ({name})")

        try:
            yield session_id
        finally:
            with self._session_lock:
                audit_session.close()
                self._current_session_id = previous_session

            # Auto-save session
            self._save_session(session_id)
            logger.debug(f"Closed audit session: {session_id}")

    def get_session(self, session_id: str) -> AuditSession | None:
        """Get a session by ID."""
        return self._sessions.get(session_id)

    def get_current_session(self) -> AuditSession | None:
        """Get the current active session."""
        if self._current_session_id:
            return self._sessions.get(self._current_session_id)
        return None

    def list_sessions(
        self,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> list[AuditSession]:
        """
        List sessions within a time range.

        Args:
            start_time: Filter sessions starting after this time
            end_time: Filter sessions ending before this time
        """
        sessions = []

        for session in self._sessions.values():
            if start_time and session.start_time < start_time:
                continue
            if end_time and session.end_time and session.end_time > end_time:
                continue
            sessions.append(session)

        return sorted(sessions, key=lambda s: s.start_time, reverse=True)

    # =========================================================================
    # Recording
    # =========================================================================

    def _on_api_call(self, record: APICallRecord) -> None:
        """Callback for API call records from hooks."""
        with self._session_lock:
            # Update global stats
            self._total_calls += 1
            if record.category == APICategory.READ:
                self._total_read_calls += 1
            elif record.category == APICategory.WRITE:
                self._total_write_calls += 1
            elif record.category == APICategory.DELETE:
                self._total_delete_calls += 1
            elif record.category == APICategory.ADMIN:
                self._total_admin_calls += 1

            # Add to current session
            if self._current_session_id:
                session = self._sessions.get(self._current_session_id)
                if session:
                    session.add_record(record)

    def record_manual(
        self,
        service: str,
        operation: str,
        region: str,
        duration_ms: int = 0,
        http_status: int = 200,
        error_code: str | None = None,
        account_id: str | None = None,
    ) -> None:
        """
        Manually record an API call (for operations not using boto3).

        Args:
            service: AWS service name
            operation: Operation name
            region: AWS region
            duration_ms: Call duration in milliseconds
            http_status: HTTP status code
            error_code: Error code if failed
            account_id: AWS account ID
        """
        record = APICallRecord(
            timestamp=datetime.utcnow(),
            duration_ms=duration_ms,
            service=service,
            operation=operation,
            region=region,
            request_id=str(uuid.uuid4())[:8],
            category=classifier.classify(operation),
            http_status=http_status,
            error_code=error_code,
            account_id=account_id,
        )
        self._on_api_call(record)

    # =========================================================================
    # Reporting
    # =========================================================================

    def generate_report(
        self,
        period_start: datetime | None = None,
        period_end: datetime | None = None,
        session_ids: list[str] | None = None,
    ) -> TrustCenterReport:
        """
        Generate a comprehensive audit report.

        Args:
            period_start: Start of reporting period
            period_end: End of reporting period
            session_ids: Specific sessions to include (None = all)

        Returns:
            TrustCenterReport instance
        """
        period_end = period_end or datetime.utcnow()
        period_start = period_start or (period_end - timedelta(days=30))

        # Collect sessions
        if session_ids:
            sessions = [
                self._sessions[sid]
                for sid in session_ids
                if sid in self._sessions
            ]
        else:
            sessions = self.list_sessions(period_start, period_end)

        # Aggregate statistics
        total_calls = 0
        total_duration = 0.0
        calls_by_category: dict[str, int] = {}
        calls_by_service: dict[str, int] = {}
        all_operations: set[str] = set()
        write_operations: set[str] = set()
        total_errors = 0

        for session in sessions:
            if session.duration_seconds:
                total_duration += session.duration_seconds

            for record in session.records:
                total_calls += 1

                # By category
                cat = record.category.value
                calls_by_category[cat] = calls_by_category.get(cat, 0) + 1

                # By service
                calls_by_service[record.service] = (
                    calls_by_service.get(record.service, 0) + 1
                )

                # Operations
                all_operations.add(record.operation)
                if not record.is_read_only:
                    write_operations.add(record.operation)

                # Errors
                if not record.is_success:
                    total_errors += 1

        # Calculate percentages
        read_calls = calls_by_category.get("read", 0)
        read_only_pct = (read_calls / total_calls * 100) if total_calls > 0 else 100.0
        error_rate = (total_errors / total_calls * 100) if total_calls > 0 else 0.0

        # Compliance statement
        if read_only_pct == 100.0:
            compliance = (
                "COMPLIANT: This tool performed 100% READ-ONLY operations during "
                "the audit period. No AWS resources were created, modified, or deleted. "
                "This confirms the tool's non-invasive, agentless architecture."
            )
        else:
            compliance = (
                f"WARNING: {100 - read_only_pct:.1f}% of operations were WRITE/DELETE. "
                f"Non-read operations: {', '.join(sorted(write_operations))}. "
                "Review these operations for compliance requirements."
            )

        return TrustCenterReport(
            report_id=str(uuid.uuid4())[:8],
            generated_at=datetime.utcnow(),
            report_period_start=period_start,
            report_period_end=period_end,
            tool_name=self.TOOL_NAME,
            tool_version=self.VERSION,
            total_sessions=len(sessions),
            total_api_calls=total_calls,
            total_duration_seconds=total_duration,
            read_only_percentage=read_only_pct,
            is_fully_read_only=(read_only_pct == 100.0),
            calls_by_category=calls_by_category,
            unique_services=sorted(calls_by_service.keys()),
            calls_by_service=calls_by_service,
            unique_operations=sorted(all_operations),
            write_operations=sorted(write_operations),
            total_errors=total_errors,
            error_rate_percentage=error_rate,
            compliance_statement=compliance,
            session_summaries=[s.to_dict() for s in sessions],
        )

    def get_quick_summary(self) -> dict[str, Any]:
        """
        Get a quick summary of audit status.

        Returns:
            Dictionary with key metrics
        """
        read_pct = (
            self._total_read_calls / self._total_calls * 100
            if self._total_calls > 0
            else 100.0
        )

        return {
            "enabled": self._enabled,
            "active_session": self._current_session_id,
            "total_sessions": len(self._sessions),
            "total_calls": self._total_calls,
            "read_calls": self._total_read_calls,
            "write_calls": self._total_write_calls,
            "delete_calls": self._total_delete_calls,
            "admin_calls": self._total_admin_calls,
            "read_only_percentage": round(read_pct, 2),
            "is_fully_read_only": (
                self._total_write_calls == 0
                and self._total_delete_calls == 0
                and self._total_admin_calls == 0
            ),
        }

    # =========================================================================
    # Storage
    # =========================================================================

    def _save_session(self, session_id: str) -> Path:
        """Save session to disk."""
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        filename = (
            f"session_{session_id}_"
            f"{session.start_time.strftime('%Y%m%d_%H%M%S')}.json"
        )
        filepath = self._storage_dir / filename

        with open(filepath, "w") as f:
            json.dump(
                {
                    "session": session.to_dict(),
                    "records": [r.to_dict() for r in session.records],
                },
                f,
                indent=2,
            )

        return filepath

    def load_sessions_from_disk(self) -> int:
        """
        Load previously saved sessions from disk.

        Returns:
            Number of sessions loaded
        """
        loaded = 0

        for filepath in self._storage_dir.glob("session_*.json"):
            try:
                with open(filepath) as f:
                    data = json.load(f)

                session_data = data.get("session", {})
                session_id = session_data.get("session_id")

                if session_id and session_id not in self._sessions:
                    session = AuditSession.from_dict(session_data)

                    # Load records if available
                    records_data = data.get("records", [])
                    for record_data in records_data:
                        try:
                            record = APICallRecord.from_dict(record_data)
                            session.records.append(record)
                        except (KeyError, ValueError):
                            continue

                    self._sessions[session_id] = session
                    loaded += 1

            except (json.JSONDecodeError, KeyError, ValueError) as e:
                logger.warning(f"Failed to load session from {filepath}: {e}")
                continue

        logger.info(f"Loaded {loaded} sessions from disk")
        return loaded

    def set_storage_dir(self, path: Path | str) -> None:
        """Set the storage directory for audit files."""
        self._storage_dir = Path(path)
        self._storage_dir.mkdir(parents=True, exist_ok=True)

    def clear_sessions(self) -> int:
        """
        Clear all in-memory sessions.

        Returns:
            Number of sessions cleared
        """
        count = len(self._sessions)
        self._sessions.clear()
        self._current_session_id = None
        return count
