"""
Tests for feature gating functions (v3.2 pricing).

These tests verify that feature gates work correctly for each plan tier.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

from replimap.licensing.gates import (
    check_audit_export_format_allowed,
    check_compliance_apra_allowed,
    check_compliance_essential_eight_allowed,
    check_compliance_nzism_allowed,
    check_compliance_rbnz_allowed,
    check_cost_diff_allowed,
    check_local_cache_allowed,
    check_remediate_beta_allowed,
    check_snapshot_allowed,
    check_snapshot_limit,
    check_trust_center_allowed,
    check_trust_compliance_allowed,
    check_trust_export_allowed,
    check_trust_verify_allowed,
    get_audit_first_critical_preview_lines,
    get_email_support_sla,
    get_remediate_priority,
    get_snapshot_retention_days,
)
from replimap.licensing.manager import LicenseManager, set_license_manager
from replimap.licensing.models import License, Plan, get_machine_fingerprint


def mock_validate_online(manager: "LicenseManager", license_key: str) -> License:
    """Mock _validate_online for testing."""
    from datetime import UTC, datetime, timedelta

    key_upper = license_key.upper()
    if "FREE" in key_upper:
        plan = Plan.FREE
    elif "SOLO" in key_upper:
        plan = Plan.SOLO
    elif "PRO" in key_upper:
        plan = Plan.PRO
    elif "TEAM" in key_upper:
        plan = Plan.TEAM
    elif "ENTR" in key_upper:
        plan = Plan.ENTERPRISE
    else:
        plan = Plan.SOLO

    return License(
        license_key=key_upper,
        plan=plan,
        email="test@example.com",
        issued_at=datetime.now(UTC),
        expires_at=datetime.now(UTC) + timedelta(days=365),
        machine_fingerprint=get_machine_fingerprint(),
    )


class TestStorageLayerGates:
    """Tests for storage layer feature gates (Solo+)."""

    def test_local_cache_blocked_for_free(self) -> None:
        """Test local cache is blocked for FREE plan."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            set_license_manager(manager)  # FREE tier

            result = check_local_cache_allowed()
            assert result.allowed is False
            assert "Solo" in result.prompt
            assert "$49" in result.prompt

    @patch.object(LicenseManager, "_validate_online", mock_validate_online)
    def test_local_cache_allowed_for_solo(self) -> None:
        """Test local cache is allowed for Solo plan."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            manager.activate("RM-SOLO-1234-5678-ABCD")
            set_license_manager(manager)

            result = check_local_cache_allowed()
            assert result.allowed is True

    def test_snapshot_blocked_for_free(self) -> None:
        """Test snapshots are blocked for FREE plan."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            set_license_manager(manager)  # FREE tier

            result = check_snapshot_allowed()
            assert result.allowed is False
            assert "Solo" in result.prompt

    @patch.object(LicenseManager, "_validate_online", mock_validate_online)
    def test_snapshot_allowed_for_solo(self) -> None:
        """Test snapshots are allowed for Solo plan."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            manager.activate("RM-SOLO-1234-5678-ABCD")
            set_license_manager(manager)

            result = check_snapshot_allowed()
            assert result.allowed is True

    @patch.object(LicenseManager, "_validate_online", mock_validate_online)
    def test_snapshot_limit_solo(self) -> None:
        """Test Solo plan has 5 snapshot limit."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            manager.activate("RM-SOLO-1234-5678-ABCD")
            set_license_manager(manager)

            # Under limit
            result = check_snapshot_limit(3)
            assert result.allowed is True
            assert result.data["remaining"] == 2
            assert result.data["limit"] == 5

            # At limit
            result = check_snapshot_limit(5)
            assert result.allowed is False
            assert "5/5" in result.prompt

    @patch.object(LicenseManager, "_validate_online", mock_validate_online)
    def test_snapshot_limit_pro(self) -> None:
        """Test Pro plan has 15 snapshot limit."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            manager.activate("RM-PRO0-1234-5678-ABCD")
            set_license_manager(manager)

            result = check_snapshot_limit(10)
            assert result.allowed is True
            assert result.data["remaining"] == 5
            assert result.data["limit"] == 15

    @patch.object(LicenseManager, "_validate_online", mock_validate_online)
    def test_snapshot_limit_enterprise_unlimited(self) -> None:
        """Test Enterprise plan has unlimited snapshots."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            manager.activate("RM-ENTR-1234-5678-ABCD")
            set_license_manager(manager)

            result = check_snapshot_limit(1000)
            assert result.allowed is True

    @patch.object(LicenseManager, "_validate_online", mock_validate_online)
    def test_snapshot_retention_days_by_plan(self) -> None:
        """Test snapshot retention days vary by plan."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            set_license_manager(manager)

            # FREE = 0 days
            assert get_snapshot_retention_days() == 0

            manager.activate("RM-SOLO-1234-5678-ABCD")
            assert get_snapshot_retention_days() == 7

            manager.deactivate()
            manager.activate("RM-PRO0-1234-5678-ABCD")
            assert get_snapshot_retention_days() == 30

            manager.deactivate()
            manager.activate("RM-TEAM-1234-5678-ABCD")
            assert get_snapshot_retention_days() == 90

            manager.deactivate()
            manager.activate("RM-ENTR-1234-5678-ABCD")
            assert get_snapshot_retention_days() == 365


class TestTrustCenterGates:
    """Tests for Trust Center feature gates (Team+)."""

    def test_trust_center_blocked_for_free(self) -> None:
        """Test Trust Center is blocked for FREE plan."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            set_license_manager(manager)

            result = check_trust_center_allowed()
            assert result.allowed is False
            assert "Team" in result.prompt
            assert "$199" in result.prompt

    @patch.object(LicenseManager, "_validate_online", mock_validate_online)
    def test_trust_center_blocked_for_solo(self) -> None:
        """Test Trust Center is blocked for Solo plan."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            manager.activate("RM-SOLO-1234-5678-ABCD")
            set_license_manager(manager)

            result = check_trust_center_allowed()
            assert result.allowed is False

    @patch.object(LicenseManager, "_validate_online", mock_validate_online)
    def test_trust_center_blocked_for_pro(self) -> None:
        """Test Trust Center is blocked for Pro plan."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            manager.activate("RM-PRO0-1234-5678-ABCD")
            set_license_manager(manager)

            result = check_trust_center_allowed()
            assert result.allowed is False

    @patch.object(LicenseManager, "_validate_online", mock_validate_online)
    def test_trust_center_allowed_for_team(self) -> None:
        """Test Trust Center is allowed for Team plan."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            manager.activate("RM-TEAM-1234-5678-ABCD")
            set_license_manager(manager)

            result = check_trust_center_allowed()
            assert result.allowed is True

    @patch.object(LicenseManager, "_validate_online", mock_validate_online)
    def test_trust_export_json_for_team(self) -> None:
        """Test Team plan can export JSON only."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            manager.activate("RM-TEAM-1234-5678-ABCD")
            set_license_manager(manager)

            result = check_trust_export_allowed("json")
            assert result.allowed is True

            result = check_trust_export_allowed("csv")
            assert result.allowed is False
            assert "Enterprise" in result.prompt

            result = check_trust_export_allowed("pdf")
            assert result.allowed is False

    @patch.object(LicenseManager, "_validate_online", mock_validate_online)
    def test_trust_export_all_for_enterprise(self) -> None:
        """Test Enterprise plan can export all formats."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            manager.activate("RM-ENTR-1234-5678-ABCD")
            set_license_manager(manager)

            for fmt in ["json", "csv", "pdf"]:
                result = check_trust_export_allowed(fmt)
                assert result.allowed is True, f"Format {fmt} should be allowed"

    @patch.object(LicenseManager, "_validate_online", mock_validate_online)
    def test_trust_verify_enterprise_only(self) -> None:
        """Test trust verify (digital signatures) is Enterprise only."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            manager.activate("RM-TEAM-1234-5678-ABCD")
            set_license_manager(manager)

            result = check_trust_verify_allowed()
            assert result.allowed is False
            assert "Enterprise" in result.prompt

            manager.deactivate()
            manager.activate("RM-ENTR-1234-5678-ABCD")
            result = check_trust_verify_allowed()
            assert result.allowed is True

    @patch.object(LicenseManager, "_validate_online", mock_validate_online)
    def test_trust_compliance_enterprise_only(self) -> None:
        """Test trust compliance reports is Enterprise only."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            manager.activate("RM-TEAM-1234-5678-ABCD")
            set_license_manager(manager)

            result = check_trust_compliance_allowed()
            assert result.allowed is False

            manager.deactivate()
            manager.activate("RM-ENTR-1234-5678-ABCD")
            result = check_trust_compliance_allowed()
            assert result.allowed is True


class TestCostFeatureGates:
    """Tests for cost feature gates."""

    def test_cost_diff_blocked_for_free(self) -> None:
        """Test cost diff is blocked for FREE plan."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            set_license_manager(manager)

            result = check_cost_diff_allowed()
            assert result.allowed is False
            assert "Solo" in result.prompt
            assert "$49" in result.prompt

    @patch.object(LicenseManager, "_validate_online", mock_validate_online)
    def test_cost_diff_allowed_for_solo(self) -> None:
        """Test cost diff is allowed for Solo+ plans."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            manager.activate("RM-SOLO-1234-5678-ABCD")
            set_license_manager(manager)

            result = check_cost_diff_allowed()
            assert result.allowed is True


class TestAuditExportGates:
    """Tests for audit export format gates."""

    def test_audit_export_blocked_for_free(self) -> None:
        """Test audit export is blocked for FREE plan."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            set_license_manager(manager)

            result = check_audit_export_format_allowed("html")
            assert result.allowed is False

    @patch.object(LicenseManager, "_validate_online", mock_validate_online)
    def test_audit_export_html_only_for_solo(self) -> None:
        """Test Solo plan can only export HTML."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            manager.activate("RM-SOLO-1234-5678-ABCD")
            set_license_manager(manager)

            result = check_audit_export_format_allowed("html")
            assert result.allowed is True

            result = check_audit_export_format_allowed("pdf")
            assert result.allowed is False

    @patch.object(LicenseManager, "_validate_online", mock_validate_online)
    def test_audit_export_html_pdf_for_pro(self) -> None:
        """Test Pro plan can export HTML + PDF."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            manager.activate("RM-PRO0-1234-5678-ABCD")
            set_license_manager(manager)

            for fmt in ["html", "pdf"]:
                result = check_audit_export_format_allowed(fmt)
                assert result.allowed is True, f"Format {fmt} should be allowed"

            result = check_audit_export_format_allowed("json")
            assert result.allowed is False

    @patch.object(LicenseManager, "_validate_online", mock_validate_online)
    def test_audit_export_html_pdf_json_for_team(self) -> None:
        """Test Team plan can export HTML + PDF + JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            manager.activate("RM-TEAM-1234-5678-ABCD")
            set_license_manager(manager)

            for fmt in ["html", "pdf", "json"]:
                result = check_audit_export_format_allowed(fmt)
                assert result.allowed is True, f"Format {fmt} should be allowed"

            result = check_audit_export_format_allowed("csv")
            assert result.allowed is False

    @patch.object(LicenseManager, "_validate_online", mock_validate_online)
    def test_audit_export_all_for_enterprise(self) -> None:
        """Test Enterprise plan can export all formats."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            manager.activate("RM-ENTR-1234-5678-ABCD")
            set_license_manager(manager)

            for fmt in ["html", "pdf", "json", "csv"]:
                result = check_audit_export_format_allowed(fmt)
                assert result.allowed is True, f"Format {fmt} should be allowed"

    def test_audit_first_critical_preview_lines_free(self) -> None:
        """Test FREE plan shows 2-line preview for first critical."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            set_license_manager(manager)

            lines = get_audit_first_critical_preview_lines()
            assert lines == 2

    @patch.object(LicenseManager, "_validate_online", mock_validate_online)
    def test_audit_first_critical_preview_lines_paid(self) -> None:
        """Test paid plans show full remediation (None = unlimited)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            manager.activate("RM-SOLO-1234-5678-ABCD")
            set_license_manager(manager)

            lines = get_audit_first_critical_preview_lines()
            assert lines is None


class TestRegionalComplianceGates:
    """Tests for regional compliance feature gates (Enterprise only)."""

    @patch.object(LicenseManager, "_validate_online", mock_validate_online)
    def test_apra_blocked_for_team(self) -> None:
        """Test APRA CPS 234 is blocked for Team plan."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            manager.activate("RM-TEAM-1234-5678-ABCD")
            set_license_manager(manager)

            result = check_compliance_apra_allowed()
            assert result.allowed is False
            assert "Enterprise" in result.prompt
            assert "APRA CPS 234" in result.prompt

    @patch.object(LicenseManager, "_validate_online", mock_validate_online)
    def test_apra_allowed_for_enterprise(self) -> None:
        """Test APRA CPS 234 is allowed for Enterprise plan."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            manager.activate("RM-ENTR-1234-5678-ABCD")
            set_license_manager(manager)

            result = check_compliance_apra_allowed()
            assert result.allowed is True

    @patch.object(LicenseManager, "_validate_online", mock_validate_online)
    def test_essential_eight_enterprise_only(self) -> None:
        """Test Essential Eight is Enterprise only."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            manager.activate("RM-TEAM-1234-5678-ABCD")
            set_license_manager(manager)

            result = check_compliance_essential_eight_allowed()
            assert result.allowed is False

            manager.deactivate()
            manager.activate("RM-ENTR-1234-5678-ABCD")
            result = check_compliance_essential_eight_allowed()
            assert result.allowed is True

    @patch.object(LicenseManager, "_validate_online", mock_validate_online)
    def test_rbnz_enterprise_only(self) -> None:
        """Test RBNZ BS11 is Enterprise only."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            manager.activate("RM-TEAM-1234-5678-ABCD")
            set_license_manager(manager)

            result = check_compliance_rbnz_allowed()
            assert result.allowed is False

            manager.deactivate()
            manager.activate("RM-ENTR-1234-5678-ABCD")
            result = check_compliance_rbnz_allowed()
            assert result.allowed is True

    @patch.object(LicenseManager, "_validate_online", mock_validate_online)
    def test_nzism_enterprise_only(self) -> None:
        """Test NZISM is Enterprise only."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            manager.activate("RM-TEAM-1234-5678-ABCD")
            set_license_manager(manager)

            result = check_compliance_nzism_allowed()
            assert result.allowed is False

            manager.deactivate()
            manager.activate("RM-ENTR-1234-5678-ABCD")
            result = check_compliance_nzism_allowed()
            assert result.allowed is True


class TestRemediateBetaGates:
    """Tests for Remediate beta feature gates."""

    def test_remediate_blocked_for_free(self) -> None:
        """Test Remediate beta is blocked for FREE plan."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            set_license_manager(manager)

            result = check_remediate_beta_allowed()
            assert result.allowed is False
            assert "Pro" in result.prompt

    @patch.object(LicenseManager, "_validate_online", mock_validate_online)
    def test_remediate_blocked_for_solo(self) -> None:
        """Test Remediate beta is blocked for Solo plan."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            manager.activate("RM-SOLO-1234-5678-ABCD")
            set_license_manager(manager)

            result = check_remediate_beta_allowed()
            assert result.allowed is False

    @patch.object(LicenseManager, "_validate_online", mock_validate_online)
    def test_remediate_allowed_for_pro(self) -> None:
        """Test Remediate beta is allowed for Pro+ plans."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            manager.activate("RM-PRO0-1234-5678-ABCD")
            set_license_manager(manager)

            result = check_remediate_beta_allowed()
            assert result.allowed is True
            assert result.data["priority"] == "priority"

    @patch.object(LicenseManager, "_validate_online", mock_validate_online)
    def test_remediate_priority_by_plan(self) -> None:
        """Test Remediate priority varies by plan."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            set_license_manager(manager)

            # FREE = none
            assert get_remediate_priority() == "none"

            manager.activate("RM-SOLO-1234-5678-ABCD")
            assert get_remediate_priority() == "none"

            manager.deactivate()
            manager.activate("RM-PRO0-1234-5678-ABCD")
            assert get_remediate_priority() == "priority"

            manager.deactivate()
            manager.activate("RM-TEAM-1234-5678-ABCD")
            assert get_remediate_priority() == "priority"

            manager.deactivate()
            manager.activate("RM-ENTR-1234-5678-ABCD")
            assert get_remediate_priority() == "first"


class TestSupportGates:
    """Tests for email support SLA."""

    def test_no_support_for_free(self) -> None:
        """Test FREE plan has no email support."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            set_license_manager(manager)

            sla = get_email_support_sla()
            assert sla is None

    @patch.object(LicenseManager, "_validate_online", mock_validate_online)
    def test_support_sla_by_plan(self) -> None:
        """Test email support SLA varies by plan."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            manager.activate("RM-SOLO-1234-5678-ABCD")
            set_license_manager(manager)

            assert get_email_support_sla() == 48

            manager.deactivate()
            manager.activate("RM-PRO0-1234-5678-ABCD")
            assert get_email_support_sla() == 24

            manager.deactivate()
            manager.activate("RM-TEAM-1234-5678-ABCD")
            assert get_email_support_sla() == 12

            manager.deactivate()
            manager.activate("RM-ENTR-1234-5678-ABCD")
            assert get_email_support_sla() == 4


class TestPricingV32:
    """Tests to verify v3.2 pricing is correctly configured."""

    def test_free_tier_pricing(self) -> None:
        """Verify FREE tier pricing."""
        from replimap.licensing.models import PLAN_FEATURES, Plan

        features = PLAN_FEATURES[Plan.FREE]
        assert features.price_monthly == 0
        assert features.price_annual == 0

    def test_solo_tier_pricing(self) -> None:
        """Verify Solo tier pricing ($49/mo, $490/yr)."""
        from replimap.licensing.models import PLAN_FEATURES, Plan

        features = PLAN_FEATURES[Plan.SOLO]
        assert features.price_monthly == 49
        assert features.price_annual == 490  # 2 months free

    def test_pro_tier_pricing(self) -> None:
        """Verify Pro tier pricing ($99/mo, $990/yr)."""
        from replimap.licensing.models import PLAN_FEATURES, Plan

        features = PLAN_FEATURES[Plan.PRO]
        assert features.price_monthly == 99
        assert features.price_annual == 990  # 2 months free

    def test_team_tier_pricing(self) -> None:
        """Verify Team tier pricing ($199/mo, $1990/yr)."""
        from replimap.licensing.models import PLAN_FEATURES, Plan

        features = PLAN_FEATURES[Plan.TEAM]
        assert features.price_monthly == 199
        assert features.price_annual == 1990  # 2 months free

    def test_enterprise_tier_pricing(self) -> None:
        """Verify Enterprise tier pricing (from $500/mo)."""
        from replimap.licensing.models import PLAN_FEATURES, Plan

        features = PLAN_FEATURES[Plan.ENTERPRISE]
        assert features.price_monthly == 500
        assert features.price_annual == 5000


class TestAWSAccountLimits:
    """Tests for AWS account limits by plan."""

    def test_account_limits_by_plan(self) -> None:
        """Verify AWS account limits match v3.2 spec."""
        from replimap.licensing.models import PLAN_FEATURES, Plan

        assert PLAN_FEATURES[Plan.FREE].max_aws_accounts == 1
        assert PLAN_FEATURES[Plan.SOLO].max_aws_accounts == 1
        assert PLAN_FEATURES[Plan.PRO].max_aws_accounts == 3
        assert PLAN_FEATURES[Plan.TEAM].max_aws_accounts == 10
        assert PLAN_FEATURES[Plan.ENTERPRISE].max_aws_accounts is None  # Unlimited
