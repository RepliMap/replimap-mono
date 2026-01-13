"""
License verification with Ed25519 digital signatures.

Security Model:
- Server signs license with Ed25519 private key
- Client verifies with hardcoded public key
- No local secrets = no secret to steal
- Tamper-evident: any change invalidates signature

Verification Steps:
1. Parse blob format (payload.signature)
2. Decode base64url components
3. Extract key ID from payload
4. Verify signature with public key
5. Validate time (issued, expires, not-before)
6. Check system time integrity
7. Return verified license data
"""

from __future__ import annotations

import base64
import binascii
import json
import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from replimap.licensing.crypto.keys import KeyRegistry
from replimap.licensing.crypto.time_validator import TimeValidationError, TimeValidator

if TYPE_CHECKING:
    from replimap.licensing.secure_models import SecureLicenseData

logger = logging.getLogger(__name__)

UTC = timezone.utc


class LicenseVerificationError(Exception):
    """Base class for license verification errors."""

    pass


class LicenseSignatureError(LicenseVerificationError):
    """License signature verification failed."""

    pass


class LicenseExpiredError(LicenseVerificationError):
    """License has expired."""

    pass


class LicenseNotYetValidError(LicenseVerificationError):
    """License is not yet valid (nbf in future)."""

    pass


class LicenseFormatError(LicenseVerificationError):
    """License blob format is invalid."""

    pass


class LicenseTimeError(LicenseVerificationError):
    """System time validation failed."""

    pass


class LicenseVerifier:
    """
    Verifies Ed25519-signed license blobs.

    Usage:
        verifier = LicenseVerifier()

        try:
            license_data = verifier.verify(license_blob)
            print(f"Valid license: {license_data.plan}")
        except LicenseVerificationError as e:
            print(f"Invalid license: {e}")

    Blob Format:
        BASE64URL(payload_json).BASE64URL(signature_64_bytes)

    Security Properties:
        - Ed25519 signature verification
        - Key rotation support via 'kid' field
        - Time validation (anti-tampering)
        - Strict error handling (fail closed)
    """

    def __init__(
        self,
        time_validator: Optional[TimeValidator] = None,
        strict_time: bool = True,
    ) -> None:
        """
        Initialize verifier.

        Args:
            time_validator: Custom time validator (for testing)
            strict_time: If True, fail on time validation errors
        """
        self.time_validator = time_validator or TimeValidator()
        self.strict_time = strict_time

    def verify(self, license_blob: str) -> "SecureLicenseData":
        """
        Verify license blob and return license data.

        Args:
            license_blob: Format "payload_base64url.signature_base64url"

        Returns:
            Verified SecureLicenseData object

        Raises:
            LicenseFormatError: Invalid blob format
            LicenseSignatureError: Signature verification failed
            LicenseExpiredError: License has expired
            LicenseNotYetValidError: License not yet valid
            LicenseTimeError: System time validation failed
        """
        # Import here to avoid circular imports
        from replimap.licensing.secure_models import SecureLicenseData

        # Step 1: Validate system time
        self._validate_time()

        # Step 2: Parse blob format
        payload_bytes, signature_bytes = self._parse_blob(license_blob)

        # Step 3: Parse payload JSON
        payload = self._parse_payload(payload_bytes)

        # Step 4: Verify signature
        self._verify_signature(payload, payload_bytes, signature_bytes)

        # Step 5: Validate time claims
        self._validate_time_claims(payload)

        # Step 6: Create license data
        return SecureLicenseData.from_payload(payload)

    def verify_payload_only(self, license_blob: str) -> dict:
        """
        Verify and return raw payload without creating SecureLicenseData.

        Useful for debugging or when you need the raw payload.

        Args:
            license_blob: Format "payload_base64url.signature_base64url"

        Returns:
            Verified payload dictionary

        Raises:
            LicenseVerificationError subclass on failure
        """
        # Step 1: Validate system time
        self._validate_time()

        # Step 2: Parse blob format
        payload_bytes, signature_bytes = self._parse_blob(license_blob)

        # Step 3: Parse payload JSON
        payload = self._parse_payload(payload_bytes)

        # Step 4: Verify signature
        self._verify_signature(payload, payload_bytes, signature_bytes)

        # Step 5: Validate time claims
        self._validate_time_claims(payload)

        return payload

    def _validate_time(self) -> None:
        """Validate system time integrity."""
        try:
            is_valid, reason = self.time_validator.validate()
        except TimeValidationError as e:
            if self.strict_time:
                raise LicenseTimeError(str(e)) from e
            logger.warning(f"Time validation error: {e}")
            return

        if not is_valid:
            if self.strict_time:
                raise LicenseTimeError(reason)
            else:
                logger.warning(f"Time validation warning: {reason}")

    def _parse_blob(self, blob: str) -> tuple[bytes, bytes]:
        """Parse blob into payload and signature bytes."""
        blob = blob.strip()

        # Split on '.'
        parts = blob.split(".")
        if len(parts) != 2:
            raise LicenseFormatError(
                f"Invalid blob format: expected 'payload.signature', got {len(parts)} parts"
            )

        payload_b64, signature_b64 = parts

        # Decode base64url (add padding if needed)
        try:
            payload_bytes = self._base64url_decode(payload_b64)
            signature_bytes = self._base64url_decode(signature_b64)
        except (ValueError, binascii.Error) as e:
            raise LicenseFormatError(f"Invalid base64url encoding: {e}") from e

        # Ed25519 signatures are always 64 bytes
        if len(signature_bytes) != 64:
            raise LicenseFormatError(
                f"Invalid signature length: expected 64, got {len(signature_bytes)}"
            )

        return payload_bytes, signature_bytes

    def _parse_payload(self, payload_bytes: bytes) -> dict:
        """Parse payload JSON."""
        try:
            payload_str = payload_bytes.decode("utf-8")
            payload = json.loads(payload_str)
        except UnicodeDecodeError as e:
            raise LicenseFormatError(f"Payload is not valid UTF-8: {e}") from e
        except json.JSONDecodeError as e:
            raise LicenseFormatError(f"Payload is not valid JSON: {e}") from e

        if not isinstance(payload, dict):
            raise LicenseFormatError("Payload must be a JSON object")

        # Validate required fields
        required_fields = ["lic", "plan", "iat"]
        missing = [f for f in required_fields if f not in payload]
        if missing:
            raise LicenseFormatError(f"Missing required fields: {missing}")

        return payload

    def _verify_signature(
        self,
        payload: dict,
        payload_bytes: bytes,
        signature_bytes: bytes,
    ) -> None:
        """Verify Ed25519 signature."""
        # Get key ID (default to current key)
        kid = payload.get("kid", KeyRegistry.CURRENT_KEY_ID)

        # Check if key is valid
        if not KeyRegistry.is_key_valid(kid):
            raise LicenseSignatureError(
                f"Unknown or revoked key ID: {kid}. "
                "This license may have been issued with a compromised key."
            )

        # Verify signature
        is_valid = KeyRegistry.verify_signature(kid, signature_bytes, payload_bytes)

        if not is_valid:
            raise LicenseSignatureError(
                "License signature verification failed. "
                "This license may have been tampered with or is not authentic."
            )

        logger.debug(f"Signature verified with key {kid}")

    def _validate_time_claims(self, payload: dict) -> None:
        """Validate time-related claims (exp, nbf, iat)."""
        now = datetime.now(UTC)
        now_ts = int(now.timestamp())

        # Check expiration
        exp = payload.get("exp")
        if exp is not None:
            if now_ts > exp:
                expires_at = datetime.fromtimestamp(exp, UTC)
                raise LicenseExpiredError(
                    f"License expired at {expires_at.isoformat()}"
                )

        # Check not-before
        nbf = payload.get("nbf")
        if nbf is not None:
            if now_ts < nbf:
                not_before = datetime.fromtimestamp(nbf, UTC)
                raise LicenseNotYetValidError(
                    f"License not valid until {not_before.isoformat()}"
                )

        # Sanity check: issued-at shouldn't be in the future
        iat = payload.get("iat")
        if iat is not None:
            # Allow 5 minutes of clock skew
            if iat > now_ts + 300:
                issued_at = datetime.fromtimestamp(iat, UTC)
                logger.warning(
                    f"License issued in the future: {issued_at.isoformat()}. "
                    "Check system clock."
                )

    @staticmethod
    def _base64url_decode(data: str) -> bytes:
        """Decode base64url with automatic padding."""
        # Add padding if needed
        padding = 4 - len(data) % 4
        if padding != 4:
            data += "=" * padding

        return base64.urlsafe_b64decode(data)


def verify_license_file(
    file_path: str,
    strict_time: bool = True,
) -> Optional["SecureLicenseData"]:
    """
    Convenience function to verify a license file.

    Args:
        file_path: Path to license.key file
        strict_time: If True, fail on time validation errors

    Returns:
        SecureLicenseData if valid, None if file doesn't exist

    Raises:
        LicenseVerificationError: If license is invalid
    """
    from pathlib import Path

    path = Path(file_path)
    if not path.exists():
        return None

    blob = path.read_text().strip()
    verifier = LicenseVerifier(strict_time=strict_time)
    return verifier.verify(blob)
