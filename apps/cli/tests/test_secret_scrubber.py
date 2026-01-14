"""
Tests for the SecretScrubber security module.

Verifies detection and redaction of sensitive patterns including:
- AWS access keys (permanent and temporary)
- AWS secret access keys
- Private keys
- Generic secrets and passwords
- Bearer tokens
- Database URLs with embedded credentials
- Various API tokens (GitHub, Slack, Stripe, SendGrid)
"""

from replimap.core.security import SecretScrubber


class TestSecretScrubberBasics:
    """Test basic SecretScrubber functionality."""

    def test_init(self) -> None:
        """Scrubber initializes with empty state."""
        scrubber = SecretScrubber()
        assert scrubber.findings == []
        assert len(scrubber.counts) == 0
        assert not scrubber.has_findings()

    def test_clean_none(self) -> None:
        """Cleaning None returns None."""
        scrubber = SecretScrubber()
        assert scrubber.clean(None) is None
        assert not scrubber.has_findings()

    def test_clean_empty_string(self) -> None:
        """Cleaning empty string returns empty string."""
        scrubber = SecretScrubber()
        assert scrubber.clean("") == ""
        assert not scrubber.has_findings()

    def test_clean_safe_text(self) -> None:
        """Text without secrets passes through unchanged."""
        scrubber = SecretScrubber()
        text = "This is safe text with no secrets"
        assert scrubber.clean(text) == text
        assert not scrubber.has_findings()

    def test_reset(self) -> None:
        """Reset clears all findings and counts."""
        scrubber = SecretScrubber()
        # Create some findings
        scrubber.clean("KEY=AKIAIOSFODNN7EXAMPLE")
        assert scrubber.has_findings()

        # Reset
        scrubber.reset()
        assert scrubber.findings == []
        assert len(scrubber.counts) == 0
        assert not scrubber.has_findings()


class TestAWSKeyDetection:
    """Test detection of AWS access keys."""

    def test_permanent_access_key(self) -> None:
        """Detects and redacts permanent AWS access key (AKIA prefix)."""
        scrubber = SecretScrubber()
        text = "AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE"
        result = scrubber.clean(text)

        assert "AKIAIOSFODNN7EXAMPLE" not in result
        assert SecretScrubber.REDACTED in result
        assert scrubber.has_findings()
        assert scrubber.counts["AWS Access Key ID"] == 1

    def test_temporary_access_key(self) -> None:
        """Detects and redacts temporary AWS access key (ASIA prefix - STS)."""
        scrubber = SecretScrubber()
        # AWS keys are exactly 20 characters: AKIA/ASIA (4) + 16 alphanumeric
        # ASIAXOSFODNN7EXAMPLE = 20 characters total
        text = "KEY=ASIAXOSFODNN7EXAMPLE"
        result = scrubber.clean(text)

        assert "ASIAXOSFODNN7EXAMPLE" not in result
        assert SecretScrubber.REDACTED in result
        assert scrubber.has_findings()
        assert scrubber.counts["AWS Access Key ID"] == 1

    def test_secret_access_key(self) -> None:
        """Detects and redacts AWS secret access key."""
        scrubber = SecretScrubber()
        # 40 character secret key
        text = "aws_secret_access_key=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
        result = scrubber.clean(text)

        assert "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY" not in result
        assert SecretScrubber.REDACTED in result
        assert scrubber.has_findings()

    def test_multiple_keys_in_same_text(self) -> None:
        """Detects multiple AWS keys in the same text."""
        scrubber = SecretScrubber()
        # Both keys are exactly 20 characters (AKIA/ASIA + 16)
        text = """
        export AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
        export AWS_ACCESS_KEY_ID=ASIAYOSFODNN7EXAMPLE
        """
        result = scrubber.clean(text)

        assert "AKIAIOSFODNN7EXAMPLE" not in result
        assert "ASIAYOSFODNN7EXAMPLE" not in result
        assert scrubber.counts["AWS Access Key ID"] == 2


class TestPrivateKeyDetection:
    """Test detection of private keys."""

    def test_rsa_private_key(self) -> None:
        """Detects RSA private key header."""
        scrubber = SecretScrubber()
        text = "-----BEGIN RSA PRIVATE KEY-----\nMIIE..."
        result = scrubber.clean(text)

        assert "BEGIN RSA PRIVATE KEY" not in result
        assert scrubber.has_findings()
        assert scrubber.counts["Private Key"] == 1

    def test_ec_private_key(self) -> None:
        """Detects EC private key header."""
        scrubber = SecretScrubber()
        text = "-----BEGIN EC PRIVATE KEY-----"
        result = scrubber.clean(text)

        assert "BEGIN EC PRIVATE KEY" not in result
        assert scrubber.has_findings()

    def test_openssh_private_key(self) -> None:
        """Detects OpenSSH private key header."""
        scrubber = SecretScrubber()
        text = "-----BEGIN OPENSSH PRIVATE KEY-----"
        result = scrubber.clean(text)

        assert "BEGIN OPENSSH PRIVATE KEY" not in result
        assert scrubber.has_findings()

    def test_generic_private_key(self) -> None:
        """Detects generic private key header."""
        scrubber = SecretScrubber()
        text = "-----BEGIN PRIVATE KEY-----"
        result = scrubber.clean(text)

        assert "BEGIN PRIVATE KEY" not in result
        assert scrubber.has_findings()


class TestGenericSecretDetection:
    """Test detection of generic secrets and passwords."""

    def test_password_in_env(self) -> None:
        """Detects password in environment variable format."""
        scrubber = SecretScrubber()
        text = "password=SuperSecretP@ss123!"
        result = scrubber.clean(text)

        assert "SuperSecretP@ss123!" not in result
        assert scrubber.has_findings()
        assert scrubber.counts["Generic Secret"] == 1

    def test_db_password(self) -> None:
        """Detects database password."""
        scrubber = SecretScrubber()
        text = "db_password: MyDatabasePassword99"
        result = scrubber.clean(text)

        assert "MyDatabasePassword99" not in result
        assert scrubber.has_findings()

    def test_api_key(self) -> None:
        """Detects API key."""
        scrubber = SecretScrubber()
        text = "api_key=abcdef123456789012"
        result = scrubber.clean(text)

        assert "abcdef123456789012" not in result
        assert scrubber.has_findings()

    def test_short_values_ignored(self) -> None:
        """Values shorter than 12 characters are not flagged."""
        scrubber = SecretScrubber()
        text = "password=short"
        result = scrubber.clean(text)

        # Short value should not be flagged
        assert result == text
        assert not scrubber.has_findings()


class TestTokenDetection:
    """Test detection of various tokens."""

    def test_bearer_token(self) -> None:
        """Detects Bearer token."""
        scrubber = SecretScrubber()
        text = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        result = scrubber.clean(text)

        assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in result
        assert scrubber.has_findings()
        assert scrubber.counts["Bearer Token"] == 1

    def test_github_pat(self) -> None:
        """Detects GitHub personal access token."""
        scrubber = SecretScrubber()
        text = "GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        result = scrubber.clean(text)

        assert "ghp_" not in result
        assert scrubber.has_findings()
        assert scrubber.counts["GitHub Token"] == 1

    def test_slack_token(self) -> None:
        """Detects Slack token."""
        scrubber = SecretScrubber()
        text = "SLACK_TOKEN=xoxb-123456789012-123456789012-xxxxxxxxxxxx"
        result = scrubber.clean(text)

        assert "xoxb-" not in result
        assert scrubber.has_findings()
        assert scrubber.counts["Slack Token"] == 1

    def test_stripe_key(self) -> None:
        """Detects Stripe API key."""
        scrubber = SecretScrubber()
        text = "STRIPE_KEY=sk_live_51xxxxxxxxxxxxxxxxxxxxxxxxx"
        result = scrubber.clean(text)

        assert "sk_live_" not in result
        assert scrubber.has_findings()
        assert scrubber.counts["Stripe Key"] == 1


class TestDatabaseURLDetection:
    """Test detection of database URLs with embedded credentials."""

    def test_postgres_url(self) -> None:
        """Detects PostgreSQL URL with embedded password."""
        scrubber = SecretScrubber()
        text = "DATABASE_URL=postgres://user:password123@host:5432/db"
        result = scrubber.clean(text)

        assert "password123" not in result
        assert scrubber.has_findings()
        assert scrubber.counts["Database URL"] == 1

    def test_mysql_url(self) -> None:
        """Detects MySQL URL with embedded password."""
        scrubber = SecretScrubber()
        text = "mysql://root:secretpass@localhost/mydb"
        result = scrubber.clean(text)

        assert "secretpass" not in result
        assert scrubber.has_findings()

    def test_redis_url(self) -> None:
        """Detects Redis URL with embedded password."""
        scrubber = SecretScrubber()
        text = "redis://default:myredispass@redis.example.com:6379"
        result = scrubber.clean(text)

        assert "myredispass" not in result
        assert scrubber.has_findings()


class TestDictCleaning:
    """Test cleaning of dictionaries."""

    def test_clean_flat_dict(self) -> None:
        """Cleans secrets from flat dictionary values."""
        scrubber = SecretScrubber()
        data = {
            "safe_key": "safe_value",
            "aws_key": "AKIAIOSFODNN7EXAMPLE",
            "password": "password=SuperSecret12",
        }
        result = scrubber.clean_dict(data)

        assert result["safe_key"] == "safe_value"
        assert "AKIAIOSFODNN7EXAMPLE" not in result["aws_key"]
        assert "SuperSecret12" not in result["password"]
        assert scrubber.has_findings()

    def test_clean_nested_dict(self) -> None:
        """Cleans secrets from nested dictionaries."""
        scrubber = SecretScrubber()
        data = {
            "level1": {
                "level2": {
                    "secret": "api_key=12345678901234567890",
                }
            }
        }
        result = scrubber.clean_dict(data)

        assert "12345678901234567890" not in result["level1"]["level2"]["secret"]
        assert scrubber.has_findings()

    def test_clean_dict_with_list(self) -> None:
        """Cleans secrets from lists within dictionaries."""
        scrubber = SecretScrubber()
        data = {
            "items": [
                "safe",
                "AKIAIOSFODNN7EXAMPLE",
                {"nested": "password=SecretValue12"},
            ]
        }
        result = scrubber.clean_dict(data)

        assert result["items"][0] == "safe"
        assert "AKIAIOSFODNN7EXAMPLE" not in result["items"][1]
        assert "SecretValue12" not in result["items"][2]["nested"]
        assert scrubber.has_findings()

    def test_clean_preserves_non_strings(self) -> None:
        """Non-string values are preserved unchanged."""
        scrubber = SecretScrubber()
        data = {
            "count": 42,
            "enabled": True,
            "ratio": 3.14,
            "nothing": None,
        }
        result = scrubber.clean_dict(data)

        assert result["count"] == 42
        assert result["enabled"] is True
        assert result["ratio"] == 3.14
        assert result["nothing"] is None
        assert not scrubber.has_findings()


class TestContextTracking:
    """Test context tracking for findings."""

    def test_context_in_findings(self) -> None:
        """Findings include context information."""
        scrubber = SecretScrubber()
        scrubber.clean("AKIAIOSFODNN7EXAMPLE", "resource.user_data")

        assert len(scrubber.findings) == 1
        assert scrubber.findings[0]["context"] == "resource.user_data"
        assert scrubber.findings[0]["type"] == "AWS Access Key ID"
        assert scrubber.findings[0]["count"] == 1

    def test_dict_context_paths(self) -> None:
        """Dictionary cleaning builds correct context paths."""
        scrubber = SecretScrubber()
        data = {
            "env": {
                "AWS_KEY": "AKIAIOSFODNN7EXAMPLE",
            }
        }
        scrubber.clean_dict(data, "resource")

        assert len(scrubber.findings) == 1
        assert scrubber.findings[0]["context"] == "resource.env.AWS_KEY"


class TestEdgeCases:
    """Test edge cases and potential false positives."""

    def test_similar_but_not_aws_key(self) -> None:
        """Text similar to AWS key format but not valid is not flagged."""
        scrubber = SecretScrubber()
        # Too short
        text = "AKIA12345"
        result = scrubber.clean(text)
        assert result == text

    def test_public_key_not_flagged(self) -> None:
        """Public key headers should not be flagged."""
        scrubber = SecretScrubber()
        text = "-----BEGIN PUBLIC KEY-----"
        result = scrubber.clean(text)
        assert result == text
        assert not scrubber.has_findings()

    def test_certificate_not_flagged(self) -> None:
        """Certificate headers should not be flagged."""
        scrubber = SecretScrubber()
        text = "-----BEGIN CERTIFICATE-----"
        result = scrubber.clean(text)
        assert result == text
        assert not scrubber.has_findings()

    def test_case_insensitive_keywords(self) -> None:
        """Secret detection is case-insensitive for keywords."""
        scrubber = SecretScrubber()
        text = "PASSWORD=MySecretValue12"
        result = scrubber.clean(text)

        assert "MySecretValue12" not in result
        assert scrubber.has_findings()


class TestUserDataScenarios:
    """Test realistic user_data scenarios."""

    def test_bash_script_with_aws_creds(self) -> None:
        """Detects secrets in bash script user_data."""
        scrubber = SecretScrubber()
        user_data = """#!/bin/bash
export AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
export AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
aws s3 cp s3://bucket/file /tmp/
"""
        result = scrubber.clean(user_data, "i-123.user_data")

        assert "AKIAIOSFODNN7EXAMPLE" not in result
        assert "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY" not in result
        # Script structure should be preserved
        assert "#!/bin/bash" in result
        assert "aws s3 cp" in result
        assert scrubber.has_findings()
        assert scrubber.counts["AWS Access Key ID"] >= 1

    def test_cloud_init_with_database_url(self) -> None:
        """Detects secrets in cloud-init user_data."""
        scrubber = SecretScrubber()
        user_data = """#cloud-config
write_files:
  - path: /etc/app/config.env
    content: |
      DATABASE_URL=postgres://admin:SuperSecret123@db.example.com:5432/app
      REDIS_URL=redis://:password123@cache.example.com:6379
"""
        result = scrubber.clean(user_data, "i-456.user_data")

        assert "SuperSecret123" not in result
        assert "password123" not in result
        assert scrubber.has_findings()


class TestBase64UserDataIntegrity:
    """Test Base64 integrity preservation for UserData fields.

    CRITICAL: When secrets are found in Base64-encoded UserData,
    the ENTIRE field must be replaced to preserve encoding validity.
    """

    def test_userdata_with_aws_key_full_replacement(self) -> None:
        """Verify entire UserData is replaced when AWS key is found."""
        import base64

        scrubber = SecretScrubber()

        # UserData containing AWS access key
        script = """#!/bin/bash
export AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
export AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
echo "Hello World"
"""
        user_data = base64.b64encode(script.encode()).decode()

        result = scrubber.scrub_user_data(user_data, "i-1234567890abcdef0")

        assert result.was_modified is True
        assert "AWS Access Key ID" in result.secrets_found

        # Verify result is valid Base64
        decoded = base64.b64decode(result.value).decode()
        assert "REDACTED BY REPLIMAP" in decoded
        assert "AKIAIOSFODNN7EXAMPLE" not in decoded

    def test_userdata_base64_integrity_always_valid(self) -> None:
        """Verify output is always valid Base64 for various secret types."""
        import base64

        scrubber = SecretScrubber()

        # Various inputs with secrets
        test_cases = [
            "export PASSWORD=secret12345678",
            "api_key=sk_1234567890abcdef1234",
            "-----BEGIN RSA PRIVATE KEY-----\nMIIE...",
            "mysql://user:pass@localhost/db",
        ]

        for script in test_cases:
            user_data = base64.b64encode(script.encode()).decode()
            result = scrubber.scrub_user_data(user_data, "test")

            if result.was_modified:
                # Must be valid Base64
                try:
                    decoded = base64.b64decode(result.value)
                    assert decoded is not None
                except Exception as e:
                    raise AssertionError(
                        f"Invalid Base64 output for input '{script[:30]}...': {e}"
                    )

            scrubber.reset()

    def test_userdata_no_secrets_unchanged(self) -> None:
        """Verify clean UserData is not modified."""
        import base64

        scrubber = SecretScrubber()

        script = """#!/bin/bash
echo "Hello World"
apt-get update
"""
        user_data = base64.b64encode(script.encode()).decode()

        result = scrubber.scrub_user_data(user_data, "test")

        assert result.was_modified is False
        assert result.value == user_data

    def test_userdata_plain_text_handling(self) -> None:
        """Handle non-Base64 UserData gracefully."""
        scrubber = SecretScrubber()

        script = "export API_KEY=secret12345678901234"

        result = scrubber.scrub_user_data(script, "test")

        assert result.was_modified is True
        assert "REDACTED BY REPLIMAP" in result.value

    def test_scrub_attribute_userdata_detection(self) -> None:
        """scrub_attribute recognizes UserData field names."""
        import base64

        scrubber = SecretScrubber()

        script = "export PASSWORD=mysecretpassword123"
        user_data = base64.b64encode(script.encode()).decode()

        # Test various UserData field name variants
        for field_name in ["user_data", "UserData", "userData", "userdata"]:
            scrubber.reset()
            result = scrubber.scrub_attribute(field_name, user_data, "test")

            assert result.was_modified is True
            # Should be valid Base64 (full replacement)
            decoded = base64.b64decode(result.value).decode()
            assert "REDACTED BY REPLIMAP" in decoded

    def test_generic_attribute_inline_redaction(self) -> None:
        """Non-UserData attributes use inline redaction."""
        scrubber = SecretScrubber()

        result = scrubber.scrub_attribute(
            "description",
            "Server with password=secret123456789",
            "test",
        )

        assert result.was_modified is True
        assert "REPLIMAP_REDACTED_SECRET" in result.value
        assert "secret123456789" not in result.value

    def test_scrub_resource_recursive(self) -> None:
        """Test full resource scrubbing with nested structures."""
        import base64

        scrubber = SecretScrubber()

        resource = {
            "id": "i-1234567890abcdef0",
            "user_data": base64.b64encode(
                b"export AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE"
            ).decode(),
            "tags": {
                "Name": "web-server",
                "Password": "password=should-not-be-here-secret123",
            },
            "nested": {
                "api_key": "api_key=sk_12345678901234567890",
            },
        }

        result = scrubber.scrub_resource(resource, "i-1234567890abcdef0")

        # UserData fully replaced (valid Base64)
        decoded_userdata = base64.b64decode(result["user_data"]).decode()
        assert "AKIAIOSFODNN7EXAMPLE" not in decoded_userdata
        assert "REDACTED BY REPLIMAP" in decoded_userdata

        # Other fields inline redacted
        assert "secret123" not in result["tags"]["Password"]
        assert "sk_12345678901234567890" not in result["nested"]["api_key"]

    def test_scrub_resource_preserves_structure(self) -> None:
        """Resource structure is preserved after scrubbing."""
        scrubber = SecretScrubber()

        resource = {
            "id": "test-123",
            "config": {
                "items": ["a", "b", "c"],
                "count": 42,
                "enabled": True,
            },
        }

        result = scrubber.scrub_resource(resource, "test")

        assert result["id"] == "test-123"
        assert result["config"]["items"] == ["a", "b", "c"]
        assert result["config"]["count"] == 42
        assert result["config"]["enabled"] is True

    def test_findings_tracking_with_scrub_user_data(self) -> None:
        """Verify findings are tracked correctly for UserData."""
        import base64

        scrubber = SecretScrubber()

        script = "PASSWORD=secret12345678"
        user_data = base64.b64encode(script.encode()).decode()

        scrubber.scrub_user_data(user_data, "resource-1")
        scrubber.scrub_attribute("desc", "api_key=test1234567890", "resource-2")

        summary = scrubber.get_summary()

        assert summary["total_findings"] == 2
        assert summary["resources_affected"] == 2
