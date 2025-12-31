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

    def test_audit_command_registered(self, runner):
        """Audit command should be registered."""
        result = runner.invoke(app, ["audit", "--help"])
        assert result.exit_code == 0
        assert "Audit" in result.output or "audit" in result.output.lower()

    def test_graph_command_registered(self, runner):
        """Graph command should be registered."""
        result = runner.invoke(app, ["graph", "--help"])
        assert result.exit_code == 0
        assert "graph" in result.output.lower()

    def test_drift_command_registered(self, runner):
        """Drift command should be registered."""
        result = runner.invoke(app, ["drift", "--help"])
        assert result.exit_code == 0
        assert "drift" in result.output.lower()

    def test_deps_command_registered(self, runner):
        """Deps command should be registered."""
        result = runner.invoke(app, ["deps", "--help"])
        assert result.exit_code == 0
        assert "depend" in result.output.lower()

    def test_cost_command_registered(self, runner):
        """Cost command should be registered."""
        result = runner.invoke(app, ["cost", "--help"])
        assert result.exit_code == 0
        assert "cost" in result.output.lower()

    def test_remediate_command_registered(self, runner):
        """Remediate command should be registered."""
        result = runner.invoke(app, ["remediate", "--help"])
        assert result.exit_code == 0
        assert "remediat" in result.output.lower()

    def test_validate_command_registered(self, runner):
        """Validate command should be registered."""
        result = runner.invoke(app, ["validate", "--help"])
        assert result.exit_code == 0
        assert "validat" in result.output.lower()

    def test_unused_command_registered(self, runner):
        """Unused command should be registered."""
        result = runner.invoke(app, ["unused", "--help"])
        assert result.exit_code == 0
        assert "unused" in result.output.lower()

    def test_trends_command_registered(self, runner):
        """Trends command should be registered."""
        result = runner.invoke(app, ["trends", "--help"])
        assert result.exit_code == 0
        assert "trend" in result.output.lower()

    def test_transfer_command_registered(self, runner):
        """Transfer command should be registered."""
        result = runner.invoke(app, ["transfer", "--help"])
        assert result.exit_code == 0
        assert "transfer" in result.output.lower()


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


class TestUpgradeSubcommands:
    """Tests for upgrade sub-command group."""

    def test_upgrade_command_registered(self, runner):
        """Upgrade command group should be registered."""
        result = runner.invoke(app, ["upgrade", "--help"])
        assert result.exit_code == 0
        assert "upgrade" in result.output.lower()

    def test_upgrade_solo_subcommand(self, runner):
        """Upgrade solo subcommand should be accessible."""
        result = runner.invoke(app, ["upgrade", "solo", "--help"])
        assert result.exit_code == 0

    def test_upgrade_pro_subcommand(self, runner):
        """Upgrade pro subcommand should be accessible."""
        result = runner.invoke(app, ["upgrade", "pro", "--help"])
        assert result.exit_code == 0

    def test_upgrade_team_subcommand(self, runner):
        """Upgrade team subcommand should be accessible."""
        result = runner.invoke(app, ["upgrade", "team", "--help"])
        assert result.exit_code == 0


class TestSnapshotSubcommands:
    """Tests for snapshot sub-command group."""

    def test_snapshot_command_registered(self, runner):
        """Snapshot command group should be registered."""
        result = runner.invoke(app, ["snapshot", "--help"])
        assert result.exit_code == 0
        assert "snapshot" in result.output.lower()

    def test_snapshot_save_subcommand(self, runner):
        """Snapshot save subcommand should be accessible."""
        result = runner.invoke(app, ["snapshot", "save", "--help"])
        assert result.exit_code == 0

    def test_snapshot_list_subcommand(self, runner):
        """Snapshot list subcommand should be accessible."""
        result = runner.invoke(app, ["snapshot", "list", "--help"])
        assert result.exit_code == 0

    def test_snapshot_diff_subcommand(self, runner):
        """Snapshot diff subcommand should be accessible."""
        result = runner.invoke(app, ["snapshot", "diff", "--help"])
        assert result.exit_code == 0

    def test_snapshot_show_subcommand(self, runner):
        """Snapshot show subcommand should be accessible."""
        result = runner.invoke(app, ["snapshot", "show", "--help"])
        assert result.exit_code == 0


class TestTrustCenterSubcommands:
    """Tests for trust-center sub-command group."""

    def test_trust_center_command_registered(self, runner):
        """Trust-center command group should be registered."""
        result = runner.invoke(app, ["trust-center", "--help"])
        assert result.exit_code == 0
        assert "trust" in result.output.lower()

    def test_trust_center_status_subcommand(self, runner):
        """Trust-center status subcommand should be accessible."""
        result = runner.invoke(app, ["trust-center", "status", "--help"])
        assert result.exit_code == 0

    def test_trust_center_report_subcommand(self, runner):
        """Trust-center report subcommand should be accessible."""
        result = runner.invoke(app, ["trust-center", "report", "--help"])
        assert result.exit_code == 0


class TestDRSubcommands:
    """Tests for dr sub-command group."""

    def test_dr_command_registered(self, runner):
        """DR command group should be registered."""
        result = runner.invoke(app, ["dr", "--help"])
        assert result.exit_code == 0
        # dr = disaster recovery
        assert (
            "disaster" in result.output.lower()
            or "recovery" in result.output.lower()
            or "dr" in result.output.lower()
        )

    def test_dr_assess_subcommand(self, runner):
        """DR assess subcommand should be accessible."""
        result = runner.invoke(app, ["dr", "assess", "--help"])
        assert result.exit_code == 0

    def test_dr_scorecard_subcommand(self, runner):
        """DR scorecard subcommand should be accessible."""
        result = runner.invoke(app, ["dr", "scorecard", "--help"])
        assert result.exit_code == 0


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

    def test_audit_module_importable(self):
        """Audit command module should be importable."""
        from replimap.cli.commands import audit

        assert hasattr(audit, "register")

    def test_graph_module_importable(self):
        """Graph command module should be importable."""
        from replimap.cli.commands import graph

        assert hasattr(graph, "register")

    def test_drift_module_importable(self):
        """Drift command module should be importable."""
        from replimap.cli.commands import drift

        assert hasattr(drift, "register")

    def test_deps_module_importable(self):
        """Deps command module should be importable."""
        from replimap.cli.commands import deps

        assert hasattr(deps, "register")

    def test_cost_module_importable(self):
        """Cost command module should be importable."""
        from replimap.cli.commands import cost

        assert hasattr(cost, "register")

    def test_remediate_module_importable(self):
        """Remediate command module should be importable."""
        from replimap.cli.commands import remediate

        assert hasattr(remediate, "register")

    def test_validate_module_importable(self):
        """Validate command module should be importable."""
        from replimap.cli.commands import validate

        assert hasattr(validate, "register")

    def test_unused_module_importable(self):
        """Unused command module should be importable."""
        from replimap.cli.commands import unused

        assert hasattr(unused, "register")

    def test_trends_module_importable(self):
        """Trends command module should be importable."""
        from replimap.cli.commands import trends

        assert hasattr(trends, "register")

    def test_transfer_module_importable(self):
        """Transfer command module should be importable."""
        from replimap.cli.commands import transfer

        assert hasattr(transfer, "register")

    def test_upgrade_module_importable(self):
        """Upgrade command module should be importable."""
        from replimap.cli.commands import upgrade

        assert hasattr(upgrade, "register")

    def test_snapshot_module_importable(self):
        """Snapshot command module should be importable."""
        from replimap.cli.commands import snapshot

        assert hasattr(snapshot, "register")

    def test_trust_center_module_importable(self):
        """Trust center command module should be importable."""
        from replimap.cli.commands import trust_center

        assert hasattr(trust_center, "register")

    def test_dr_module_importable(self):
        """DR command module should be importable."""
        from replimap.cli.commands import dr

        assert hasattr(dr, "register")

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
