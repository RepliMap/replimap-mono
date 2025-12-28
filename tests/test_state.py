"""
Tests for the state management module.

Tests cover:
- State creation and persistence
- Scan recording
- Resource hash tracking for incremental scanning
- Error logging
- Snapshot registration
- State migration
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from replimap.core.state import (
    ErrorRecord,
    RepliMapState,
    ScanRecord,
    SnapshotInfo,
    StateManager,
    compute_config_hash,
)


class TestScanRecord:
    """Tests for ScanRecord dataclass."""

    def test_create_scan_record(self) -> None:
        """Can create a scan record."""
        record = ScanRecord(
            account_id="123456789012",
            region="us-east-1",
            started_at=datetime.now(),
        )

        assert record.account_id == "123456789012"
        assert record.region == "us-east-1"
        assert record.status == "in_progress"

    def test_scan_record_serialization(self) -> None:
        """Scan record can be serialized and deserialized."""
        original = ScanRecord(
            account_id="123456789012",
            region="us-east-1",
            started_at=datetime.now(),
            completed_at=datetime.now(),
            duration_seconds=45.5,
            node_count=100,
            edge_count=200,
            status="completed",
        )

        data = original.to_dict()
        restored = ScanRecord.from_dict(data)

        assert restored.account_id == original.account_id
        assert restored.region == original.region
        assert restored.duration_seconds == original.duration_seconds
        assert restored.node_count == original.node_count
        assert restored.edge_count == original.edge_count
        assert restored.status == original.status


class TestErrorRecord:
    """Tests for ErrorRecord dataclass."""

    def test_create_error_record(self) -> None:
        """Can create an error record."""
        error = ErrorRecord(
            timestamp=datetime.now(),
            resource_type="aws_instance",
            error_code="Throttling",
            error_message="Rate exceeded",
            region="us-east-1",
            retried=True,
        )

        assert error.resource_type == "aws_instance"
        assert error.error_code == "Throttling"
        assert error.retried is True

    def test_error_record_serialization(self) -> None:
        """Error record can be serialized and deserialized."""
        original = ErrorRecord(
            timestamp=datetime.now(),
            resource_type="aws_vpc",
            error_code="AccessDenied",
            error_message="Permission denied",
        )

        data = original.to_dict()
        restored = ErrorRecord.from_dict(data)

        assert restored.resource_type == original.resource_type
        assert restored.error_code == original.error_code


class TestSnapshotInfo:
    """Tests for SnapshotInfo dataclass."""

    def test_snapshot_info_serialization(self) -> None:
        """Snapshot info can be serialized and deserialized."""
        original = SnapshotInfo(
            snapshot_id="snap_20250115",
            timestamp=datetime.now(),
            db_file="graph_20250115.db",
            node_count=1000,
            edge_count=2000,
            account_id="123456789012",
            regions=["us-east-1", "us-west-2"],
        )

        data = original.to_dict()
        restored = SnapshotInfo.from_dict(data)

        assert restored.snapshot_id == original.snapshot_id
        assert restored.db_file == original.db_file
        assert restored.regions == original.regions


class TestRepliMapState:
    """Tests for RepliMapState."""

    def test_record_scan_start(self) -> None:
        """Can record scan start."""
        state = RepliMapState()
        state.record_scan_start("123456789012", "us-east-1")

        assert state.current_scan is not None
        assert state.current_scan.account_id == "123456789012"
        assert state.current_scan.status == "in_progress"

    def test_record_scan_complete(self) -> None:
        """Can record scan completion."""
        state = RepliMapState()
        state.record_scan_start("123456789012", "us-east-1")
        state.record_scan_complete(node_count=100, edge_count=200)

        assert state.current_scan is None
        assert len(state.scan_history) == 1
        assert state.scan_history[0].status == "completed"
        assert state.scan_history[0].node_count == 100
        assert state.scan_history[0].edge_count == 200

    def test_record_scan_failed(self) -> None:
        """Can record scan failure."""
        state = RepliMapState()
        state.record_scan_start("123456789012", "us-east-1")
        state.record_scan_failed("Connection timeout")

        assert state.current_scan is None
        assert len(state.scan_history) == 1
        assert state.scan_history[0].status == "failed"
        assert len(state.errors) == 1
        assert state.errors[0].error_message == "Connection timeout"

    def test_scan_history_limit(self) -> None:
        """Scan history is limited to MAX_SCAN_HISTORY."""
        state = RepliMapState()

        for i in range(15):
            state.record_scan_start(f"account_{i}", "us-east-1")
            state.record_scan_complete(node_count=i)

        assert len(state.scan_history) == state.MAX_SCAN_HISTORY

    def test_resource_hash_tracking(self) -> None:
        """Can track resource hashes for change detection."""
        state = RepliMapState()

        # Add some hashes
        state.update_resource_hash("vpc-123", "hash1")
        state.update_resource_hash("vpc-456", "hash2")

        # Check change detection
        assert state.has_resource_changed("vpc-123", "hash1") is False
        assert state.has_resource_changed("vpc-123", "hash_new") is True
        assert state.has_resource_changed("vpc-new", "hash_any") is True

    def test_batch_hash_update(self) -> None:
        """Can batch update resource hashes."""
        state = RepliMapState()

        hashes = {
            "vpc-1": "hash1",
            "vpc-2": "hash2",
            "vpc-3": "hash3",
        }
        state.update_resource_hashes_batch(hashes)

        assert len(state.resource_hashes) == 3
        assert state.has_resource_changed("vpc-1", "hash1") is False

    def test_get_changed_resources(self) -> None:
        """Can identify changed resources."""
        state = RepliMapState()
        state.resource_hashes = {
            "vpc-1": "old_hash1",
            "vpc-2": "old_hash2",
        }

        new_hashes = {
            "vpc-1": "old_hash1",  # Unchanged
            "vpc-2": "new_hash2",  # Changed
            "vpc-3": "new_hash3",  # New
        }

        changed = state.get_changed_resources(new_hashes)
        unchanged = state.get_unchanged_resources(new_hashes)

        assert "vpc-1" in unchanged
        assert "vpc-2" in changed
        assert "vpc-3" in changed

    def test_register_snapshot(self) -> None:
        """Can register a snapshot."""
        state = RepliMapState()

        snapshot = state.register_snapshot(
            snapshot_id="snap_123",
            db_file="graph.db",
            node_count=100,
            edge_count=200,
            account_id="123456789012",
            regions=["us-east-1"],
        )

        assert len(state.snapshots) == 1
        assert snapshot.snapshot_id == "snap_123"

    def test_error_logging(self) -> None:
        """Can log errors."""
        state = RepliMapState()

        state.record_error(
            resource_type="aws_instance",
            error_code="Throttling",
            error_message="Rate exceeded",
            region="us-east-1",
        )

        assert len(state.errors) == 1
        assert state.errors[0].error_code == "Throttling"

    def test_error_log_limit(self) -> None:
        """Error log is limited to MAX_ERROR_LOG."""
        state = RepliMapState()

        for i in range(150):
            state.record_error(
                resource_type=f"resource_{i}",
                error_code="Error",
                error_message=f"Error {i}",
            )

        assert len(state.errors) == state.MAX_ERROR_LOG

    def test_get_scan_stats(self) -> None:
        """Can get scan statistics."""
        state = RepliMapState()

        # Add some scans
        for i in range(5):
            state.record_scan_start("account", "us-east-1")
            state.record_scan_complete(node_count=100 + i * 10)

        stats = state.get_scan_stats()

        assert stats["total_scans"] == 5
        assert stats["successful_scans"] == 5
        assert stats["failed_scans"] == 0
        assert stats["avg_node_count"] > 0

    def test_state_serialization(self) -> None:
        """State can be serialized and deserialized."""
        state = RepliMapState()

        # Add some data
        state.record_scan_start("123456789012", "us-east-1")
        state.record_scan_complete(node_count=100)
        state.update_resource_hash("vpc-123", "hash123")
        state.record_error("aws_vpc", "Error", "Test error")
        state.register_snapshot(
            "snap_1", "graph.db", 100, 200, "123456789012", ["us-east-1"]
        )

        # Serialize and deserialize
        data = state.to_dict()
        restored = RepliMapState.from_dict(data)

        assert len(restored.scan_history) == 1
        assert restored.resource_hashes["vpc-123"] == "hash123"
        assert len(restored.errors) == 1
        assert len(restored.snapshots) == 1


class TestStateManager:
    """Tests for StateManager."""

    @pytest.fixture
    def manager(self, tmp_path: Path) -> StateManager:
        """Create a state manager with temporary directory."""
        return StateManager(working_dir=tmp_path)

    def test_load_creates_new_state(self, manager: StateManager) -> None:
        """Load creates new state if none exists."""
        state = manager.load()

        assert state is not None
        assert state.version == 2

    def test_save_and_load(self, manager: StateManager) -> None:
        """State can be saved and loaded."""
        state = manager.load()
        state.record_scan_start("123456789012", "us-east-1")
        state.record_scan_complete(node_count=50)
        state.update_resource_hash("vpc-123", "hash123")

        manager.save(state)

        # Create new manager and load
        manager2 = StateManager(
            working_dir=manager.working_dir,
            state_dir=manager.state_dir,
        )
        loaded = manager2.load()

        assert len(loaded.scan_history) == 1
        assert loaded.resource_hashes["vpc-123"] == "hash123"

    def test_state_file_location(self, manager: StateManager) -> None:
        """State file is created in .replimap directory."""
        state = manager.load()
        manager.save(state)

        assert manager.state_path.exists()
        assert manager.state_path.name == "state.yaml"
        assert manager.state_path.parent.name == ".replimap"

    def test_delete_state(self, manager: StateManager) -> None:
        """Can delete state file."""
        state = manager.load()
        manager.save(state)

        assert manager.state_path.exists()

        result = manager.delete()

        assert result is True
        assert not manager.state_path.exists()

    def test_delete_nonexistent_state(self, manager: StateManager) -> None:
        """Deleting nonexistent state returns False."""
        result = manager.delete()
        assert result is False

    def test_clear_resource_hashes(self, manager: StateManager) -> None:
        """Can clear resource hashes."""
        state = manager.load()
        state.update_resource_hash("vpc-123", "hash123")
        manager.save(state)

        manager.clear_resource_hashes()

        loaded = manager.load()
        assert len(loaded.resource_hashes) == 0

    def test_state_property_caches(self, manager: StateManager) -> None:
        """State property returns cached instance."""
        state1 = manager.state
        state2 = manager.state

        assert state1 is state2


class TestComputeConfigHash:
    """Tests for config hash computation."""

    def test_same_config_same_hash(self) -> None:
        """Same config produces same hash."""
        config = {"VpcId": "vpc-123", "CidrBlock": "10.0.0.0/16"}

        hash1 = compute_config_hash(config)
        hash2 = compute_config_hash(config)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex

    def test_different_config_different_hash(self) -> None:
        """Different configs produce different hashes."""
        config1 = {"VpcId": "vpc-123"}
        config2 = {"VpcId": "vpc-456"}

        hash1 = compute_config_hash(config1)
        hash2 = compute_config_hash(config2)

        assert hash1 != hash2

    def test_ignores_volatile_fields(self) -> None:
        """Volatile fields are ignored in hash computation."""
        config1 = {
            "VpcId": "vpc-123",
            "CreateTime": "2024-01-01T00:00:00Z",
            "LastModifiedTime": "2024-01-02T00:00:00Z",
        }

        config2 = {
            "VpcId": "vpc-123",
            "CreateTime": "2024-06-01T00:00:00Z",  # Different
            "LastModifiedTime": "2024-06-02T00:00:00Z",  # Different
        }

        hash1 = compute_config_hash(config1)
        hash2 = compute_config_hash(config2)

        # Should be same because only volatile fields differ
        assert hash1 == hash2

    def test_nested_config_hash(self) -> None:
        """Nested configs are properly hashed."""
        config = {
            "VpcId": "vpc-123",
            "Tags": [
                {"Key": "Name", "Value": "Test"},
            ],
            "Nested": {
                "Level1": {
                    "Level2": "value",
                },
            },
        }

        hash1 = compute_config_hash(config)
        assert len(hash1) == 64

    def test_order_independent_hash(self) -> None:
        """Hash is independent of key order."""
        config1 = {"a": 1, "b": 2, "c": 3}
        config2 = {"c": 3, "a": 1, "b": 2}

        hash1 = compute_config_hash(config1)
        hash2 = compute_config_hash(config2)

        assert hash1 == hash2


class TestIncrementalScanning:
    """Tests for incremental scanning workflow."""

    def test_incremental_scan_workflow(self, tmp_path: Path) -> None:
        """Full incremental scanning workflow."""
        manager = StateManager(working_dir=tmp_path)

        # First scan
        state = manager.load()
        state.record_scan_start("123456789012", "us-east-1")

        # Simulate scanning and hashing
        resources = {
            "vpc-1": compute_config_hash({"VpcId": "vpc-1", "CidrBlock": "10.0.0.0/16"}),
            "vpc-2": compute_config_hash({"VpcId": "vpc-2", "CidrBlock": "10.1.0.0/16"}),
        }
        state.update_resource_hashes_batch(resources)

        state.record_scan_complete(node_count=2)
        manager.save(state)

        # Second scan - check for changes
        manager2 = StateManager(working_dir=tmp_path)
        state2 = manager2.load()

        # Simulate new scan with one changed resource
        new_resources = {
            "vpc-1": compute_config_hash({"VpcId": "vpc-1", "CidrBlock": "10.0.0.0/16"}),  # Same
            "vpc-2": compute_config_hash({"VpcId": "vpc-2", "CidrBlock": "10.2.0.0/16"}),  # Changed!
            "vpc-3": compute_config_hash({"VpcId": "vpc-3", "CidrBlock": "10.3.0.0/16"}),  # New
        }

        changed = state2.get_changed_resources(new_resources)

        assert "vpc-1" not in changed  # Unchanged
        assert "vpc-2" in changed  # Changed
        assert "vpc-3" in changed  # New
