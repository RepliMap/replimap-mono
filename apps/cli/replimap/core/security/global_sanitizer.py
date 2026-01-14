"""
Global Data Sanitizer for RepliMap.

This module provides comprehensive sanitization of AWS resource configurations
with features including:
- Recursive dictionary/list traversal with depth limits
- Deterministic redaction (enables drift detection)
- Base64 UserData decoding and scanning
- Environment variable container handling
- Circular reference protection

Architecture:
    This is the primary sanitization layer that runs at scan time,
    BEFORE data is stored in cache.

    AWS API Response
         │
         ▼
    GlobalSanitizer.sanitize()
         │
         ├── DeterministicRedactor (for sensitive fields)
         ├── SensitivePatternLibrary (for UserData/containers)
         └── Recursive traversal (with depth/cycle protection)
         │
         ▼
    Clean Configuration (safe for storage)

Usage:
    sanitizer = GlobalSanitizer()

    # Sanitize a resource config
    clean_config = sanitizer.sanitize(raw_config, service='ec2')

    # Get detailed results
    result = sanitizer.sanitize_with_result(raw_config, service='ec2')
    if result.was_modified:
        logger.info(f"Redacted {result.redacted_count} fields")

Thread Safety:
    Each call to sanitize() uses fresh state tracking.
    Safe for concurrent use.
"""

from __future__ import annotations

import base64
import binascii
import logging
from dataclasses import dataclass, field
from typing import Any

from replimap.core.security.patterns import SensitivePatternLibrary
from replimap.core.security.redactor import DeterministicRedactor

logger = logging.getLogger(__name__)


@dataclass
class SanitizationResult:
    """Result of sanitization operation."""

    data: Any
    redacted_count: int = 0
    redacted_fields: list[str] = field(default_factory=list)
    findings: list[str] = field(default_factory=list)

    @property
    def was_modified(self) -> bool:
        return self.redacted_count > 0


class GlobalSanitizer:
    """
    Global data sanitizer for AWS resource configurations.

    Features:
    - Recursive dictionary/list traversal
    - Deterministic redaction (enables drift detection)
    - Base64 UserData decoding and scanning
    - Environment variable container handling
    - Circular reference protection
    - Depth limit protection

    Usage:
        sanitizer = GlobalSanitizer()

        # Sanitize a resource config
        clean_config = sanitizer.sanitize(raw_config, service='ec2')

        # Get detailed results
        result = sanitizer.sanitize_with_result(raw_config, service='ec2')
        if result.was_modified:
            logger.info(f"Redacted {result.redacted_count} fields")

    Thread Safety:
        Each call to sanitize() uses fresh state tracking.
        Safe for concurrent use.
    """

    # Maximum recursion depth (prevents stack overflow)
    MAX_DEPTH = 50

    # Sensitive field names (lowercase for case-insensitive matching)
    SENSITIVE_KEYS: set[str] = {
        # Database passwords
        "masteruserpassword",
        "masterpassword",
        "password",
        "adminpassword",
        "tdecredentialpassword",
        "dbpassword",
        "db_password",
        "admin_password",
        # Keys and credentials
        "privatekey",
        "private_key",
        "secretkey",
        "secret_key",
        "keymaterial",
        "key_material",
        "accesskey",
        "access_key",
        "secretaccesskey",
        "secret_access_key",
        # Tokens
        "sessiontoken",
        "session_token",
        "authtoken",
        "auth_token",
        "bearertoken",
        "bearer_token",
        "accesstoken",
        "access_token",
        "refreshtoken",
        "refresh_token",
        "apikey",
        "api_key",
        # Generic
        "credentials",
        "credential",
        "secret",
        "secrets",
        "connectionstring",
        "connection_string",
        "connstring",
    }

    # Keys that contain nested sensitive data (need deep inspection)
    CONTAINER_KEYS: set[str] = {
        "environment",
        "variables",
        "env",
        "secrets",
        "environmentvariables",
        "environment_variables",
    }

    # Keys with potential encoded content
    ENCODED_KEYS: set[str] = {
        "userdata",
        "user_data",
    }

    def __init__(self, redactor: DeterministicRedactor | None = None) -> None:
        """
        Initialize sanitizer.

        Args:
            redactor: Optional custom redactor. If None, creates default.
        """
        self.redactor = redactor or DeterministicRedactor()

    def sanitize(
        self,
        data: Any,
        service: str = "",
    ) -> Any:
        """
        Sanitize data, returning clean copy.

        Args:
            data: Data to sanitize (dict, list, or primitive)
            service: AWS service name (for service-specific handling)

        Returns:
            Sanitized copy of data
        """
        result = self.sanitize_with_result(data, service)
        return result.data

    def sanitize_with_result(
        self,
        data: Any,
        service: str = "",
    ) -> SanitizationResult:
        """
        Sanitize data with detailed result.

        Args:
            data: Data to sanitize
            service: AWS service name

        Returns:
            SanitizationResult with sanitized data and metadata
        """
        # Fresh state for this sanitization pass
        seen_ids: set[int] = set()
        redacted_fields: list[str] = []
        all_findings: list[str] = []

        sanitized = self._sanitize_recursive(
            data=data,
            service=service,
            path="",
            depth=0,
            seen_ids=seen_ids,
            redacted_fields=redacted_fields,
            all_findings=all_findings,
        )

        return SanitizationResult(
            data=sanitized,
            redacted_count=len(redacted_fields),
            redacted_fields=redacted_fields,
            findings=all_findings,
        )

    def _sanitize_recursive(
        self,
        data: Any,
        service: str,
        path: str,
        depth: int,
        seen_ids: set[int],
        redacted_fields: list[str],
        all_findings: list[str],
    ) -> Any:
        """Internal recursive sanitization."""

        # Depth check
        if depth > self.MAX_DEPTH:
            logger.warning(f"Max depth exceeded at path: {path}")
            return "[MAX_DEPTH_EXCEEDED]"

        # Handle None
        if data is None:
            return None

        # Handle primitives
        if isinstance(data, bool):
            return data

        if isinstance(data, (int, float)):
            return data

        if isinstance(data, str):
            # Strings are handled by parent based on key
            return data

        if isinstance(data, bytes):
            # Try to decode and sanitize
            try:
                decoded = data.decode("utf-8")
                sanitized = self._sanitize_recursive(
                    decoded,
                    service,
                    path,
                    depth,
                    seen_ids,
                    redacted_fields,
                    all_findings,
                )
                return (
                    sanitized.encode("utf-8")
                    if isinstance(sanitized, str)
                    else sanitized
                )
            except UnicodeDecodeError:
                return b"[BINARY_REDACTED]"

        # Circular reference check for containers
        data_id = id(data)
        if data_id in seen_ids:
            return "[CIRCULAR_REFERENCE]"

        seen_ids.add(data_id)

        try:
            if isinstance(data, dict):
                return self._sanitize_dict(
                    data,
                    service,
                    path,
                    depth,
                    seen_ids,
                    redacted_fields,
                    all_findings,
                )

            if isinstance(data, (list, tuple)):
                result = [
                    self._sanitize_recursive(
                        item,
                        service,
                        f"{path}[{i}]",
                        depth + 1,
                        seen_ids,
                        redacted_fields,
                        all_findings,
                    )
                    for i, item in enumerate(data)
                ]
                return tuple(result) if isinstance(data, tuple) else result

            # Unknown type - convert to string
            return str(data)

        finally:
            seen_ids.discard(data_id)

    def _sanitize_dict(
        self,
        data: dict[str, Any],
        service: str,
        path: str,
        depth: int,
        seen_ids: set[int],
        redacted_fields: list[str],
        all_findings: list[str],
    ) -> dict[str, Any]:
        """Sanitize dictionary."""
        result: dict[str, Any] = {}

        for key, value in data.items():
            key_lower = key.lower()
            field_path = f"{path}.{key}" if path else key

            # 1. Check if this is a sensitive key
            if key_lower in self.SENSITIVE_KEYS:
                if isinstance(value, str) and value:
                    result[key] = self.redactor.redact(value, key)
                    redacted_fields.append(field_path)
                elif isinstance(value, dict):
                    # Container with sensitive name - redact all string values
                    result[key] = self._redact_container(
                        value, field_path, redacted_fields
                    )
                elif value is not None:
                    result[key] = "[REDACTED]"
                    redacted_fields.append(field_path)
                else:
                    result[key] = value
                continue

            # 2. Check if this is an encoded field (UserData)
            if key_lower in self.ENCODED_KEYS:
                if isinstance(value, str) and value:
                    sanitized, findings = self._sanitize_encoded_content(value, key)
                    result[key] = sanitized
                    if findings:
                        redacted_fields.append(field_path)
                        all_findings.extend(findings)
                else:
                    result[key] = value
                continue

            # 3. Check if this is a container that needs deep inspection
            if key_lower in self.CONTAINER_KEYS:
                if isinstance(value, dict):
                    result[key] = self._sanitize_container(
                        value, field_path, redacted_fields, all_findings
                    )
                else:
                    result[key] = self._sanitize_recursive(
                        value,
                        service,
                        field_path,
                        depth + 1,
                        seen_ids,
                        redacted_fields,
                        all_findings,
                    )
                continue

            # 4. Recurse into nested structures
            if isinstance(value, (dict, list, tuple)):
                result[key] = self._sanitize_recursive(
                    value,
                    service,
                    field_path,
                    depth + 1,
                    seen_ids,
                    redacted_fields,
                    all_findings,
                )
            else:
                result[key] = value

        return result

    def _redact_container(
        self,
        container: dict[str, Any],
        path: str,
        redacted_fields: list[str],
    ) -> dict[str, Any]:
        """Redact all string values in a container."""
        result: dict[str, Any] = {}

        for key, value in container.items():
            field_path = f"{path}.{key}"

            if isinstance(value, str) and value:
                result[key] = self.redactor.redact(value, key)
                redacted_fields.append(field_path)
            elif isinstance(value, dict):
                result[key] = self._redact_container(value, field_path, redacted_fields)
            elif isinstance(value, list):
                result[key] = [
                    self.redactor.redact(v, key) if isinstance(v, str) and v else v
                    for v in value
                ]
                if any(isinstance(v, str) and v for v in value):
                    redacted_fields.append(field_path)
            else:
                result[key] = value

        return result

    def _sanitize_container(
        self,
        container: dict[str, Any],
        path: str,
        redacted_fields: list[str],
        all_findings: list[str],
    ) -> dict[str, Any]:
        """
        Sanitize a container (like Lambda environment variables).

        Inspects both key names and value contents for sensitive data.
        """
        result: dict[str, Any] = {}

        # Patterns that suggest a key holds sensitive data
        sensitive_key_patterns = {
            "password",
            "passwd",
            "pwd",
            "secret",
            "key",
            "token",
            "credential",
            "auth",
            "api_key",
            "apikey",
            "private",
        }

        for key, value in container.items():
            key_lower = key.lower()
            field_path = f"{path}.{key}"

            # Check if key name suggests sensitive content
            is_sensitive_key = any(
                pattern in key_lower for pattern in sensitive_key_patterns
            )

            if isinstance(value, str):
                if is_sensitive_key and value:
                    # Key name suggests sensitive - redact
                    result[key] = self.redactor.redact(value, key)
                    redacted_fields.append(field_path)
                elif value:
                    # Scan value content for patterns
                    if SensitivePatternLibrary.contains_sensitive(value):
                        sanitized, findings = SensitivePatternLibrary.scan_text(value)
                        result[key] = sanitized
                        redacted_fields.append(field_path)
                        all_findings.extend(findings)
                    else:
                        result[key] = value
                else:
                    result[key] = value
            elif isinstance(value, dict):
                result[key] = self._sanitize_container(
                    value, field_path, redacted_fields, all_findings
                )
            else:
                result[key] = value

        return result

    def _sanitize_encoded_content(
        self,
        encoded: str,
        field_name: str,
    ) -> tuple[str, list[str]]:
        """
        Sanitize potentially Base64-encoded content (like UserData).

        Process:
        1. Try to decode as Base64
        2. Scan decoded content for sensitive patterns
        3. If sensitive found, sanitize and re-encode
        4. If not Base64 or no sensitive data, return as-is
        """
        if not encoded:
            return encoded, []

        # Try Base64 decode
        try:
            decoded = base64.b64decode(encoded, validate=True).decode("utf-8")
            is_base64 = True
        except (binascii.Error, UnicodeDecodeError, ValueError):
            # Not valid Base64, treat as plain text
            decoded = encoded
            is_base64 = False

        # Scan for sensitive patterns
        sanitized, findings = SensitivePatternLibrary.scan_text(decoded)

        if findings:
            # Found sensitive data
            logger.debug(f"Sanitized {field_name}: {len(findings)} patterns found")

            if is_base64:
                # Re-encode sanitized content
                return (
                    base64.b64encode(sanitized.encode("utf-8")).decode("utf-8"),
                    findings,
                )
            else:
                return sanitized, findings

        # No sensitive data found, return original
        return encoded, []


# Convenience function for backward compatibility
def sanitize_resource_config(
    config: dict[str, Any], service: str = ""
) -> dict[str, Any]:
    """
    Convenience function to sanitize a resource configuration.

    Args:
        config: Resource configuration dictionary
        service: AWS service name

    Returns:
        Sanitized configuration
    """
    sanitizer = GlobalSanitizer()
    return sanitizer.sanitize(config, service)
