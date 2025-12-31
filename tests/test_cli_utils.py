"""Tests for CLI utility modules."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import pytest

from replimap.cli.utils import (
    CREDENTIAL_CACHE_FILE,
    clear_credential_cache,
    console,
    get_available_profiles,
    get_cached_credentials,
    get_console,
    get_logger,
    get_profile_region,
    logger,
    save_cached_credentials,
)
from replimap.cli.utils.aws_session import (
    CACHE_DIR,
    CREDENTIAL_CACHE_TTL,
    get_credential_cache_key,
)


class TestConsoleUtils:
    """Tests for console.py utilities."""

    def test_console_exists(self):
        """Console instance should be available."""
        assert console is not None

    def test_get_console_returns_console(self):
        """get_console() should return the console instance."""
        assert get_console() is console

    def test_logger_exists(self):
        """Logger instance should be available."""
        assert logger is not None

    def test_get_logger_returns_logger(self):
        """get_logger() should return the logger instance."""
        assert get_logger() is logger

    def test_logger_name(self):
        """Logger should have correct name."""
        assert logger.name == "replimap"


class TestCredentialCacheKey:
    """Tests for credential cache key generation."""

    def test_default_profile_key(self):
        """Default profile should have consistent key."""
        key1 = get_credential_cache_key(None)
        key2 = get_credential_cache_key(None)
        assert key1 == key2

    def test_named_profile_key(self):
        """Named profile should have different key from default."""
        default_key = get_credential_cache_key(None)
        named_key = get_credential_cache_key("production")
        assert default_key != named_key

    def test_different_profiles_different_keys(self):
        """Different profiles should have different keys."""
        key1 = get_credential_cache_key("dev")
        key2 = get_credential_cache_key("prod")
        assert key1 != key2

    def test_key_is_hex_string(self):
        """Cache key should be a hex string (MD5)."""
        key = get_credential_cache_key("test")
        assert len(key) == 32  # MD5 produces 32 hex chars
        assert all(c in "0123456789abcdef" for c in key)


class TestCredentialCaching:
    """Tests for credential caching functions."""

    @pytest.fixture
    def temp_cache_dir(self, tmp_path):
        """Create a temporary cache directory."""
        cache_dir = tmp_path / ".replimap" / "cache"
        cache_dir.mkdir(parents=True)
        return cache_dir

    @pytest.fixture
    def mock_cache_paths(self, temp_cache_dir, monkeypatch):
        """Mock the cache directory paths."""
        cache_file = temp_cache_dir / "credentials.json"
        monkeypatch.setattr("replimap.cli.utils.aws_session.CACHE_DIR", temp_cache_dir)
        monkeypatch.setattr(
            "replimap.cli.utils.aws_session.CREDENTIAL_CACHE_FILE", cache_file
        )
        return cache_file

    def test_get_cached_credentials_no_file(self, mock_cache_paths):
        """Should return None if cache file doesn't exist."""
        result = get_cached_credentials("test")
        assert result is None

    def test_save_and_get_credentials(self, mock_cache_paths):
        """Should save and retrieve credentials."""
        creds = {
            "access_key": "AKIATEST123",
            "secret_key": "secret123",
            "session_token": "token123",
        }
        save_cached_credentials("test-profile", creds)

        retrieved = get_cached_credentials("test-profile")
        assert retrieved is not None
        assert retrieved["access_key"] == "AKIATEST123"
        assert retrieved["secret_key"] == "secret123"  # noqa: S105
        assert retrieved["session_token"] == "token123"  # noqa: S105

    def test_expired_credentials_return_none(self, mock_cache_paths):
        """Should return None for expired credentials."""
        creds = {
            "access_key": "AKIATEST123",
            "secret_key": "secret123",
        }
        # Save with expiration in the past
        past_expiration = datetime.now() - timedelta(hours=1)
        save_cached_credentials("test-profile", creds, expiration=past_expiration)

        retrieved = get_cached_credentials("test-profile")
        assert retrieved is None

    def test_clear_specific_profile(self, mock_cache_paths):
        """Should clear credentials for a specific profile."""
        creds = {"access_key": "test", "secret_key": "test"}

        save_cached_credentials("profile1", creds)
        save_cached_credentials("profile2", creds)

        # Clear only profile1
        clear_credential_cache("profile1")

        assert get_cached_credentials("profile1") is None
        assert get_cached_credentials("profile2") is not None

    def test_clear_all_credentials(self, mock_cache_paths):
        """Should clear all credentials when no profile specified."""
        creds = {"access_key": "test", "secret_key": "test"}

        save_cached_credentials("profile1", creds)
        save_cached_credentials("profile2", creds)

        # Clear all
        clear_credential_cache(None)

        assert get_cached_credentials("profile1") is None
        assert get_cached_credentials("profile2") is None
        assert not mock_cache_paths.exists()

    def test_cache_file_permissions(self, mock_cache_paths):
        """Cache file should have restricted permissions (600)."""
        creds = {"access_key": "test", "secret_key": "test"}
        save_cached_credentials("test", creds)

        # Check file permissions
        mode = mock_cache_paths.stat().st_mode & 0o777
        assert mode == 0o600


class TestProfileManagement:
    """Tests for AWS profile management functions."""

    @pytest.fixture
    def mock_aws_config(self, tmp_path, monkeypatch):
        """Create mock AWS config files."""
        aws_dir = tmp_path / ".aws"
        aws_dir.mkdir()

        # Create config file
        config_file = aws_dir / "config"
        config_file.write_text("""
[default]
region = us-east-1

[profile dev]
region = us-west-2

[profile production]
region = eu-west-1
""")

        # Create credentials file
        creds_file = aws_dir / "credentials"
        creds_file.write_text("""
[default]
aws_access_key_id = AKIADEFAULT

[staging]
aws_access_key_id = AKIASTAGING
""")

        # Mock Path.home() to return our temp directory
        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        return aws_dir

    def test_get_available_profiles(self, mock_aws_config):
        """Should return all available profiles."""
        profiles = get_available_profiles()

        assert "default" in profiles
        assert "dev" in profiles
        assert "production" in profiles
        assert "staging" in profiles

    def test_get_profile_region_default(self, mock_aws_config):
        """Should get region for default profile."""
        region = get_profile_region(None)
        assert region == "us-east-1"

    def test_get_profile_region_named(self, mock_aws_config):
        """Should get region for named profile."""
        region = get_profile_region("dev")
        assert region == "us-west-2"

    def test_get_profile_region_not_found(self, mock_aws_config):
        """Should return None for unknown profile."""
        region = get_profile_region("nonexistent")
        assert region is None

    def test_get_profile_region_from_env(self, mock_aws_config, monkeypatch):
        """Should fall back to environment variable."""
        monkeypatch.setenv("AWS_DEFAULT_REGION", "ap-northeast-1")
        region = get_profile_region("nonexistent")
        assert region == "ap-northeast-1"


class TestCacheConstants:
    """Tests for cache-related constants."""

    def test_cache_dir_path(self):
        """CACHE_DIR should be under user's home directory."""
        assert ".replimap" in str(CACHE_DIR)
        assert "cache" in str(CACHE_DIR)

    def test_credential_cache_file_path(self):
        """CREDENTIAL_CACHE_FILE should be in cache directory."""
        assert CREDENTIAL_CACHE_FILE.name == "credentials.json"
        assert CREDENTIAL_CACHE_FILE.parent == CACHE_DIR

    def test_cache_ttl_is_12_hours(self):
        """Cache TTL should be 12 hours."""
        assert CREDENTIAL_CACHE_TTL == timedelta(hours=12)


class TestOptionsExports:
    """Tests that options are properly exported."""

    def test_profile_option_exists(self):
        """ProfileOption should be importable."""
        from replimap.cli.utils import ProfileOption
        assert ProfileOption is not None

    def test_region_option_exists(self):
        """RegionOption should be importable."""
        from replimap.cli.utils import RegionOption
        assert RegionOption is not None

    def test_optional_region_option_exists(self):
        """OptionalRegionOption should be importable."""
        from replimap.cli.utils import OptionalRegionOption
        assert OptionalRegionOption is not None

    def test_output_dir_option_exists(self):
        """OutputDirOption should be importable."""
        from replimap.cli.utils import OutputDirOption
        assert OutputDirOption is not None

    def test_vpc_option_exists(self):
        """VpcOption should be importable."""
        from replimap.cli.utils import VpcOption
        assert VpcOption is not None

    def test_tag_option_exists(self):
        """TagOption should be importable."""
        from replimap.cli.utils import TagOption
        assert TagOption is not None

    def test_format_option_exists(self):
        """FormatOption should be importable."""
        from replimap.cli.utils import FormatOption
        assert FormatOption is not None

    def test_quiet_option_exists(self):
        """QuietOption should be importable."""
        from replimap.cli.utils import QuietOption
        assert QuietOption is not None

    def test_dry_run_option_exists(self):
        """DryRunOption should be importable."""
        from replimap.cli.utils import DryRunOption
        assert DryRunOption is not None

    def test_force_option_exists(self):
        """ForceOption should be importable."""
        from replimap.cli.utils import ForceOption
        assert ForceOption is not None

    def test_yes_option_exists(self):
        """YesOption should be importable."""
        from replimap.cli.utils import YesOption
        assert YesOption is not None
