"""Tests for CLI command separation and registration."""

from __future__ import annotations

import pytest
import typer.testing

from replimap.cli import app, create_app


@pytest.fixture
def runner():
    """Create a CLI test runner."""
    return typer.testing.CliRunner()


class TestCLIAppCreation:
    """Tests for CLI app creation."""

    def test_create_app_returns_typer_app(self):
        """create_app should return a Typer instance."""
        test_app = create_app()
        assert isinstance(test_app, typer.Typer)

    def test_app_is_typer_instance(self):
        """Module-level app should be a Typer instance."""
        assert isinstance(app, typer.Typer)

    def test_app_has_name(self):
        """App should have the correct name."""
        assert app.info.name == "replimap"


class TestMainCommands:
    """Tests for main command registration."""

    def test_scan_command_registered(self, runner):
        """Scan command should be registered."""
        result = runner.invoke(app, ["scan", "--help"])
        assert result.exit_code == 0
        assert "Scan AWS resources" in result.output

    def test_clone_command_registered(self, runner):
        """Clone command should be registered."""
        result = runner.invoke(app, ["clone", "--help"])
        assert result.exit_code == 0
        assert "Clone AWS environment" in result.output

    def test_load_command_registered(self, runner):
        """Load command should be registered."""
        result = runner.invoke(app, ["load", "--help"])
        assert result.exit_code == 0
        assert "Load and display" in result.output

    def test_profiles_command_registered(self, runner):
        """Profiles command should be registered."""
        result = runner.invoke(app, ["profiles", "--help"])
        assert result.exit_code == 0
        assert "List available AWS profiles" in result.output


class TestCacheSubcommands:
    """Tests for cache sub-command group."""

    def test_cache_command_registered(self, runner):
        """Cache command group should be registered."""
        result = runner.invoke(app, ["cache", "--help"])
        assert result.exit_code == 0
        assert "Credential cache management" in result.output

    def test_cache_clear_subcommand(self, runner):
        """Cache clear subcommand should be accessible."""
        result = runner.invoke(app, ["cache", "clear", "--help"])
        assert result.exit_code == 0
        assert "Clear cached AWS credentials" in result.output

    def test_cache_status_subcommand(self, runner):
        """Cache status subcommand should be accessible."""
        result = runner.invoke(app, ["cache", "status", "--help"])
        assert result.exit_code == 0
        assert "Show credential cache status" in result.output


class TestScanCacheSubcommands:
    """Tests for scan-cache sub-command group."""

    def test_scan_cache_command_registered(self, runner):
        """Scan-cache command group should be registered."""
        result = runner.invoke(app, ["scan-cache", "--help"])
        assert result.exit_code == 0
        assert "Scan result cache management" in result.output

    def test_scan_cache_status_subcommand(self, runner):
        """Scan-cache status subcommand should be accessible."""
        result = runner.invoke(app, ["scan-cache", "status", "--help"])
        assert result.exit_code == 0
        assert "Show scan cache status" in result.output

    def test_scan_cache_clear_subcommand(self, runner):
        """Scan-cache clear subcommand should be accessible."""
        result = runner.invoke(app, ["scan-cache", "clear", "--help"])
        assert result.exit_code == 0
        assert "Clear scan result cache" in result.output

    def test_scan_cache_info_subcommand(self, runner):
        """Scan-cache info subcommand should be accessible."""
        result = runner.invoke(app, ["scan-cache", "info", "--help"])
        assert result.exit_code == 0
        assert "Show detailed cache info" in result.output


class TestLicenseSubcommands:
    """Tests for license sub-command group."""

    def test_license_command_registered(self, runner):
        """License command group should be registered."""
        result = runner.invoke(app, ["license", "--help"])
        assert result.exit_code == 0
        assert "License management commands" in result.output

    def test_license_activate_subcommand(self, runner):
        """License activate subcommand should be accessible."""
        result = runner.invoke(app, ["license", "activate", "--help"])
        assert result.exit_code == 0
        assert "Activate a license key" in result.output

    def test_license_status_subcommand(self, runner):
        """License status subcommand should be accessible."""
        result = runner.invoke(app, ["license", "status", "--help"])
        assert result.exit_code == 0
        assert "Show current license status" in result.output

    def test_license_deactivate_subcommand(self, runner):
        """License deactivate subcommand should be accessible."""
        result = runner.invoke(app, ["license", "deactivate", "--help"])
        assert result.exit_code == 0
        assert "Deactivate the current license" in result.output

    def test_license_usage_subcommand(self, runner):
        """License usage subcommand should be accessible."""
        result = runner.invoke(app, ["license", "usage", "--help"])
        assert result.exit_code == 0
        assert "Show detailed usage statistics" in result.output


class TestCommandOptions:
    """Tests for command options."""

    def test_scan_has_profile_option(self, runner):
        """Scan command should have --profile option."""
        result = runner.invoke(app, ["scan", "--help"])
        assert "--profile" in result.output

    def test_scan_has_region_option(self, runner):
        """Scan command should have --region option."""
        result = runner.invoke(app, ["scan", "--help"])
        assert "--region" in result.output

    def test_clone_has_output_dir_option(self, runner):
        """Clone command should have --output-dir option."""
        result = runner.invoke(app, ["clone", "--help"])
        assert "--output-dir" in result.output

    def test_clone_has_format_option(self, runner):
        """Clone command should have --format option."""
        result = runner.invoke(app, ["clone", "--help"])
        assert "--format" in result.output


class TestCommandModuleImports:
    """Tests for command module imports."""

    def test_scan_module_importable(self):
        """Scan command module should be importable."""
        from replimap.cli.commands import scan
        assert hasattr(scan, "register")

    def test_clone_module_importable(self):
        """Clone command module should be importable."""
        from replimap.cli.commands import clone
        assert hasattr(clone, "register")

    def test_load_module_importable(self):
        """Load command module should be importable."""
        from replimap.cli.commands import load
        assert hasattr(load, "register")

    def test_profiles_module_importable(self):
        """Profiles command module should be importable."""
        from replimap.cli.commands import profiles
        assert hasattr(profiles, "register")

    def test_cache_module_importable(self):
        """Cache command module should be importable."""
        from replimap.cli.commands import cache
        assert hasattr(cache, "register")

    def test_license_module_importable(self):
        """License command module should be importable."""
        from replimap.cli.commands import license
        assert hasattr(license, "register")

    def test_register_all_commands_importable(self):
        """register_all_commands should be importable."""
        from replimap.cli.commands import register_all_commands
        assert callable(register_all_commands)


class TestVersionOption:
    """Tests for version option."""

    def test_version_option(self, runner):
        """--version should show version."""
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "RepliMap" in result.output

    def test_version_short_option(self, runner):
        """-v should show version."""
        result = runner.invoke(app, ["-v"])
        assert result.exit_code == 0
        assert "RepliMap" in result.output
