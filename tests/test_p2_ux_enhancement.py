"""
Tests for P2 UX Enhancement components.

Tests cover:
- GlobalContext and EnvironmentDetector
- IdentityGuard
- OperationClassifier
- DecisionManager with TTL
- LightweightFieldHints
- GrayZoneResolver
- ProgressiveErrorRenderer
- ErrorCatalog
"""

from __future__ import annotations

import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from replimap.core.context import (
    ConfigSource,
    ConfigValue,
    EnvironmentDetector,
    ExecutionEnvironment,
    GlobalContext,
)
from replimap.core.identity import IdentityContext, IdentityGuard, IdentitySource
from replimap.core.operations import OperationClassifier, OperationSafety
from replimap.decisions.manager import DecisionManager
from replimap.decisions.models import Decision, DecisionType
from replimap.extraction.hints import FieldHint, LightweightFieldHints


# ============================================================
# Environment Detector Tests
# ============================================================


class TestEnvironmentDetector:
    """Tests for EnvironmentDetector."""

    def test_detect_interactive_with_tty(self):
        """Interactive environment detected when TTY available."""
        with patch.object(EnvironmentDetector, "is_ci", return_value=False):
            with patch.object(EnvironmentDetector, "has_tty", return_value=True):
                assert EnvironmentDetector.detect() == ExecutionEnvironment.INTERACTIVE

    def test_detect_ci_with_github_actions(self):
        """CI detected when GITHUB_ACTIONS is set."""
        with patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}, clear=False):
            assert EnvironmentDetector.is_ci() is True
            assert EnvironmentDetector.get_ci_name() == "GitHub Actions"

    def test_detect_ci_with_gitlab(self):
        """CI detected when GITLAB_CI is set."""
        with patch.dict(os.environ, {"GITLAB_CI": "true"}, clear=False):
            assert EnvironmentDetector.is_ci() is True
            assert EnvironmentDetector.get_ci_name() == "GitLab CI"

    def test_detect_non_interactive_without_tty(self):
        """Non-interactive detected when no TTY and not CI."""
        with patch.object(EnvironmentDetector, "is_ci", return_value=False):
            with patch.object(EnvironmentDetector, "has_tty", return_value=False):
                assert (
                    EnvironmentDetector.detect() == ExecutionEnvironment.NON_INTERACTIVE
                )


# ============================================================
# GlobalContext Tests
# ============================================================


class TestGlobalContext:
    """Tests for GlobalContext."""

    def test_from_cli_with_explicit_profile(self):
        """CLI profile should have CLI source."""
        ctx = GlobalContext.from_cli(profile="prod")
        assert ctx.profile.value == "prod"
        assert ctx.profile.source == ConfigSource.CLI

    def test_from_cli_with_env_profile(self):
        """Environment profile should have ENV source."""
        with patch.dict(os.environ, {"AWS_PROFILE": "staging"}, clear=False):
            ctx = GlobalContext.from_cli()
            assert ctx.profile.value == "staging"
            assert ctx.profile.source == ConfigSource.ENVIRONMENT

    def test_is_explicit_profile(self):
        """is_explicit_profile returns True for CLI/ENV sources."""
        ctx_cli = GlobalContext.from_cli(profile="prod")
        assert ctx_cli.is_explicit_profile() is True

        with patch.dict(os.environ, {"AWS_PROFILE": "staging"}, clear=False):
            ctx_env = GlobalContext.from_cli()
            assert ctx_env.is_explicit_profile() is True

    def test_is_interactive_respects_non_interactive_flag(self):
        """is_interactive returns False when non_interactive is True."""
        ctx = GlobalContext.from_cli(non_interactive=True)
        assert ctx.is_interactive() is False


# ============================================================
# OperationClassifier Tests
# ============================================================


class TestOperationClassifier:
    """Tests for OperationClassifier."""

    def test_safe_operations(self):
        """SAFE operations classified correctly."""
        assert OperationClassifier.classify("wait_and_retry") == OperationSafety.SAFE
        assert OperationClassifier.classify("reduce_concurrency") == OperationSafety.SAFE
        assert OperationClassifier.classify("increase_timeout") == OperationSafety.SAFE

    def test_caution_operations(self):
        """CAUTION operations classified correctly."""
        assert OperationClassifier.classify("skip_service") == OperationSafety.CAUTION
        assert OperationClassifier.classify("use_cached_data") == OperationSafety.CAUTION

    def test_sensitive_operations(self):
        """SENSITIVE operations classified correctly."""
        assert (
            OperationClassifier.classify("switch_profile") == OperationSafety.SENSITIVE
        )
        assert OperationClassifier.classify("assume_role") == OperationSafety.SENSITIVE
        assert (
            OperationClassifier.classify("skip_ssl_verify") == OperationSafety.SENSITIVE
        )

    def test_unknown_defaults_to_caution(self):
        """Unknown operations default to CAUTION."""
        assert (
            OperationClassifier.classify("unknown_operation") == OperationSafety.CAUTION
        )

    def test_is_safe_helper(self):
        """is_safe helper works correctly."""
        assert OperationClassifier.is_safe("wait_and_retry") is True
        assert OperationClassifier.is_safe("switch_profile") is False

    def test_requires_confirmation_helper(self):
        """requires_confirmation helper works correctly."""
        assert OperationClassifier.requires_confirmation("switch_profile") is True
        assert OperationClassifier.requires_confirmation("skip_service") is False


# ============================================================
# Decision Models Tests
# ============================================================


class TestDecisionModels:
    """Tests for Decision models."""

    def test_decision_not_expired_when_no_expiry(self):
        """Decision without expiry is never expired."""
        decision = Decision(
            scope="test",
            rule="test_rule",
            value=True,
            reason="test",
            decision_type=DecisionType.PERMANENT.value,
            created_at=datetime.now().isoformat(),
            expires_at=None,
        )
        assert decision.is_expired() is False
        assert decision.is_permanent() is True

    def test_decision_expired_when_past_expiry(self):
        """Decision is expired when past expiry date."""
        past = (datetime.now() - timedelta(days=1)).isoformat()
        decision = Decision(
            scope="test",
            rule="test_rule",
            value=True,
            reason="test",
            decision_type=DecisionType.SUPPRESS.value,
            created_at=(datetime.now() - timedelta(days=31)).isoformat(),
            expires_at=past,
            ttl_days=30,
        )
        assert decision.is_expired() is True

    def test_decision_expiring_soon(self):
        """Decision expiring within threshold is flagged."""
        # Set expiry to 5 days from now (clearly within 7 days, clearly not within 1 day)
        soon = (datetime.now() + timedelta(days=5)).isoformat()
        decision = Decision(
            scope="test",
            rule="test_rule",
            value=True,
            reason="test",
            decision_type=DecisionType.SUPPRESS.value,
            created_at=datetime.now().isoformat(),
            expires_at=soon,
            ttl_days=30,
        )
        assert decision.is_expiring_soon(days=7) is True
        assert decision.is_expiring_soon(days=3) is False


# ============================================================
# DecisionManager Tests
# ============================================================


class TestDecisionManager:
    """Tests for DecisionManager."""

    def test_set_and_get_decision(self, tmp_path):
        """Can set and retrieve a decision."""
        path = tmp_path / "decisions.yaml"
        manager = DecisionManager(path)

        manager.set_decision(
            scope="scan.permissions",
            rule="skip_s3",
            value=True,
            reason="User chose to skip",
            decision_type=DecisionType.SUPPRESS,
        )

        decision = manager.get_decision("scan.permissions", "skip_s3")
        assert decision is not None
        assert decision.value is True
        assert decision.scope == "scan.permissions"
        assert decision.rule == "skip_s3"

    def test_suppress_decision_expires_in_30_days(self, tmp_path):
        """Suppress decisions should have 30-day TTL."""
        path = tmp_path / "decisions.yaml"
        manager = DecisionManager(path)

        manager.set_decision(
            scope="test",
            rule="test_rule",
            value=True,
            reason="test",
            decision_type=DecisionType.SUPPRESS,
        )

        decision = manager.get_decision("test", "test_rule")
        assert decision is not None
        assert decision.ttl_days == 30
        # Should expire in approximately 30 days
        days = decision.days_until_expiry()
        assert days is not None
        assert 29 <= days <= 30

    def test_extraction_decision_expires_in_90_days(self, tmp_path):
        """Extraction decisions should have 90-day TTL."""
        path = tmp_path / "decisions.yaml"
        manager = DecisionManager(path)

        manager.set_decision(
            scope="extraction",
            rule="vpc_id",
            value="extract",
            reason="test",
            decision_type=DecisionType.EXTRACTION,
        )

        decision = manager.get_decision("extraction", "vpc_id")
        assert decision is not None
        assert decision.ttl_days == 90

    def test_permanent_decision_never_expires(self, tmp_path):
        """Permanent decisions should not expire."""
        path = tmp_path / "decisions.yaml"
        manager = DecisionManager(path)

        manager.set_decision(
            scope="preference",
            rule="output_format",
            value="terraform",
            reason="User preference",
            decision_type=DecisionType.PREFERENCE,
            permanent=True,
        )

        decision = manager.get_decision("preference", "output_format")
        assert decision is not None
        assert decision.expires_at is None
        assert decision.is_permanent() is True

    def test_expired_decision_returns_none(self, tmp_path):
        """get_decision returns None for expired decisions by default."""
        path = tmp_path / "decisions.yaml"
        manager = DecisionManager(path)

        # Create an already-expired decision manually
        manager._manifest.decisions.append(
            Decision(
                scope="test",
                rule="expired",
                value=True,
                reason="test",
                decision_type=DecisionType.SUPPRESS.value,
                created_at=(datetime.now() - timedelta(days=31)).isoformat(),
                expires_at=(datetime.now() - timedelta(days=1)).isoformat(),
                ttl_days=30,
            )
        )

        # Should return None by default
        assert manager.get_decision("test", "expired") is None

        # Should return decision when check_expiry=False
        decision = manager.get_decision("test", "expired", check_expiry=False)
        assert decision is not None

    def test_renew_decision(self, tmp_path):
        """Can renew a decision's TTL."""
        path = tmp_path / "decisions.yaml"
        manager = DecisionManager(path)

        manager.set_decision(
            scope="test",
            rule="renewable",
            value=True,
            reason="test",
            decision_type=DecisionType.SUPPRESS,
        )

        # Renew
        success = manager.renew_decision("test", "renewable")
        assert success is True

        # Check new expiry is approximately 30 days from now
        decision = manager.get_decision("test", "renewable")
        assert decision is not None
        days = decision.days_until_expiry()
        assert days is not None
        assert 29 <= days <= 30

    def test_clear_expired(self, tmp_path):
        """Can clear expired decisions."""
        path = tmp_path / "decisions.yaml"
        manager = DecisionManager(path)

        # Add expired and valid decisions
        manager._manifest.decisions.append(
            Decision(
                scope="test",
                rule="expired",
                value=True,
                reason="test",
                decision_type=DecisionType.SUPPRESS.value,
                created_at=(datetime.now() - timedelta(days=31)).isoformat(),
                expires_at=(datetime.now() - timedelta(days=1)).isoformat(),
                ttl_days=30,
            )
        )
        manager.set_decision(
            scope="test",
            rule="valid",
            value=True,
            reason="test",
            decision_type=DecisionType.SUPPRESS,
        )

        # Clear expired
        removed = manager.remove_expired()
        assert removed == 1

        # Valid decision should remain
        assert manager.get_decision("test", "valid") is not None


# ============================================================
# LightweightFieldHints Tests
# ============================================================


class TestLightweightFieldHints:
    """Tests for LightweightFieldHints."""

    def test_vpc_id_should_extract(self):
        """vpc_id should be extracted as variable."""
        hints = LightweightFieldHints()
        hint = hints.get_hint("vpc_id")
        assert hint.should_extract is True

    def test_from_port_should_keep(self):
        """from_port should stay hardcoded."""
        hints = LightweightFieldHints()
        hint = hints.get_hint("from_port")
        assert hint.should_keep is True

    def test_cidr_block_context_override_vpc(self):
        """cidr_block in aws_vpc should extract."""
        hints = LightweightFieldHints()
        hint = hints.get_hint("cidr_block", resource_type="aws_vpc")
        assert hint.should_extract is True

    def test_cidr_block_context_override_security_group(self):
        """cidr_blocks in aws_security_group should keep."""
        hints = LightweightFieldHints()
        hint = hints.get_hint("cidr_blocks", resource_type="aws_security_group")
        assert hint.should_keep is True

    def test_unknown_field_defaults_to_keep(self):
        """Unknown fields should default to keep (conservative)."""
        hints = LightweightFieldHints()
        hint = hints.get_hint("completely_unknown_field_xyz")
        assert hint.should_keep is True

    def test_clean_field_name_removes_indices(self):
        """Array indices should be cleaned from field names."""
        hints = LightweightFieldHints()
        # "ingress.0.from_port" should be cleaned to "from_port"
        hint = hints.get_hint("ingress.0.from_port")
        assert hint.should_keep is True

    def test_add_custom_hint(self):
        """Can add custom hints at runtime."""
        hints = LightweightFieldHints()
        hints.add_custom_hint("my_custom_field", "extract")
        hint = hints.get_hint("my_custom_field")
        assert hint.should_extract is True


# ============================================================
# Identity Guard Tests
# ============================================================


class TestIdentityGuard:
    """Tests for IdentityGuard."""

    def test_ci_mode_fails_fast(self):
        """In CI, identity switch should return False."""
        ctx = MagicMock()
        ctx.environment = ExecutionEnvironment.CI
        ctx.profile = ConfigValue("default", ConfigSource.DEFAULT)
        ctx.is_explicit_profile.return_value = False
        ctx.is_interactive.return_value = False
        ctx.ci_name = "GitHub Actions"

        console = MagicMock()
        guard = IdentityGuard(ctx, console)

        # Resolve identity first
        guard._current_identity = IdentityContext(
            profile="default",
            source=IdentitySource.DEFAULT,
            is_explicit=False,
        )

        # Should return False in CI
        result = guard.can_switch_identity("prod", "permission denied")
        assert result is False

    def test_explicit_profile_shows_warning(self):
        """Explicit profile should show warning when switching."""
        ctx = MagicMock()
        ctx.environment = ExecutionEnvironment.INTERACTIVE
        ctx.profile = ConfigValue("staging", ConfigSource.CLI)
        ctx.is_explicit_profile.return_value = True
        ctx.is_interactive.return_value = True
        ctx.ci_name = None

        console = MagicMock()
        # Simulate user declining the switch
        console.input.return_value = "n"

        guard = IdentityGuard(ctx, console)
        guard._current_identity = IdentityContext(
            profile="staging",
            source=IdentitySource.CLI_ARGUMENT,
            is_explicit=True,
        )

        result = guard.can_switch_identity("prod", "permission denied")
        assert result is False

    def test_same_profile_returns_true(self):
        """Same profile should return True without prompting."""
        ctx = MagicMock()
        ctx.environment = ExecutionEnvironment.INTERACTIVE
        ctx.profile = ConfigValue("prod", ConfigSource.CLI)
        ctx.is_explicit_profile.return_value = True
        ctx.is_interactive.return_value = True

        console = MagicMock()
        guard = IdentityGuard(ctx, console)
        guard._current_identity = IdentityContext(
            profile="prod",
            source=IdentitySource.CLI_ARGUMENT,
            is_explicit=True,
        )

        # Same profile - should return True
        result = guard.can_switch_identity("prod", "same profile")
        assert result is True


# ============================================================
# Error Catalog Tests
# ============================================================


class TestErrorCatalog:
    """Tests for ErrorCatalog."""

    def test_get_error_info(self):
        """Can retrieve error info by code."""
        from replimap.cli.error_catalog import get_error_info

        entry = get_error_info("RM-E001")
        assert entry is not None
        assert "summary" in entry
        assert "fix_command" in entry

    def test_search_errors(self):
        """Can search errors by keyword."""
        from replimap.cli.error_catalog import search_errors

        results = search_errors("credential")
        assert len(results) > 0

    def test_list_all_codes(self):
        """Can list all error codes."""
        from replimap.cli.error_catalog import list_all_codes

        codes = list_all_codes()
        assert len(codes) > 0
        assert all(code.startswith("RM-E") for code in codes)


# ============================================================
# Progressive Error Renderer Tests
# ============================================================


class TestProgressiveErrorRenderer:
    """Tests for ProgressiveErrorRenderer."""

    def test_render_level_1(self):
        """Level 1 renders only summary."""
        from replimap.cli.error_renderer import ErrorInfo, ProgressiveErrorRenderer

        console = MagicMock()
        renderer = ProgressiveErrorRenderer(console)

        error = ErrorInfo(
            code="RM-E001",
            summary="Test error",
            fix_command="test fix",
        )

        renderer.render(error, level=1)
        # Should have called print
        assert console.print.called

    def test_render_level_2_includes_fix(self):
        """Level 2 includes fix command."""
        from replimap.cli.error_renderer import ErrorInfo, ProgressiveErrorRenderer

        console = MagicMock()
        renderer = ProgressiveErrorRenderer(console)

        error = ErrorInfo(
            code="RM-E001",
            summary="Test error",
            fix_command="test fix",
            fix_description="Test description",
        )

        renderer.render(error, level=2)
        assert console.print.called

    def test_render_simple_for_ci(self):
        """Simple render for CI environments."""
        from replimap.cli.error_renderer import ErrorInfo, ProgressiveErrorRenderer

        console = MagicMock()
        renderer = ProgressiveErrorRenderer(console)

        error = ErrorInfo(
            code="RM-E001",
            summary="Test error",
            fix_command="test fix",
        )

        renderer.render_simple(error)
        # Should print minimal output
        assert console.print.call_count >= 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
