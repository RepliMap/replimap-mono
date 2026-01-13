"""
Sensitive Pattern Library for RepliMap.

Comprehensive library of sensitive information patterns based on:
- truffleHog (https://github.com/trufflesecurity/trufflehog)
- detect-secrets (https://github.com/Yelp/detect-secrets)
- git-secrets (https://github.com/awslabs/git-secrets)
- AWS documentation

This module provides pattern matching for detecting:
- AWS credentials (access keys, secret keys, session tokens)
- Private keys (RSA, EC, PGP, OpenSSH)
- Database credentials and connection strings
- API keys (Stripe, GitHub, Slack, SendGrid, Twilio)
- Generic secrets, passwords, and tokens

Usage:
    from replimap.core.security.patterns import SensitivePatternLibrary

    # Scan and sanitize text
    sanitized_text, findings = SensitivePatternLibrary.scan_text(user_data)
    if findings:
        logger.warning(f"Found sensitive data: {findings}")

    # Quick check without sanitization
    if SensitivePatternLibrary.contains_sensitive(text):
        # Handle sensitive data
        pass
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple

logger = logging.getLogger(__name__)


class Severity(Enum):
    """Sensitivity severity levels."""

    CRITICAL = "critical"  # Immediate access risk (AWS keys, private keys)
    HIGH = "high"  # Significant risk (database passwords, API keys)
    MEDIUM = "medium"  # Moderate risk (generic secrets)
    LOW = "low"  # Minor risk (potentially sensitive)


@dataclass
class SensitivePattern:
    """Definition of a sensitive information pattern."""

    name: str
    pattern: re.Pattern[str]
    severity: Severity
    replacement: str
    description: str = ""


class SensitivePatternLibrary:
    """
    Comprehensive library of sensitive information patterns.

    Based on:
    - truffleHog (https://github.com/trufflesecurity/trufflehog)
    - detect-secrets (https://github.com/Yelp/detect-secrets)
    - git-secrets (https://github.com/awslabs/git-secrets)
    - AWS documentation

    Usage:
        sanitized_text, findings = SensitivePatternLibrary.scan_text(user_data)
        if findings:
            logger.warning(f"Found sensitive data: {findings}")
    """

    PATTERNS: List[SensitivePattern] = [
        # ═══════════════════════════════════════════════════════════════════
        # AWS CREDENTIALS (Critical)
        # ═══════════════════════════════════════════════════════════════════
        SensitivePattern(
            name="AWS_ACCESS_KEY_ID",
            pattern=re.compile(
                r"(?:A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}"
            ),
            severity=Severity.CRITICAL,
            replacement="<<AWS_ACCESS_KEY_REDACTED>>",
            description="AWS Access Key ID (starts with AKIA, ASIA, etc.)",
        ),
        SensitivePattern(
            name="AWS_SECRET_KEY_ASSIGNMENT",
            pattern=re.compile(
                r"(?i)(aws[_\-]?secret[_\-]?(?:access[_\-]?)?key)\s*[=:]\s*[\"']?"
                r"([A-Za-z0-9/+=]{40})[\"']?"
            ),
            severity=Severity.CRITICAL,
            replacement=r"\1=<<AWS_SECRET_REDACTED>>",
            description="AWS Secret Access Key assignment",
        ),
        SensitivePattern(
            name="AWS_SESSION_TOKEN",
            pattern=re.compile(
                r"(?i)(aws[_\-]?session[_\-]?token)\s*[=:]\s*[\"']?"
                r"([A-Za-z0-9/+=]{100,})[\"']?"
            ),
            severity=Severity.CRITICAL,
            replacement=r"\1=<<AWS_SESSION_TOKEN_REDACTED>>",
            description="AWS Session Token",
        ),
        # ═══════════════════════════════════════════════════════════════════
        # PRIVATE KEYS (Critical)
        # ═══════════════════════════════════════════════════════════════════
        SensitivePattern(
            name="RSA_PRIVATE_KEY",
            pattern=re.compile(
                r"-----BEGIN RSA PRIVATE KEY-----[\s\S]*?-----END RSA PRIVATE KEY-----"
            ),
            severity=Severity.CRITICAL,
            replacement="<<RSA_PRIVATE_KEY_REDACTED>>",
            description="RSA Private Key block",
        ),
        SensitivePattern(
            name="OPENSSH_PRIVATE_KEY",
            pattern=re.compile(
                r"-----BEGIN OPENSSH PRIVATE KEY-----[\s\S]*?"
                r"-----END OPENSSH PRIVATE KEY-----"
            ),
            severity=Severity.CRITICAL,
            replacement="<<OPENSSH_KEY_REDACTED>>",
            description="OpenSSH Private Key block",
        ),
        SensitivePattern(
            name="EC_PRIVATE_KEY",
            pattern=re.compile(
                r"-----BEGIN EC PRIVATE KEY-----[\s\S]*?-----END EC PRIVATE KEY-----"
            ),
            severity=Severity.CRITICAL,
            replacement="<<EC_PRIVATE_KEY_REDACTED>>",
            description="EC Private Key block",
        ),
        SensitivePattern(
            name="PGP_PRIVATE_KEY",
            pattern=re.compile(
                r"-----BEGIN PGP PRIVATE KEY BLOCK-----[\s\S]*?"
                r"-----END PGP PRIVATE KEY BLOCK-----"
            ),
            severity=Severity.CRITICAL,
            replacement="<<PGP_KEY_REDACTED>>",
            description="PGP Private Key block",
        ),
        SensitivePattern(
            name="GENERIC_PRIVATE_KEY",
            pattern=re.compile(
                r"-----BEGIN (?:ENCRYPTED )?PRIVATE KEY-----[\s\S]*?"
                r"-----END (?:ENCRYPTED )?PRIVATE KEY-----"
            ),
            severity=Severity.CRITICAL,
            replacement="<<PRIVATE_KEY_REDACTED>>",
            description="Generic Private Key block",
        ),
        # ═══════════════════════════════════════════════════════════════════
        # DATABASE CREDENTIALS (High)
        # ═══════════════════════════════════════════════════════════════════
        SensitivePattern(
            name="DATABASE_URL",
            pattern=re.compile(
                r"(?i)(mysql|postgres(?:ql)?|mongodb(?:\+srv)?|redis|mssql|mariadb)"
                r"://[^\s<>\"']+:[^\s<>\"']+@[^\s<>\"']+"
            ),
            severity=Severity.HIGH,
            replacement="<<DATABASE_URL_REDACTED>>",
            description="Database connection URL with credentials",
        ),
        SensitivePattern(
            name="DB_PASSWORD_ENV",
            pattern=re.compile(
                r"(?i)(db[_\-]?pass(?:word)?|database[_\-]?pass(?:word)?|"
                r"mysql[_\-]?pass(?:word)?|pg[_\-]?pass(?:word)?|"
                r"postgres[_\-]?pass(?:word)?|mongo[_\-]?pass(?:word)?|"
                r"redis[_\-]?pass(?:word)?)\s*[=:]\s*[\"']?([^\s\"'<>]{4,})[\"']?"
            ),
            severity=Severity.HIGH,
            replacement=r"\1=<<DB_PASSWORD_REDACTED>>",
            description="Database password environment variable",
        ),
        SensitivePattern(
            name="CONNECTION_STRING",
            pattern=re.compile(
                r"(?i)(connection[_\-]?string|connstr|conn[_\-]?str)\s*[=:]\s*"
                r"[\"']?([^\s\"'<>]{20,})[\"']?"
            ),
            severity=Severity.HIGH,
            replacement=r"\1=<<CONNECTION_STRING_REDACTED>>",
            description="Database connection string",
        ),
        # ═══════════════════════════════════════════════════════════════════
        # API KEYS (High)
        # ═══════════════════════════════════════════════════════════════════
        SensitivePattern(
            name="STRIPE_KEY",
            pattern=re.compile(r"(?:sk|pk|rk)_(?:test|live)_[0-9a-zA-Z]{24,}"),
            severity=Severity.CRITICAL,
            replacement="<<STRIPE_KEY_REDACTED>>",
            description="Stripe API key",
        ),
        SensitivePattern(
            name="GITHUB_TOKEN",
            pattern=re.compile(r"(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{36,}"),
            severity=Severity.HIGH,
            replacement="<<GITHUB_TOKEN_REDACTED>>",
            description="GitHub personal access token",
        ),
        SensitivePattern(
            name="GITHUB_OAUTH",
            pattern=re.compile(r"ghu_[A-Za-z0-9]{36}"),
            severity=Severity.HIGH,
            replacement="<<GITHUB_OAUTH_REDACTED>>",
            description="GitHub OAuth token",
        ),
        SensitivePattern(
            name="SLACK_TOKEN",
            pattern=re.compile(
                r"xox[baprs]-[0-9]{10,13}-[0-9]{10,13}(-[a-zA-Z0-9]{24})?"
            ),
            severity=Severity.HIGH,
            replacement="<<SLACK_TOKEN_REDACTED>>",
            description="Slack API token",
        ),
        SensitivePattern(
            name="SLACK_WEBHOOK",
            pattern=re.compile(
                r"https://hooks\.slack\.com/services/"
                r"T[A-Z0-9]{8}/B[A-Z0-9]{8}/[A-Za-z0-9]{24}"
            ),
            severity=Severity.HIGH,
            replacement="<<SLACK_WEBHOOK_REDACTED>>",
            description="Slack webhook URL",
        ),
        SensitivePattern(
            name="SENDGRID_KEY",
            pattern=re.compile(r"SG\.[A-Za-z0-9_-]{22}\.[A-Za-z0-9_-]{43}"),
            severity=Severity.HIGH,
            replacement="<<SENDGRID_KEY_REDACTED>>",
            description="SendGrid API key",
        ),
        SensitivePattern(
            name="TWILIO_KEY",
            pattern=re.compile(r"SK[0-9a-fA-F]{32}"),
            severity=Severity.HIGH,
            replacement="<<TWILIO_KEY_REDACTED>>",
            description="Twilio API key",
        ),
        SensitivePattern(
            name="GENERIC_API_KEY",
            pattern=re.compile(
                r"(?i)(api[_\-]?key|apikey|api[_\-]?secret)\s*[=:]\s*"
                r"[\"']?([A-Za-z0-9_\-]{20,})[\"']?"
            ),
            severity=Severity.HIGH,
            replacement=r"\1=<<API_KEY_REDACTED>>",
            description="Generic API key assignment",
        ),
        # ═══════════════════════════════════════════════════════════════════
        # GENERIC SECRETS (Medium)
        # ═══════════════════════════════════════════════════════════════════
        SensitivePattern(
            name="PASSWORD_ASSIGNMENT",
            pattern=re.compile(
                r"(?i)(pass(?:word)?|passwd|pwd)\s*[=:]\s*[\"']?"
                r"([^\s\"'<>]{6,})[\"']?"
            ),
            severity=Severity.MEDIUM,
            replacement=r"\1=<<PASSWORD_REDACTED>>",
            description="Password assignment",
        ),
        SensitivePattern(
            name="SECRET_ASSIGNMENT",
            pattern=re.compile(
                r"(?i)(secret(?:[_\-]?key)?|token|credential)\s*[=:]\s*"
                r"[\"']?([^\s\"'<>]{8,})[\"']?"
            ),
            severity=Severity.MEDIUM,
            replacement=r"\1=<<SECRET_REDACTED>>",
            description="Secret/token assignment",
        ),
        SensitivePattern(
            name="AUTH_HEADER",
            pattern=re.compile(
                r"(?i)(authorization|bearer|auth[_\-]?token)\s*[=:]\s*"
                r"[\"']?([^\s\"'<>]+)[\"']?"
            ),
            severity=Severity.MEDIUM,
            replacement=r"\1=<<AUTH_REDACTED>>",
            description="Authorization header/token",
        ),
        SensitivePattern(
            name="PRIVATE_KEY_PATH",
            pattern=re.compile(
                r"(?i)(private[_\-]?key[_\-]?(?:file|path)?|key[_\-]?file)\s*[=:]\s*"
                r"[\"']?([^\s\"'<>]+\.(?:pem|key|p12|pfx))[\"']?"
            ),
            severity=Severity.MEDIUM,
            replacement=r"\1=<<KEY_PATH_REDACTED>>",
            description="Private key file path",
        ),
        # ═══════════════════════════════════════════════════════════════════
        # JWT TOKENS (Medium)
        # ═══════════════════════════════════════════════════════════════════
        SensitivePattern(
            name="JWT_TOKEN",
            pattern=re.compile(
                r"eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"
            ),
            severity=Severity.MEDIUM,
            replacement="<<JWT_TOKEN_REDACTED>>",
            description="JWT token",
        ),
    ]

    @classmethod
    def scan_text(cls, text: str) -> Tuple[str, List[str]]:
        """
        Scan text for sensitive information and redact.

        Args:
            text: Text to scan

        Returns:
            Tuple of (sanitized_text, list_of_finding_descriptions)
        """
        if not text:
            return text, []

        findings: List[str] = []
        result = text

        for pattern in cls.PATTERNS:
            matches = pattern.pattern.findall(text)
            if matches:
                count = len(matches) if isinstance(matches[0], str) else len(matches)
                findings.append(f"{pattern.name}: {count} occurrence(s)")
                result = pattern.pattern.sub(pattern.replacement, result)
                logger.debug(f"Redacted {pattern.name}: {count} matches")

        return result, findings

    @classmethod
    def contains_sensitive(cls, text: str) -> bool:
        """
        Quick check if text contains any sensitive patterns.

        More efficient than scan_text() when you don't need the sanitized result.
        """
        if not text:
            return False

        for pattern in cls.PATTERNS:
            if pattern.pattern.search(text):
                return True

        return False

    @classmethod
    def get_patterns_by_severity(
        cls, min_severity: Severity
    ) -> List[SensitivePattern]:
        """Get patterns at or above a severity level."""
        severity_order = [Severity.LOW, Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL]
        min_index = severity_order.index(min_severity)

        return [
            p
            for p in cls.PATTERNS
            if severity_order.index(p.severity) >= min_index
        ]
