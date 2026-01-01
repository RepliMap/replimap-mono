"""
Secret Scrubber - Detect and redact sensitive information.

This module provides a SecretScrubber class that scans text for sensitive
patterns (AWS keys, passwords, tokens, etc.) and replaces them with a
redacted placeholder to prevent accidental exposure in generated Terraform.
"""

from __future__ import annotations

import logging
import re
from collections import Counter
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from rich.console import Console


logger = logging.getLogger(__name__)


class SecretScrubber:
    """
    Detects and redacts sensitive patterns in text.

    Designed to be injected into TerraformGenerator to sanitize
    user_data, environment variables, and other potentially sensitive fields.
    """

    # Regex patterns for detecting secrets
    # Each pattern is designed to minimize false positives while catching real secrets
    PATTERNS: dict[str, re.Pattern[str]] = {
        # AWS Keys - includes AKIA (permanent) and ASIA (temporary/STS credentials)
        "AWS Access Key ID": re.compile(
            r"(?<![A-Z0-9])((?:AKIA|ASIA)[A-Z0-9]{16})(?![A-Z0-9])"
        ),
        # AWS Secret Access Key - 40 character base64-like string
        # Require context to reduce false positives (must be near key-like words)
        "AWS Secret Access Key": re.compile(
            r"(?i)(?:secret|aws_secret|secret_access_key|secretaccesskey)"
            r"[\s]*[=:][\s]*['\"]?([A-Za-z0-9/+=]{40})['\"]?"
        ),
        # Private Keys (RSA, EC, DSA, OpenSSH)
        "Private Key": re.compile(
            r"-----BEGIN\s+(?:RSA\s+|EC\s+|DSA\s+|OPENSSH\s+)?PRIVATE\s+KEY-----"
        ),
        # Generic secrets - stricter pattern to reduce false positives
        # Requires: keyword, separator, and value that looks like a secret
        # (min 12 chars, contains mix of chars, not a common placeholder)
        "Generic Secret": re.compile(
            r"(?i)(password|secret_key|api_key|apikey|access_token|auth_token|"
            r"private_key|db_password|database_password|mysql_password|"
            r"postgres_password|redis_password|admin_password)"
            r"[\s]*[=:][\s]*['\"]?([A-Za-z0-9_\-\.!@#$%^&*]{12,})['\"]?"
        ),
        # Bearer tokens
        "Bearer Token": re.compile(r"(?i)bearer\s+[a-zA-Z0-9_\-\.]{20,}"),
        # Database URLs with embedded passwords
        # Handles both user:password@host and :password@host formats
        "Database URL": re.compile(
            r"(?i)(mysql|postgres|postgresql|mongodb|redis|amqp)://[^:]*:[^@]+@"
        ),
        # GitHub tokens
        "GitHub Token": re.compile(
            r"(?:ghp_[A-Za-z0-9]{36}|gho_[A-Za-z0-9]{36}|"
            r"ghu_[A-Za-z0-9]{36}|ghs_[A-Za-z0-9]{36})"
        ),
        # Slack tokens
        "Slack Token": re.compile(r"xox[baprs]-[A-Za-z0-9\-]+"),
        # SendGrid API keys
        "SendGrid Key": re.compile(r"SG\.[A-Za-z0-9_\-]{22}\.[A-Za-z0-9_\-]{43}"),
        # Stripe keys
        "Stripe Key": re.compile(r"(?:sk|pk)_(?:live|test)_[A-Za-z0-9]{24,}"),
    }

    # Placeholder used to replace secrets
    REDACTED = "REPLIMAP_REDACTED_SECRET"

    def __init__(self) -> None:
        """Initialize a new SecretScrubber instance."""
        self.findings: list[dict[str, Any]] = []
        self.counts: Counter[str] = Counter()

    def clean(self, text: str | None, context: str = "") -> str | None:
        """
        Scan and redact secrets from text.

        Args:
            text: The text to scan and clean
            context: Optional context string for logging (e.g., "resource.user_data")

        Returns:
            The text with secrets redacted, or None if input was None
        """
        if not text or not isinstance(text, str):
            return text

        cleaned = text
        for name, pattern in self.PATTERNS.items():
            matches = pattern.findall(cleaned)
            if matches:
                match_count = len(matches) if isinstance(matches, list) else 1
                self.findings.append(
                    {
                        "type": name,
                        "context": context,
                        "count": match_count,
                    }
                )
                self.counts[name] += match_count
                cleaned = pattern.sub(self.REDACTED, cleaned)
                logger.debug(f"Redacted {match_count} {name} in {context}")

        return cleaned

    def clean_dict(self, data: dict[str, Any], context: str = "") -> dict[str, Any]:
        """
        Recursively clean a dictionary, scanning all string values.

        Args:
            data: The dictionary to clean
            context: Optional context prefix for logging

        Returns:
            A new dictionary with secrets redacted
        """
        cleaned: dict[str, Any] = {}
        for key, value in data.items():
            ctx = f"{context}.{key}" if context else key
            if isinstance(value, str):
                cleaned[key] = self.clean(value, ctx)
            elif isinstance(value, dict):
                cleaned[key] = self.clean_dict(value, ctx)
            elif isinstance(value, list):
                cleaned[key] = self._clean_list(value, ctx)
            else:
                cleaned[key] = value
        return cleaned

    def _clean_list(self, data: list[Any], context: str) -> list[Any]:
        """
        Recursively clean a list, scanning all string values.

        Args:
            data: The list to clean
            context: Context prefix for logging

        Returns:
            A new list with secrets redacted
        """
        cleaned: list[Any] = []
        for i, item in enumerate(data):
            ctx = f"{context}[{i}]"
            if isinstance(item, str):
                cleaned.append(self.clean(item, ctx))
            elif isinstance(item, dict):
                cleaned.append(self.clean_dict(item, ctx))
            elif isinstance(item, list):
                cleaned.append(self._clean_list(item, ctx))
            else:
                cleaned.append(item)
        return cleaned

    def has_findings(self) -> bool:
        """Check if any secrets were detected during cleaning."""
        return len(self.findings) > 0

    def print_warnings(self, console: Console) -> None:
        """
        Print a summary of redacted secrets to the Rich console.

        Args:
            console: Rich Console instance for output
        """
        if not self.counts:
            return

        console.print()
        console.print("[bold yellow]⚠️  Sensitive Data Redacted:[/bold yellow]")
        for name, count in self.counts.most_common():
            console.print(f"   • {name}: [bold]{count}[/bold]")
        console.print()
        console.print(
            "[dim]Review generated files. Use Terraform variables for secrets.[/dim]"
        )

    def reset(self) -> None:
        """Reset findings and counts for a fresh scan."""
        self.findings = []
        self.counts = Counter()
