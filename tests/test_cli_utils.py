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


# =============================================================================
# New tests for error_handler, update_checker, tips, and helpers
# =============================================================================


class TestErrorHandler:
    """Tests for error handler module."""

    def test_error_messages_dict_exists(self) -> None:
        """Test that ERROR_MESSAGES dict is populated."""
        from replimap.cli.utils.error_handler import ERROR_MESSAGES

        assert len(ERROR_MESSAGES) > 0
        assert "AccessDenied" in ERROR_MESSAGES
        assert "ExpiredToken" in ERROR_MESSAGES

    def test_error_message_has_required_keys(self) -> None:
        """Test that error messages have required keys."""
        from replimap.cli.utils.error_handler import ERROR_MESSAGES

        for code, info in ERROR_MESSAGES.items():
            assert "title" in info, f"Missing 'title' for {code}"
            assert "message" in info, f"Missing 'message' for {code}"
            assert "fix" in info, f"Missing 'fix' for {code}"

    def test_get_error_code_from_client_error(self) -> None:
        """Test extracting error code from ClientError-like exception."""
        from unittest.mock import MagicMock

        from replimap.cli.utils.error_handler import _get_error_code

        # Mock a ClientError-like exception
        error = MagicMock()
        error.response = {"Error": {"Code": "AccessDenied"}}

        code = _get_error_code(error)
        assert code == "AccessDenied"

    def test_get_error_code_returns_empty_for_unknown(self) -> None:
        """Test that unknown exceptions return empty string."""
        from replimap.cli.utils.error_handler import _get_error_code

        error = Exception("generic error")
        code = _get_error_code(error)
        assert code == ""

    def test_get_error_info_returns_known_error(self) -> None:
        """Test getting info for known error code."""
        from unittest.mock import MagicMock

        from replimap.cli.utils.error_handler import _get_error_info

        error = MagicMock()
        error.response = {"Error": {"Code": "AccessDenied"}}

        info = _get_error_info(error)
        assert info["title"] == "Permission Denied"

    def test_get_error_info_returns_default_for_unknown(self) -> None:
        """Test getting default info for unknown error."""
        from replimap.cli.utils.error_handler import _get_error_info

        error = Exception("unknown error")
        info = _get_error_info(error)
        assert "title" in info
        assert "fix" in info


class TestUpdateChecker:
    """Tests for update checker module."""

    def test_parse_version(self) -> None:
        """Test version parsing."""
        from replimap.cli.utils.update_checker import _parse_version

        assert _parse_version("1.0.0") == (1, 0, 0)
        assert _parse_version("0.1.29") == (0, 1, 29)
        assert _parse_version("2.0.0-beta1") == (2, 0, 0)

    def test_is_newer_version(self) -> None:
        """Test version comparison."""
        from replimap.cli.utils.update_checker import _is_newer_version

        assert _is_newer_version("1.0.0", "0.9.0") is True
        assert _is_newer_version("0.9.0", "1.0.0") is False
        assert _is_newer_version("1.0.0", "1.0.0") is False
        assert _is_newer_version("0.2.0", "0.1.29") is True

    def test_start_update_check_respects_env_var(self, monkeypatch) -> None:
        """Test that update check respects NO_UPDATE_CHECK env var."""
        from replimap.cli.utils.update_checker import start_update_check

        monkeypatch.setenv("REPLIMAP_NO_UPDATE_CHECK", "1")
        # Should not raise, just return early
        start_update_check("1.0.0")

    def test_show_update_notice_respects_env_var(self, monkeypatch) -> None:
        """Test that show_update_notice respects env var."""
        from unittest.mock import MagicMock

        from replimap.cli.utils.update_checker import show_update_notice

        monkeypatch.setenv("REPLIMAP_NO_UPDATE_CHECK", "1")
        console = MagicMock()
        show_update_notice(console)
        # Should not print anything


class TestTips:
    """Tests for tips module."""

    def test_tips_list_not_empty(self) -> None:
        """Test that TIPS list is populated."""
        from replimap.cli.utils.tips import TIPS

        assert len(TIPS) > 0

    def test_show_random_tip_respects_no_tips_env(self, monkeypatch) -> None:
        """Test that tips respect NO_TIPS env var."""
        from unittest.mock import MagicMock

        from replimap.cli.utils.tips import show_random_tip

        monkeypatch.setenv("REPLIMAP_NO_TIPS", "1")
        console = MagicMock()
        show_random_tip(console, probability=1.0)
        console.print.assert_not_called()

    def test_show_random_tip_respects_quiet_env(self, monkeypatch) -> None:
        """Test that tips respect QUIET env var."""
        from unittest.mock import MagicMock

        from replimap.cli.utils.tips import show_random_tip

        monkeypatch.setenv("REPLIMAP_QUIET", "1")
        console = MagicMock()
        show_random_tip(console, probability=1.0)
        console.print.assert_not_called()

    def test_show_random_tip_prints_with_probability_1(self, monkeypatch) -> None:
        """Test that tip is shown with probability 1."""
        from unittest.mock import MagicMock

        from replimap.cli.utils.tips import show_random_tip

        # Clear env vars
        monkeypatch.delenv("REPLIMAP_NO_TIPS", raising=False)
        monkeypatch.delenv("REPLIMAP_QUIET", raising=False)

        console = MagicMock()
        show_random_tip(console, probability=1.0)
        console.print.assert_called_once()

    def test_show_tip_for_command_has_contextual_tips(self, monkeypatch) -> None:
        """Test that contextual tips exist for known commands."""
        from unittest.mock import MagicMock

        from replimap.cli.utils.tips import show_tip_for_command

        monkeypatch.setenv("REPLIMAP_NO_TIPS", "1")
        console = MagicMock()
        # Just verify it doesn't crash
        show_tip_for_command(console, "scan")
        show_tip_for_command(console, "audit")
        show_tip_for_command(console, "unknown")


class TestHelpersFunctions:
    """Tests for helpers module functions."""

    def test_print_graph_stats_empty_graph(self) -> None:
        """Test print_graph_stats with empty graph."""
        from unittest.mock import patch

        from replimap.cli.utils.helpers import print_graph_stats
        from replimap.core import GraphEngine

        graph = GraphEngine()
        # Should not raise
        with patch("replimap.cli.utils.helpers.console") as mock_console:
            print_graph_stats(graph)
            mock_console.print.assert_called()

    def test_print_graph_stats_with_resources(self) -> None:
        """Test print_graph_stats with resources."""
        from unittest.mock import patch

        from replimap.cli.utils.helpers import print_graph_stats
        from replimap.core import GraphEngine
        from replimap.core.models import ResourceNode, ResourceType

        graph = GraphEngine()
        for i in range(5):
            node = ResourceNode(
                id=f"vpc-{i}",
                resource_type=ResourceType.VPC,
                region="us-east-1",
                original_name=f"test-vpc-{i}",
            )
            graph.add_resource(node)

        with patch("replimap.cli.utils.helpers.console") as mock_console:
            print_graph_stats(graph)
            mock_console.print.assert_called()

    def test_print_next_steps(self, monkeypatch) -> None:
        """Test print_next_steps function."""
        from unittest.mock import patch

        from replimap.cli.utils.helpers import print_next_steps

        monkeypatch.setenv("REPLIMAP_NO_TIPS", "1")
        with patch("replimap.cli.utils.helpers.console") as mock_console:
            print_next_steps()
            # Should have printed the panel
            assert mock_console.print.call_count >= 1

    def test_print_scan_summary_is_noop(self) -> None:
        """Test that print_scan_summary is now a no-op."""
        from replimap.cli.utils.helpers import print_scan_summary
        from replimap.core import GraphEngine

        graph = GraphEngine()
        # Should not raise and should be a no-op
        print_scan_summary(graph, 1.0)

    def test_print_next_steps_export(self) -> None:
        """Test that print_next_steps is properly exported."""
        from replimap.cli.utils import print_next_steps

        assert print_next_steps is not None
