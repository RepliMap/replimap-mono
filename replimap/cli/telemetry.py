"""
TelemetryHook - Usage Telemetry Placeholder.

NOTE: This version only provides the interface - no actual data is sent.
Future implementations can integrate with Segment, Amplitude, or custom services.

Design Principles:
- Hooks must be defined NOW to avoid modifying all commands later
- Disabled by default, requires explicit user opt-in
- Never sends sensitive information (credentials, resource IDs)
- All tracking is no-op when disabled

Usage:
    # Track command execution
    Telemetry.track_command_start("scan", {"region": "us-east-1"})
    try:
        result = do_scan()
        Telemetry.track_command_success("scan", duration_ms)
    except Exception as e:
        Telemetry.track_command_error("scan", e)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class TelemetryEvent:
    """
    A telemetry event to track.

    Events are stored locally when telemetry is enabled but not yet
    connected to a backend service.
    """

    event_type: str  # command_start, command_success, command_error
    command: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    duration_ms: int | None = None
    error_type: str | None = None
    error_message: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert event to JSON-serializable dict."""
        return {
            "event_type": self.event_type,
            "command": self.command,
            "timestamp": self.timestamp.isoformat(),
            "duration_ms": self.duration_ms,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "metadata": self._sanitize_metadata(self.metadata),
        }

    def _sanitize_metadata(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Sanitize metadata to remove sensitive information.

        Removes:
        - Any keys containing 'secret', 'key', 'token', 'password', 'credential'
        - Any values that look like AWS ARNs or resource IDs
        """
        sensitive_patterns = {
            "secret",
            "key",
            "token",
            "password",
            "credential",
            "auth",
        }

        result = {}
        for key, value in data.items():
            # Skip sensitive keys
            key_lower = key.lower()
            if any(pattern in key_lower for pattern in sensitive_patterns):
                continue

            # Skip sensitive values
            if isinstance(value, str):
                value_lower = value.lower()
                # Skip ARNs
                if value.startswith("arn:"):
                    continue
                # Skip resource IDs (vpc-xxx, subnet-xxx, etc.)
                if any(
                    value_lower.startswith(prefix)
                    for prefix in ["vpc-", "subnet-", "sg-", "i-", "vol-", "ami-"]
                ):
                    continue

            result[key] = value

        return result


class Telemetry:
    """
    Singleton telemetry service.

    Provides hooks for tracking command execution and errors.
    Currently stores events locally - future versions will send to analytics.

    Usage:
        Telemetry.enable()  # User opt-in
        Telemetry.track_command_start("scan")
        Telemetry.track_command_success("scan", 1500)
    """

    _instance: Telemetry | None = None
    _enabled: bool = False
    _events: list[TelemetryEvent] = []

    def __new__(cls) -> Telemetry:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._enabled = False
            cls._instance._events = []
        return cls._instance

    @classmethod
    def enable(cls) -> None:
        """Enable telemetry collection (user opt-in)."""
        instance = cls()
        instance._enabled = True

    @classmethod
    def disable(cls) -> None:
        """Disable telemetry collection."""
        instance = cls()
        instance._enabled = False

    @classmethod
    def is_enabled(cls) -> bool:
        """Check if telemetry is enabled."""
        instance = cls()
        return instance._enabled

    @classmethod
    def track_command_start(
        cls,
        command: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Track the start of a command execution.

        Args:
            command: Command name (e.g., "scan", "clone")
            metadata: Optional metadata (region, format, etc.)
        """
        instance = cls()
        if not instance._enabled:
            return

        event = TelemetryEvent(
            event_type="command_start",
            command=command,
            metadata=metadata or {},
        )
        instance._emit(event)

    @classmethod
    def track_command_success(
        cls,
        command: str,
        duration_ms: int,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Track successful command completion.

        Args:
            command: Command name
            duration_ms: Execution time in milliseconds
            metadata: Optional metadata
        """
        instance = cls()
        if not instance._enabled:
            return

        event = TelemetryEvent(
            event_type="command_success",
            command=command,
            duration_ms=duration_ms,
            metadata=metadata or {},
        )
        instance._emit(event)

    @classmethod
    def track_command_error(
        cls,
        command: str,
        error: Exception,
        duration_ms: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Track command error.

        Args:
            command: Command name
            error: The exception that occurred
            duration_ms: Execution time until error
            metadata: Optional metadata
        """
        instance = cls()
        if not instance._enabled:
            return

        # Sanitize error message to remove sensitive info
        error_msg = str(error)
        # Remove potential ARNs from error message
        if "arn:" in error_msg.lower():
            error_msg = "[Error message contained ARN - redacted]"

        event = TelemetryEvent(
            event_type="command_error",
            command=command,
            duration_ms=duration_ms,
            error_type=type(error).__name__,
            error_message=error_msg[:200],  # Truncate long messages
            metadata=metadata or {},
        )
        instance._emit(event)

    @classmethod
    def get_local_events(cls) -> list[TelemetryEvent]:
        """
        Get locally stored events.

        Returns:
            List of stored telemetry events (for debugging/testing)
        """
        instance = cls()
        return list(instance._events)

    @classmethod
    def clear_events(cls) -> None:
        """Clear locally stored events."""
        instance = cls()
        instance._events = []

    def _emit(self, event: TelemetryEvent) -> None:
        """
        Emit a telemetry event.

        Currently stores locally. Future: send to analytics backend.

        Args:
            event: The event to emit
        """
        if not self._enabled:
            return

        # Store locally (future: send to analytics)
        self._events.append(event)

        # Keep only last 100 events to prevent memory bloat
        if len(self._events) > 100:
            self._events = self._events[-100:]


# Context manager for tracking command execution
class TelemetryContext:
    """
    Context manager for tracking command execution with automatic timing.

    Usage:
        with TelemetryContext("scan", {"region": "us-east-1"}) as ctx:
            do_scan()
        # Automatically tracks success/error and duration
    """

    def __init__(self, command: str, metadata: dict[str, Any] | None = None) -> None:
        self.command = command
        self.metadata = metadata or {}
        self._start_time: datetime | None = None
        self._error: Exception | None = None

    def __enter__(self) -> TelemetryContext:
        self._start_time = datetime.now(UTC)
        Telemetry.track_command_start(self.command, self.metadata)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        if self._start_time is None:
            return

        duration_ms = int((datetime.now(UTC) - self._start_time).total_seconds() * 1000)

        if exc_val is not None and isinstance(exc_val, Exception):
            Telemetry.track_command_error(
                self.command, exc_val, duration_ms, self.metadata
            )
        else:
            Telemetry.track_command_success(self.command, duration_ms, self.metadata)


__all__ = [
    "Telemetry",
    "TelemetryContext",
    "TelemetryEvent",
]
