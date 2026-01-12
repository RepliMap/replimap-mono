"""
Tests for Credential Security & Session Management.

Tests the three core security components:
- SecureStorage: Atomic file writes with permission enforcement
- SessionManager: Singleton AWS session management
- CredentialChecker: Credential health checks

These tests verify:
- File permissions are set correctly (0o600 for files, 0o700 for directories)
- Atomic writes prevent race conditions
- Permission validation rejects insecure files in strict mode
- SessionManager singleton pattern works correctly
- Client caching and invalidation functions properly
- Credential expiration detection works
- CredentialChecker handles various scenarios gracefully
"""

from __future__ import annotations

import json
import os
import stat
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from replimap.core.security.credential_checker import CredentialChecker
from replimap.core.security.session_manager import SessionManager
from replimap.core.security.storage import SecureStorage


class TestSecureStorage:
    """Tests for SecureStorage class."""

    def test_ensure_secure_dir_creates_with_700(self, tmp_path: Path) -> None:
        """Directory created with 0o700 permissions."""
        test_dir = tmp_path / "secure_dir"
        SecureStorage.ensure_secure_dir(test_dir)

        assert test_dir.exists()
        mode = stat.S_IMODE(test_dir.stat().st_mode)
        assert mode == 0o700, f"Expected 0o700, got 0o{mode:o}"

    def test_ensure_secure_dir_fixes_existing_permissions(
        self, tmp_path: Path
    ) -> None:
        """Existing directory with wrong permissions gets fixed."""
        test_dir = tmp_path / "existing_dir"
        test_dir.mkdir()
        os.chmod(test_dir, 0o755)  # Insecure permissions

        SecureStorage.ensure_secure_dir(test_dir)

        mode = stat.S_IMODE(test_dir.stat().st_mode)
        assert mode == 0o700, f"Expected 0o700, got 0o{mode:o}"

    def test_ensure_secure_dir_creates_parents(self, tmp_path: Path) -> None:
        """Nested directories are created with correct permissions."""
        test_dir = tmp_path / "level1" / "level2" / "level3"
        SecureStorage.ensure_secure_dir(test_dir)

        assert test_dir.exists()
        # Check all levels have secure permissions
        for level in [
            tmp_path / "level1",
            tmp_path / "level1" / "level2",
            test_dir,
        ]:
            mode = stat.S_IMODE(level.stat().st_mode)
            assert mode == 0o700, f"{level} has mode 0o{mode:o}, expected 0o700"

    def test_write_json_creates_with_600(self, tmp_path: Path) -> None:
        """File created with 0o600 permissions."""
        test_file = tmp_path / "test.json"
        SecureStorage.write_json(test_file, {"key": "value"})

        assert test_file.exists()
        mode = stat.S_IMODE(test_file.stat().st_mode)
        assert mode == 0o600, f"Expected 0o600, got 0o{mode:o}"

    def test_write_json_content_correct(self, tmp_path: Path) -> None:
        """JSON content is written correctly."""
        test_file = tmp_path / "test.json"
        data = {"string": "hello", "number": 42, "nested": {"a": 1, "b": 2}}
        SecureStorage.write_json(test_file, data)

        with open(test_file) as f:
            written_data = json.load(f)

        assert written_data == data

    def test_write_json_atomic_overwrites(self, tmp_path: Path) -> None:
        """Overwriting existing file preserves atomicity."""
        test_file = tmp_path / "test.json"

        # Write initial content
        SecureStorage.write_json(test_file, {"version": 1})
        assert json.loads(test_file.read_text()) == {"version": 1}

        # Overwrite
        SecureStorage.write_json(test_file, {"version": 2})
        assert json.loads(test_file.read_text()) == {"version": 2}

        # Permissions still correct
        mode = stat.S_IMODE(test_file.stat().st_mode)
        assert mode == 0o600

    def test_write_json_creates_parent_directory(self, tmp_path: Path) -> None:
        """Parent directories are created securely when needed."""
        test_file = tmp_path / "subdir" / "nested" / "test.json"
        SecureStorage.write_json(test_file, {"data": True})

        assert test_file.exists()

        # Check parent directories have correct permissions
        parent_mode = stat.S_IMODE((tmp_path / "subdir").stat().st_mode)
        assert parent_mode == 0o700

    def test_read_json_strict_rejects_insecure(self, tmp_path: Path) -> None:
        """Strict mode rejects files with group/world permissions."""
        test_file = tmp_path / "insecure.json"
        test_file.write_text('{"key": "value"}')
        os.chmod(test_file, 0o644)  # world-readable

        with pytest.raises(PermissionError) as exc_info:
            SecureStorage.read_json(test_file, strict=True)

        assert "Insecure file permissions" in str(exc_info.value)
        assert "world-readable" in str(exc_info.value)

    def test_read_json_strict_accepts_secure(self, tmp_path: Path) -> None:
        """Strict mode accepts properly secured files."""
        test_file = tmp_path / "secure.json"
        SecureStorage.write_json(test_file, {"secure": True})

        data = SecureStorage.read_json(test_file, strict=True)
        assert data == {"secure": True}

    def test_read_json_non_strict_warns_but_reads(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Non-strict mode warns but reads insecure files."""
        test_file = tmp_path / "insecure.json"
        test_file.write_text('{"key": "value"}')
        os.chmod(test_file, 0o644)

        data = SecureStorage.read_json(test_file, strict=False)

        assert data == {"key": "value"}
        assert "Insecure file permissions" in caplog.text

    def test_read_json_not_found_raises(self, tmp_path: Path) -> None:
        """FileNotFoundError raised for missing files."""
        test_file = tmp_path / "missing.json"

        with pytest.raises(FileNotFoundError):
            SecureStorage.read_json(test_file)

    def test_verify_permissions_secure_file(self, tmp_path: Path) -> None:
        """verify_permissions returns True for secure files."""
        test_file = tmp_path / "secure.json"
        SecureStorage.write_json(test_file, {})

        is_secure, message = SecureStorage.verify_permissions(test_file)

        assert is_secure is True
        assert "Secure" in message

    def test_verify_permissions_insecure_group(self, tmp_path: Path) -> None:
        """verify_permissions detects group-readable permissions."""
        test_file = tmp_path / "group.json"
        test_file.write_text("{}")
        os.chmod(test_file, 0o640)

        is_secure, message = SecureStorage.verify_permissions(test_file)

        assert is_secure is False
        assert "group-readable" in message

    def test_verify_permissions_insecure_world(self, tmp_path: Path) -> None:
        """verify_permissions detects world-readable permissions."""
        test_file = tmp_path / "world.json"
        test_file.write_text("{}")
        os.chmod(test_file, 0o604)

        is_secure, message = SecureStorage.verify_permissions(test_file)

        assert is_secure is False
        assert "world-readable" in message

    def test_delete_secure_removes_file(self, tmp_path: Path) -> None:
        """delete_secure removes existing files."""
        test_file = tmp_path / "to_delete.json"
        SecureStorage.write_json(test_file, {"delete": "me"})

        result = SecureStorage.delete_secure(test_file)

        assert result is True
        assert not test_file.exists()

    def test_delete_secure_returns_false_for_missing(self, tmp_path: Path) -> None:
        """delete_secure returns False for non-existent files."""
        test_file = tmp_path / "not_there.json"

        result = SecureStorage.delete_secure(test_file)

        assert result is False

    def test_read_json_or_default_returns_default(self, tmp_path: Path) -> None:
        """read_json_or_default returns default for missing files."""
        test_file = tmp_path / "missing.json"

        result = SecureStorage.read_json_or_default(test_file, default={"default": True})

        assert result == {"default": True}

    def test_read_json_or_default_returns_file_content(self, tmp_path: Path) -> None:
        """read_json_or_default returns file content when exists."""
        test_file = tmp_path / "exists.json"
        SecureStorage.write_json(test_file, {"exists": True})

        result = SecureStorage.read_json_or_default(test_file, default={})

        assert result == {"exists": True}


class TestSessionManager:
    """Tests for SessionManager singleton class."""

    def setup_method(self) -> None:
        """Reset singleton before each test."""
        SessionManager.reset()

    def teardown_method(self) -> None:
        """Ensure singleton is reset after each test."""
        SessionManager.reset()

    def test_singleton_pattern(self) -> None:
        """Only one instance is created."""
        with patch("boto3.Session"):
            mgr1 = SessionManager.initialize(profile="test")
            mgr2 = SessionManager.get_instance()

            assert mgr1 is mgr2

    def test_initialize_returns_same_instance(self) -> None:
        """Multiple initialize calls return same instance."""
        with patch("boto3.Session"):
            mgr1 = SessionManager.initialize(profile="test")
            mgr2 = SessionManager.initialize(profile="other")

            assert mgr1 is mgr2

    def test_get_instance_before_init_raises(self) -> None:
        """get_instance() before initialize() raises RuntimeError."""
        with pytest.raises(RuntimeError) as exc_info:
            SessionManager.get_instance()

        assert "not initialized" in str(exc_info.value)

    def test_is_initialized_before_init(self) -> None:
        """is_initialized returns False before initialization."""
        assert SessionManager.is_initialized() is False

    def test_is_initialized_after_init(self) -> None:
        """is_initialized returns True after initialization."""
        with patch("boto3.Session"):
            SessionManager.initialize()

            assert SessionManager.is_initialized() is True

    def test_get_client_caches_by_service_region(self) -> None:
        """Clients are cached by (service, region)."""
        with patch("boto3.Session") as mock_session:
            mock_client = MagicMock()
            mock_session.return_value.client.return_value = mock_client

            mgr = SessionManager.initialize(default_region="us-east-1")

            client1 = mgr.get_client("ec2", "us-east-1")
            client2 = mgr.get_client("ec2", "us-east-1")

            assert client1 is client2
            assert mock_session.return_value.client.call_count == 1

    def test_get_client_different_regions_different_clients(self) -> None:
        """Different regions get different clients."""
        with patch("boto3.Session") as mock_session:
            mgr = SessionManager.initialize(default_region="us-east-1")

            mgr.get_client("ec2", "us-east-1")
            mgr.get_client("ec2", "eu-west-1")

            assert mock_session.return_value.client.call_count == 2

    def test_get_client_different_services_different_clients(self) -> None:
        """Different services get different clients."""
        with patch("boto3.Session") as mock_session:
            mgr = SessionManager.initialize(default_region="us-east-1")

            mgr.get_client("ec2")
            mgr.get_client("rds")

            assert mock_session.return_value.client.call_count == 2

    def test_get_client_uses_default_region(self) -> None:
        """get_client uses default_region when not specified."""
        with patch("boto3.Session") as mock_session:
            mgr = SessionManager.initialize(default_region="us-west-2")

            mgr.get_client("s3")

            mock_session.return_value.client.assert_called_with(
                "s3",
                region_name="us-west-2",
                config=pytest.approx(object, abs=1e10),  # Just check it's called
            )

    def test_get_client_requires_region(self) -> None:
        """get_client raises if no region specified and no default."""
        with patch("boto3.Session"):
            mgr = SessionManager.initialize()  # No default region

            with pytest.raises(ValueError) as exc_info:
                mgr.get_client("ec2")

            assert "Region must be specified" in str(exc_info.value)

    def test_is_expiring_soon_no_expiration(self) -> None:
        """is_expiring_soon returns False for long-term credentials."""
        with patch("boto3.Session") as mock_session:
            mock_creds = MagicMock()
            mock_creds.get_frozen_credentials.return_value.token = None
            mock_session.return_value.get_credentials.return_value = mock_creds

            mgr = SessionManager.initialize()

            assert mgr.is_expiring_soon() is False

    def test_invalidate_clients_clears_cache(self) -> None:
        """invalidate_clients clears the client cache."""
        with patch("boto3.Session"):
            mgr = SessionManager.initialize(default_region="us-east-1")
            mgr.get_client("ec2")
            mgr.get_client("rds")

            assert len(mgr._clients) == 2

            mgr.invalidate_clients()

            assert len(mgr._clients) == 0

    def test_reset_clears_singleton(self) -> None:
        """reset() clears the singleton instance."""
        with patch("boto3.Session"):
            SessionManager.initialize()
            assert SessionManager.is_initialized() is True

            SessionManager.reset()

            assert SessionManager.is_initialized() is False

    def test_get_session_returns_boto3_session(self) -> None:
        """get_session returns the underlying boto3 session."""
        with patch("boto3.Session") as mock_session:
            mock_session_instance = MagicMock()
            mock_session.return_value = mock_session_instance

            mgr = SessionManager.initialize()
            session = mgr.get_session()

            assert session is mock_session_instance


class TestCredentialChecker:
    """Tests for CredentialChecker class."""

    def test_check_skipped_when_flag_set(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Checks are skipped when skip_check=True."""
        session = MagicMock()
        checker = CredentialChecker(session)

        checker.check_and_warn(skip_check=True)

        assert "skipped" in caplog.text
        session.client.assert_not_called()

    def test_handles_expired_credentials_gracefully(self) -> None:
        """Expired credentials are handled gracefully."""
        session = MagicMock()
        session.client.return_value.get_caller_identity.side_effect = (
            create_client_error("ExpiredToken", "Token expired")
        )

        checker = CredentialChecker(session)
        # Should not raise
        checker.check_and_warn()

    def test_handles_access_denied_gracefully(self) -> None:
        """Access denied errors are handled gracefully."""
        session = MagicMock()
        session.client.return_value.get_caller_identity.side_effect = (
            create_client_error("AccessDenied", "Not authorized")
        )

        checker = CredentialChecker(session)
        # Should not raise
        checker.check_and_warn()

    def test_warns_on_old_key(self) -> None:
        """Warning displayed for keys over 90 days old."""
        session = MagicMock()

        # Mock STS identity
        session.client.return_value.get_caller_identity.return_value = {
            "Arn": "arn:aws:iam::123456789012:user/testuser",
            "Account": "123456789012",
            "UserId": "AIDAEXAMPLE",
        }

        # Mock IAM list_access_keys with old key
        old_date = datetime.now(UTC) - timedelta(days=100)
        session.client.return_value.list_access_keys.return_value = {
            "AccessKeyMetadata": [
                {
                    "AccessKeyId": "AKIAIOSFODNN7EXAMPLE",
                    "Status": "Active",
                    "CreateDate": old_date,
                }
            ]
        }

        # Mock credentials (long-term)
        mock_creds = MagicMock()
        mock_creds.get_frozen_credentials.return_value.token = None
        session.get_credentials.return_value = mock_creds

        checker = CredentialChecker(session)

        with patch("rich.console.Console.print") as mock_print:
            checker.check_and_warn()

            # Should have printed a warning panel
            assert mock_print.called

    def test_skips_check_for_temporary_credentials(self) -> None:
        """Key age check skipped for temporary credentials (roles)."""
        session = MagicMock()

        session.client.return_value.get_caller_identity.return_value = {
            "Arn": "arn:aws:iam::123456789012:user/testuser",
            "Account": "123456789012",
            "UserId": "AIDAEXAMPLE",
        }

        # Mock temporary credentials (has session token)
        mock_creds = MagicMock()
        mock_creds.get_frozen_credentials.return_value.token = "some-session-token"
        session.get_credentials.return_value = mock_creds

        checker = CredentialChecker(session)
        checker.check_and_warn()

        # Should not call list_access_keys for temporary creds
        session.client.return_value.list_access_keys.assert_not_called()

    def test_warns_on_root_account(self) -> None:
        """Warning displayed for root account usage."""
        session = MagicMock()
        session.client.return_value.get_caller_identity.return_value = {
            "Arn": "arn:aws:iam::123456789012:root",
            "Account": "123456789012",
            "UserId": "123456789012",
        }

        checker = CredentialChecker(session)

        with patch("rich.console.Console.print") as mock_print:
            checker.check_and_warn()

            # Should have printed a warning
            assert mock_print.called

    def test_get_credential_summary_iam_user(self) -> None:
        """get_credential_summary works for IAM users."""
        session = MagicMock()

        session.client.return_value.get_caller_identity.return_value = {
            "Arn": "arn:aws:iam::123456789012:user/testuser",
            "Account": "123456789012",
            "UserId": "AIDAEXAMPLE",
        }

        checker = CredentialChecker(session)
        summary = checker.get_credential_summary()

        assert summary is not None
        assert summary["account_id"] == "123456789012"
        assert summary["credential_type"] == "iam_user"

    def test_get_credential_summary_assumed_role(self) -> None:
        """get_credential_summary identifies assumed roles."""
        session = MagicMock()

        session.client.return_value.get_caller_identity.return_value = {
            "Arn": "arn:aws:sts::123456789012:assumed-role/TestRole/session",
            "Account": "123456789012",
            "UserId": "AROAEXAMPLE:session",
        }

        checker = CredentialChecker(session)
        summary = checker.get_credential_summary()

        assert summary is not None
        assert summary["credential_type"] == "assumed_role"

    def test_get_credential_summary_handles_errors(self) -> None:
        """get_credential_summary returns None on errors."""
        session = MagicMock()
        session.client.return_value.get_caller_identity.side_effect = Exception(
            "Network error"
        )

        checker = CredentialChecker(session)
        summary = checker.get_credential_summary()

        assert summary is None


class TestPaginatorSessionManagerIntegration:
    """Tests for RobustPaginator integration with SessionManager."""

    def setup_method(self) -> None:
        """Reset singleton before each test."""
        SessionManager.reset()

    def teardown_method(self) -> None:
        """Ensure singleton is reset after each test."""
        SessionManager.reset()

    def test_paginator_accepts_session_manager(self) -> None:
        """RobustPaginator accepts session_manager parameter."""
        from replimap.core.pagination import RobustPaginator

        with patch("boto3.Session"):
            session_manager = SessionManager.initialize(default_region="us-east-1")

            mock_client = MagicMock()
            mock_client.meta.service_model.service_name = "ec2"
            mock_client.meta.region_name = "us-east-1"

            # Should not raise
            paginator = RobustPaginator(
                client=mock_client,
                method_name="describe_instances",
                session_manager=session_manager,
            )

            assert paginator._session_manager is session_manager


# Helper function for creating ClientError mocks
def create_client_error(code: str, message: str):
    """Create a ClientError exception for testing."""
    from botocore.exceptions import ClientError

    return ClientError(
        {"Error": {"Code": code, "Message": message}},
        "TestOperation",
    )
