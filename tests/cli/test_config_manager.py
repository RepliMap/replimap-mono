"""
ConfigManager Tests.

Tests for the profile-aware configuration management system.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from replimap.cli.config import (
    DEFAULTS,
    ConfigManager,
    ConfigResolution,
    create_config_manager,
)


class TestConfigManagerDefaults:
    """Tests for default configuration values."""

    def test_defaults_exist(self) -> None:
        """DEFAULTS should contain expected keys."""
        assert "region" in DEFAULTS
        assert "profile" in DEFAULTS
        assert "output_format" in DEFAULTS

    def test_get_returns_default(self) -> None:
        """get() should return default value when nothing else configured."""
        config = ConfigManager()
        # Without any config file, should return DEFAULTS
        region = config.get("region")
        assert region == DEFAULTS["region"]

    def test_get_with_explicit_default(self) -> None:
        """get() should return provided default when key not found."""
        config = ConfigManager()
        value = config.get("nonexistent_key", default="fallback")
        assert value == "fallback"


class TestConfigManagerCLIOverrides:
    """Tests for CLI override priority."""

    def test_cli_override_highest_priority(self) -> None:
        """CLI overrides should have highest priority."""
        config = ConfigManager(
            cli_overrides={"region": "us-west-2"},
        )

        region = config.get("region")
        assert region == "us-west-2"

    def test_set_cli_override(self) -> None:
        """set_cli_override should add to overrides."""
        config = ConfigManager()
        config.set_cli_override("region", "eu-west-1")

        region = config.get("region")
        assert region == "eu-west-1"

    def test_cli_override_ignores_none(self) -> None:
        """set_cli_override should ignore None values."""
        config = ConfigManager(cli_overrides={"region": "us-west-2"})
        config.set_cli_override("region", None)

        # Should still have original value
        region = config.get("region")
        assert region == "us-west-2"


class TestConfigManagerEnvironment:
    """Tests for environment variable resolution."""

    def test_env_var_override(self) -> None:
        """Environment variables should override defaults."""
        config = ConfigManager()

        # Set env var
        os.environ["REPLIMAP_REGION"] = "ap-northeast-1"
        try:
            region = config.get("region")
            assert region == "ap-northeast-1"
        finally:
            del os.environ["REPLIMAP_REGION"]

    def test_cli_overrides_env(self) -> None:
        """CLI should override environment variables."""
        config = ConfigManager(cli_overrides={"region": "us-west-2"})

        os.environ["REPLIMAP_REGION"] = "eu-central-1"
        try:
            region = config.get("region")
            assert region == "us-west-2"  # CLI wins
        finally:
            del os.environ["REPLIMAP_REGION"]

    def test_env_key_generation(self) -> None:
        """_key_to_env should generate correct env var names."""
        config = ConfigManager()

        assert config._key_to_env("region") == "REPLIMAP_REGION"
        assert (
            config._key_to_env("scan.parallel_scanners")
            == "REPLIMAP_SCAN_PARALLEL_SCANNERS"
        )
        assert config._key_to_env("output_dir") == "REPLIMAP_OUTPUT_DIR"


class TestConfigManagerEnvParsing:
    """Tests for environment variable value parsing."""

    def test_parse_boolean_true(self) -> None:
        """Boolean values should be parsed correctly."""
        config = ConfigManager()

        for value in ("true", "True", "TRUE", "yes", "1", "on"):
            result = config._parse_env_value(value)
            assert result is True, f"Failed for '{value}'"

    def test_parse_boolean_false(self) -> None:
        """False boolean values should be parsed correctly."""
        config = ConfigManager()

        for value in ("false", "False", "FALSE", "no", "0", "off"):
            result = config._parse_env_value(value)
            assert result is False, f"Failed for '{value}'"

    def test_parse_integer(self) -> None:
        """Integer values should be parsed correctly."""
        config = ConfigManager()

        assert config._parse_env_value("42") == 42
        assert config._parse_env_value("-10") == -10

    def test_parse_float(self) -> None:
        """Float values should be parsed correctly."""
        config = ConfigManager()

        assert config._parse_env_value("3.14") == 3.14
        assert config._parse_env_value("-0.5") == -0.5

    def test_parse_list(self) -> None:
        """Comma-separated values should become lists."""
        config = ConfigManager()

        result = config._parse_env_value("a, b, c")
        assert result == ["a", "b", "c"]

    def test_parse_string(self) -> None:
        """Regular strings should pass through."""
        config = ConfigManager()

        result = config._parse_env_value("hello world")
        assert result == "hello world"


class TestConfigManagerTOML:
    """Tests for TOML configuration file loading."""

    def test_load_nonexistent_file(self) -> None:
        """Loading nonexistent file should not raise."""
        config = ConfigManager(config_path=Path("/nonexistent/config.toml"))
        # Should use defaults
        region = config.get("region")
        assert region == DEFAULTS["region"]

    def test_load_valid_toml(self) -> None:
        """Loading valid TOML should work."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write("""
[global]
region = "eu-west-1"
output_format = "cloudformation"

[profiles.prod]
region = "us-east-1"
output_dir = "/prod/output"
""")
            f.flush()
            config_path = Path(f.name)

        try:
            config = ConfigManager(config_path=config_path)

            # Global config
            assert config.get("region") == "eu-west-1"
            assert config.get("output_format") == "cloudformation"
        finally:
            config_path.unlink()

    def test_profile_override(self) -> None:
        """Profile-specific config should override global."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write("""
[global]
region = "us-east-1"

[profiles.prod]
region = "us-west-2"
""")
            f.flush()
            config_path = Path(f.name)

        try:
            # Without profile
            config_default = ConfigManager(config_path=config_path)
            assert config_default.get("region") == "us-east-1"

            # With prod profile
            config_prod = ConfigManager(profile="prod", config_path=config_path)
            assert config_prod.get("region") == "us-west-2"
        finally:
            config_path.unlink()


class TestConfigManagerCommandConfig:
    """Tests for command-specific configuration."""

    def test_get_all_for_command(self) -> None:
        """get_all_for_command should gather command config."""
        config = ConfigManager(
            cli_overrides={
                "scan.parallel_scanners": 8,
                "scan.use_cache": True,
            }
        )

        scan_config = config.get_all_for_command("scan")

        assert scan_config.get("parallel_scanners") == 8
        assert scan_config.get("use_cache") is True


class TestConfigManagerExplain:
    """Tests for configuration explanation."""

    def test_explain_cli_source(self) -> None:
        """explain() should show CLI as source."""
        config = ConfigManager(cli_overrides={"region": "us-west-2"})
        config.get("region")  # Force resolution

        explanation = config.explain("region")
        assert "cli" in explanation
        assert "us-west-2" in explanation

    def test_explain_default_source(self) -> None:
        """explain() should show default as source."""
        config = ConfigManager()
        config.get("region")  # Force resolution

        explanation = config.explain("region")
        assert "default" in explanation

    def test_to_display_dict(self) -> None:
        """to_display_dict should return displayable config."""
        config = ConfigManager(profile="test")
        display = config.to_display_dict()

        assert "active_profile" in display
        assert display["active_profile"] == "test"
        assert "resolved_values" in display


class TestConfigResolution:
    """Tests for ConfigResolution dataclass."""

    def test_resolution_str(self) -> None:
        """ConfigResolution should have readable string representation."""
        resolution = ConfigResolution(
            key="region",
            value="us-east-1",
            source="cli",
        )

        result = str(resolution)
        assert "region" in result
        assert "us-east-1" in result
        assert "cli" in result


class TestConfigManagerFactory:
    """Tests for factory function."""

    def test_create_config_manager(self) -> None:
        """create_config_manager should create valid instances."""
        config = create_config_manager(
            profile="prod",
            cli_overrides={"region": "us-west-2"},
        )

        assert isinstance(config, ConfigManager)
        assert config.profile == "prod"
        assert config.get("region") == "us-west-2"
