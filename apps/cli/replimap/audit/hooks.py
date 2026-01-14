"""
boto3 event hooks for automatic API call auditing.

This module provides non-invasive integration with boto3 to
capture all AWS API calls without modifying existing code.

Usage:
    hooks = AuditHooks(on_call=lambda record: print(record))
    hooks.register(boto3.Session())

    # Now all API calls through this session are audited
    ec2 = session.client('ec2')
    ec2.describe_instances()  # This call is captured
"""

from __future__ import annotations

import logging
import threading
import uuid
from collections.abc import Callable
from datetime import datetime
from typing import TYPE_CHECKING, Any

from .classifier import classifier
from .models import APICallRecord

if TYPE_CHECKING:
    import boto3

logger = logging.getLogger(__name__)

# Thread-local storage for timing context
_timing_context = threading.local()


class AuditHooks:
    """
    boto3 event hooks for capturing API calls.

    Provides automatic capture of all AWS API calls made through
    a boto3 session, classifying them and invoking callbacks.

    Thread-safe via thread-local storage for timing context.
    """

    # Parameters that should be redacted for security
    SENSITIVE_PARAMS: set[str] = {
        "Password",
        "SecretKey",
        "AccessKey",
        "Token",
        "Credential",
        "Secret",
        "PrivateKey",
        "Certificate",
        "SessionToken",
        "AuthToken",
        "ApiKey",
        "AuthorizationToken",
        "MasterUserPassword",
        "NewMasterUserPassword",
        "OldPassword",
        "NewPassword",
        "TemporaryPassword",
    }

    def __init__(
        self,
        on_call: Callable[[APICallRecord], None] | None = None,
        sanitize_params: bool = True,
        capture_params: bool = False,
    ) -> None:
        """
        Initialize audit hooks.

        Args:
            on_call: Callback invoked after each API call with the record
            sanitize_params: If True, redact sensitive parameters
            capture_params: If True, include sanitized params in records
        """
        self.on_call = on_call
        self.sanitize_params = sanitize_params
        self.capture_params = capture_params
        self._registered_sessions: set[int] = set()
        self._lock = threading.Lock()

    def register(self, session: boto3.Session) -> None:
        """
        Register hooks with a boto3 session.

        Args:
            session: boto3 Session instance
        """
        session_id = id(session)
        with self._lock:
            if session_id in self._registered_sessions:
                return

            try:
                # Access the underlying botocore session's event system
                events = session._session.get_component("event_emitter")

                # Register before-call handler
                events.register("before-call.*.*", self._before_call_handler)

                # Register after-call handler
                events.register("after-call.*.*", self._after_call_handler)

                self._registered_sessions.add(session_id)
                logger.debug(f"Registered audit hooks for session {session_id}")

            except Exception as e:
                logger.error(f"Failed to register audit hooks: {e}")

    def unregister(self, session: boto3.Session) -> None:
        """
        Unregister hooks from a boto3 session.

        Args:
            session: boto3 Session instance
        """
        session_id = id(session)
        with self._lock:
            if session_id not in self._registered_sessions:
                return

            try:
                events = session._session.get_component("event_emitter")
                events.unregister("before-call.*.*", self._before_call_handler)
                events.unregister("after-call.*.*", self._after_call_handler)

                self._registered_sessions.discard(session_id)
                logger.debug(f"Unregistered audit hooks for session {session_id}")

            except Exception as e:
                logger.error(f"Failed to unregister audit hooks: {e}")

    def _before_call_handler(
        self,
        model: Any,
        params: dict[str, Any],
        request_signer: Any,
        **kwargs: Any,
    ) -> None:
        """Handler called before each API request."""
        _timing_context.start_time = datetime.utcnow()
        _timing_context.params = params if self.capture_params else {}

    def _after_call_handler(
        self,
        http_response: Any,
        parsed: dict[str, Any],
        model: Any,
        **kwargs: Any,
    ) -> None:
        """Handler called after each API response."""
        end_time = datetime.utcnow()

        # Calculate duration
        start_time = getattr(_timing_context, "start_time", end_time)
        duration_ms = int((end_time - start_time).total_seconds() * 1000)

        # Extract service and operation from model
        service = "unknown"
        operation = "unknown"
        if model:
            try:
                service = model.service_model.service_name
                operation = model.name
            except AttributeError:
                pass

        # Get region from context
        region = kwargs.get("context", {}).get("client_region", "unknown")

        # Extract HTTP status
        status_code = 200
        if http_response:
            status_code = getattr(http_response, "status_code", 200)

        # Extract error info
        error_code = None
        error_message = None
        if isinstance(parsed, dict) and "Error" in parsed:
            error_code = parsed["Error"].get("Code")
            error_message = parsed["Error"].get("Message")

        # Get request ID
        request_id = None
        if isinstance(parsed, dict):
            request_id = parsed.get("ResponseMetadata", {}).get("RequestId")
        if not request_id:
            request_id = str(uuid.uuid4())[:8]

        # Classify operation
        category = classifier.classify(operation)

        # Build parameters (sanitized if enabled)
        params: dict[str, Any] = {}
        if self.capture_params:
            raw_params = getattr(_timing_context, "params", {})
            params = (
                self._sanitize_params(raw_params)
                if self.sanitize_params
                else raw_params
            )

        # Get account ID from response metadata if available
        account_id = None
        if isinstance(parsed, dict):
            # Some responses include account info
            if "Account" in parsed:
                account_id = parsed.get("Account")
            elif "OwnerId" in parsed:
                account_id = parsed.get("OwnerId")

        # Create record
        record = APICallRecord(
            timestamp=end_time,
            duration_ms=duration_ms,
            service=service,
            operation=operation,
            region=region,
            request_id=request_id,
            category=category,
            http_status=status_code,
            error_code=error_code,
            error_message=error_message,
            parameters=params,
            account_id=account_id,
        )

        # Invoke callback
        if self.on_call:
            try:
                self.on_call(record)
            except Exception as e:
                # Don't let callback errors affect the API call
                logger.warning(f"Audit callback error: {e}")

    def _sanitize_params(self, params: dict[str, Any]) -> dict[str, Any]:
        """Redact sensitive parameters."""
        if not params:
            return {}

        sanitized: dict[str, Any] = {}
        for key, value in params.items():
            # Check if key contains sensitive terms
            is_sensitive = any(s.lower() in key.lower() for s in self.SENSITIVE_PARAMS)

            if is_sensitive:
                sanitized[key] = "***REDACTED***"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_params(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    self._sanitize_params(v) if isinstance(v, dict) else v
                    for v in value
                ]
            else:
                sanitized[key] = value

        return sanitized

    @property
    def registered_session_count(self) -> int:
        """Get the number of registered sessions."""
        return len(self._registered_sessions)
