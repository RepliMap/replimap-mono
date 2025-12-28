"""
Tests for P3-1: Incremental Scanning.

Tests verify:
1. IncrementalScanner change detection
2. ResourceFingerprint hash generation
3. ScanStateStore persistence
4. Change categorization (created, modified, deleted, unchanged)
"""

import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from replimap.scanners.incremental import (
    ChangeType,
    IncrementalScanner,
    IncrementalScanResult,
    ResourceChange,
    ResourceFingerprint,
    ScanState,
    ScanStateStore,
)


class TestResourceFingerprint:
    """Test ResourceFingerprint model."""

    def test_create_fingerprint(self):
        """Test creating a resource fingerprint."""
        fp = ResourceFingerprint(
            resource_id="vpc-12345",
            resource_type="aws_vpc",
            config_hash="abc123",
            last_seen=datetime.utcnow(),
        )

        assert fp.resource_id == "vpc-12345"
        assert fp.resource_type == "aws_vpc"
        assert fp.config_hash == "abc123"
        assert fp.last_seen is not None

    def test_fingerprint_to_dict(self):
        """Test fingerprint serialization."""
        now = datetime.utcnow()
        fp = ResourceFingerprint(
            resource_id="vpc-12345",
            resource_type="aws_vpc",
            config_hash="abc123",
            last_seen=now,
            tags={"Environment": "prod"},
        )

        data = fp.to_dict()
        assert data["resource_id"] == "vpc-12345"
        assert data["resource_type"] == "aws_vpc"
        assert data["config_hash"] == "abc123"
        assert data["tags"] == {"Environment": "prod"}

    def test_fingerprint_from_dict(self):
        """Test fingerprint deserialization."""
        now = datetime.utcnow()
        data = {
            "resource_id": "vpc-12345",
            "resource_type": "aws_vpc",
            "config_hash": "abc123",
            "last_seen": now.isoformat(),
            "tags": {"Name": "test"},
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
        assert change.is_significant

    def test_deleted_change(self):
        """Test deleted change type."""
        change = ResourceChange(
            resource_id="vpc-old",
            resource_type="aws_vpc",
            change_type=ChangeType.DELETED,
        )

        assert change.change_type == ChangeType.DELETED
        assert change.is_significant

    def test_modified_change(self):
        """Test modified change type."""
        change = ResourceChange(
            resource_id="vpc-12345",
            resource_type="aws_vpc",
            change_type=ChangeType.MODIFIED,
            old_hash="old123",
            new_hash="new456",
        )

        assert change.change_type == ChangeType.MODIFIED
        assert change.is_significant
        assert change.old_hash != change.new_hash

    def test_unchanged(self):
        """Test unchanged type."""
        change = ResourceChange(
            resource_id="vpc-stable",
            resource_type="aws_vpc",
            change_type=ChangeType.UNCHANGED,
        )

        assert change.change_type == ChangeType.UNCHANGED
        assert not change.is_significant


class TestScanStateStore:
    """Test ScanStateStore persistence."""

    def test_save_and_load_state(self):
        """Test saving and loading scan state."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ScanStateStore(Path(tmpdir))

            # Create and save state
            state = ScanState(
                account_id="123456789012",
                region="us-east-1",
            )
            state.fingerprints["vpc-12345"] = ResourceFingerprint(
                resource_id="vpc-12345",
                resource_type="aws_vpc",
                config_hash="abc123",
                last_seen=datetime.utcnow(),
            )

            store.save(state)

            # Load and verify
            loaded = store.load("123456789012", "us-east-1")
            assert loaded is not None
            assert "vpc-12345" in loaded.fingerprints
            assert loaded.fingerprints["vpc-12345"].config_hash == "abc123"

    def test_load_nonexistent_state(self):
        """Test loading state that doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ScanStateStore(Path(tmpdir))
            loaded = store.load("nonexistent", "us-east-1")
            assert loaded is None


class TestIncrementalScanResult:
    """Test IncrementalScanResult."""

    def test_result_summary(self):
        """Test scan result summary."""
        result = IncrementalScanResult(
            account_id="123456789012",
            region="us-east-1",
            scan_time=datetime.utcnow(),
            is_incremental=True,
            created=[
                ResourceChange(
                    "vpc-new", "aws_vpc", ChangeType.CREATED
                )
            ],
            modified=[
                ResourceChange(
                    "vpc-mod", "aws_vpc", ChangeType.MODIFIED
                )
            ],
            deleted=[
                ResourceChange(
                    "vpc-old", "aws_vpc", ChangeType.DELETED
                )
            ],
            unchanged=[
                ResourceChange(
                    "vpc-same", "aws_vpc", ChangeType.UNCHANGED
                )
            ],
        )

        summary = result.summary
        assert summary["created"] == 1
        assert summary["modified"] == 1
        assert summary["deleted"] == 1
        assert summary["unchanged"] == 1
        assert summary["total_changes"] == 3
        assert summary["total_resources"] == 4

    def test_has_changes(self):
        """Test has_changes property."""
        # No changes
        result = IncrementalScanResult(
            account_id="123",
            region="us-east-1",
            scan_time=datetime.utcnow(),
            is_incremental=True,
            unchanged=[ResourceChange("vpc-1", "aws_vpc", ChangeType.UNCHANGED)],
        )
        assert not result.has_changes

        # Has changes
        result_with_changes = IncrementalScanResult(
            account_id="123",
            region="us-east-1",
            scan_time=datetime.utcnow(),
            is_incremental=True,
            created=[ResourceChange("vpc-new", "aws_vpc", ChangeType.CREATED)],
        )
        assert result_with_changes.has_changes


class TestIncrementalScanner:
    """Test IncrementalScanner."""

    def test_compute_hash(self):
        """Test config hash computation."""
        scanner = IncrementalScanner(region="us-east-1")

        config1 = {"cidr_block": "10.0.0.0/16", "tags": {"Name": "test"}}
        config2 = {"cidr_block": "10.0.0.0/16", "tags": {"Name": "test"}}
        config3 = {"cidr_block": "10.0.0.0/8", "tags": {"Name": "test"}}

        hash1 = scanner._compute_config_hash(config1)
        hash2 = scanner._compute_config_hash(config2)
        hash3 = scanner._compute_config_hash(config3)

        # Same config should produce same hash
        assert hash1 == hash2
        # Different config should produce different hash
        assert hash1 != hash3

    def test_detect_changes(self):
        """Test change detection."""
        scanner = IncrementalScanner(region="us-east-1")

        # Previous state
        old_fingerprints = {
            "vpc-same": ResourceFingerprint(
                "vpc-same", "aws_vpc", "hash1", datetime.utcnow()
            ),
            "vpc-modified": ResourceFingerprint(
                "vpc-modified", "aws_vpc", "old_hash", datetime.utcnow()
            ),
            "vpc-deleted": ResourceFingerprint(
                "vpc-deleted", "aws_vpc", "hash3", datetime.utcnow()
            ),
        }

        # Current resources
        current_resources = {
            "vpc-same": {"type": "aws_vpc", "hash": "hash1"},
            "vpc-modified": {"type": "aws_vpc", "hash": "new_hash"},
            "vpc-created": {"type": "aws_vpc", "hash": "hash4"},
        }

        changes = scanner._detect_changes(old_fingerprints, current_resources)

        created = [c for c in changes if c.change_type == ChangeType.CREATED]
        modified = [c for c in changes if c.change_type == ChangeType.MODIFIED]
        deleted = [c for c in changes if c.change_type == ChangeType.DELETED]
        unchanged = [c for c in changes if c.change_type == ChangeType.UNCHANGED]

        assert len(created) == 1
        assert created[0].resource_id == "vpc-created"

        assert len(modified) == 1
        assert modified[0].resource_id == "vpc-modified"

        assert len(deleted) == 1
        assert deleted[0].resource_id == "vpc-deleted"

        assert len(unchanged) == 1
        assert unchanged[0].resource_id == "vpc-same"
