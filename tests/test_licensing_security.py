"""
Comprehensive tests for licensing security.

Tests cover:
- Signature verification
- Time validation
- Key rotation
- Tampering detection
- Dev mode removal verification
"""

from __future__ import annotations

import base64
import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

UTC = timezone.utc


class TestKeyRegistry:
    """Tests for Ed25519 key registry."""

    def test_get_valid_key(self):
        """Valid key ID returns public key."""
        from replimap.licensing.crypto.keys import KeyRegistry

        # Should have at least the current key
        key = KeyRegistry.get_public_key(KeyRegistry.CURRENT_KEY_ID)
        assert key is not None
        assert b"BEGIN PUBLIC KEY" in key

    def test_get_unknown_key(self):
        """Unknown key ID returns None."""
        from replimap.licensing.crypto.keys import KeyRegistry

        key = KeyRegistry.get_public_key("nonexistent-key")
        assert key is None

    def test_revoked_key_rejected(self):
        """Revoked keys return None."""
        from replimap.licensing.crypto.keys import KeyRegistry

        # Temporarily add a revoked key
        original_revoked = KeyRegistry.REVOKED_KEY_IDS.copy()
        original_keys = KeyRegistry.PUBLIC_KEYS.copy()
        try:
            KeyRegistry.PUBLIC_KEYS["test-revoked-key"] = b"test"
            KeyRegistry.REVOKED_KEY_IDS.add("test-revoked-key")

            key = KeyRegistry.get_public_key("test-revoked-key")
            assert key is None

        finally:
            KeyRegistry.REVOKED_KEY_IDS = original_revoked
            KeyRegistry.PUBLIC_KEYS = original_keys

    def test_keypair_generation(self):
        """Generated keypairs are valid Ed25519."""
        from replimap.licensing.crypto.keys import generate_keypair

        private_pem, public_pem = generate_keypair()

        assert b"BEGIN PRIVATE KEY" in private_pem
        assert b"BEGIN PUBLIC KEY" in public_pem

        # Verify they work together
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import ed25519

        private_key = serialization.load_pem_private_key(private_pem, password=None)
        public_key = serialization.load_pem_public_key(public_pem)

        assert isinstance(private_key, ed25519.Ed25519PrivateKey)
        assert isinstance(public_key, ed25519.Ed25519PublicKey)

        # Test sign/verify
        message = b"test message"
        signature = private_key.sign(message)
        public_key.verify(signature, message)  # Should not raise

    def test_all_valid_key_ids(self):
        """Get all valid key IDs returns non-revoked keys."""
        from replimap.licensing.crypto.keys import KeyRegistry

        valid_ids = KeyRegistry.get_all_valid_key_ids()
        assert KeyRegistry.CURRENT_KEY_ID in valid_ids

        # None of the revoked keys should be in valid_ids
        for revoked_id in KeyRegistry.REVOKED_KEY_IDS:
            assert revoked_id not in valid_ids


class TestTimeValidator:
    """Tests for time validation."""

    def test_normal_time_progression(self, tmp_path):
        """Normal time progression passes validation."""
        from replimap.licensing.crypto.time_validator import TimeValidator

        time_file = tmp_path / ".time_tracking"
        validator = TimeValidator(time_file=time_file)

        is_valid, reason = validator.validate()
        assert is_valid
        assert reason == "OK"

    def test_detects_backwards_time(self, tmp_path):
        """Detects significant backwards time movement."""
        from replimap.licensing.crypto.time_validator import TimeValidator

        time_file = tmp_path / ".time_tracking"
        validator = TimeValidator(time_file=time_file)

        # Record a future time
        future_time = datetime.now(UTC) + timedelta(days=30)
        data = {
            "time": future_time.isoformat(),
            "checked_at": future_time.isoformat(),
            "version": 1,
        }
        time_file.write_text(json.dumps(data))

        # Now validation should fail
        is_valid, reason = validator.validate()
        assert not is_valid
        assert "backwards" in reason.lower()

    def test_tolerates_minor_drift(self, tmp_path):
        """Tolerates minor clock drift."""
        from replimap.licensing.crypto.time_validator import TimeValidator

        time_file = tmp_path / ".time_tracking"
        validator = TimeValidator(time_file=time_file)

        # Record time 1 hour ago
        past_time = datetime.now(UTC) - timedelta(hours=1)
        data = {
            "time": past_time.isoformat(),
            "checked_at": past_time.isoformat(),
            "version": 1,
        }
        time_file.write_text(json.dumps(data))

        # Should pass (within tolerance)
        is_valid, reason = validator.validate()
        assert is_valid

    def test_reset_clears_tracking(self, tmp_path):
        """Reset removes time tracking file."""
        from replimap.licensing.crypto.time_validator import TimeValidator

        time_file = tmp_path / ".time_tracking"
        validator = TimeValidator(time_file=time_file)

        # Create tracking file
        validator.validate()
        assert time_file.exists()

        # Reset should remove it
        validator.reset()
        assert not time_file.exists()

    def test_corrupted_time_record_handled(self, tmp_path):
        """Corrupted time record is handled gracefully."""
        from replimap.licensing.crypto.time_validator import TimeValidator

        time_file = tmp_path / ".time_tracking"
        time_file.write_text("not valid json")

        validator = TimeValidator(time_file=time_file)
        is_valid, reason = validator.validate()

        # Should pass (treats corrupted record as missing)
        assert is_valid


class TestLicenseVerifier:
    """Tests for license verification."""

    @pytest.fixture
    def test_keypair(self):
        """Generate a test keypair."""
        from replimap.licensing.crypto.keys import generate_keypair

        return generate_keypair()

    @pytest.fixture
    def valid_license_blob(self, test_keypair):
        """Create a valid signed license blob."""
        from replimap.licensing.server.signer import LicenseSigner

        private_pem, public_pem = test_keypair
        signer = LicenseSigner(private_pem, key_id="test-key-001")

        blob = signer.sign_license(
            license_key="RM-TEST-1234-ABCD",
            plan="enterprise",
            email="test@example.com",
            expires_days=365,
        )

        return blob, public_pem

    def test_verify_valid_license(self, valid_license_blob, tmp_path):
        """Valid license passes verification."""
        from replimap.licensing.crypto.keys import KeyRegistry
        from replimap.licensing.verifier import LicenseVerifier

        blob, public_pem = valid_license_blob

        # Add test key to registry
        original_keys = KeyRegistry.PUBLIC_KEYS.copy()
        KeyRegistry.PUBLIC_KEYS["test-key-001"] = public_pem

        try:
            verifier = LicenseVerifier(
                time_validator=MagicMock(validate=MagicMock(return_value=(True, "OK")))
            )

            license_data = verifier.verify(blob)

            assert license_data.license_key == "RM-TEST-1234-ABCD"
            assert license_data.plan.value == "enterprise"
            assert license_data.email == "test@example.com"

        finally:
            KeyRegistry.PUBLIC_KEYS = original_keys

    def test_reject_tampered_license(self, valid_license_blob, tmp_path):
        """Tampered license fails verification."""
        from replimap.licensing.crypto.keys import KeyRegistry
        from replimap.licensing.verifier import LicenseSignatureError, LicenseVerifier

        blob, public_pem = valid_license_blob

        # Tamper with payload
        payload_b64, signature_b64 = blob.split(".")
        # Add padding for base64 decode
        payload_padded = payload_b64 + "=" * (4 - len(payload_b64) % 4)
        payload_bytes = base64.urlsafe_b64decode(payload_padded)
        payload = json.loads(payload_bytes)
        payload["plan"] = "enterprise_plus"  # Tamper!

        tampered_payload = json.dumps(payload).encode()
        tampered_b64 = (
            base64.urlsafe_b64encode(tampered_payload).rstrip(b"=").decode()
        )
        tampered_blob = f"{tampered_b64}.{signature_b64}"

        # Add test key
        original_keys = KeyRegistry.PUBLIC_KEYS.copy()
        KeyRegistry.PUBLIC_KEYS["test-key-001"] = public_pem

        try:
            verifier = LicenseVerifier(
                time_validator=MagicMock(validate=MagicMock(return_value=(True, "OK")))
            )

            with pytest.raises(LicenseSignatureError):
                verifier.verify(tampered_blob)

        finally:
            KeyRegistry.PUBLIC_KEYS = original_keys

    def test_reject_expired_license(self, test_keypair, tmp_path):
        """Expired license is rejected."""
        from cryptography.hazmat.primitives import serialization

        from replimap.licensing.crypto.keys import KeyRegistry
        from replimap.licensing.verifier import LicenseExpiredError, LicenseVerifier

        private_pem, public_pem = test_keypair

        # Manually create expired payload
        now = int(time.time())
        payload = {
            "v": 1,
            "kid": "test-key-001",
            "lic": "RM-EXPIRED-1234",
            "plan": "solo",
            "email": "test@example.com",
            "iat": now - 86400 * 365,  # Issued 1 year ago
            "exp": now - 86400,  # Expired yesterday
        }

        payload_bytes = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
        private_key = serialization.load_pem_private_key(private_pem, password=None)
        signature = private_key.sign(payload_bytes)

        payload_b64 = base64.urlsafe_b64encode(payload_bytes).rstrip(b"=").decode()
        sig_b64 = base64.urlsafe_b64encode(signature).rstrip(b"=").decode()
        expired_blob = f"{payload_b64}.{sig_b64}"

        # Add test key
        original_keys = KeyRegistry.PUBLIC_KEYS.copy()
        KeyRegistry.PUBLIC_KEYS["test-key-001"] = public_pem

        try:
            verifier = LicenseVerifier(
                time_validator=MagicMock(validate=MagicMock(return_value=(True, "OK")))
            )

            with pytest.raises(LicenseExpiredError):
                verifier.verify(expired_blob)

        finally:
            KeyRegistry.PUBLIC_KEYS = original_keys

    def test_invalid_blob_format(self):
        """Invalid blob format raises error."""
        from replimap.licensing.verifier import LicenseFormatError, LicenseVerifier

        verifier = LicenseVerifier(
            time_validator=MagicMock(validate=MagicMock(return_value=(True, "OK")))
        )

        with pytest.raises(LicenseFormatError):
            verifier.verify("not-a-valid-blob")

        with pytest.raises(LicenseFormatError):
            verifier.verify("too.many.parts.here")

    def test_invalid_signature_length(self):
        """Invalid signature length raises error."""
        from replimap.licensing.verifier import LicenseFormatError, LicenseVerifier

        verifier = LicenseVerifier(
            time_validator=MagicMock(validate=MagicMock(return_value=(True, "OK")))
        )

        # Create a blob with wrong signature length
        payload = {"lic": "test", "plan": "free", "iat": int(time.time())}
        payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()
        short_sig = base64.urlsafe_b64encode(b"short").rstrip(b"=").decode()

        with pytest.raises(LicenseFormatError) as exc_info:
            verifier.verify(f"{payload_b64}.{short_sig}")

        assert "signature length" in str(exc_info.value).lower()


class TestDevModeRemoval:
    """Tests to verify dev mode bypass is removed."""

    def test_no_dev_mode_env_var(self, monkeypatch):
        """REPLIMAP_DEV_MODE environment variable has no effect on secure manager."""
        from replimap.licensing.models import Plan
        from replimap.licensing.secure_manager import SecureLicenseManager

        # Set the env var
        monkeypatch.setenv("REPLIMAP_DEV_MODE", "1")

        # Create manager with no license file
        manager = SecureLicenseManager(license_file=Path("/nonexistent/license.key"))

        # Should be FREE, not ENTERPRISE
        assert manager.current_plan == Plan.FREE

    def test_env_vars_not_checked(self, monkeypatch):
        """No environment variables grant license access in secure manager."""
        from replimap.licensing.models import Plan
        from replimap.licensing.secure_manager import SecureLicenseManager

        # Try various env vars that might be bypass attempts
        bypass_attempts = [
            ("REPLIMAP_DEV_MODE", "1"),
            ("REPLIMAP_DEBUG", "1"),
            ("REPLIMAP_ENTERPRISE", "1"),
            ("REPLIMAP_LICENSE_BYPASS", "1"),
            ("DEBUG", "1"),
        ]

        for var, val in bypass_attempts:
            monkeypatch.setenv(var, val)

        manager = SecureLicenseManager(license_file=Path("/nonexistent/license.key"))
        assert manager.current_plan == Plan.FREE

    def test_legacy_manager_still_has_dev_mode(self, monkeypatch):
        """Legacy manager still has dev mode for backward compatibility."""
        # This test documents that the LEGACY manager still has dev mode
        # The secure manager does NOT have dev mode
        from replimap.licensing.manager import is_dev_mode

        monkeypatch.setenv("REPLIMAP_DEV_MODE", "1")
        assert is_dev_mode() is True

        monkeypatch.delenv("REPLIMAP_DEV_MODE")
        assert is_dev_mode() is False


class TestSecureLicenseManager:
    """Tests for SecureLicenseManager."""

    def test_no_license_returns_free(self, tmp_path):
        """No license file returns FREE plan."""
        from replimap.licensing.models import Plan
        from replimap.licensing.secure_manager import SecureLicenseManager

        manager = SecureLicenseManager(license_file=tmp_path / "nonexistent.key")
        assert manager.current_plan == Plan.FREE

    def test_has_feature_respects_plan(self, tmp_path):
        """Feature access respects plan level."""
        from replimap.licensing.models import Feature, Plan
        from replimap.licensing.secure_manager import SecureLicenseManager
        from replimap.licensing.secure_models import SECURE_PLAN_FEATURES

        manager = SecureLicenseManager(license_file=tmp_path / "nonexistent.key")

        # Should have FREE features
        for feature in SECURE_PLAN_FEATURES[Plan.FREE]:
            assert manager.has_feature(feature)

        # Should NOT have ENTERPRISE-only features
        enterprise_only = SECURE_PLAN_FEATURES[Plan.ENTERPRISE] - SECURE_PLAN_FEATURES[Plan.FREE]
        for feature in list(enterprise_only)[:5]:  # Test first 5
            assert not manager.has_feature(feature)

    def test_deactivate_removes_file(self, tmp_path):
        """Deactivate removes license file."""
        from replimap.licensing.secure_manager import SecureLicenseManager

        license_file = tmp_path / "license.key"
        license_file.write_text("test-blob")

        manager = SecureLicenseManager(license_file=license_file)
        manager.deactivate()

        assert not license_file.exists()

    def test_status_without_license(self, tmp_path):
        """Status returns free tier info when no license."""
        from replimap.licensing.secure_manager import SecureLicenseManager

        manager = SecureLicenseManager(license_file=tmp_path / "nonexistent.key")
        status = manager.status()

        assert status["status"] == "free"
        assert status["plan"] == "Free"

    def test_get_limits_returns_free_limits(self, tmp_path):
        """Get limits returns FREE plan limits when no license."""
        from replimap.licensing.secure_manager import SecureLicenseManager
        from replimap.licensing.secure_models import SECURE_PLAN_LIMITS
        from replimap.licensing.models import Plan

        manager = SecureLicenseManager(license_file=tmp_path / "nonexistent.key")
        limits = manager.get_limits()

        expected = SECURE_PLAN_LIMITS[Plan.FREE]
        assert limits.max_accounts == expected.max_accounts
        assert limits.max_regions == expected.max_regions


class TestLicenseSigner:
    """Tests for server-side license signing."""

    def test_sign_and_verify_roundtrip(self):
        """Sign license and verify it works."""
        from replimap.licensing.crypto.keys import KeyRegistry, generate_keypair
        from replimap.licensing.server.signer import LicenseSigner
        from replimap.licensing.verifier import LicenseVerifier

        # Generate keypair
        private_pem, public_pem = generate_keypair()

        # Sign a license
        signer = LicenseSigner(private_pem, key_id="test-roundtrip-key")
        blob = signer.sign_license(
            license_key="RM-ROUND-TRIP-TEST",
            plan="team",
            email="test@example.com",
            organization="Test Org",
            expires_days=30,
        )

        # Verify
        original_keys = KeyRegistry.PUBLIC_KEYS.copy()
        KeyRegistry.PUBLIC_KEYS["test-roundtrip-key"] = public_pem

        try:
            verifier = LicenseVerifier(
                time_validator=MagicMock(validate=MagicMock(return_value=(True, "OK")))
            )
            license_data = verifier.verify(blob)

            assert license_data.license_key == "RM-ROUND-TRIP-TEST"
            assert license_data.plan.value == "team"
            assert license_data.email == "test@example.com"
            assert license_data.organization == "Test Org"

        finally:
            KeyRegistry.PUBLIC_KEYS = original_keys

    def test_sign_developer_license(self):
        """Sign developer license with all features."""
        from replimap.licensing.crypto.keys import KeyRegistry, generate_keypair
        from replimap.licensing.server.signer import LicenseSigner
        from replimap.licensing.verifier import LicenseVerifier

        private_pem, public_pem = generate_keypair()
        signer = LicenseSigner(private_pem, key_id="test-dev-key")

        blob = signer.sign_developer_license(email="dev@example.com", expires_days=7)

        # Verify
        original_keys = KeyRegistry.PUBLIC_KEYS.copy()
        KeyRegistry.PUBLIC_KEYS["test-dev-key"] = public_pem

        try:
            verifier = LicenseVerifier(
                time_validator=MagicMock(validate=MagicMock(return_value=(True, "OK")))
            )
            license_data = verifier.verify(blob)

            assert license_data.plan.value == "enterprise"
            assert license_data.email == "dev@example.com"
            assert license_data.limits.max_accounts == -1  # Unlimited

        finally:
            KeyRegistry.PUBLIC_KEYS = original_keys


class TestSecureLicenseData:
    """Tests for SecureLicenseData model."""

    def test_from_payload_basic(self):
        """Create SecureLicenseData from payload."""
        from replimap.licensing.models import Plan
        from replimap.licensing.secure_models import SecureLicenseData

        now = int(time.time())
        payload = {
            "lic": "RM-TEST-1234",
            "plan": "solo",
            "email": "test@example.com",
            "org": "Test Org",
            "iat": now,
            "exp": now + 86400 * 365,
            "kid": "test-key",
        }

        data = SecureLicenseData.from_payload(payload)

        assert data.license_key == "RM-TEST-1234"
        assert data.plan == Plan.SOLO
        assert data.email == "test@example.com"
        assert data.organization == "Test Org"
        assert data.kid == "test-key"
        assert not data.is_expired()

    def test_has_feature_includes_plan_features(self):
        """has_feature includes plan-level features."""
        from replimap.licensing.models import Feature
        from replimap.licensing.secure_models import SECURE_PLAN_FEATURES, SecureLicenseData

        now = int(time.time())
        payload = {
            "lic": "RM-TEST",
            "plan": "solo",
            "email": "test@example.com",
            "iat": now,
        }

        data = SecureLicenseData.from_payload(payload)

        # Should have SOLO features
        for feature in SECURE_PLAN_FEATURES[data.plan]:
            assert data.has_feature(feature)

    def test_is_expired(self):
        """is_expired correctly detects expiration."""
        from replimap.licensing.secure_models import SecureLicenseData

        now = int(time.time())

        # Not expired
        payload_valid = {
            "lic": "RM-TEST",
            "plan": "solo",
            "email": "test@example.com",
            "iat": now,
            "exp": now + 86400,  # Tomorrow
        }
        data_valid = SecureLicenseData.from_payload(payload_valid)
        assert not data_valid.is_expired()

        # Expired
        payload_expired = {
            "lic": "RM-TEST",
            "plan": "solo",
            "email": "test@example.com",
            "iat": now - 86400 * 2,
            "exp": now - 86400,  # Yesterday
        }
        data_expired = SecureLicenseData.from_payload(payload_expired)
        assert data_expired.is_expired()

        # No expiry
        payload_no_exp = {
            "lic": "RM-TEST",
            "plan": "enterprise",
            "email": "test@example.com",
            "iat": now,
        }
        data_no_exp = SecureLicenseData.from_payload(payload_no_exp)
        assert not data_no_exp.is_expired()

    def test_to_dict_serialization(self):
        """to_dict produces valid serialization."""
        from replimap.licensing.secure_models import SecureLicenseData

        now = int(time.time())
        payload = {
            "lic": "RM-TEST-1234",
            "plan": "team",
            "email": "test@example.com",
            "org": "Test Org",
            "iat": now,
            "exp": now + 86400 * 30,
            "kid": "test-key",
            "nonce": "abc123",
        }

        data = SecureLicenseData.from_payload(payload)
        serialized = data.to_dict()

        assert serialized["license_key"] == "RM-TEST-1234"
        assert serialized["plan"] == "team"
        assert serialized["email"] == "test@example.com"
        assert serialized["kid"] == "test-key"
        assert serialized["nonce"] == "abc123"


class TestDeveloperLicense:
    """Tests for developer license functionality."""

    def test_is_test_environment(self):
        """is_test_environment returns True in pytest."""
        from replimap.licensing.developer import DeveloperLicense

        # Should be True since we're running in pytest
        assert DeveloperLicense.is_test_environment() is True

    def test_get_test_license_data_only_in_tests(self):
        """get_test_license_data works in test environment."""
        from replimap.licensing.developer import DeveloperLicense

        # Should work since we're in pytest
        data = DeveloperLicense.get_test_license_data()

        assert data["plan"] == "enterprise"
        assert data["email"] == "test@replimap.dev"
        assert data["limits"]["max_accounts"] == -1

    def test_allowed_domains(self):
        """Developer license allowed domains are set."""
        from replimap.licensing.developer import DeveloperLicense

        assert "replimap.dev" in DeveloperLicense.ALLOWED_DOMAINS
        assert "replimap.io" in DeveloperLicense.ALLOWED_DOMAINS
