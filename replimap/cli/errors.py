"""
ErrorTelemetry - Structured Error Handling with Reference Codes.

Error Reference Format: ERR-{SERVICE}-{STATUS}-{HASH}
Example: ERR-EC2-403-A7X9

Log Storage: ~/.replimap/logs/errors/ERR-EC2-403-A7X9_20260113_103000.log

Log Contents:
- error_reference: Unique error code
- timestamp: When error occurred
- exception: Type, message, traceback
- context: Command, region, profile, parameters
- reproduction: Command to reproduce the error

This module provides structured error capture and user-friendly display
with actionable error references for support.
"""

from __future__ import annotations

import functools
import hashlib
import sys
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

from rich.panel import Panel

if TYPE_CHECKING:
    from collections.abc import Callable

# Sensitive keys to redact from error logs
SENSITIVE_KEYS = frozenset({
    "password",
    "secret",
    "token",
    "key",
    "credential",
    "api_key",
    "apikey",
    "access_key",
    "secret_key",
    "aws_access_key_id",
    "aws_secret_access_key",
    "aws_session_token",
})


@dataclass
class ErrorContext:
    """
    Context information for an error occurrence.

    This captures the state when an error occurred to aid debugging.
    Sensitive values are automatically redacted.
    """

    command: str
    service: str | None = None
    operation: str | None = None
    region: str | None = None
    profile: str | None = None
    parameters: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict with sensitive values redacted."""
        return {
            "command": self.command,
            "service": self.service,
            "operation": self.operation,
            "region": self.region,
            "profile": self.profile,
            "parameters": self._redact_sensitive(self.parameters),
        }

    def _redact_sensitive(self, data: dict[str, Any]) -> dict[str, Any]:
        """Redact sensitive values from dict."""
        result = {}
        for key, value in data.items():
            key_lower = key.lower()
            if any(s in key_lower for s in SENSITIVE_KEYS):
                result[key] = "[REDACTED]"
            elif isinstance(value, dict):
                result[key] = self._redact_sensitive(value)
            else:
                result[key] = value
        return result


@dataclass
class ErrorReference:
    """
    A unique reference to a captured error.

    This provides a short, memorable code that can be used
    for support requests and correlating with log files.
    """

    code: str  # e.g., "ERR-EC2-403-A7X9"
    timestamp: datetime
    log_path: Path | None
    context: ErrorContext
    exception_type: str
    exception_message: str
    traceback_str: str | None = None

    def to_display(self) -> str:
        """Get display string for user output."""
        return f"Error Reference: {self.code}"

    def to_support_info(self) -> str:
        """Get full support information string."""
        lines = [
            f"Error Reference: {self.code}",
            f"Time: {self.timestamp.isoformat()}",
            f"Exception: {self.exception_type}: {self.exception_message}",
            f"Command: {self.context.command}",
        ]

        if self.context.region:
            lines.append(f"Region: {self.context.region}")

        if self.context.profile:
            lines.append(f"Profile: {self.context.profile}")

        if self.log_path:
            lines.append(f"Log: {self.log_path}")

        return "\n".join(lines)


class ErrorTelemetry:
    """
    Captures and logs errors with structured reference codes.

    Usage:
        telemetry = ErrorTelemetry()
        try:
            do_something()
        except Exception as e:
            context = ErrorContext(command="scan", region="us-east-1")
            ref = telemetry.capture(e, context)
            print(f"Error reference: {ref.code}")
    """

    LOG_DIR = Path.home() / ".replimap" / "logs" / "errors"

    def __init__(self, log_dir: Path | None = None) -> None:
        """
        Initialize error telemetry.

        Args:
            log_dir: Custom log directory (defaults to ~/.replimap/logs/errors/)
        """
        self._log_dir = log_dir or self.LOG_DIR

    def capture(
        self,
        exception: Exception,
        context: ErrorContext,
    ) -> ErrorReference:
        """
        Capture an exception and create an error reference.

        Args:
            exception: The exception that occurred
            context: Context information about the error

        Returns:
            ErrorReference with unique code and log path
        """
        timestamp = datetime.now(timezone.utc)
        code = self._generate_code(exception, context)
        log_path = self._create_log_file(code, exception, context, timestamp)

        return ErrorReference(
            code=code,
            timestamp=timestamp,
            log_path=log_path,
            context=context,
            exception_type=type(exception).__name__,
            exception_message=str(exception),
            traceback_str=traceback.format_exc(),
        )

    def _generate_code(
        self,
        exception: Exception,
        context: ErrorContext,
    ) -> str:
        """
        Generate a unique error reference code.

        Format: ERR-{SERVICE}-{STATUS}-{HASH}
        Example: ERR-EC2-403-A7X9

        Args:
            exception: The exception
            context: Error context

        Returns:
            Unique error code string
        """
        # Extract service
        service = context.service or "CLI"
        service = service.upper()[:3]

        # Extract status code
        status = self._extract_status(exception)

        # Generate hash from exception details
        hash_input = f"{type(exception).__name__}:{exception}:{context.command}"
        hash_bytes = hashlib.md5(hash_input.encode()).digest()  # noqa: S324
        hash_str = "".join(
            f"{b:02X}" for b in hash_bytes[:2]
        )  # 4 hex chars

        return f"ERR-{service}-{status}-{hash_str}"

    def _extract_status(self, exception: Exception) -> str:
        """
        Extract HTTP status code from exception if available.

        Args:
            exception: The exception

        Returns:
            Status code string (e.g., "403") or "UNK"
        """
        # Try to extract from botocore ClientError
        if hasattr(exception, "response"):
            response = getattr(exception, "response", {})
            if isinstance(response, dict):
                http_status = response.get("ResponseMetadata", {}).get(
                    "HTTPStatusCode"
                )
                if http_status:
                    return str(http_status)

                # Also check Error.Code
                error_code = response.get("Error", {}).get("Code", "")
                if error_code == "AccessDenied":
                    return "403"
                if error_code in ("Throttling", "TooManyRequestsException"):
                    return "429"

        # Check for common exception patterns
        exc_name = type(exception).__name__.lower()
        if "timeout" in exc_name:
            return "408"
        if "connection" in exc_name:
            return "503"
        if "permission" in exc_name or "access" in exc_name:
            return "403"

        return "UNK"

    def _create_log_file(
        self,
        code: str,
        exception: Exception,
        context: ErrorContext,
        timestamp: datetime,
    ) -> Path | None:
        """
        Create a detailed error log file.

        Args:
            code: Error reference code
            exception: The exception
            context: Error context
            timestamp: When error occurred

        Returns:
            Path to log file, or None if creation failed
        """
        # Ensure log directory exists
        try:
            self._log_dir.mkdir(parents=True, exist_ok=True)
        except OSError:
            return None

        # Generate filename
        time_str = timestamp.strftime("%Y%m%d_%H%M%S")
        filename = f"{code}_{time_str}.log"
        log_path = self._log_dir / filename

        # Build log content
        reproduction = self._build_reproduction_command(context)

        content = [
            "=" * 60,
            f"ERROR REFERENCE: {code}",
            "=" * 60,
            "",
            "TIMESTAMP",
            "-" * 40,
            f"  {timestamp.isoformat()}",
            "",
            "EXCEPTION",
            "-" * 40,
            f"  Type: {type(exception).__name__}",
            f"  Message: {exception}",
            "",
            "TRACEBACK",
            "-" * 40,
            traceback.format_exc(),
            "",
            "CONTEXT",
            "-" * 40,
        ]

        # Add context details
        ctx_dict = context.to_dict()
        for key, value in ctx_dict.items():
            content.append(f"  {key}: {value}")

        content.extend([
            "",
            "REPRODUCTION",
            "-" * 40,
            f"  {reproduction}",
            "",
            "=" * 60,
        ])

        try:
            with open(log_path, "w", encoding="utf-8") as f:
                f.write("\n".join(content))
            return log_path
        except OSError:
            return None

    def _build_reproduction_command(self, context: ErrorContext) -> str:
        """
        Build a command string to reproduce the error.

        Args:
            context: Error context

        Returns:
            Command string for reproduction
        """
        parts = ["replimap", context.command]

        if context.profile:
            parts.extend(["--profile", context.profile])

        if context.region:
            parts.extend(["--region", context.region])

        # Add non-sensitive parameters
        for key, value in context.parameters.items():
            key_lower = key.lower()
            if any(s in key_lower for s in SENSITIVE_KEYS):
                continue
            if isinstance(value, bool):
                if value:
                    parts.append(f"--{key.replace('_', '-')}")
            elif isinstance(value, list):
                for item in value:
                    parts.extend([f"--{key.replace('_', '-')}", str(item)])
            elif value is not None:
                parts.extend([f"--{key.replace('_', '-')}", str(value)])

        return " ".join(parts)


# Global telemetry instance
_telemetry: ErrorTelemetry | None = None


def get_error_telemetry() -> ErrorTelemetry:
    """Get the global error telemetry instance."""
    global _telemetry
    if _telemetry is None:
        _telemetry = ErrorTelemetry()
    return _telemetry


def enhanced_cli_error_handler(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator for CLI commands that provides enhanced error handling.

    This wraps a command to:
    - Catch all exceptions
    - Generate error reference codes
    - Display user-friendly error panels
    - Log detailed error information

    Usage:
        @app.command()
        @enhanced_cli_error_handler
        def my_command(ctx: typer.Context):
            ...
    """
    import os

    import botocore.exceptions
    import typer

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # Import here to avoid circular imports
        from replimap.cli.utils.console import console

        debug = os.getenv("REPLIMAP_DEBUG", "").lower() in ("1", "true", "yes")

        try:
            return func(*args, **kwargs)

        except KeyboardInterrupt:
            console.print("\n[yellow]Cancelled by user[/yellow]")
            sys.exit(130)

        except typer.Exit:
            raise

        except typer.Abort:
            raise

        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            # AWS-specific error handling
            context = _extract_context_from_args(func, args, kwargs)
            context.service = _extract_service_from_error(e)
            telemetry = get_error_telemetry()
            ref = telemetry.capture(e, context)

            _display_error_panel(
                console=console,
                reference=ref,
                is_aws_error=True,
                debug=debug,
            )
            sys.exit(1)

        except Exception as e:
            # Generic error handling
            context = _extract_context_from_args(func, args, kwargs)
            telemetry = get_error_telemetry()
            ref = telemetry.capture(e, context)

            _display_error_panel(
                console=console,
                reference=ref,
                is_aws_error=False,
                debug=debug,
            )
            sys.exit(1)

    return wrapper


def _extract_context_from_args(
    func: Callable[..., Any],
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> ErrorContext:
    """Extract error context from function arguments."""
    command = func.__name__

    # Try to get profile and region from kwargs
    profile = kwargs.get("profile")
    region = kwargs.get("region")

    # Try to get from typer Context if present
    for arg in args:
        if hasattr(arg, "obj") and arg.obj is not None:
            if hasattr(arg.obj, "profile"):
                profile = profile or arg.obj.profile
            if hasattr(arg.obj, "region"):
                region = region or arg.obj.region
            break

    return ErrorContext(
        command=command,
        profile=profile,
        region=region,
        parameters=dict(kwargs),
    )


def _extract_service_from_error(error: Exception) -> str | None:
    """Extract AWS service name from error."""
    if hasattr(error, "response"):
        response = getattr(error, "response", {})
        if isinstance(response, dict):
            # Try to extract from error metadata
            metadata = response.get("ResponseMetadata", {})
            if "ServiceName" in metadata:
                return metadata["ServiceName"]

    # Try to infer from exception message
    error_str = str(error).lower()
    services = ["ec2", "s3", "rds", "iam", "lambda", "ecs", "eks", "sqs", "sns"]
    for service in services:
        if service in error_str:
            return service.upper()

    return None


def _display_error_panel(
    console: Any,
    reference: ErrorReference,
    is_aws_error: bool,
    debug: bool,
) -> None:
    """Display a user-friendly error panel."""
    from replimap.core.constants import EMAIL_SUPPORT, URL_ISSUES

    if is_aws_error:
        title = "[red]AWS Error[/red]"
    else:
        title = "[red]Error[/red]"

    content_lines = [
        f"[bold red]{reference.exception_type}[/bold red]",
        "",
        f"{reference.exception_message}",
        "",
        f"[dim]{reference.to_display()}[/dim]",
    ]

    if reference.log_path:
        content_lines.extend([
            "",
            f"[dim]Details logged to: {reference.log_path}[/dim]",
        ])

    content_lines.extend([
        "",
        f"[bold]Need help?[/bold] "
        f"[link=mailto:{EMAIL_SUPPORT}]{EMAIL_SUPPORT}[/link] or "
        f"[link={URL_ISSUES}]open an issue[/link]",
    ])

    console.print()
    console.print(Panel("\n".join(content_lines), title=title, border_style="red"))

    if debug and reference.traceback_str:
        console.print()
        console.print("[dim]Debug traceback:[/dim]")
        console.print(reference.traceback_str)


__all__ = [
    "ErrorContext",
    "ErrorReference",
    "ErrorTelemetry",
    "enhanced_cli_error_handler",
    "get_error_telemetry",
]
