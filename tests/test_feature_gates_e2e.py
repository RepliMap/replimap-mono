"""
End-to-End Tests for Feature Gating (v3.2 Pricing Matrix).

These tests simulate complete user workflows for each plan tier,
verifying that feature gates work correctly across the entire system.

Test Scenarios:
1. FREE tier: Scan → Graph → Audit → Clone (with gates)
2. SOLO tier: Full access to basic features
3. PRO tier: Multi-account + CI/CD + Drift
4. TEAM tier: Trust Center + Collaboration
5. ENTERPRISE tier: All features including compliance
"""

import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from replimap.licensing.gates import (
    GateResult,
    check_audit_ci_mode_allowed,
    check_audit_export_allowed,
    check_audit_export_format_allowed,
    check_clone_download_allowed,
    check_compliance_apra_allowed,
    check_cost_diff_allowed,
    check_drift_allowed,
    check_graph_export_watermark,
    check_local_cache_allowed,
    check_multi_account_allowed,
    check_remediate_beta_allowed,
    check_scan_allowed,
    check_snapshot_allowed,
    check_snapshot_limit,
    check_trust_center_allowed,
    check_trust_export_allowed,
    get_audit_first_critical_preview_lines,
    get_email_support_sla,
)
from replimap.licensing.manager import LicenseManager, set_license_manager
from replimap.licensing.models import (
    License,
    Plan,
    get_machine_fingerprint,
    get_plan_features,
)
from replimap.licensing.tracker import UsageTracker, set_usage_tracker


def mock_validate_online(manager: "LicenseManager", license_key: str) -> License:
    """Mock _validate_online for testing."""
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


class TestFreeUserWorkflow:
    """
    E2E tests for FREE tier user workflow.

    Scenario: User signs up, scans AWS, views graph, runs audit, tries to download code.
    Expected: Can scan 3x/month, see graphs with watermark, see audit titles only,
              preview 100 lines of code, cannot download.
    """

    def test_free_scan_limited_frequency(self) -> None:
        """FREE users can scan 3 times per month."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            tracker = UsageTracker(data_dir=Path(tmpdir))
            set_license_manager(manager)
            set_usage_tracker(tracker)

            # First 3 scans should be allowed
            for i in range(3):
                result = check_scan_allowed()
                assert result.allowed is True, f"Scan {i+1} should be allowed"
                # Record the scan
                tracker.record_scan(
                    scan_id=f"scan-{i}",
                    region="ap-southeast-2",
                    resource_count=100,
                    resource_types={"aws_vpc": 5},
                    duration_seconds=10.0,
                )

            # 4th scan should be blocked
            result = check_scan_allowed()
            assert result.allowed is False
            assert "3/3" in result.prompt or "limit" in result.prompt.lower()

    def test_free_graph_has_watermark(self) -> None:
        """FREE users' graph exports have watermark."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            set_license_manager(manager)

            # check_graph_export_watermark returns bool (True = has watermark)
            has_watermark = check_graph_export_watermark()
            assert has_watermark is True

    def test_free_audit_titles_only(self) -> None:
        """FREE users see all issue titles but limited remediation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            set_license_manager(manager)

            features = get_plan_features(Plan.FREE)

            # Titles are visible
            assert features.audit_titles_visible is True

            # First critical shows 2-line preview
            preview_lines = get_audit_first_critical_preview_lines()
            assert preview_lines == 2

            # Full details are not visible
            assert features.audit_details_visible is False

    def test_free_clone_preview_only(self) -> None:
        """FREE users can preview 100 lines but cannot download."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            set_license_manager(manager)

            # Check preview lines from plan features
            features = get_plan_features(Plan.FREE)
            assert features.clone_preview_lines == 100

            # Download is blocked
            result = check_clone_download_allowed()
            assert result.allowed is False
            assert "$49" in result.prompt  # Shows upgrade price

    def test_free_no_local_cache(self) -> None:
        """FREE users cannot use local caching."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            set_license_manager(manager)

            result = check_local_cache_allowed()
            assert result.allowed is False

    def test_free_no_snapshots(self) -> None:
        """FREE users cannot create snapshots."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            set_license_manager(manager)

            result = check_snapshot_allowed()
            assert result.allowed is False


class TestSoloUserWorkflow:
    """
    E2E tests for SOLO tier ($49/mo) user workflow.

    Scenario: User upgrades to Solo, scans unlimited, downloads code,
              sees full audit reports, uses local caching.
    """

    @patch.object(LicenseManager, "_validate_online", mock_validate_online)
    def test_solo_unlimited_scans(self) -> None:
        """SOLO users have unlimited scans."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            manager.activate("RM-SOLO-1234-5678-ABCD")
            tracker = UsageTracker(data_dir=Path(tmpdir))
            set_license_manager(manager)
            set_usage_tracker(tracker)

            # 100 scans should all be allowed
            for i in range(100):
                result = check_scan_allowed()
                assert result.allowed is True
                tracker.record_scan(
                    scan_id=f"scan-{i}",
                    region="ap-southeast-2",
                    resource_count=100,
                    resource_types={"aws_vpc": 5},
                    duration_seconds=1.0,
                )

    @patch.object(LicenseManager, "_validate_online", mock_validate_online)
    def test_solo_full_clone_download(self) -> None:
        """SOLO users can download full Terraform code."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            manager.activate("RM-SOLO-1234-5678-ABCD")
            set_license_manager(manager)

            # Preview is unlimited
            features = get_plan_features(Plan.SOLO)
            assert features.clone_preview_lines is None  # No limit

            # Download is allowed
            result = check_clone_download_allowed()
            assert result.allowed is True

    @patch.object(LicenseManager, "_validate_online", mock_validate_online)
    def test_solo_full_audit_details(self) -> None:
        """SOLO users see full audit remediation details."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            manager.activate("RM-SOLO-1234-5678-ABCD")
            set_license_manager(manager)

            features = get_plan_features(Plan.SOLO)

            # Full details visible
            assert features.audit_details_visible is True

            # No line limit on remediation
            preview_lines = get_audit_first_critical_preview_lines()
            assert preview_lines is None

            # Can export to HTML
            result = check_audit_export_format_allowed("html")
            assert result.allowed is True

            # Cannot export to PDF (Pro+)
            result = check_audit_export_format_allowed("pdf")
            assert result.allowed is False

    @patch.object(LicenseManager, "_validate_online", mock_validate_online)
    def test_solo_local_cache_and_snapshots(self) -> None:
        """SOLO users have local cache and 5 snapshots."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            manager.activate("RM-SOLO-1234-5678-ABCD")
            set_license_manager(manager)

            # Local cache allowed
            result = check_local_cache_allowed()
            assert result.allowed is True

            # Snapshots allowed
            result = check_snapshot_allowed()
            assert result.allowed is True

            # 5 snapshot limit
            result = check_snapshot_limit(3)
            assert result.allowed is True
            assert result.data["remaining"] == 2

            result = check_snapshot_limit(5)
            assert result.allowed is False

    @patch.object(LicenseManager, "_validate_online", mock_validate_online)
    def test_solo_cost_diff_enabled(self) -> None:
        """SOLO users can use cost diff."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            manager.activate("RM-SOLO-1234-5678-ABCD")
            set_license_manager(manager)

            result = check_cost_diff_allowed()
            assert result.allowed is True

    @patch.object(LicenseManager, "_validate_online", mock_validate_online)
    def test_solo_no_drift(self) -> None:
        """SOLO users cannot use drift detection."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            manager.activate("RM-SOLO-1234-5678-ABCD")
            set_license_manager(manager)

            result = check_drift_allowed()
            assert result.allowed is False
            assert "$99" in result.prompt  # Pro price

    @patch.object(LicenseManager, "_validate_online", mock_validate_online)
    def test_solo_email_support_48h(self) -> None:
        """SOLO users have 48h email SLA."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            manager.activate("RM-SOLO-1234-5678-ABCD")
            set_license_manager(manager)

            sla = get_email_support_sla()
            assert sla == 48


class TestProUserWorkflow:
    """
    E2E tests for PRO tier ($99/mo) user workflow.

    Scenario: User manages multiple AWS accounts, uses CI/CD integration,
              detects drift between Terraform and AWS.
    """

    @patch.object(LicenseManager, "_validate_online", mock_validate_online)
    def test_pro_multi_account_3(self) -> None:
        """PRO users can use 3 AWS accounts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            manager.activate("RM-PRO0-1234-5678-ABCD")
            set_license_manager(manager)

            # 3 accounts allowed
            result = check_multi_account_allowed(3)
            assert result.allowed is True

            # 4 accounts blocked
            result = check_multi_account_allowed(4)
            assert result.allowed is False
            assert "Team" in result.prompt  # Upgrade to Team

    @patch.object(LicenseManager, "_validate_online", mock_validate_online)
    def test_pro_cicd_mode_enabled(self) -> None:
        """PRO users can use --fail-on-high in CI/CD."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            manager.activate("RM-PRO0-1234-5678-ABCD")
            set_license_manager(manager)

            result = check_audit_ci_mode_allowed()
            assert result.allowed is True

    @patch.object(LicenseManager, "_validate_online", mock_validate_online)
    def test_pro_drift_detection(self) -> None:
        """PRO users can use drift detection."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            manager.activate("RM-PRO0-1234-5678-ABCD")
            set_license_manager(manager)

            result = check_drift_allowed()
            assert result.allowed is True

    @patch.object(LicenseManager, "_validate_online", mock_validate_online)
    def test_pro_pdf_export(self) -> None:
        """PRO users can export PDF reports."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            manager.activate("RM-PRO0-1234-5678-ABCD")
            set_license_manager(manager)

            for fmt in ["html", "pdf"]:
                result = check_audit_export_format_allowed(fmt)
                assert result.allowed is True, f"{fmt} should be allowed"

    @patch.object(LicenseManager, "_validate_online", mock_validate_online)
    def test_pro_remediate_beta_access(self) -> None:
        """PRO users have priority remediate beta access."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            manager.activate("RM-PRO0-1234-5678-ABCD")
            set_license_manager(manager)

            result = check_remediate_beta_allowed()
            assert result.allowed is True
            assert result.data["priority"] == "priority"

    @patch.object(LicenseManager, "_validate_online", mock_validate_online)
    def test_pro_no_trust_center(self) -> None:
        """PRO users cannot access Trust Center."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            manager.activate("RM-PRO0-1234-5678-ABCD")
            set_license_manager(manager)

            result = check_trust_center_allowed()
            assert result.allowed is False


class TestTeamUserWorkflow:
    """
    E2E tests for TEAM tier ($199/mo) user workflow.

    Scenario: DevOps team uses Trust Center for compliance,
              shares graphs, uses drift watch for monitoring.
    """

    @patch.object(LicenseManager, "_validate_online", mock_validate_online)
    def test_team_10_accounts(self) -> None:
        """TEAM users can use 10 AWS accounts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            manager.activate("RM-TEAM-1234-5678-ABCD")
            set_license_manager(manager)

            result = check_multi_account_allowed(10)
            assert result.allowed is True

            result = check_multi_account_allowed(11)
            assert result.allowed is False

    @patch.object(LicenseManager, "_validate_online", mock_validate_online)
    def test_team_trust_center_basic(self) -> None:
        """TEAM users have Trust Center with basic features."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            manager.activate("RM-TEAM-1234-5678-ABCD")
            set_license_manager(manager)

            # Trust Center enabled
            result = check_trust_center_allowed()
            assert result.allowed is True

            # JSON export only
            result = check_trust_export_allowed("json")
            assert result.allowed is True

            result = check_trust_export_allowed("csv")
            assert result.allowed is False

    @patch.object(LicenseManager, "_validate_online", mock_validate_online)
    def test_team_json_audit_export(self) -> None:
        """TEAM users can export JSON audit reports."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            manager.activate("RM-TEAM-1234-5678-ABCD")
            set_license_manager(manager)

            for fmt in ["html", "pdf", "json"]:
                result = check_audit_export_format_allowed(fmt)
                assert result.allowed is True, f"{fmt} should be allowed"

    @patch.object(LicenseManager, "_validate_online", mock_validate_online)
    def test_team_30_snapshots(self) -> None:
        """TEAM users have 30 snapshot limit."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            manager.activate("RM-TEAM-1234-5678-ABCD")
            set_license_manager(manager)

            result = check_snapshot_limit(25)
            assert result.allowed is True
            assert result.data["remaining"] == 5
            assert result.data["limit"] == 30


class TestEnterpriseUserWorkflow:
    """
    E2E tests for ENTERPRISE tier (from $500/mo) user workflow.

    Scenario: Regulated financial institution uses all compliance features,
              digital signatures, unlimited everything.
    """

    @patch.object(LicenseManager, "_validate_online", mock_validate_online)
    def test_enterprise_unlimited_accounts(self) -> None:
        """ENTERPRISE users have unlimited AWS accounts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            manager.activate("RM-ENTR-1234-5678-ABCD")
            set_license_manager(manager)

            # 1000 accounts should be allowed
            result = check_multi_account_allowed(1000)
            assert result.allowed is True

    @patch.object(LicenseManager, "_validate_online", mock_validate_online)
    def test_enterprise_full_trust_center(self) -> None:
        """ENTERPRISE users have full Trust Center."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            manager.activate("RM-ENTR-1234-5678-ABCD")
            set_license_manager(manager)

            # All export formats
            for fmt in ["json", "csv", "pdf"]:
                result = check_trust_export_allowed(fmt)
                assert result.allowed is True, f"{fmt} should be allowed"

    @patch.object(LicenseManager, "_validate_online", mock_validate_online)
    def test_enterprise_regional_compliance(self) -> None:
        """ENTERPRISE users have all regional compliance mappings."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            manager.activate("RM-ENTR-1234-5678-ABCD")
            set_license_manager(manager)

            # All compliance features
            assert check_compliance_apra_allowed().allowed is True

    @patch.object(LicenseManager, "_validate_online", mock_validate_online)
    def test_enterprise_unlimited_snapshots(self) -> None:
        """ENTERPRISE users have unlimited snapshots."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            manager.activate("RM-ENTR-1234-5678-ABCD")
            set_license_manager(manager)

            # 10,000 snapshots should be allowed
            result = check_snapshot_limit(10000)
            assert result.allowed is True

    @patch.object(LicenseManager, "_validate_online", mock_validate_online)
    def test_enterprise_csv_audit_export(self) -> None:
        """ENTERPRISE users can export CSV audit reports."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            manager.activate("RM-ENTR-1234-5678-ABCD")
            set_license_manager(manager)

            for fmt in ["html", "pdf", "json", "csv"]:
                result = check_audit_export_format_allowed(fmt)
                assert result.allowed is True, f"{fmt} should be allowed"

    @patch.object(LicenseManager, "_validate_online", mock_validate_online)
    def test_enterprise_4h_sla(self) -> None:
        """ENTERPRISE users have 4h email SLA."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            manager.activate("RM-ENTR-1234-5678-ABCD")
            set_license_manager(manager)

            sla = get_email_support_sla()
            assert sla == 4


class TestUpgradePathWorkflow:
    """
    E2E tests for upgrade path scenarios.

    Tests the FOMO-driven upgrade triggers as specified in the pricing matrix.
    """

    def test_free_to_solo_trigger_download(self) -> None:
        """
        FREE → SOLO: Triggered when user tries to download code.

        User sees 12,000 lines of Terraform but cannot download.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            set_license_manager(manager)

            result = check_clone_download_allowed()
            assert result.allowed is False
            assert "$49" in result.prompt
            assert "Solo" in result.prompt

    @patch.object(LicenseManager, "_validate_online", mock_validate_online)
    def test_solo_to_pro_trigger_second_account(self) -> None:
        """
        SOLO → PRO: Triggered when user tries to scan 2nd AWS account.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            manager.activate("RM-SOLO-1234-5678-ABCD")
            set_license_manager(manager)

            # 1 account is fine
            result = check_multi_account_allowed(1)
            assert result.allowed is True

            # 2 accounts triggers upgrade prompt
            result = check_multi_account_allowed(2)
            assert result.allowed is False
            assert "$99" in result.prompt or "Pro" in result.prompt

    @patch.object(LicenseManager, "_validate_online", mock_validate_online)
    def test_pro_to_team_trigger_trust_center(self) -> None:
        """
        PRO → TEAM: Triggered when user needs Trust Center for compliance.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            manager.activate("RM-PRO0-1234-5678-ABCD")
            set_license_manager(manager)

            result = check_trust_center_allowed()
            assert result.allowed is False
            assert "$199" in result.prompt or "Team" in result.prompt

    @patch.object(LicenseManager, "_validate_online", mock_validate_online)
    def test_team_to_enterprise_trigger_compliance(self) -> None:
        """
        TEAM → ENTERPRISE: Triggered when user needs APRA/RBNZ compliance.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            manager.activate("RM-TEAM-1234-5678-ABCD")
            set_license_manager(manager)

            result = check_compliance_apra_allowed()
            assert result.allowed is False
            assert "Enterprise" in result.prompt
