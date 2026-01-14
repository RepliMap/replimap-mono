"""
Comprehensive tests for the data sanitization system.

Tests cover:
- DeterministicRedactor: HMAC-based redaction with salt
- SensitivePatternLibrary: Pattern detection
- GlobalSanitizer: Recursive sanitization
- DriftDetector: Configuration drift detection
"""

from __future__ import annotations

import base64
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

import pytest

from replimap.core.security.drift import DriftDetector, DriftType
from replimap.core.security.global_sanitizer import GlobalSanitizer
from replimap.core.security.patterns import SensitivePatternLibrary, Severity
from replimap.core.security.redactor import DeterministicRedactor


@contextmanager
def isolated_redactor_salt(salt_file: Path) -> Generator[None, None, None]:
    """
    Context manager that isolates DeterministicRedactor salt operations.

    Patches SALT_FILE and resets the cache to ensure tests get a fresh salt.
    """
    with patch.object(DeterministicRedactor, "SALT_FILE", salt_file):
        # Reset the cached salt to force re-read/creation
        old_cached = DeterministicRedactor._cached_salt
        DeterministicRedactor._cached_salt = None
        try:
            yield
        finally:
            # Restore cached salt for other tests
            DeterministicRedactor._cached_salt = old_cached


@pytest.fixture
def fresh_redactor_salt(tmp_path: Path) -> Generator[Path, None, None]:
    """Fixture that provides an isolated salt file path with cache reset."""
    salt_file = tmp_path / ".sanitizer_salt"
    with isolated_redactor_salt(salt_file):
        yield salt_file


class TestDeterministicRedactor:
    """Tests for DeterministicRedactor."""

    def test_redact_produces_consistent_output(self, tmp_path: Path) -> None:
        """Same input → same output."""
        salt_file = tmp_path / ".sanitizer_salt"

        with isolated_redactor_salt(salt_file):
            redactor = DeterministicRedactor()

            result1 = redactor.redact("my-secret", "password")
            result2 = redactor.redact("my-secret", "password")

            assert result1 == result2
            assert result1.startswith("REDACTED:")

    def test_different_values_produce_different_output(self, tmp_path: Path) -> None:
        """Different inputs → different outputs."""
        salt_file = tmp_path / ".sanitizer_salt"

        with isolated_redactor_salt(salt_file):
            redactor = DeterministicRedactor()

            result1 = redactor.redact("secret1", "password")
            result2 = redactor.redact("secret2", "password")

            assert result1 != result2

    def test_field_name_affects_hash(self, tmp_path: Path) -> None:
        """Same value with different field names → different hashes."""
        salt_file = tmp_path / ".sanitizer_salt"

        with isolated_redactor_salt(salt_file):
            redactor = DeterministicRedactor()

            result1 = redactor.redact("secret", "password")
            result2 = redactor.redact("secret", "api_key")

            assert result1 != result2

    def test_is_redacted_detection(self, tmp_path: Path) -> None:
        """Can detect redacted values."""
        salt_file = tmp_path / ".sanitizer_salt"

        with isolated_redactor_salt(salt_file):
            redactor = DeterministicRedactor()

            redacted = redactor.redact("secret", "field")

            assert redactor.is_redacted(redacted)
            assert not redactor.is_redacted("plain text")
            assert not redactor.is_redacted("REDACTED")  # Missing format

    def test_salt_file_permissions(self, tmp_path: Path) -> None:
        """Salt file created with secure permissions."""
        salt_file = tmp_path / ".sanitizer_salt"

        with isolated_redactor_salt(salt_file):
            _redactor = DeterministicRedactor()  # noqa: F841 - triggers salt creation

            assert salt_file.exists()
            mode = salt_file.stat().st_mode & 0o777
            assert mode == 0o600

    def test_extract_hash(self, tmp_path: Path) -> None:
        """Can extract hash from redacted value."""
        salt_file = tmp_path / ".sanitizer_salt"

        with isolated_redactor_salt(salt_file):
            redactor = DeterministicRedactor()

            redacted = redactor.redact("secret", "password")
            hash_value = redactor.extract_hash(redacted)

            assert hash_value is not None
            assert len(hash_value) == 16  # HASH_LENGTH

    def test_empty_value_not_redacted(self, tmp_path: Path) -> None:
        """Empty values are not redacted."""
        salt_file = tmp_path / ".sanitizer_salt"

        with isolated_redactor_salt(salt_file):
            redactor = DeterministicRedactor()

            assert redactor.redact("", "field") == ""
            assert redactor.redact(None, "field") is None  # type: ignore

    def test_already_redacted_not_double_redacted(self, tmp_path: Path) -> None:
        """Already redacted values are not double-redacted."""
        salt_file = tmp_path / ".sanitizer_salt"

        with isolated_redactor_salt(salt_file):
            redactor = DeterministicRedactor()

            redacted = redactor.redact("secret", "field")
            double_redacted = redactor.redact(redacted, "field")

            assert redacted == double_redacted

    def test_concurrent_salt_creation(self, tmp_path: Path) -> None:
        """Multiple threads creating redactors simultaneously should be safe."""
        import concurrent.futures

        salt_file = tmp_path / ".sanitizer_salt"
        results: list[str] = []
        errors: list[Exception] = []

        def create_and_redact() -> str:
            """Create a redactor and redact a value."""
            try:
                redactor = DeterministicRedactor()
                return redactor.redact("test-value", "password")
            except Exception as e:
                errors.append(e)
                raise

        with isolated_redactor_salt(salt_file):
            # Run 10 concurrent threads all trying to create redactors
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(create_and_redact) for _ in range(10)]
                for future in concurrent.futures.as_completed(futures):
                    result = future.result()  # Will raise if thread failed
                    results.append(result)

        # No errors should have occurred
        assert len(errors) == 0, f"Concurrent creation errors: {errors}"

        # All results should be identical (same salt used)
        assert len(results) == 10
        assert all(r == results[0] for r in results), "All redactions should be identical"

        # Salt file should exist
        assert salt_file.exists()


class TestSensitivePatternLibrary:
    """Tests for SensitivePatternLibrary."""

    def test_detects_aws_access_key(self) -> None:
        """Detects AWS access key IDs."""
        text = "aws_access_key_id = AKIAIOSFODNN7EXAMPLE"

        sanitized, findings = SensitivePatternLibrary.scan_text(text)

        assert len(findings) > 0
        assert "AKIAIOSFODNN7EXAMPLE" not in sanitized

    def test_detects_private_key(self) -> None:
        """Detects RSA private keys."""
        text = """-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA0Z3VS5JJcds3xfn/ygWyF8PbnGy
-----END RSA PRIVATE KEY-----"""

        sanitized, findings = SensitivePatternLibrary.scan_text(text)

        assert len(findings) > 0
        assert "BEGIN RSA PRIVATE KEY" not in sanitized

    def test_detects_database_url(self) -> None:
        """Detects database connection URLs."""
        text = "DATABASE_URL=postgres://user:password123@localhost:5432/db"

        sanitized, findings = SensitivePatternLibrary.scan_text(text)

        assert len(findings) > 0
        assert "password123" not in sanitized

    def test_detects_stripe_key(self) -> None:
        """Detects Stripe API keys."""
        text = "STRIPE_KEY=sk_live_abcdefghijklmnopqrstuvwx"

        sanitized, findings = SensitivePatternLibrary.scan_text(text)

        assert len(findings) > 0
        assert "sk_live_" not in sanitized

    def test_contains_sensitive_quick_check(self) -> None:
        """Quick check returns correct boolean."""
        assert SensitivePatternLibrary.contains_sensitive("AKIAIOSFODNN7EXAMPLE")
        assert not SensitivePatternLibrary.contains_sensitive("hello world")

    def test_detects_github_token(self) -> None:
        """Detects GitHub personal access tokens."""
        text = "GITHUB_TOKEN=ghp_abcdefghijklmnopqrstuvwxyz1234567890"

        sanitized, findings = SensitivePatternLibrary.scan_text(text)

        assert len(findings) > 0
        assert "ghp_" not in sanitized

    def test_detects_jwt_token(self) -> None:
        """Detects JWT tokens."""
        text = "token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"

        sanitized, findings = SensitivePatternLibrary.scan_text(text)

        assert len(findings) > 0
        assert "eyJ" not in sanitized

    def test_get_patterns_by_severity(self) -> None:
        """Gets patterns at or above severity level."""
        critical_patterns = SensitivePatternLibrary.get_patterns_by_severity(
            Severity.CRITICAL
        )
        high_patterns = SensitivePatternLibrary.get_patterns_by_severity(Severity.HIGH)

        # Critical should be a subset of high+critical
        assert len(critical_patterns) <= len(high_patterns)

        # All critical patterns should be severity CRITICAL
        for pattern in critical_patterns:
            assert pattern.severity == Severity.CRITICAL


class TestGlobalSanitizer:
    """Tests for GlobalSanitizer."""

    def test_sanitizes_password_field(self, tmp_path: Path) -> None:
        """Password fields are redacted."""
        salt_file = tmp_path / ".sanitizer_salt"

        with patch.object(DeterministicRedactor, "SALT_FILE", salt_file):
            sanitizer = GlobalSanitizer()

            config = {
                "MasterUserPassword": "super-secret-123",
                "DBName": "mydb",
            }

            result = sanitizer.sanitize(config, service="rds")

            assert result["MasterUserPassword"].startswith("REDACTED:")
            assert result["DBName"] == "mydb"

    def test_sanitizes_nested_structure(self, tmp_path: Path) -> None:
        """Nested sensitive fields are redacted."""
        salt_file = tmp_path / ".sanitizer_salt"

        with patch.object(DeterministicRedactor, "SALT_FILE", salt_file):
            sanitizer = GlobalSanitizer()

            config = {
                "Database": {
                    "Connection": {
                        "Password": "nested-secret",
                        "Host": "localhost",
                    }
                }
            }

            result = sanitizer.sanitize(config)

            assert result["Database"]["Connection"]["Password"].startswith("REDACTED:")
            assert result["Database"]["Connection"]["Host"] == "localhost"

    def test_sanitizes_userdata_base64(self, tmp_path: Path) -> None:
        """UserData with embedded secrets is sanitized."""
        salt_file = tmp_path / ".sanitizer_salt"

        with patch.object(DeterministicRedactor, "SALT_FILE", salt_file):
            sanitizer = GlobalSanitizer()

            # Create Base64 UserData with embedded secret
            script = "#!/bin/bash\nexport DB_PASSWORD=mysecret123\necho hello"
            encoded = base64.b64encode(script.encode()).decode()

            config = {"UserData": encoded}

            result = sanitizer.sanitize(config, service="ec2")

            # Decode and check secret is gone
            decoded = base64.b64decode(result["UserData"]).decode()
            assert "mysecret123" not in decoded
            assert "REDACTED" in decoded or "DB_PASSWORD" in decoded

    def test_handles_circular_reference(self, tmp_path: Path) -> None:
        """Circular references don't cause infinite loop."""
        salt_file = tmp_path / ".sanitizer_salt"

        with patch.object(DeterministicRedactor, "SALT_FILE", salt_file):
            sanitizer = GlobalSanitizer()

            config: dict = {"name": "test"}
            config["self"] = config  # Circular reference

            # Should not hang
            result = sanitizer.sanitize(config)

            assert result["name"] == "test"
            assert result["self"] == "[CIRCULAR_REFERENCE]"

    def test_respects_max_depth(self, tmp_path: Path) -> None:
        """Deep nesting is handled safely."""
        salt_file = tmp_path / ".sanitizer_salt"

        with patch.object(DeterministicRedactor, "SALT_FILE", salt_file):
            sanitizer = GlobalSanitizer()

            # Create deeply nested structure
            config: dict = {"level": 0}
            current = config
            for i in range(100):
                current["nested"] = {"level": i + 1}
                current = current["nested"]

            # Should not crash
            result = sanitizer.sanitize(config)

            assert result["level"] == 0

    def test_sanitization_result_metadata(self, tmp_path: Path) -> None:
        """Sanitization result includes metadata."""
        salt_file = tmp_path / ".sanitizer_salt"

        with patch.object(DeterministicRedactor, "SALT_FILE", salt_file):
            sanitizer = GlobalSanitizer()

            config = {
                "Password": "secret1",
                "ApiKey": "secret2",
                "Name": "test",
            }

            result = sanitizer.sanitize_with_result(config)

            assert result.was_modified
            assert result.redacted_count == 2
            assert "Password" in str(result.redacted_fields)

    def test_preserves_data_types(self, tmp_path: Path) -> None:
        """Data types are preserved during sanitization."""
        salt_file = tmp_path / ".sanitizer_salt"

        with patch.object(DeterministicRedactor, "SALT_FILE", salt_file):
            sanitizer = GlobalSanitizer()

            config = {
                "count": 42,
                "enabled": True,
                "ratio": 3.14,
                "tags": ["a", "b"],
                "nested": {"key": "value"},
            }

            result = sanitizer.sanitize(config)

            assert isinstance(result["count"], int)
            assert isinstance(result["enabled"], bool)
            assert isinstance(result["ratio"], float)
            assert isinstance(result["tags"], list)
            assert isinstance(result["nested"], dict)


class TestDriftDetector:
    """Tests for DriftDetector."""

    def test_detects_value_change(self, tmp_path: Path) -> None:
        """Detects normal value changes."""
        salt_file = tmp_path / ".sanitizer_salt"

        with patch.object(DeterministicRedactor, "SALT_FILE", salt_file):
            detector = DriftDetector()

            old = {"name": "old-name", "size": 10}
            new = {"name": "new-name", "size": 10}

            result = detector.compare(old, new)

            assert result.has_drift
            assert result.value_changes == 1
            assert any(d.field == "name" for d in result.drifts)

    def test_detects_sensitive_change(self, tmp_path: Path) -> None:
        """Detects changes in redacted values via hash."""
        salt_file = tmp_path / ".sanitizer_salt"

        with patch.object(DeterministicRedactor, "SALT_FILE", salt_file):
            redactor = DeterministicRedactor()
            detector = DriftDetector(redactor)

            old = {"Password": redactor.redact("secret1", "Password")}
            new = {"Password": redactor.redact("secret2", "Password")}

            result = detector.compare(old, new)

            assert result.has_drift
            assert result.sensitive_changes == 1

    def test_no_drift_same_redacted_value(self, tmp_path: Path) -> None:
        """Same redacted value = no drift."""
        salt_file = tmp_path / ".sanitizer_salt"

        with patch.object(DeterministicRedactor, "SALT_FILE", salt_file):
            redactor = DeterministicRedactor()
            detector = DriftDetector(redactor)

            redacted = redactor.redact("same-secret", "Password")
            old = {"Password": redacted}
            new = {"Password": redacted}

            result = detector.compare(old, new)

            assert not result.has_drift

    def test_detects_field_added(self, tmp_path: Path) -> None:
        """Detects new fields."""
        salt_file = tmp_path / ".sanitizer_salt"

        with patch.object(DeterministicRedactor, "SALT_FILE", salt_file):
            detector = DriftDetector()

            old = {"name": "test"}
            new = {"name": "test", "new_field": "value"}

            result = detector.compare(old, new)

            assert result.has_drift
            assert any(d.drift_type == DriftType.FIELD_ADDED for d in result.drifts)

    def test_detects_field_removed(self, tmp_path: Path) -> None:
        """Detects removed fields."""
        salt_file = tmp_path / ".sanitizer_salt"

        with patch.object(DeterministicRedactor, "SALT_FILE", salt_file):
            detector = DriftDetector()

            old = {"name": "test", "old_field": "value"}
            new = {"name": "test"}

            result = detector.compare(old, new)

            assert result.has_drift
            assert any(d.drift_type == DriftType.FIELD_REMOVED for d in result.drifts)

    def test_drift_summary(self, tmp_path: Path) -> None:
        """Drift result provides human-readable summary."""
        salt_file = tmp_path / ".sanitizer_salt"

        with patch.object(DeterministicRedactor, "SALT_FILE", salt_file):
            detector = DriftDetector()

            old = {"name": "old", "count": 1}
            new = {"name": "new", "count": 2, "extra": "value"}

            result = detector.compare(old, new)

            summary = result.summary()
            assert "Drift detected" in summary
            assert "value change" in summary

    def test_nested_drift_detection(self, tmp_path: Path) -> None:
        """Detects drift in nested structures."""
        salt_file = tmp_path / ".sanitizer_salt"

        with patch.object(DeterministicRedactor, "SALT_FILE", salt_file):
            detector = DriftDetector()

            old = {"config": {"setting": "old-value"}}
            new = {"config": {"setting": "new-value"}}

            result = detector.compare(old, new)

            assert result.has_drift
            assert any("config.setting" in d.field for d in result.drifts)


class TestIntegration:
    """Integration tests for the full sanitization pipeline."""

    def test_full_ec2_instance_sanitization(self, tmp_path: Path) -> None:
        """Test sanitization of realistic EC2 instance data."""
        salt_file = tmp_path / ".sanitizer_salt"

        with patch.object(DeterministicRedactor, "SALT_FILE", salt_file):
            # Simulate EC2 describe_instances response
            userdata_script = """#!/bin/bash
export AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
export AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
export DB_PASSWORD=supersecret123
echo "Starting application..."
"""
            encoded_userdata = base64.b64encode(userdata_script.encode()).decode()

            ec2_instance = {
                "InstanceId": "i-1234567890abcdef0",
                "InstanceType": "t3.micro",
                "UserData": encoded_userdata,
                "Tags": [{"Key": "Name", "Value": "WebServer"}],
                "NetworkInterfaces": [
                    {
                        "SubnetId": "subnet-12345",
                        "PrivateIpAddress": "10.0.1.100",
                    }
                ],
            }

            sanitizer = GlobalSanitizer()
            result = sanitizer.sanitize_with_result(ec2_instance, service="ec2")

            # Verify UserData is sanitized
            decoded_userdata = base64.b64decode(result.data["UserData"]).decode()

            assert "AKIAIOSFODNN7EXAMPLE" not in decoded_userdata
            assert "wJalrXUtnFEMI" not in decoded_userdata
            assert "supersecret123" not in decoded_userdata

            # Verify non-sensitive data preserved
            assert result.data["InstanceId"] == "i-1234567890abcdef0"
            assert result.data["InstanceType"] == "t3.micro"

    def test_rds_instance_sanitization(self, tmp_path: Path) -> None:
        """Test sanitization of RDS instance data."""
        salt_file = tmp_path / ".sanitizer_salt"

        with patch.object(DeterministicRedactor, "SALT_FILE", salt_file):
            rds_instance = {
                "DBInstanceIdentifier": "mydb",
                "MasterUserPassword": "super-secret-password",
                "Engine": "postgres",
                "Endpoint": {"Address": "mydb.cluster.us-east-1.rds.amazonaws.com"},
            }

            sanitizer = GlobalSanitizer()
            result = sanitizer.sanitize(rds_instance, service="rds")

            assert result["MasterUserPassword"].startswith("REDACTED:")
            assert result["DBInstanceIdentifier"] == "mydb"
            assert result["Engine"] == "postgres"

    def test_lambda_environment_sanitization(self, tmp_path: Path) -> None:
        """Test sanitization of Lambda environment variables."""
        salt_file = tmp_path / ".sanitizer_salt"

        with patch.object(DeterministicRedactor, "SALT_FILE", salt_file):
            lambda_config = {
                "FunctionName": "my-function",
                "Environment": {
                    "Variables": {
                        "DB_PASSWORD": "secret123",
                        "API_KEY": "sk-1234567890",
                        "LOG_LEVEL": "INFO",
                    }
                },
            }

            sanitizer = GlobalSanitizer()
            result = sanitizer.sanitize(lambda_config, service="lambda")

            # Environment.Variables should have sensitive values redacted
            env_vars = result["Environment"]["Variables"]

            # Sensitive keys should be redacted
            assert (
                env_vars["DB_PASSWORD"].startswith("REDACTED:")
                or "secret123" not in env_vars["DB_PASSWORD"]
            )
            assert (
                env_vars["API_KEY"].startswith("REDACTED:")
                or "sk-1234567890" not in env_vars["API_KEY"]
            )

            # Non-sensitive preserved
            assert result["FunctionName"] == "my-function"

    def test_drift_detection_with_sanitized_data(self, tmp_path: Path) -> None:
        """Test drift detection works with sanitized data."""
        salt_file = tmp_path / ".sanitizer_salt"

        with patch.object(DeterministicRedactor, "SALT_FILE", salt_file):
            sanitizer = GlobalSanitizer()
            detector = DriftDetector()

            # Old state
            old_raw = {"Password": "secret1", "Name": "test"}
            old_sanitized = sanitizer.sanitize(old_raw)

            # New state - password changed
            new_raw = {"Password": "secret2", "Name": "test"}
            new_sanitized = sanitizer.sanitize(new_raw)

            result = detector.compare(old_sanitized, new_sanitized)

            # Should detect password changed
            assert result.has_drift
            assert result.sensitive_changes == 1
