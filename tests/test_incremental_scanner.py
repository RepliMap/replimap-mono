"""
Tests for P3-1: Incremental Scanning.

Tests verify:
1. ResourceFingerprint model
2. ResourceChange model
3. ScanState model
4. ScanStateStore persistence
5. IncrementalScanResult model
"""

import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

from replimap.scanners.incremental import (
    ChangeType,
    IncrementalScanResult,
    ResourceChange,
    ResourceFingerprint,
    ScanState,
    ScanStateStore,
    get_change_summary,
)


class TestResourceFingerprint:
    """Test ResourceFingerprint model."""

    def test_create_fingerprint(self):
        """Test creating a resource fingerprint."""
        fp = ResourceFingerprint(
            resource_id="vpc-12345",
            resource_type="aws_vpc",
            arn="arn:aws:ec2:us-east-1:123456789012:vpc/vpc-12345",
            last_modified=datetime.now(UTC),
            config_hash="abc123",
            tags_hash="def456",
        )

        assert fp.resource_id == "vpc-12345"
        assert fp.resource_type == "aws_vpc"
        assert fp.config_hash == "abc123"
        assert fp.tags_hash == "def456"

    def test_fingerprint_to_dict(self):
        """Test fingerprint serialization."""
        now = datetime.now(UTC)
        fp = ResourceFingerprint(
            resource_id="vpc-12345",
            resource_type="aws_vpc",
            arn="arn:aws:ec2:us-east-1:123456789012:vpc/vpc-12345",
            last_modified=now,
            config_hash="abc123",
            tags_hash="def456",
            version="v1",
        )

        data = fp.to_dict()
        assert data["resource_id"] == "vpc-12345"
        assert data["resource_type"] == "aws_vpc"
        assert data["config_hash"] == "abc123"
        assert data["version"] == "v1"

    def test_fingerprint_from_dict(self):
        """Test fingerprint deserialization."""
        now = datetime.now(UTC)
        data = {
            "resource_id": "vpc-12345",
            "resource_type": "aws_vpc",
            "arn": None,
            "last_modified": now.isoformat(),
            "config_hash": "abc123",
            "tags_hash": "def456",
            "version": "",
        }

        fp = ResourceFingerprint.from_dict(data)
        assert fp.resource_id == "vpc-12345"
        assert fp.config_hash == "abc123"


class TestResourceChange:
    """Test ResourceChange model."""

    def test_created_change(self):
        """Test created change type."""
        change = ResourceChange(
            resource_id="vpc-new",
            resource_type="aws_vpc",
            change_type=ChangeType.CREATED,
        )

        assert change.change_type == ChangeType.CREATED
        assert change.previous_fingerprint is None

    def test_deleted_change(self):
        """Test deleted change type."""
        fp = ResourceFingerprint(
            resource_id="vpc-old",
            resource_type="aws_vpc",
            config_hash="abc",
        )
        change = ResourceChange(
            resource_id="vpc-old",
            resource_type="aws_vpc",
            change_type=ChangeType.DELETED,
            previous_fingerprint=fp,
        )

        assert change.change_type == ChangeType.DELETED
        assert change.previous_fingerprint is not None
        assert change.current_fingerprint is None

    def test_modified_change(self):
        """Test modified change type."""
        old_fp = ResourceFingerprint(
            resource_id="vpc-12345",
            resource_type="aws_vpc",
            config_hash="old123",
        )
        new_fp = ResourceFingerprint(
            resource_id="vpc-12345",
            resource_type="aws_vpc",
            config_hash="new456",
        )
        change = ResourceChange(
            resource_id="vpc-12345",
            resource_type="aws_vpc",
            change_type=ChangeType.MODIFIED,
            previous_fingerprint=old_fp,
            current_fingerprint=new_fp,
        )

        assert change.change_type == ChangeType.MODIFIED
        assert change.previous_fingerprint.config_hash == "old123"
        assert change.current_fingerprint.config_hash == "new456"

    def test_unchanged(self):
        """Test unchanged type."""
        change = ResourceChange(
            resource_id="vpc-stable",
            resource_type="aws_vpc",
            change_type=ChangeType.UNCHANGED,
        )

        assert change.change_type == ChangeType.UNCHANGED

    def test_change_to_dict(self):
        """Test change serialization."""
        change = ResourceChange(
            resource_id="vpc-1",
            resource_type="aws_vpc",
            change_type=ChangeType.CREATED,
        )

        data = change.to_dict()
        assert data["resource_id"] == "vpc-1"
        assert data["change_type"] == "created"


class TestScanState:
    """Test ScanState model."""

    def test_create_state(self):
        """Test creating scan state."""
        state = ScanState(region="us-east-1")
        assert state.region == "us-east-1"
        assert state.resource_count == 0

    def test_add_fingerprint(self):
        """Test adding fingerprint to state."""
        state = ScanState(region="us-east-1")
        fp = ResourceFingerprint(
            resource_id="vpc-12345",
            resource_type="aws_vpc",
            config_hash="abc123",
        )

        state.update_fingerprint(fp)
        assert state.resource_count == 1
        assert state.get_fingerprint("vpc-12345") is not None

    def test_remove_fingerprint(self):
        """Test removing fingerprint from state."""
        state = ScanState(region="us-east-1")
        fp = ResourceFingerprint(
            resource_id="vpc-12345",
            resource_type="aws_vpc",
            config_hash="abc123",
        )

        state.update_fingerprint(fp)
        state.remove_fingerprint("vpc-12345")
        assert state.get_fingerprint("vpc-12345") is None

    def test_state_to_dict(self):
        """Test state serialization."""
        state = ScanState(region="us-east-1")
        state.last_scan = datetime.now(UTC)
        state.metadata = {"scan_type": "full"}

        data = state.to_dict()
        assert data["region"] == "us-east-1"
        assert data["last_scan"] is not None
        assert data["metadata"]["scan_type"] == "full"

    def test_state_from_dict(self):
        """Test state deserialization."""
        data = {
            "region": "us-east-1",
            "last_scan": None,
            "fingerprints": {},
            "metadata": {},
        }

        state = ScanState.from_dict(data)
        assert state.region == "us-east-1"


class TestScanStateStore:
    """Test ScanStateStore persistence."""

    def test_save_and_load_state(self):
        """Test saving and loading scan state."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ScanStateStore(Path(tmpdir))

            # Create and save state
            state = ScanState(region="us-east-1")
            state.fingerprints["vpc-12345"] = ResourceFingerprint(
                resource_id="vpc-12345",
                resource_type="aws_vpc",
                config_hash="abc123",
            )

            store.save(state, account_id="123456789012")

            # Load and verify
            loaded = store.load("us-east-1", "123456789012")
            assert loaded is not None
            assert "vpc-12345" in loaded.fingerprints
            assert loaded.fingerprints["vpc-12345"].config_hash == "abc123"

    def test_load_nonexistent_state(self):
        """Test loading state that doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ScanStateStore(Path(tmpdir))
            loaded = store.load("nonexistent", "123456789012")
            assert loaded is None

    def test_delete_state(self):
        """Test deleting state."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ScanStateStore(Path(tmpdir))

            # Create and save
            state = ScanState(region="us-east-1")
            store.save(state, account_id="123456789012")

            # Verify exists
            assert store.load("us-east-1", "123456789012") is not None

            # Delete
            store.delete("us-east-1", "123456789012")

            # Verify deleted
            assert store.load("us-east-1", "123456789012") is None

    def test_list_regions(self):
        """Test listing regions with saved state."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ScanStateStore(Path(tmpdir))

            # Save states for multiple regions
            for region in ["us-east-1", "us-west-2", "eu-west-1"]:
                state = ScanState(region=region)
                store.save(state, account_id="test")

            regions = store.list_regions("test")
            assert len(regions) == 3
            assert "us-east-1" in regions
            assert "us-west-2" in regions
            assert "eu-west-1" in regions


class TestIncrementalScanResult:
    """Test IncrementalScanResult."""

    def test_result_creation(self):
        """Test scan result creation."""
        now = datetime.now(UTC)
        result = IncrementalScanResult(
            region="us-east-1",
            scan_start=now - timedelta(minutes=5),
            scan_end=now,
            resources_checked=100,
            resources_updated=10,
            resources_deleted=2,
            resources_unchanged=88,
            full_scan=False,
        )

        assert result.region == "us-east-1"
        assert result.resources_checked == 100
        assert result.duration_seconds > 0

    def test_has_changes(self):
        """Test has_changes property."""
        now = datetime.now(UTC)

        # No changes
        result = IncrementalScanResult(
            region="us-east-1",
            scan_start=now,
            scan_end=now,
            changes=[],
        )
        assert not result.has_changes

        # Has changes
        result_with_changes = IncrementalScanResult(
            region="us-east-1",
            scan_start=now,
            scan_end=now,
            changes=[
                ResourceChange("vpc-new", "aws_vpc", ChangeType.CREATED),
            ],
        )
        assert result_with_changes.has_changes

    def test_result_to_dict(self):
        """Test result serialization."""
        now = datetime.now(UTC)
        result = IncrementalScanResult(
            region="us-east-1",
            scan_start=now - timedelta(seconds=30),
            scan_end=now,
            resources_checked=50,
            resources_updated=5,
            full_scan=True,
        )

        data = result.to_dict()
        assert data["region"] == "us-east-1"
        assert data["summary"]["resources_checked"] == 50
        assert data["full_scan"] is True


class TestChangeSummary:
    """Test change summary function."""

    def test_empty_changes(self):
        """Test summary with no changes."""
        summary = get_change_summary([])
        assert summary["total_changes"] == 0

    def test_change_summary(self):
        """Test summary with multiple changes."""
        changes = [
            ResourceChange("vpc-1", "aws_vpc", ChangeType.CREATED),
            ResourceChange("vpc-2", "aws_vpc", ChangeType.CREATED),
            ResourceChange("subnet-1", "aws_subnet", ChangeType.MODIFIED),
            ResourceChange("sg-1", "aws_security_group", ChangeType.DELETED),
        ]

        summary = get_change_summary(changes)
        assert summary["total_changes"] == 4
        assert summary["by_change_type"]["created"] == 2
        assert summary["by_change_type"]["modified"] == 1
        assert summary["by_change_type"]["deleted"] == 1
        assert summary["by_resource_type"]["aws_vpc"] == 2
        assert summary["by_resource_type"]["aws_subnet"] == 1
