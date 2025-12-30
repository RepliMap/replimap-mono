"""
Structured logging configuration for RepliMap.

This module provides structured logging using structlog with support for:
- Human-readable colored output (default for CLI)
- JSON output (for machine processing / log aggregation)
- Context binding (request IDs, resource types, etc.)
- Performance timing
- Integration with Rich console

Usage:
    from replimap.core.logging import get_logger, configure_logging

    # Configure once at startup
    configure_logging(level="INFO", json_output=False)

    # Get a logger
    logger = get_logger(__name__)

    # Use structured logging
    logger.info("scanning_started", resource_type="ec2", region="us-east-1")
    logger.info("api_call", service="ec2", operation="describe_instances", duration_ms=123)

Environment Variables:
    REPLIMAP_LOG_LEVEL: DEBUG, INFO, WARNING, ERROR (default: INFO)
    REPLIMAP_LOG_JSON: 1/true for JSON output (default: false)
    REPLIMAP_LOG_FILE: Path to log file (optional)
"""

from __future__ import annotations

import logging
import os
import sys
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Any

import structlog
from rich.console import Console
from rich.logging import RichHandler

if TYPE_CHECKING:
    from structlog.types import Processor

# Global state
_configured = False
_json_output = False
_log_file: Path | None = None


def _add_timestamp(
    logger: logging.Logger, method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Add ISO timestamp to log entries."""
    event_dict["timestamp"] = datetime.now(UTC).isoformat()
    return event_dict


def _add_caller_info(
    logger: logging.Logger, method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Add caller module and function info."""
    # structlog already adds this in some processors, but we ensure consistency
    if "module" not in event_dict:
        event_dict["module"] = logger.name if hasattr(logger, "name") else "unknown"
    return event_dict


def _sanitize_sensitive(
    logger: logging.Logger, method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Remove or mask sensitive information from logs."""
    sensitive_keys = {
        "password",
        "secret",
        "token",
        "api_key",
        "access_key",
        "secret_key",
        "credentials",
    }

    for key in list(event_dict.keys()):
        key_lower = key.lower()
        if any(s in key_lower for s in sensitive_keys):
            event_dict[key] = "[REDACTED]"

    return event_dict


def _get_human_processors() -> list[Processor]:
    """Get processors for human-readable output."""
    return [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        _sanitize_sensitive,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(
            colors=True,
            exception_formatter=structlog.dev.plain_traceback,
        ),
    ]


def _get_json_processors() -> list[Processor]:
    """Get processors for JSON output."""
    return [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        _sanitize_sensitive,
        _add_timestamp,
        _add_caller_info,
        structlog.processors.JSONRenderer(),
    ]


def configure_logging(
    level: str = "INFO",
    json_output: bool | None = None,
    log_file: str | Path | None = None,
    force: bool = False,
) -> None:
    """
    Configure structured logging for RepliMap.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        json_output: If True, output JSON. If None, check REPLIMAP_LOG_JSON env var.
        log_file: Optional path to write logs to file
        force: If True, reconfigure even if already configured
    """
    global _configured, _json_output, _log_file

    if _configured and not force:
        return

    # Resolve settings from environment if not explicitly set
    level = os.environ.get("REPLIMAP_LOG_LEVEL", level).upper()

    if json_output is None:
        env_json = os.environ.get("REPLIMAP_LOG_JSON", "").lower()
        json_output = env_json in ("1", "true", "yes")

    if log_file is None:
        env_file = os.environ.get("REPLIMAP_LOG_FILE")
        if env_file:
            log_file = Path(env_file)

    _json_output = json_output
    _log_file = Path(log_file) if log_file else None

    # Configure standard logging
    log_level = getattr(logging, level, logging.INFO)

    # Set up handlers
    handlers: list[logging.Handler] = []

    if json_output:
        # JSON to stderr
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter("%(message)s"))
        handlers.append(handler)
    else:
        # Rich handler for beautiful CLI output
        console = Console(stderr=True, force_terminal=True)
        handler = RichHandler(
            console=console,
            show_time=True,
            show_path=False,
            rich_tracebacks=True,
            tracebacks_show_locals=False,
        )
        handlers.append(handler)

    # File handler if specified
    if _log_file:
        _log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(_log_file)
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
        )
        handlers.append(file_handler)

    # Configure root logger
    logging.basicConfig(
        level=log_level,
        handlers=handlers,
        force=True,
    )

    # Suppress noisy loggers
    logging.getLogger("boto3").setLevel(logging.WARNING)
    logging.getLogger("botocore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("aiobotocore").setLevel(logging.WARNING)

    # Configure structlog
    processors = _get_json_processors() if json_output else _get_human_processors()

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    _configured = True


@lru_cache(maxsize=128)
def get_logger(name: str | None = None) -> structlog.BoundLogger:
    """
    Get a structured logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        A structlog BoundLogger instance

    Example:
        logger = get_logger(__name__)
        logger.info("event_name", key="value", count=42)
    """
    if not _configured:
        configure_logging()

    return structlog.get_logger(name or "replimap")


class LogContext:
    """
    Context manager for adding temporary context to logs.

    Usage:
        with LogContext(request_id="abc123", user="admin"):
            logger.info("processing")  # includes request_id and user
        logger.info("done")  # does not include request_id or user
    """

    def __init__(self, **kwargs: Any) -> None:
        self.context = kwargs
        self._token = None

    def __enter__(self) -> LogContext:
        self._token = structlog.contextvars.bind_contextvars(**self.context)
        return self

    def __exit__(self, *args: Any) -> None:
        if self._token:
            structlog.contextvars.unbind_contextvars(*self.context.keys())


class Timer:
    """
    Context manager for timing operations and logging duration.

    Usage:
        logger = get_logger(__name__)
        with Timer(logger, "api_call", service="ec2"):
            response = client.describe_instances()
        # Logs: api_call service=ec2 duration_ms=123
    """

    def __init__(
        self,
        logger: structlog.BoundLogger,
        event: str,
        level: str = "info",
        **context: Any,
    ) -> None:
        self.logger = logger
        self.event = event
        self.level = level
        self.context = context
        self.start_time: float | None = None
        self.duration_ms: float | None = None

    def __enter__(self) -> Timer:
        import time

        self.start_time = time.perf_counter()
        return self

    def __exit__(self, *args: Any) -> None:
        import time

        if self.start_time:
            self.duration_ms = (time.perf_counter() - self.start_time) * 1000
            log_method = getattr(self.logger, self.level)
            log_method(
                self.event,
                duration_ms=round(self.duration_ms, 2),
                **self.context,
            )


class ScanMetrics:
    """
    Collect and report metrics during a scan operation.

    Usage:
        metrics = ScanMetrics()
        metrics.record_api_call("ec2", "describe_instances", 123.4)
        metrics.record_resource("aws_instance", 42)
        metrics.report(logger)
    """

    def __init__(self) -> None:
        self.api_calls: list[dict[str, Any]] = []
        self.resources: dict[str, int] = {}
        self.errors: list[dict[str, Any]] = []
        self.start_time: float | None = None
        self.end_time: float | None = None

    def start(self) -> None:
        import time

        self.start_time = time.perf_counter()

    def stop(self) -> None:
        import time

        self.end_time = time.perf_counter()

    def record_api_call(
        self, service: str, operation: str, duration_ms: float, success: bool = True
    ) -> None:
        self.api_calls.append(
            {
                "service": service,
                "operation": operation,
                "duration_ms": duration_ms,
                "success": success,
            }
        )

    def record_resource(self, resource_type: str, count: int = 1) -> None:
        self.resources[resource_type] = self.resources.get(resource_type, 0) + count

    def record_error(self, error_type: str, message: str, **context: Any) -> None:
        self.errors.append({"type": error_type, "message": message, **context})

    @property
    def total_duration_ms(self) -> float:
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time) * 1000
        return 0.0

    @property
    def total_api_calls(self) -> int:
        return len(self.api_calls)

    @property
    def total_resources(self) -> int:
        return sum(self.resources.values())

    @property
    def avg_api_latency_ms(self) -> float:
        if not self.api_calls:
            return 0.0
        return sum(c["duration_ms"] for c in self.api_calls) / len(self.api_calls)

    @property
    def p95_api_latency_ms(self) -> float:
        if not self.api_calls:
            return 0.0
        sorted_latencies = sorted(c["duration_ms"] for c in self.api_calls)
        idx = int(len(sorted_latencies) * 0.95)
        return sorted_latencies[min(idx, len(sorted_latencies) - 1)]

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_duration_ms": round(self.total_duration_ms, 2),
            "total_api_calls": self.total_api_calls,
            "total_resources": self.total_resources,
            "resources_by_type": self.resources,
            "avg_api_latency_ms": round(self.avg_api_latency_ms, 2),
            "p95_api_latency_ms": round(self.p95_api_latency_ms, 2),
            "error_count": len(self.errors),
        }

    def report(self, logger: structlog.BoundLogger) -> None:
        """Log a summary of the scan metrics."""
        logger.info("scan_metrics", **self.to_dict())

        if self.errors:
            for error in self.errors[:5]:  # Limit to first 5
                logger.warning("scan_error", **error)
            if len(self.errors) > 5:
                logger.warning(
                    "additional_errors", count=len(self.errors) - 5, message="..."
                )
