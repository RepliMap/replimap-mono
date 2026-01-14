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
import tempfile
import threading
from pathlib import Path

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

    # Class-level lock for thread-safe salt file operations
    _salt_lock = threading.Lock()
    # Cached salt to avoid repeated file reads
    _cached_salt: bytes | None = None

    def __init__(self, salt: bytes | None = None) -> None:
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
        Uses thread-safe operations to prevent race conditions when multiple
        scanners run concurrently.
        """
        # Fast path: use cached salt if available
        if DeterministicRedactor._cached_salt is not None:
            return DeterministicRedactor._cached_salt

        with DeterministicRedactor._salt_lock:
            # Double-check after acquiring lock
            if DeterministicRedactor._cached_salt is not None:
                return DeterministicRedactor._cached_salt

            # Try to read existing salt file (EAFP pattern)
            try:
                salt = self.SALT_FILE.read_bytes()
                # Verify permissions
                mode = self.SALT_FILE.stat().st_mode & 0o777
                if mode != 0o600:
                    logger.warning(
                        f"Salt file has insecure permissions {oct(mode)}. "
                        "Regenerating for security."
                    )
                    salt = self._create_new_salt()
                DeterministicRedactor._cached_salt = salt
                return salt
            except FileNotFoundError:
                # Salt file doesn't exist, create it
                salt = self._create_new_salt()
                DeterministicRedactor._cached_salt = salt
                return salt

    def _create_new_salt(self) -> bytes:
        """
        Create and securely store new salt.

        Uses atomic file operations with unique temp files to prevent
        race conditions when multiple processes try to create the salt
        simultaneously.
        """
        salt = os.urandom(32)

        # Ensure directory exists with secure permissions
        parent_dir = self.SALT_FILE.parent
        old_umask = os.umask(0o077)  # Block all group/other access
        try:
            parent_dir.mkdir(parents=True, exist_ok=True)
        finally:
            os.umask(old_umask)

        # Create temp file with unique name using mkstemp for atomic write
        fd = None
        temp_path = None

        try:
            fd, temp_path = tempfile.mkstemp(
                suffix=".tmp",
                prefix=".sanitizer_salt.",
                dir=parent_dir,
            )

            # CRITICAL: Set permissions BEFORE writing any content
            os.fchmod(fd, 0o600)

            # Write salt bytes
            os.write(fd, salt)
            os.fsync(fd)  # Ensure data hits disk
            os.close(fd)
            fd = None  # Mark as closed

            # Atomic rename to target path
            os.rename(temp_path, self.SALT_FILE)
            temp_path = None  # Rename succeeded

            logger.debug(f"Created new sanitizer salt at {self.SALT_FILE}")
            return salt

        except Exception:
            # Clean up on failure
            if fd is not None:
                try:
                    os.close(fd)
                except OSError:
                    pass
            if temp_path is not None:
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass
            raise

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

    def extract_hash(self, redacted_value: str) -> str | None:
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
        with cls._salt_lock:
            # Clear the cached salt
            cls._cached_salt = None
            if cls.SALT_FILE.exists():
                cls.SALT_FILE.unlink()
                logger.warning(
                    "Sanitizer salt deleted. All redacted values will change on next run."
                )
