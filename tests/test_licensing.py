"""Tests for the licensing module."""

import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from replimap.licensing.gates import (
    FeatureNotAvailableError,
    ResourceLimitExceededError,
    check_resource_limit,
    feature_gate,
    get_available_features,
    get_unavailable_features,
    get_upgrade_prompt,
    is_feature_available,
    require_plan,
)
from replimap.licensing.manager import LicenseManager, set_license_manager
from replimap.licensing.models import (
    Feature,
    License,
    LicenseStatus,
    LicenseValidationError,
    Plan,
    get_machine_fingerprint,
    get_plan_features,
)
from replimap.licensing.tracker import ScanRecord, UsageStats, UsageTracker


class TestPlanFeatures:
    """Tests for plan features configuration."""

    def test_free_plan_limits(self) -> None:
        """Test free plan has correct limits."""
        features = get_plan_features(Plan.FREE)
        assert features.max_resources_per_scan == 5
        assert features.max_scans_per_month == 3
        assert features.max_aws_accounts == 1
        assert features.price_monthly == 0

    def test_solo_plan_unlimited_resources(self) -> None:
        """Test solo plan has unlimited resources."""
        features = get_plan_features(Plan.SOLO)
        assert features.max_resources_per_scan is None
        assert features.max_scans_per_month is None
        assert features.max_aws_accounts == 1
        assert features.price_monthly == 49

    def test_pro_plan_multi_account(self) -> None:
        """Test pro plan has multi-account support."""
        features = get_plan_features(Plan.PRO)
        assert features.max_aws_accounts == 3
        assert features.has_feature(Feature.MULTI_ACCOUNT)
        assert features.has_feature(Feature.WEB_DASHBOARD)

    def test_team_plan_collaboration(self) -> None:
        """Test team plan has collaboration features."""
        features = get_plan_features(Plan.TEAM)
        assert features.max_aws_accounts == 10
        assert features.has_feature(Feature.COLLABORATION)
        assert features.has_feature(Feature.SHARED_GRAPHS)

    def test_enterprise_plan_all_features(self) -> None:
        """Test enterprise plan has all features."""
        features = get_plan_features(Plan.ENTERPRISE)
        assert features.max_aws_accounts is None  # Unlimited
        assert features.has_feature(Feature.SSO)
        assert features.has_feature(Feature.AUDIT_LOGS)
        assert features.has_feature(Feature.PRIORITY_SUPPORT)

    def test_feature_check(self) -> None:
        """Test feature availability check."""
        free_features = get_plan_features(Plan.FREE)
        assert free_features.has_feature(Feature.BASIC_SCAN)
        assert not free_features.has_feature(Feature.ASYNC_SCANNING)

    def test_can_scan_resources(self) -> None:
        """Test resource limit checking."""
        free_features = get_plan_features(Plan.FREE)
        assert free_features.can_scan_resources(3)
        assert free_features.can_scan_resources(5)
        assert not free_features.can_scan_resources(10)

        solo_features = get_plan_features(Plan.SOLO)
        assert solo_features.can_scan_resources(1000)  # Unlimited


class TestLicense:
    """Tests for License model."""

    def test_create_license(self) -> None:
        """Test creating a license."""
        license_obj = License(
            license_key="TEST-1234-5678-ABCD",
            plan=Plan.SOLO,
            email="test@example.com",
        )
        assert license_obj.plan == Plan.SOLO
        assert license_obj.email == "test@example.com"
        assert not license_obj.is_expired

    def test_license_expiration(self) -> None:
        """Test license expiration check."""
        # Non-expired license
        license_obj = License(
            license_key="TEST-1234-5678-ABCD",
            plan=Plan.SOLO,
            email="test@example.com",
            expires_at=datetime.now(UTC) + timedelta(days=30),
        )
        assert not license_obj.is_expired

        # Expired license
        expired_license = License(
            license_key="TEST-1234-5678-ABCD",
            plan=Plan.SOLO,
            email="test@example.com",
            expires_at=datetime.now(UTC) - timedelta(days=1),
        )
        assert expired_license.is_expired

    def test_license_features(self) -> None:
        """Test license features access."""
        license_obj = License(
            license_key="TEST-1234-5678-ABCD",
            plan=Plan.PRO,
            email="test@example.com",
        )
        assert license_obj.has_feature(Feature.MULTI_ACCOUNT)
        assert license_obj.has_feature(Feature.WEB_DASHBOARD)
        assert not license_obj.has_feature(Feature.SSO)

    def test_license_serialization(self) -> None:
        """Test license to/from dict."""
        license_obj = License(
            license_key="TEST-1234-5678-ABCD",
            plan=Plan.TEAM,
            email="test@example.com",
            organization="TestCorp",
        )

        data = license_obj.to_dict()
        restored = License.from_dict(data)

        assert restored.license_key == license_obj.license_key
        assert restored.plan == license_obj.plan
        assert restored.email == license_obj.email
        assert restored.organization == license_obj.organization


class TestMachineFingerprint:
    """Tests for machine fingerprinting."""

    def test_fingerprint_is_stable(self) -> None:
        """Test that fingerprint is consistent."""
        fp1 = get_machine_fingerprint()
        fp2 = get_machine_fingerprint()
        assert fp1 == fp2

    def test_fingerprint_format(self) -> None:
        """Test fingerprint format."""
        fp = get_machine_fingerprint()
        assert len(fp) == 32
        assert all(c in "0123456789abcdef" for c in fp)


class TestLicenseManager:
    """Tests for LicenseManager."""

    def test_manager_defaults_to_free(self) -> None:
        """Test manager defaults to free plan."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            assert manager.current_plan == Plan.FREE
            assert manager.current_license is None

    def test_activate_valid_key(self) -> None:
        """Test activating a valid license key."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            license_obj = manager.activate("SOLO-1234-5678-ABCD")

            assert license_obj.plan == Plan.SOLO
            assert manager.current_plan == Plan.SOLO
            assert manager.current_license is not None

    def test_activate_invalid_format(self) -> None:
        """Test activating with invalid key format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))

            with pytest.raises(LicenseValidationError):
                manager.activate("invalid-key")

    def test_deactivate(self) -> None:
        """Test deactivating a license."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            manager.activate("SOLO-1234-5678-ABCD")
            assert manager.current_plan == Plan.SOLO

            manager.deactivate()
            assert manager.current_plan == Plan.FREE
            assert manager.current_license is None

    def test_validate_status(self) -> None:
        """Test license validation status."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))

            # Free tier is valid
            status, message = manager.validate()
            assert status == LicenseStatus.VALID

            # Activated license is valid
            manager.activate("PRO0-1234-5678-ABCD")
            status, message = manager.validate()
            assert status == LicenseStatus.VALID

    def test_check_feature(self) -> None:
        """Test feature checking through manager."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))

            # Free tier features
            assert manager.check_feature("basic_scan")
            assert not manager.check_feature("async_scanning")

            # After upgrade
            manager.activate("SOLO-1234-5678-ABCD")
            assert manager.check_feature("async_scanning")

    def test_cache_persistence(self) -> None:
        """Test license cache persistence."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Activate license
            manager1 = LicenseManager(cache_dir=Path(tmpdir))
            manager1.activate("TEAM-1234-5678-ABCD")

            # Create new manager instance
            manager2 = LicenseManager(cache_dir=Path(tmpdir))
            assert manager2.current_plan == Plan.TEAM


class TestFeatureGates:
    """Tests for feature gating decorators."""

    def test_feature_gate_allows_when_available(self) -> None:
        """Test feature gate allows execution when feature available."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            manager.activate("SOLO-1234-5678-ABCD")
            set_license_manager(manager)

            @feature_gate(Feature.ASYNC_SCANNING)
            def async_scan() -> str:
                return "scanned"

            result = async_scan()
            assert result == "scanned"

    def test_feature_gate_blocks_when_unavailable(self) -> None:
        """Test feature gate blocks execution when feature unavailable."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            set_license_manager(manager)  # Free tier

            @feature_gate(Feature.SSO)
            def sso_login() -> str:
                return "logged in"

            with pytest.raises(FeatureNotAvailableError):
                sso_login()

    def test_feature_gate_with_fallback(self) -> None:
        """Test feature gate with fallback value."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            set_license_manager(manager)  # Free tier

            @feature_gate(Feature.ASYNC_SCANNING, fallback="sync mode")
            def scan_mode() -> str:
                return "async mode"

            result = scan_mode()
            assert result == "sync mode"

    def test_require_plan_allows_higher_tiers(self) -> None:
        """Test require_plan allows higher tier plans."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            manager.activate("TEAM-1234-5678-ABCD")
            set_license_manager(manager)

            @require_plan(Plan.SOLO)
            def premium_feature() -> str:
                return "premium"

            result = premium_feature()
            assert result == "premium"

    def test_require_plan_blocks_lower_tiers(self) -> None:
        """Test require_plan blocks lower tier plans."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            set_license_manager(manager)  # Free tier

            @require_plan(Plan.PRO)
            def pro_feature() -> str:
                return "pro"

            with pytest.raises(FeatureNotAvailableError):
                pro_feature()

    def test_check_resource_limit(self) -> None:
        """Test resource limit checking."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            set_license_manager(manager)  # Free tier (5 resources max)

            # Within limit
            check_resource_limit(3)  # Should not raise

            # Exceeds limit
            with pytest.raises(ResourceLimitExceededError):
                check_resource_limit(10)

    def test_is_feature_available(self) -> None:
        """Test is_feature_available helper."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            set_license_manager(manager)

            assert is_feature_available(Feature.BASIC_SCAN)
            assert not is_feature_available(Feature.SSO)

    def test_get_available_features(self) -> None:
        """Test get_available_features helper."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            set_license_manager(manager)

            features = get_available_features()
            assert Feature.BASIC_SCAN in features
            assert Feature.SSO not in features

    def test_get_unavailable_features(self) -> None:
        """Test get_unavailable_features helper."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(cache_dir=Path(tmpdir))
            set_license_manager(manager)

            unavailable = get_unavailable_features()
            assert Feature.SSO in unavailable
            assert Feature.BASIC_SCAN not in unavailable

    def test_get_upgrade_prompt(self) -> None:
        """Test upgrade prompt generation."""
        prompt = get_upgrade_prompt(Feature.ASYNC_SCANNING, Plan.FREE)
        assert "solo" in prompt.lower()
        assert "$49" in prompt
        assert "upgrade" in prompt.lower()


class TestUsageTracker:
    """Tests for UsageTracker."""

    def test_record_scan(self) -> None:
        """Test recording a scan."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = UsageTracker(data_dir=Path(tmpdir))

            record = tracker.record_scan(
                scan_id="test-scan-1",
                region="us-east-1",
                resource_count=50,
                resource_types={"aws_vpc": 5, "aws_subnet": 15},
                duration_seconds=10.5,
            )

            assert record.scan_id == "test-scan-1"
            assert record.resource_count == 50

    def test_get_stats(self) -> None:
        """Test getting usage statistics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = UsageTracker(data_dir=Path(tmpdir))

            tracker.record_scan(
                scan_id="scan-1",
                region="us-east-1",
                resource_count=50,
                resource_types={"aws_vpc": 5},
                duration_seconds=5.0,
            )
            tracker.record_scan(
                scan_id="scan-2",
                region="us-west-2",
                resource_count=30,
                resource_types={"aws_vpc": 3},
                duration_seconds=3.0,
            )

            stats = tracker.get_stats()
            assert stats.total_scans == 2
            assert stats.total_resources_scanned == 80
            assert len(stats.unique_regions) == 2

    def test_scans_this_month(self) -> None:
        """Test counting scans this month."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = UsageTracker(data_dir=Path(tmpdir))

            # Record current month scan
            tracker.record_scan(
                scan_id="scan-1",
                region="us-east-1",
                resource_count=10,
                resource_types={},
                duration_seconds=1.0,
            )

            assert tracker.get_scans_this_month() == 1

    def test_check_scan_quota(self) -> None:
        """Test scan quota checking."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = UsageTracker(data_dir=Path(tmpdir))

            # No scans yet
            assert tracker.check_scan_quota(max_scans=3)

            # Record some scans
            for i in range(3):
                tracker.record_scan(
                    scan_id=f"scan-{i}",
                    region="us-east-1",
                    resource_count=10,
                    resource_types={},
                    duration_seconds=1.0,
                )

            # Now at limit
            assert not tracker.check_scan_quota(max_scans=3)

            # Unlimited is always ok
            assert tracker.check_scan_quota(max_scans=None)

    def test_recent_scans(self) -> None:
        """Test getting recent scans."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = UsageTracker(data_dir=Path(tmpdir))

            for i in range(5):
                tracker.record_scan(
                    scan_id=f"scan-{i}",
                    region="us-east-1",
                    resource_count=10,
                    resource_types={},
                    duration_seconds=1.0,
                )

            recent = tracker.get_recent_scans(limit=3)
            assert len(recent) == 3
            # Most recent first
            assert recent[0].scan_id == "scan-4"

    def test_persistence(self) -> None:
        """Test usage data persistence."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Record with first tracker
            tracker1 = UsageTracker(data_dir=Path(tmpdir))
            tracker1.record_scan(
                scan_id="scan-1",
                region="us-east-1",
                resource_count=100,
                resource_types={"aws_vpc": 10},
                duration_seconds=5.0,
            )

            # Load with second tracker
            tracker2 = UsageTracker(data_dir=Path(tmpdir))
            stats = tracker2.get_stats()

            assert stats.total_scans == 1
            assert stats.total_resources_scanned == 100

    def test_clear_history(self) -> None:
        """Test clearing usage history."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = UsageTracker(data_dir=Path(tmpdir))

            tracker.record_scan(
                scan_id="scan-1",
                region="us-east-1",
                resource_count=10,
                resource_types={},
                duration_seconds=1.0,
            )

            tracker.clear_history()
            stats = tracker.get_stats()
            assert stats.total_scans == 0

    def test_export_for_sync(self) -> None:
        """Test exporting data for cloud sync."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = UsageTracker(data_dir=Path(tmpdir))

            tracker.record_scan(
                scan_id="scan-1",
                region="us-east-1",
                resource_count=50,
                resource_types={"aws_vpc": 5},
                duration_seconds=5.0,
            )

            export = tracker.export_for_sync()
            assert "stats" in export
            assert "recent_scans" in export
            assert "exported_at" in export


class TestScanRecord:
    """Tests for ScanRecord model."""

    def test_create_record(self) -> None:
        """Test creating a scan record."""
        record = ScanRecord(
            scan_id="test-123",
            timestamp=datetime.now(UTC),
            region="us-east-1",
            resource_count=100,
            resource_types={"aws_vpc": 10, "aws_subnet": 50},
            duration_seconds=15.5,
        )

        assert record.scan_id == "test-123"
        assert record.resource_count == 100
        assert record.success is True

    def test_record_serialization(self) -> None:
        """Test scan record to/from dict."""
        record = ScanRecord(
            scan_id="test-123",
            timestamp=datetime.now(UTC),
            region="us-west-2",
            resource_count=50,
            resource_types={"aws_vpc": 5},
            duration_seconds=10.0,
            profile="prod",
        )

        data = record.to_dict()
        restored = ScanRecord.from_dict(data)

        assert restored.scan_id == record.scan_id
        assert restored.region == record.region
        assert restored.resource_count == record.resource_count
        assert restored.profile == record.profile


class TestUsageStats:
    """Tests for UsageStats model."""

    def test_default_stats(self) -> None:
        """Test default usage stats."""
        stats = UsageStats()
        assert stats.total_scans == 0
        assert stats.total_resources_scanned == 0
        assert len(stats.unique_regions) == 0

    def test_stats_to_dict(self) -> None:
        """Test usage stats serialization."""
        stats = UsageStats(
            total_scans=10,
            total_resources_scanned=500,
            scans_this_month=3,
        )
        stats.unique_regions.add("us-east-1")

        data = stats.to_dict()
        assert data["total_scans"] == 10
        assert "us-east-1" in data["unique_regions"]


class TestDevMode:
    """Tests for dev mode functionality."""

    def test_dev_mode_disabled_by_default(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that dev mode is disabled by default."""
        monkeypatch.delenv("REPLIMAP_DEV_MODE", raising=False)
        from replimap.licensing.manager import is_dev_mode

        assert is_dev_mode() is False

    def test_dev_mode_enabled_with_1(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that dev mode is enabled with '1'."""
        monkeypatch.setenv("REPLIMAP_DEV_MODE", "1")
        from replimap.licensing.manager import is_dev_mode

        assert is_dev_mode() is True

    def test_dev_mode_enabled_with_true(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that dev mode is enabled with 'true'."""
        monkeypatch.setenv("REPLIMAP_DEV_MODE", "true")
        from replimap.licensing.manager import is_dev_mode

        assert is_dev_mode() is True

    def test_dev_mode_enabled_with_yes(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that dev mode is enabled with 'yes'."""
        monkeypatch.setenv("REPLIMAP_DEV_MODE", "yes")
        from replimap.licensing.manager import is_dev_mode

        assert is_dev_mode() is True

    def test_dev_mode_case_insensitive(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that dev mode check is case insensitive."""
        monkeypatch.setenv("REPLIMAP_DEV_MODE", "TRUE")
        from replimap.licensing.manager import is_dev_mode

        assert is_dev_mode() is True

    def test_dev_mode_returns_enterprise_plan(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that dev mode enables enterprise plan."""
        monkeypatch.setenv("REPLIMAP_DEV_MODE", "1")
        manager = LicenseManager()
        assert manager.current_plan == Plan.ENTERPRISE
        assert manager.is_dev_mode is True


class TestEnsureUtc:
    """Tests for ensure_utc helper function."""

    def test_naive_datetime_becomes_utc(self) -> None:
        """Test that naive datetime is converted to UTC."""
        from replimap.licensing.tracker import ensure_utc

        naive = datetime(2024, 1, 15, 12, 30, 0)
        result = ensure_utc(naive)
        assert result.tzinfo == UTC
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15

    def test_aware_datetime_unchanged(self) -> None:
        """Test that aware datetime is not modified."""
        from replimap.licensing.tracker import ensure_utc

        aware = datetime(2024, 1, 15, 12, 30, 0, tzinfo=UTC)
        result = ensure_utc(aware)
        assert result.tzinfo == UTC
        assert result == aware

    def test_scan_record_from_dict_handles_naive_timestamp(self) -> None:
        """Test that ScanRecord.from_dict handles naive timestamps."""
        data = {
            "scan_id": "test-123",
            "timestamp": "2024-01-15T12:30:00",  # No timezone info
            "region": "us-east-1",
            "resource_count": 10,
            "resource_types": {"aws_vpc": 1},
            "duration_seconds": 5.0,
        }
        record = ScanRecord.from_dict(data)
        assert record.timestamp.tzinfo == UTC

    def test_scan_record_from_dict_handles_aware_timestamp(self) -> None:
        """Test that ScanRecord.from_dict handles aware timestamps."""
        data = {
            "scan_id": "test-123",
            "timestamp": "2024-01-15T12:30:00+00:00",  # With timezone
            "region": "us-east-1",
            "resource_count": 10,
            "resource_types": {"aws_vpc": 1},
            "duration_seconds": 5.0,
        }
        record = ScanRecord.from_dict(data)
        assert record.timestamp.tzinfo is not None
