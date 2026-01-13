"""
Deterministic Redaction for RepliMap.

This module provides HMAC-based deterministic redaction that enables
drift detection while protecting sensitive information.

Security Properties:
- Same value + same salt → same hash (enables drift detection)
- Different salts → different hashes (prevents cross-instance attacks)
- HMAC prevents length extension attacks
- Field name included in key (prevents cross-field matching)

Architecture:
    This is the foundation layer for the sanitization pipeline.
    It is used by GlobalSanitizer to redact sensitive field values.

    Raw Value → DeterministicRedactor.redact() → "REDACTED:<hint>:<hash>"
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class DeterministicRedactor:
    """
    Deterministic redaction using HMAC + instance-level salt.

    Security Properties:
    - Same value + same salt → same hash (enables drift detection)
    - Different salts → different hashes (prevents cross-instance attacks)
    - HMAC prevents length extension attacks
    - Field name included in key (prevents cross-field matching)

    Usage:
        redactor = DeterministicRedactor()
        redacted = redactor.redact("my-secret-password", "MasterUserPassword")
        # Returns: "REDACTED:MasterUs:a1b2c3d4e5f6g7h8"

        # Same input → same output (for drift detection)
        assert redactor.redact("my-secret-password", "MasterUserPassword") == redacted
    """

    SALT_FILE = Path.home() / ".replimap" / ".sanitizer_salt"
    HASH_LENGTH = 16  # Truncated hash length
    FIELD_HINT_LENGTH = 8  # Field name hint length
    REDACTED_PREFIX = "REDACTED"

    def __init__(self, salt: Optional[bytes] = None) -> None:
        """
        Initialize redactor.

        Args:
            salt: Optional salt bytes. If None, loads from file or creates new.
        """
        self._salt = salt or self._load_or_create_salt()

    def _load_or_create_salt(self) -> bytes:
        """
        Load existing salt or create new one.

        Salt is stored at ~/.replimap/.sanitizer_salt with 0o600 permissions.
        """
        if self.SALT_FILE.exists():
            # Verify permissions before reading
            mode = self.SALT_FILE.stat().st_mode & 0o777
            if mode != 0o600:
                logger.warning(
                    f"Salt file has insecure permissions {oct(mode)}. "
                    "Regenerating for security."
                )
                return self._create_new_salt()

            return self.SALT_FILE.read_bytes()

        return self._create_new_salt()

    def _create_new_salt(self) -> bytes:
        """Create and securely store new salt."""
        salt = os.urandom(32)

        # Ensure directory exists
        self.SALT_FILE.parent.mkdir(parents=True, exist_ok=True)

        # Write with secure permissions using atomic write pattern
        temp_path = self.SALT_FILE.with_suffix(".tmp")
        temp_path.write_bytes(salt)
        os.chmod(temp_path, 0o600)
        temp_path.rename(self.SALT_FILE)

        logger.debug(f"Created new sanitizer salt at {self.SALT_FILE}")
        return salt

    def redact(self, value: str, field_name: str = "") -> str:
        """
        Deterministically redact a value.

        Args:
            value: The sensitive value to redact
            field_name: Field name for context (improves security, aids debugging)

        Returns:
            Redacted string in format: REDACTED:<field_hint>:<hash>
        """
        if not value:
            return value

        if self.is_redacted(value):
            # Already redacted, return as-is
            return value

        # Create HMAC key from salt + field name
        key = self._salt + field_name.lower().encode("utf-8")

        # Compute HMAC
        mac = hmac.new(key, value.encode("utf-8"), hashlib.sha256)
        hash_value = mac.hexdigest()[: self.HASH_LENGTH]

        # Create field hint (first N chars, alphanumeric only)
        field_hint = "".join(c for c in field_name if c.isalnum())[
            : self.FIELD_HINT_LENGTH
        ]
        if not field_hint:
            field_hint = "val"

        return f"{self.REDACTED_PREFIX}:{field_hint}:{hash_value}"

    def is_redacted(self, value: str) -> bool:
        """Check if a value has already been redacted."""
        if not isinstance(value, str):
            return False
        return value.startswith(f"{self.REDACTED_PREFIX}:")

    def extract_hash(self, redacted_value: str) -> Optional[str]:
        """
        Extract the hash portion from a redacted value.

        Useful for drift detection comparisons.
        """
        if not self.is_redacted(redacted_value):
            return None

        parts = redacted_value.split(":")
        if len(parts) >= 3:
            return parts[-1]
        return None

    @classmethod
    def reset_salt(cls) -> None:
        """
        Delete existing salt (forces regeneration).

        WARNING: This will make all previously redacted values incomparable.
        Use only for testing or security incidents.
        """
        if cls.SALT_FILE.exists():
            cls.SALT_FILE.unlink()
            logger.warning(
                "Sanitizer salt deleted. All redacted values will change on next run."
            )
