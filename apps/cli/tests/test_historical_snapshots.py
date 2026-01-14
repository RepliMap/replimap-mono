"""
Tests for P3-2: Historical Snapshots (Time Machine).

Tests verify:
1. ResourceSnapshot serialization
2. SnapshotMetadata model
3. AuditTrail and AuditEvent functionality
4. SnapshotDiff model
5. SnapshotComparison model and properties
6. SnapshotManager basic operations
"""

import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

from replimap.cache.snapshots import (
    AuditEvent,
    AuditEventType,
    AuditTrail,
    ResourceSnapshot,
    SnapshotComparison,
    SnapshotDiff,
    SnapshotManager,
    SnapshotMetadata,
)


class TestResourceSnapshot:
    """Test ResourceSnapshot model."""

    def test_create_snapshot(self):
        """Test creating a resource snapshot."""
        snap = ResourceSnapshot(
            resource_id="vpc-12345",
            resource_type="aws_vpc",
            resource_name="my-vpc",
            arn="arn:aws:ec2:us-east-1:123456789012:vpc/vpc-12345",
            region="us-east-1",
            config={"cidr_block": "10.0.0.0/16"},
            tags={"Environment": "prod"},
            dependencies=[],
        )

        assert snap.resource_id == "vpc-12345"
        assert snap.resource_type == "aws_vpc"
        assert snap.config["cidr_block"] == "10.0.0.0/16"
        assert snap.config_hash  # Should be auto-computed

    def test_snapshot_to_dict(self):
        """Test snapshot serialization."""
        snap = ResourceSnapshot(
            resource_id="vpc-12345",
            resource_type="aws_vpc",
            resource_name="my-vpc",
            arn=None,
            region="us-east-1",
            config={"cidr_block": "10.0.0.0/16"},
            tags={"Environment": "prod"},
            dependencies=["igw-12345"],
        )

        data = snap.to_dict()
        assert data["resource_id"] == "vpc-12345"
        assert data["config"]["cidr_block"] == "10.0.0.0/16"
        assert data["tags"]["Environment"] == "prod"
        assert data["dependencies"] == ["igw-12345"]
        assert data["config_hash"]

    def test_snapshot_from_dict(self):
        """Test snapshot deserialization."""
        data = {
            "resource_id": "vpc-12345",
            "resource_type": "aws_vpc",
            "resource_name": "my-vpc",
            "arn": None,
            "region": "us-east-1",
            "config": {"cidr_block": "10.0.0.0/16"},
            "tags": {},
            "dependencies": [],
            "config_hash": "abc123",
        }

        snap = ResourceSnapshot.from_dict(data)
        assert snap.resource_id == "vpc-12345"
        assert snap.config["cidr_block"] == "10.0.0.0/16"
        assert snap.config_hash == "abc123"

    def test_config_hash_computed(self):
        """Test that config hash is auto-computed if not provided."""
        snap1 = ResourceSnapshot(
            resource_id="vpc-1",
            resource_type="aws_vpc",
            resource_name="vpc",
            arn=None,
            region="us-east-1",
            config={"cidr": "10.0.0.0/16"},
            tags={},
            dependencies=[],
        )

        snap2 = ResourceSnapshot(
            resource_id="vpc-2",
            resource_type="aws_vpc",
            resource_name="vpc",
            arn=None,
            region="us-east-1",
            config={"cidr": "10.0.0.0/16"},  # Same config
            tags={},
            dependencies=[],
        )

        # Same config should produce same hash
        assert snap1.config_hash == snap2.config_hash


class TestSnapshotMetadata:
    """Test SnapshotMetadata model."""

    def test_create_metadata(self):
        """Test creating snapshot metadata."""
        meta = SnapshotMetadata(
            snapshot_id="snap-001",
            created_at=datetime.now(UTC),
            region="us-east-1",
            account_id="123456789012",
            resource_count=10,
            description="Test snapshot",
        )

        assert meta.snapshot_id == "snap-001"
        assert meta.resource_count == 10

    def test_metadata_to_dict(self):
        """Test metadata serialization."""
        now = datetime.now(UTC)
        meta = SnapshotMetadata(
            snapshot_id="snap-001",
            created_at=now,
            region="us-east-1",
            account_id="123456789012",
            resource_count=10,
            description="Test snapshot",
            tags={"env": "test"},
        )

        data = meta.to_dict()
        assert data["snapshot_id"] == "snap-001"
        assert data["resource_count"] == 10
        assert data["tags"] == {"env": "test"}

    def test_metadata_from_dict(self):
        """Test metadata deserialization."""
        data = {
            "snapshot_id": "snap-001",
            "created_at": "2024-01-01T00:00:00+00:00",
            "region": "us-east-1",
            "account_id": "123456789012",
            "resource_count": 5,
        }

        meta = SnapshotMetadata.from_dict(data)
        assert meta.snapshot_id == "snap-001"
        assert meta.resource_count == 5


class TestAuditEventAndTrail:
    """Test AuditEvent and AuditTrail."""

    def test_create_audit_event(self):
        """Test creating an audit event."""
        event = AuditEvent(
            event_type=AuditEventType.SNAPSHOT_CREATED,
            timestamp=datetime.now(UTC),
            details={"resource_count": 10},
            snapshot_id="snap-001",
        )

        assert event.event_type == AuditEventType.SNAPSHOT_CREATED
        assert event.details["resource_count"] == 10

    def test_audit_event_to_dict(self):
        """Test event serialization."""
        now = datetime.now(UTC)
        event = AuditEvent(
            event_type=AuditEventType.RESOURCE_ADDED,
            timestamp=now,
            details={"resource_id": "vpc-1"},
            actor="test-user",
            snapshot_id="snap-001",
        )

        data = event.to_dict()
        assert data["event_type"] == "resource_added"
        assert data["actor"] == "test-user"

    def test_audit_event_from_dict(self):
        """Test event deserialization."""
        data = {
            "event_type": "snapshot_deleted",
            "timestamp": "2024-01-01T00:00:00+00:00",
            "details": {},
            "actor": "system",
            "snapshot_id": "snap-001",
        }

        event = AuditEvent.from_dict(data)
        assert event.event_type == AuditEventType.SNAPSHOT_DELETED

    def test_audit_trail_add_event(self):
        """Test adding events to audit trail."""
        trail = AuditTrail()

        event = AuditEvent(
            event_type=AuditEventType.SNAPSHOT_CREATED,
            timestamp=datetime.now(UTC),
            snapshot_id="snap-001",
        )

        trail.add_event(event)
        assert len(trail.events) == 1

    def test_audit_trail_get_events_by_type(self):
        """Test filtering events by type."""
        trail = AuditTrail()

        trail.add_event(
            AuditEvent(
                event_type=AuditEventType.SNAPSHOT_CREATED,
                timestamp=datetime.now(UTC),
                snapshot_id="snap-001",
            )
        )
        trail.add_event(
            AuditEvent(
                event_type=AuditEventType.SNAPSHOT_DELETED,
                timestamp=datetime.now(UTC),
                snapshot_id="snap-002",
            )
        )
        trail.add_event(
            AuditEvent(
                event_type=AuditEventType.SNAPSHOT_CREATED,
                timestamp=datetime.now(UTC),
                snapshot_id="snap-003",
            )
        )

        created_events = trail.get_events(event_type=AuditEventType.SNAPSHOT_CREATED)
        assert len(created_events) == 2

    def test_audit_trail_get_events_by_time(self):
        """Test filtering events by time."""
        trail = AuditTrail()
        now = datetime.now(UTC)

        trail.add_event(
            AuditEvent(
                event_type=AuditEventType.SNAPSHOT_CREATED,
                timestamp=now - timedelta(hours=2),
            )
        )
        trail.add_event(
            AuditEvent(
                event_type=AuditEventType.SNAPSHOT_CREATED,
                timestamp=now,
            )
        )

        # Get events from last hour
        recent_events = trail.get_events(start_time=now - timedelta(hours=1))
        assert len(recent_events) == 1

    def test_audit_trail_max_events(self):
        """Test audit trail trimming at max capacity."""
        trail = AuditTrail(max_events=5)

        for i in range(10):
            trail.add_event(
                AuditEvent(
                    event_type=AuditEventType.SNAPSHOT_CREATED,
                    timestamp=datetime.now(UTC),
                    snapshot_id=f"snap-{i}",
                )
            )

        # Should only keep last 5 events
        assert len(trail.events) == 5
        assert trail.events[0].snapshot_id == "snap-5"


class TestSnapshotDiff:
    """Test SnapshotDiff model."""

    def test_create_diff_added(self):
        """Test creating a diff for added resource."""
        new_resource = ResourceSnapshot(
            resource_id="vpc-1",
            resource_type="aws_vpc",
            resource_name="new-vpc",
            arn=None,
            region="us-east-1",
            config={"cidr": "10.0.0.0/16"},
            tags={},
            dependencies=[],
        )

        diff = SnapshotDiff(
            resource_id="vpc-1",
            resource_type="aws_vpc",
            change_type="added",
            new_snapshot=new_resource,
        )

        assert diff.change_type == "added"
        assert diff.old_snapshot is None
        assert diff.new_snapshot is not None

    def test_create_diff_modified(self):
        """Test creating a diff for modified resource."""
        old_resource = ResourceSnapshot(
            resource_id="vpc-1",
            resource_type="aws_vpc",
            resource_name="vpc",
            arn=None,
            region="us-east-1",
            config={"cidr": "10.0.0.0/16"},
            tags={},
            dependencies=[],
        )

        new_resource = ResourceSnapshot(
            resource_id="vpc-1",
            resource_type="aws_vpc",
            resource_name="vpc",
            arn=None,
            region="us-east-1",
            config={"cidr": "10.0.0.0/8"},  # Modified
            tags={},
            dependencies=[],
        )

        diff = SnapshotDiff(
            resource_id="vpc-1",
            resource_type="aws_vpc",
            change_type="modified",
            old_snapshot=old_resource,
            new_snapshot=new_resource,
            changed_fields=["cidr"],
        )

        assert diff.change_type == "modified"
        assert "cidr" in diff.changed_fields

    def test_diff_to_dict(self):
        """Test diff serialization."""
        diff = SnapshotDiff(
            resource_id="vpc-1",
            resource_type="aws_vpc",
            change_type="removed",
        )

        data = diff.to_dict()
        assert data["resource_id"] == "vpc-1"
        assert data["change_type"] == "removed"


class TestSnapshotComparison:
    """Test SnapshotComparison model."""

    def test_create_comparison(self):
        """Test creating a snapshot comparison."""
        now = datetime.now(UTC)
        comparison = SnapshotComparison(
            old_snapshot_id="snap-001",
            new_snapshot_id="snap-002",
            old_timestamp=now - timedelta(hours=1),
            new_timestamp=now,
            added_count=3,
            removed_count=1,
            modified_count=2,
        )

        assert comparison.total_changes == 6
        assert comparison.has_changes

    def test_comparison_no_changes(self):
        """Test comparison with no changes."""
        now = datetime.now(UTC)
        comparison = SnapshotComparison(
            old_snapshot_id="snap-001",
            new_snapshot_id="snap-002",
            old_timestamp=now - timedelta(hours=1),
            new_timestamp=now,
        )

        assert comparison.total_changes == 0
        assert not comparison.has_changes

    def test_comparison_to_dict(self):
        """Test comparison serialization."""
        now = datetime.now(UTC)
        comparison = SnapshotComparison(
            old_snapshot_id="snap-001",
            new_snapshot_id="snap-002",
            old_timestamp=now - timedelta(hours=1),
            new_timestamp=now,
            added_count=1,
            removed_count=1,
            modified_count=1,
        )

        data = comparison.to_dict()
        assert data["old_snapshot_id"] == "snap-001"
        assert data["summary"]["total_changes"] == 3


class TestSnapshotManager:
    """Test SnapshotManager."""

    def test_manager_initialization(self):
        """Test manager initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SnapshotManager(Path(tmpdir))
            assert manager.retention_days == 30
            assert manager.compress is True

    def test_manager_custom_retention(self):
        """Test manager with custom retention."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SnapshotManager(Path(tmpdir), retention_days=7)
            assert manager.retention_days == 7

    def test_list_empty_snapshots(self):
        """Test listing snapshots when none exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SnapshotManager(Path(tmpdir))
            snapshots = manager.list_snapshots()
            assert len(snapshots) == 0

    def test_audit_trail_property(self):
        """Test accessing audit trail."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SnapshotManager(Path(tmpdir))
            trail = manager.audit_trail
            assert isinstance(trail, AuditTrail)

    def test_delete_nonexistent_snapshot(self):
        """Test deleting a snapshot that doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SnapshotManager(Path(tmpdir))
            result = manager.delete_snapshot("nonexistent-id")
            assert result is False

    def test_load_nonexistent_snapshot(self):
        """Test loading a snapshot that doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SnapshotManager(Path(tmpdir))
            result = manager.load_snapshot("nonexistent-id")
            assert result is None

    def test_cleanup_old_snapshots_empty(self):
        """Test cleanup when no snapshots exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SnapshotManager(Path(tmpdir), retention_days=1)
            deleted = manager.cleanup_old_snapshots()
            assert deleted == 0

    def test_get_snapshot_at_time_none(self):
        """Test getting snapshot at time when none exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SnapshotManager(Path(tmpdir))
            result = manager.get_snapshot_at_time(
                target_time=datetime.now(UTC),
                region="us-east-1",
            )
            assert result is None
