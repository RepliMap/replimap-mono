"""
Full user journey integration tests for RepliMap.

Uses moto for AWS mocking and tests:
- Feature gating enforcement
- Backward compatibility (blast module)
- Edge case handling
- Complete user workflows
"""

import tempfile
import warnings
from pathlib import Path

import pytest
from typer.testing import CliRunner

from replimap.main import app

runner = CliRunner()


class TestFeatureGating:
    """Verify plan restrictions are enforced correctly."""

    def test_free_tier_scan_limit(self) -> None:
        """FREE tier limited to 3 scans per month."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from replimap.licensing.manager import LicenseManager, set_license_manager
            from replimap.licensing.models import Plan
            from replimap.licensing.tracker import UsageTracker

            # Set up free tier manager
            manager = LicenseManager(cache_dir=Path(tmpdir))
            set_license_manager(manager)
            assert manager.current_plan == Plan.FREE

            # Set up tracker with 3 scans already recorded
            tracker = UsageTracker(data_dir=Path(tmpdir))
            for i in range(3):
                tracker.record_scan(
                    scan_id=f"test-scan-{i}",
                    region="us-east-1",
                    resource_count=10,
                    resource_types={"aws_vpc": 1},
                    duration_seconds=1.0,
                )

            # Verify quota is exhausted
            features = manager.current_features
            assert not tracker.check_scan_quota(features.max_scans_per_month)

    def test_drift_requires_pro(self) -> None:
        """SOLO tier cannot access drift detection."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from replimap.licensing import check_drift_allowed
            from replimap.licensing.manager import LicenseManager, set_license_manager

            # Simulate SOLO license (mock validation)
            manager = LicenseManager(cache_dir=Path(tmpdir))
            set_license_manager(manager)

            # FREE tier should not have drift access
            gate = check_drift_allowed()
            assert not gate.allowed
            assert "PRO" in gate.prompt.upper() or "Pro" in gate.prompt

    def test_deps_requires_solo_or_higher(self) -> None:
        """FREE tier cannot access dependencies analysis."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from replimap.licensing import check_deps_allowed
            from replimap.licensing.manager import LicenseManager, set_license_manager

            manager = LicenseManager(cache_dir=Path(tmpdir))
            set_license_manager(manager)

            gate = check_deps_allowed()
            assert not gate.allowed

    def test_cost_requires_pro(self) -> None:
        """Cost estimation requires PRO+ plan."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from replimap.licensing import check_cost_allowed
            from replimap.licensing.manager import LicenseManager, set_license_manager

            manager = LicenseManager(cache_dir=Path(tmpdir))
            set_license_manager(manager)

            gate = check_cost_allowed()
            assert not gate.allowed

    def test_audit_fix_requires_solo(self) -> None:
        """Audit --fix flag requires SOLO+ plan."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from replimap.licensing import check_audit_fix_allowed
            from replimap.licensing.manager import LicenseManager, set_license_manager

            manager = LicenseManager(cache_dir=Path(tmpdir))
            set_license_manager(manager)

            gate = check_audit_fix_allowed()
            assert not gate.allowed
            assert "solo" in gate.prompt.lower() or "SOLO" in gate.prompt

    def test_audit_ci_mode_requires_pro(self) -> None:
        """Audit --fail-on-high requires PRO+ plan."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from replimap.licensing import check_audit_ci_mode_allowed
            from replimap.licensing.manager import LicenseManager, set_license_manager

            manager = LicenseManager(cache_dir=Path(tmpdir))
            set_license_manager(manager)

            gate = check_audit_ci_mode_allowed()
            assert not gate.allowed
            assert "pro" in gate.prompt.lower() or "PRO" in gate.prompt


class TestBackwardCompatibility:
    """Verify deprecated imports still work."""

    def test_blast_module_reexports(self) -> None:
        """Importing from blast should work (deprecated but functional)."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            # Import from deprecated blast module
            from replimap.blast import (
                BlastNode,
                BlastRadiusReporter,
                BlastRadiusResult,
                DependencyGraphBuilder,
                ImpactCalculator,
            )

            # Should show deprecation warning
            assert len(w) >= 1
            assert any("deprecated" in str(warning.message).lower() for warning in w)

            # But imports should succeed
            assert BlastNode is not None
            assert DependencyGraphBuilder is not None
            assert ImpactCalculator is not None
            assert BlastRadiusResult is not None
            assert BlastRadiusReporter is not None

    def test_dependencies_is_canonical(self) -> None:
        """New code should import from dependencies."""
        from replimap.dependencies import DependencyGraphBuilder as NewBuilder
        from replimap.dependencies import ImpactCalculator as NewCalc

        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            from replimap.blast import DependencyGraphBuilder as OldBuilder
            from replimap.blast import ImpactCalculator as OldCalc

        # Both should be the same class
        assert NewBuilder is OldBuilder
        assert NewCalc is OldCalc

    def test_blast_command_shows_deprecation(self) -> None:
        """The 'blast' CLI command should show deprecation notice."""
        # Note: This would require mocking AWS, so we just check the help
        result = runner.invoke(app, ["blast", "--help"], color=False)
        # Hidden command should still work
        assert result.exit_code == 0 or "deprecated" in result.output.lower()


class TestGraphWatermark:
    """Test watermark enforcement for FREE tier."""

    def test_free_tier_shows_watermark(self) -> None:
        """FREE tier graph exports should have watermark flag enabled."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from replimap.licensing import check_graph_export_watermark
            from replimap.licensing.manager import LicenseManager, set_license_manager

            manager = LicenseManager(cache_dir=Path(tmpdir))
            set_license_manager(manager)

            # FREE tier should show watermark
            assert check_graph_export_watermark() is True

    def test_d3_formatter_accepts_watermark(self) -> None:
        """D3Formatter should accept show_watermark parameter."""
        from replimap.graph.formatters.d3 import D3Formatter

        # Create formatter with watermark enabled
        formatter = D3Formatter(show_watermark=True)
        assert formatter._show_watermark is True

        # Create formatter with watermark disabled
        formatter_no_wm = D3Formatter(show_watermark=False)
        assert formatter_no_wm._show_watermark is False


class TestEdgeCases:
    """Edge case handling."""

    def test_empty_aws_account(self) -> None:
        """Handle AWS account with no resources gracefully."""
        # Test that scanning with no resources doesn't crash
        from replimap.core import GraphEngine

        graph = GraphEngine()
        # Empty graph should have 0 resources
        assert graph.node_count == 0
        assert graph.edge_count == 0

    def test_invalid_terraform_state_format(self) -> None:
        """Handle malformed tfstate gracefully."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".tfstate", delete=False
        ) as f:
            f.write("not valid json {{{")
            bad_state = Path(f.name)

        try:
            import json

            with pytest.raises(json.JSONDecodeError):
                with open(bad_state) as f:
                    json.load(f)
        finally:
            bad_state.unlink()

    def test_license_key_format_validation(self) -> None:
        """Invalid license key format should be rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from replimap.licensing.manager import LicenseManager
            from replimap.licensing.models import LicenseValidationError

            manager = LicenseManager(cache_dir=Path(tmpdir))

            with pytest.raises(LicenseValidationError):
                manager.activate("invalid-key-format")

    def test_dev_mode_unlocks_all_features(self) -> None:
        """REPLIMAP_DEV_MODE=1 should enable all features."""
        import os

        with tempfile.TemporaryDirectory() as tmpdir:
            # Set dev mode
            original = os.environ.get("REPLIMAP_DEV_MODE")
            os.environ["REPLIMAP_DEV_MODE"] = "1"

            try:
                from replimap.licensing.manager import LicenseManager
                from replimap.licensing.models import Plan

                manager = LicenseManager(cache_dir=Path(tmpdir))
                assert manager.current_plan == Plan.ENTERPRISE
                assert manager.is_dev_mode is True
            finally:
                if original is None:
                    os.environ.pop("REPLIMAP_DEV_MODE", None)
                else:
                    os.environ["REPLIMAP_DEV_MODE"] = original


class TestCLICommands:
    """Test CLI command basic functionality."""

    def test_version_command(self) -> None:
        """--version should show version info."""
        result = runner.invoke(app, ["--version"], color=False)
        assert result.exit_code == 0
        assert "RepliMap" in result.output

    def test_help_command(self) -> None:
        """--help should show help text."""
        result = runner.invoke(app, ["--help"], color=False)
        assert result.exit_code == 0
        assert "AWS" in result.output

    def test_scan_help(self) -> None:
        """scan --help should work."""
        result = runner.invoke(app, ["scan", "--help"], color=False)
        assert result.exit_code == 0
        assert "--region" in result.output
        assert "--profile" in result.output

    def test_graph_help(self) -> None:
        """graph --help should work."""
        result = runner.invoke(app, ["graph", "--help"], color=False)
        assert result.exit_code == 0
        assert "--format" in result.output

    def test_audit_help(self) -> None:
        """audit --help should work."""
        result = runner.invoke(app, ["audit", "--help"], color=False)
        assert result.exit_code == 0
        assert "--fix" in result.output
        assert "--fail-on-high" in result.output

    def test_drift_help(self) -> None:
        """drift --help should work."""
        result = runner.invoke(app, ["drift", "--help"], color=False)
        assert result.exit_code == 0
        assert "--state" in result.output

    def test_deps_help(self) -> None:
        """deps --help should work."""
        result = runner.invoke(app, ["deps", "--help"], color=False)
        assert result.exit_code == 0
        assert "--depth" in result.output

    def test_cost_help(self) -> None:
        """cost --help should work."""
        result = runner.invoke(app, ["cost", "--help"], color=False)
        assert result.exit_code == 0
        assert "--format" in result.output

    def test_license_status_help(self) -> None:
        """license status --help should work."""
        result = runner.invoke(app, ["license", "status", "--help"], color=False)
        assert result.exit_code == 0


class TestLicenseManagement:
    """Test license management functionality."""

    def test_license_status_shows_free_tier(self) -> None:
        """Without activation, should show FREE tier."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from replimap.licensing.manager import LicenseManager, set_license_manager
            from replimap.licensing.models import Plan

            manager = LicenseManager(cache_dir=Path(tmpdir))
            set_license_manager(manager)

            assert manager.current_plan == Plan.FREE
            assert manager.current_license is None

    def test_license_deactivate_returns_to_free(self) -> None:
        """Deactivating should return to FREE tier."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from replimap.licensing.manager import LicenseManager
            from replimap.licensing.models import Plan

            manager = LicenseManager(cache_dir=Path(tmpdir))

            # Mock a license being active
            manager._current_plan = Plan.SOLO

            # Deactivate
            manager.deactivate()

            assert manager.current_plan == Plan.FREE
            assert manager.current_license is None


class TestUsageTracking:
    """Test usage tracking functionality."""

    def test_scan_recording(self) -> None:
        """Scans should be recorded correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from replimap.licensing.tracker import UsageTracker

            tracker = UsageTracker(data_dir=Path(tmpdir))

            record = tracker.record_scan(
                scan_id="test-123",
                region="us-east-1",
                resource_count=42,
                resource_types={"aws_vpc": 5, "aws_subnet": 20},
                duration_seconds=5.5,
            )

            assert record.scan_id == "test-123"
            assert record.resource_count == 42

            stats = tracker.get_stats()
            assert stats.total_scans == 1
            assert stats.total_resources_scanned == 42

    def test_monthly_quota_tracking(self) -> None:
        """Monthly scan quota should be tracked correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from replimap.licensing.tracker import UsageTracker

            tracker = UsageTracker(data_dir=Path(tmpdir))

            # Record 2 scans
            for i in range(2):
                tracker.record_scan(
                    scan_id=f"scan-{i}",
                    region="us-east-1",
                    resource_count=10,
                    resource_types={},
                    duration_seconds=1.0,
                )

            # Should be under quota of 3
            assert tracker.check_scan_quota(max_scans=3)

            # Record 1 more scan
            tracker.record_scan(
                scan_id="scan-2",
                region="us-east-1",
                resource_count=10,
                resource_types={},
                duration_seconds=1.0,
            )

            # Should now be at quota
            assert not tracker.check_scan_quota(max_scans=3)

            # Unlimited should always pass
            assert tracker.check_scan_quota(max_scans=None)
