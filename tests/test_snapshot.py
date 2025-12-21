"""
Tests for the Drift Snapshot Mode.

These tests verify that:
1. Snapshot models work correctly (serialization, hashing)
2. SnapshotStore save/load/list/delete operations work
3. SnapshotDiffer comparison logic and severity assessment work
4. SnapshotReporter output formatting works
"""

import tempfile
from datetime import UTC, datetime
from pathlib import Path

import pytest

from replimap.snapshot import (
    InfraSnapshot,
    ResourceChange,
    ResourceSnapshot,
    SnapshotDiff,
    SnapshotDiffer,
    SnapshotReporter,
    SnapshotStore,
)


# =============================================================================
# RESOURCE SNAPSHOT TESTS
# =============================================================================


class TestResourceSnapshot:
    """Test ResourceSnapshot model."""

    def test_create_basic_resource(self):
        """Test creating a basic resource snapshot."""
        resource = ResourceSnapshot(
            id="vpc-12345",
            type="aws_vpc",
            name="my-vpc",
            region="us-east-1",
            config={"cidr_block": "10.0.0.0/16"},
        )

        assert resource.id == "vpc-12345"
        assert resource.type == "aws_vpc"
        assert resource.name == "my-vpc"
        assert resource.region == "us-east-1"
        assert resource.config == {"cidr_block": "10.0.0.0/16"}
        # Hash should be auto-computed
        assert resource.config_hash

    def test_config_hash_computed(self):
        """Test that config hash is computed deterministically."""
        config = {"key": "value", "nested": {"a": 1, "b": 2}}

        resource1 = ResourceSnapshot(id="r1", type="aws_test", config=config)
        resource2 = ResourceSnapshot(id="r2", type="aws_test", config=config)

        # Same config should produce same hash
        assert resource1.config_hash == resource2.config_hash

    def test_config_hash_differs_for_different_config(self):
        """Test that different configs produce different hashes."""
        resource1 = ResourceSnapshot(id="r1", type="aws_test", config={"key": "value1"})
        resource2 = ResourceSnapshot(id="r2", type="aws_test", config={"key": "value2"})

        assert resource1.config_hash != resource2.config_hash

    def test_to_dict_and_from_dict(self):
        """Test round-trip serialization."""
        resource = ResourceSnapshot(
            id="vpc-12345",
            type="aws_vpc",
            arn="arn:aws:ec2:us-east-1:123456789:vpc/vpc-12345",
            name="my-vpc",
            region="us-east-1",
            config={"cidr_block": "10.0.0.0/16"},
            tags={"Environment": "production"},
        )

        data = resource.to_dict()
        restored = ResourceSnapshot.from_dict(data)

        assert restored.id == resource.id
        assert restored.type == resource.type
        assert restored.arn == resource.arn
        assert restored.name == resource.name
        assert restored.region == resource.region
        assert restored.config == resource.config
        assert restored.tags == resource.tags
        assert restored.config_hash == resource.config_hash


# =============================================================================
# INFRA SNAPSHOT TESTS
# =============================================================================


class TestInfraSnapshot:
    """Test InfraSnapshot model."""

    def test_create_empty_snapshot(self):
        """Test creating an empty snapshot."""
        snapshot = InfraSnapshot(name="test-snapshot")

        assert snapshot.name == "test-snapshot"
        assert snapshot.resource_count == 0
        assert len(snapshot.resources) == 0
        assert snapshot.version == "1.0"

    def test_create_snapshot_with_resources(self):
        """Test creating a snapshot with resources."""
        resources = [
            ResourceSnapshot(id="vpc-1", type="aws_vpc", config={}),
            ResourceSnapshot(id="subnet-1", type="aws_subnet", config={}),
        ]

        snapshot = InfraSnapshot(
            name="test-snapshot",
            region="us-east-1",
            resources=resources,
        )

        assert snapshot.resource_count == 2
        assert len(snapshot.resources) == 2

    def test_get_resource(self):
        """Test getting a resource by ID."""
        resources = [
            ResourceSnapshot(id="vpc-1", type="aws_vpc", config={}),
            ResourceSnapshot(id="subnet-1", type="aws_subnet", config={}),
        ]
        snapshot = InfraSnapshot(name="test", resources=resources)

        found = snapshot.get_resource("vpc-1")
        not_found = snapshot.get_resource("nonexistent")

        assert found is not None
        assert found.id == "vpc-1"
        assert not_found is None

    def test_get_resources_by_type(self):
        """Test getting resources by type."""
        resources = [
            ResourceSnapshot(id="vpc-1", type="aws_vpc", config={}),
            ResourceSnapshot(id="subnet-1", type="aws_subnet", config={}),
            ResourceSnapshot(id="subnet-2", type="aws_subnet", config={}),
        ]
        snapshot = InfraSnapshot(name="test", resources=resources)

        vpcs = snapshot.get_resources_by_type("aws_vpc")
        subnets = snapshot.get_resources_by_type("aws_subnet")
        sgs = snapshot.get_resources_by_type("aws_security_group")

        assert len(vpcs) == 1
        assert len(subnets) == 2
        assert len(sgs) == 0

    def test_resource_types(self):
        """Test counting resources by type."""
        resources = [
            ResourceSnapshot(id="vpc-1", type="aws_vpc", config={}),
            ResourceSnapshot(id="subnet-1", type="aws_subnet", config={}),
            ResourceSnapshot(id="subnet-2", type="aws_subnet", config={}),
        ]
        snapshot = InfraSnapshot(name="test", resources=resources)

        types = snapshot.resource_types()

        assert types["aws_vpc"] == 1
        assert types["aws_subnet"] == 2

    def test_save_and_load(self):
        """Test saving and loading a snapshot."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "snapshot.json"

            resources = [
                ResourceSnapshot(
                    id="vpc-1",
                    type="aws_vpc",
                    name="my-vpc",
                    config={"cidr_block": "10.0.0.0/16"},
                    tags={"Environment": "test"},
                ),
            ]
            snapshot = InfraSnapshot(
                name="test-snapshot",
                region="us-east-1",
                vpc_id="vpc-1",
                profile="default",
                resources=resources,
            )

            snapshot.save(path)
            assert path.exists()

            loaded = InfraSnapshot.load(path)

            assert loaded.name == snapshot.name
            assert loaded.region == snapshot.region
            assert loaded.vpc_id == snapshot.vpc_id
            assert loaded.profile == snapshot.profile
            assert loaded.resource_count == snapshot.resource_count
            assert len(loaded.resources) == 1
            assert loaded.resources[0].id == "vpc-1"

    def test_to_dict_and_from_dict(self):
        """Test round-trip dictionary serialization."""
        resources = [
            ResourceSnapshot(id="vpc-1", type="aws_vpc", config={}),
        ]
        snapshot = InfraSnapshot(
            name="test",
            region="us-east-1",
            vpc_id="vpc-1",
            resources=resources,
        )

        data = snapshot.to_dict()
        restored = InfraSnapshot.from_dict(data)

        assert restored.name == snapshot.name
        assert restored.region == snapshot.region
        assert restored.resource_count == snapshot.resource_count


# =============================================================================
# RESOURCE CHANGE TESTS
# =============================================================================


class TestResourceChange:
    """Test ResourceChange model."""

    def test_create_added_change(self):
        """Test creating an added change."""
        change = ResourceChange(
            resource_id="vpc-1",
            resource_type="aws_vpc",
            resource_name="my-vpc",
            change_type="added",
            after={"cidr_block": "10.0.0.0/16"},
            severity="medium",
        )

        assert change.change_type == "added"
        assert change.severity == "medium"

    def test_create_modified_change(self):
        """Test creating a modified change."""
        change = ResourceChange(
            resource_id="vpc-1",
            resource_type="aws_vpc",
            change_type="modified",
            changed_attributes=["cidr_block"],
            before={"cidr_block": "10.0.0.0/16"},
            after={"cidr_block": "10.0.0.0/24"},
            severity="low",
        )

        assert change.change_type == "modified"
        assert "cidr_block" in change.changed_attributes

    def test_is_security_relevant(self):
        """Test security relevance detection."""
        security_change = ResourceChange(
            resource_id="sg-1",
            resource_type="aws_security_group",
            change_type="modified",
            changed_attributes=["ingress"],
        )
        normal_change = ResourceChange(
            resource_id="vpc-1",
            resource_type="aws_vpc",
            change_type="modified",
            changed_attributes=["tags"],
        )

        assert security_change.is_security_relevant is True
        assert normal_change.is_security_relevant is False

    def test_security_relevant_attributes(self):
        """Test various security-relevant attributes."""
        test_cases = [
            ("policy", True),
            ("ingress", True),
            ("egress", True),
            ("public_access", True),
            ("encrypted", True),
            ("kms_key_id", True),
            ("security_groups", True),
            ("iam_role", True),
            ("name", False),
            ("tags", False),
            ("description", False),
        ]

        for attr, expected in test_cases:
            change = ResourceChange(
                resource_id="r-1",
                resource_type="aws_test",
                change_type="modified",
                changed_attributes=[attr],
            )
            assert change.is_security_relevant == expected, f"Failed for {attr}"


# =============================================================================
# SNAPSHOT DIFF TESTS
# =============================================================================


class TestSnapshotDiff:
    """Test SnapshotDiff model."""

    def test_empty_diff(self):
        """Test diff with no changes."""
        diff = SnapshotDiff(
            baseline_name="baseline",
            baseline_date="2024-01-01T00:00:00Z",
            current_name="current",
            current_date="2024-01-02T00:00:00Z",
        )

        assert diff.total_changes == 0
        assert diff.has_changes is False
        assert diff.has_critical_changes is False

    def test_diff_with_changes(self):
        """Test diff with changes."""
        changes = [
            ResourceChange(
                resource_id="vpc-1", resource_type="aws_vpc", change_type="added"
            ),
            ResourceChange(
                resource_id="vpc-2", resource_type="aws_vpc", change_type="removed"
            ),
        ]
        critical_changes = [
            ResourceChange(
                resource_id="iam-1",
                resource_type="aws_iam_role",
                change_type="removed",
                severity="critical",
            )
        ]

        diff = SnapshotDiff(
            baseline_name="baseline",
            baseline_date="2024-01-01T00:00:00Z",
            current_name="current",
            current_date="2024-01-02T00:00:00Z",
            total_added=1,
            total_removed=1,
            total_modified=0,
            total_unchanged=10,
            changes=changes,
            critical_changes=critical_changes,
        )

        assert diff.total_changes == 2
        assert diff.has_changes is True
        assert diff.has_critical_changes is True

    def test_get_changes_by_type(self):
        """Test filtering changes by type."""
        changes = [
            ResourceChange(
                resource_id="r1", resource_type="aws_vpc", change_type="added"
            ),
            ResourceChange(
                resource_id="r2", resource_type="aws_vpc", change_type="added"
            ),
            ResourceChange(
                resource_id="r3", resource_type="aws_vpc", change_type="removed"
            ),
        ]

        diff = SnapshotDiff(
            baseline_name="b",
            baseline_date="",
            current_name="c",
            current_date="",
            changes=changes,
        )

        added = diff.get_changes_by_type("added")
        removed = diff.get_changes_by_type("removed")

        assert len(added) == 2
        assert len(removed) == 1

    def test_get_changes_by_severity(self):
        """Test filtering changes by severity."""
        changes = [
            ResourceChange(
                resource_id="r1",
                resource_type="aws_vpc",
                change_type="added",
                severity="low",
            ),
            ResourceChange(
                resource_id="r2",
                resource_type="aws_vpc",
                change_type="modified",
                severity="high",
            ),
            ResourceChange(
                resource_id="r3",
                resource_type="aws_iam_role",
                change_type="removed",
                severity="critical",
            ),
        ]

        diff = SnapshotDiff(
            baseline_name="b",
            baseline_date="",
            current_name="c",
            current_date="",
            changes=changes,
        )

        low = diff.get_changes_by_severity("low")
        high = diff.get_changes_by_severity("high")
        critical = diff.get_changes_by_severity("critical")

        assert len(low) == 1
        assert len(high) == 1
        assert len(critical) == 1

    def test_summary_text(self):
        """Test summary text generation."""
        diff = SnapshotDiff(
            baseline_name="baseline",
            baseline_date="2024-01-01T00:00:00Z",
            current_name="current",
            current_date="2024-01-02T00:00:00Z",
            total_added=5,
            total_removed=2,
            total_modified=3,
            total_unchanged=100,
        )

        summary = diff.summary_text()

        assert "baseline" in summary
        assert "current" in summary
        assert "Added: 5" in summary
        assert "Removed: 2" in summary
        assert "Modified: 3" in summary

    def test_to_dict_and_from_dict(self):
        """Test round-trip serialization."""
        changes = [
            ResourceChange(
                resource_id="vpc-1", resource_type="aws_vpc", change_type="added"
            ),
        ]
        diff = SnapshotDiff(
            baseline_name="baseline",
            baseline_date="2024-01-01T00:00:00Z",
            current_name="current",
            current_date="2024-01-02T00:00:00Z",
            total_added=1,
            changes=changes,
        )

        data = diff.to_dict()
        restored = SnapshotDiff.from_dict(data)

        assert restored.baseline_name == diff.baseline_name
        assert restored.current_name == diff.current_name
        assert restored.total_added == diff.total_added


# =============================================================================
# SNAPSHOT STORE TESTS
# =============================================================================


class TestSnapshotStore:
    """Test SnapshotStore class."""

    def test_save_and_load(self):
        """Test saving and loading a snapshot."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = SnapshotStore(Path(tmpdir))

            resources = [
                ResourceSnapshot(
                    id="vpc-1", type="aws_vpc", config={"cidr_block": "10.0.0.0/16"}
                ),
            ]
            snapshot = InfraSnapshot(
                name="test-snapshot",
                region="us-east-1",
                resources=resources,
            )

            path = store.save(snapshot)
            assert path.exists()

            loaded = store.load("test-snapshot")
            assert loaded is not None
            assert loaded.name == "test-snapshot"
            assert loaded.resource_count == 1

    def test_save_creates_index(self):
        """Test that save creates an index file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            store = SnapshotStore(base)

            snapshot = InfraSnapshot(name="indexed-snapshot")
            store.save(snapshot)

            index_file = base / "index.json"
            assert index_file.exists()

    def test_list_snapshots(self):
        """Test listing snapshots."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = SnapshotStore(Path(tmpdir))

            store.save(InfraSnapshot(name="snap-1", region="us-east-1"))
            store.save(InfraSnapshot(name="snap-2", region="us-west-2"))

            all_snapshots = store.list()
            assert len(all_snapshots) == 2

            east_snapshots = store.list(region="us-east-1")
            assert len(east_snapshots) == 1
            assert east_snapshots[0]["name"] == "snap-1"

    def test_delete_snapshot(self):
        """Test deleting a snapshot."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = SnapshotStore(Path(tmpdir))

            snapshot = InfraSnapshot(name="to-delete")
            path = store.save(snapshot)
            assert path.exists()

            result = store.delete("to-delete")
            assert result is True
            assert not path.exists()

            result = store.delete("nonexistent")
            assert result is False

    def test_exists(self):
        """Test checking if snapshot exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = SnapshotStore(Path(tmpdir))

            assert store.exists("nonexistent") is False

            store.save(InfraSnapshot(name="exists"))
            assert store.exists("exists") is True

    def test_get_metadata(self):
        """Test getting snapshot metadata."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = SnapshotStore(Path(tmpdir))

            resources = [
                ResourceSnapshot(id="vpc-1", type="aws_vpc", config={}),
            ]
            snapshot = InfraSnapshot(
                name="meta-test",
                region="us-east-1",
                vpc_id="vpc-1",
                profile="default",
                resources=resources,
            )
            store.save(snapshot)

            meta = store.get_metadata("meta-test")
            assert meta is not None
            assert meta["region"] == "us-east-1"
            assert meta["vpc_id"] == "vpc-1"
            assert meta["resource_count"] == 1

    def test_load_by_path(self):
        """Test loading snapshot by direct path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = SnapshotStore(Path(tmpdir))

            snapshot = InfraSnapshot(name="path-load")
            path = store.save(snapshot)

            loaded = store.load(str(path))
            assert loaded is not None
            assert loaded.name == "path-load"

    def test_load_partial_match(self):
        """Test loading by partial name match."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = SnapshotStore(Path(tmpdir))

            store.save(InfraSnapshot(name="production-snapshot-jan"))

            loaded = store.load("production")
            assert loaded is not None
            assert "production" in loaded.name

    def test_sanitize_name(self):
        """Test name sanitization for filenames."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = SnapshotStore(Path(tmpdir))

            # Names with special characters should be sanitized
            snapshot = InfraSnapshot(name="my snapshot / test")
            path = store.save(snapshot)

            assert path.exists()
            # The filename should not contain slashes
            assert "/" not in path.name


# =============================================================================
# SNAPSHOT DIFFER TESTS
# =============================================================================


class TestSnapshotDiffer:
    """Test SnapshotDiffer class."""

    def test_no_changes(self):
        """Test diff with identical snapshots."""
        resources = [
            ResourceSnapshot(
                id="vpc-1", type="aws_vpc", config={"cidr_block": "10.0.0.0/16"}
            ),
        ]

        baseline = InfraSnapshot(name="baseline", resources=resources)
        current = InfraSnapshot(name="current", resources=resources)

        differ = SnapshotDiffer()
        diff = differ.diff(baseline, current)

        assert diff.total_changes == 0
        assert diff.total_unchanged == 1

    def test_detect_added_resources(self):
        """Test detecting added resources."""
        baseline = InfraSnapshot(name="baseline", resources=[])
        current = InfraSnapshot(
            name="current",
            resources=[
                ResourceSnapshot(id="vpc-1", type="aws_vpc", config={}),
                ResourceSnapshot(id="subnet-1", type="aws_subnet", config={}),
            ],
        )

        differ = SnapshotDiffer()
        diff = differ.diff(baseline, current)

        assert diff.total_added == 2
        assert diff.total_removed == 0
        assert diff.total_modified == 0

    def test_detect_removed_resources(self):
        """Test detecting removed resources."""
        baseline = InfraSnapshot(
            name="baseline",
            resources=[
                ResourceSnapshot(id="vpc-1", type="aws_vpc", config={}),
                ResourceSnapshot(id="subnet-1", type="aws_subnet", config={}),
            ],
        )
        current = InfraSnapshot(name="current", resources=[])

        differ = SnapshotDiffer()
        diff = differ.diff(baseline, current)

        assert diff.total_added == 0
        assert diff.total_removed == 2
        assert diff.total_modified == 0

    def test_detect_modified_resources(self):
        """Test detecting modified resources."""
        baseline = InfraSnapshot(
            name="baseline",
            resources=[
                ResourceSnapshot(
                    id="vpc-1",
                    type="aws_vpc",
                    config={"cidr_block": "10.0.0.0/16"},
                ),
            ],
        )
        current = InfraSnapshot(
            name="current",
            resources=[
                ResourceSnapshot(
                    id="vpc-1",
                    type="aws_vpc",
                    config={"cidr_block": "10.0.0.0/24"},
                ),
            ],
        )

        differ = SnapshotDiffer()
        diff = differ.diff(baseline, current)

        assert diff.total_modified == 1
        assert diff.changes[0].changed_attributes == ["cidr_block"]

    def test_ignore_attributes(self):
        """Test ignoring specified attributes."""
        baseline = InfraSnapshot(
            name="baseline",
            resources=[
                ResourceSnapshot(
                    id="vpc-1",
                    type="aws_vpc",
                    config={"last_modified": "2024-01-01", "cidr_block": "10.0.0.0/16"},
                ),
            ],
        )
        current = InfraSnapshot(
            name="current",
            resources=[
                ResourceSnapshot(
                    id="vpc-1",
                    type="aws_vpc",
                    config={"last_modified": "2024-01-02", "cidr_block": "10.0.0.0/16"},
                ),
            ],
        )

        differ = SnapshotDiffer()  # Uses default ignore attributes
        diff = differ.diff(baseline, current)

        # last_modified is in DEFAULT_IGNORE_ATTRIBUTES
        assert diff.total_modified == 0

    def test_nested_attribute_changes(self):
        """Test detecting changes in nested attributes."""
        baseline = InfraSnapshot(
            name="baseline",
            resources=[
                ResourceSnapshot(
                    id="sg-1",
                    type="aws_security_group",
                    config={
                        "ingress": {
                            "from_port": 22,
                            "to_port": 22,
                            "cidr_blocks": ["0.0.0.0/0"],
                        }
                    },
                ),
            ],
        )
        current = InfraSnapshot(
            name="current",
            resources=[
                ResourceSnapshot(
                    id="sg-1",
                    type="aws_security_group",
                    config={
                        "ingress": {
                            "from_port": 22,
                            "to_port": 22,
                            "cidr_blocks": ["10.0.0.0/8"],
                        }
                    },
                ),
            ],
        )

        differ = SnapshotDiffer()
        diff = differ.diff(baseline, current)

        assert diff.total_modified == 1
        # Should find the nested attribute change
        assert any("cidr_blocks" in attr for attr in diff.changes[0].changed_attributes)

    def test_severity_critical_removed_resource(self):
        """Test critical severity for removed critical resources."""
        baseline = InfraSnapshot(
            name="baseline",
            resources=[
                ResourceSnapshot(id="role-1", type="aws_iam_role", config={}),
            ],
        )
        current = InfraSnapshot(name="current", resources=[])

        differ = SnapshotDiffer()
        diff = differ.diff(baseline, current)

        assert diff.changes[0].severity == "critical"
        assert len(diff.critical_changes) == 1

    def test_severity_high_security_attribute(self):
        """Test high severity for security-related changes."""
        baseline = InfraSnapshot(
            name="baseline",
            resources=[
                ResourceSnapshot(
                    id="sg-1",
                    type="aws_security_group",
                    config={"ingress": [{"cidr_blocks": ["10.0.0.0/8"]}]},
                ),
            ],
        )
        current = InfraSnapshot(
            name="current",
            resources=[
                ResourceSnapshot(
                    id="sg-1",
                    type="aws_security_group",
                    config={"ingress": [{"cidr_blocks": ["0.0.0.0/0"]}]},
                ),
            ],
        )

        differ = SnapshotDiffer()
        diff = differ.diff(baseline, current)

        assert diff.changes[0].severity == "high"

    def test_severity_medium_added_resource(self):
        """Test medium severity for normal added resources."""
        baseline = InfraSnapshot(name="baseline", resources=[])
        current = InfraSnapshot(
            name="current",
            resources=[
                ResourceSnapshot(id="subnet-1", type="aws_subnet", config={}),
            ],
        )

        differ = SnapshotDiffer()
        diff = differ.diff(baseline, current)

        assert diff.changes[0].severity == "medium"

    def test_severity_high_added_critical_resource(self):
        """Test high severity for added critical resources."""
        baseline = InfraSnapshot(name="baseline", resources=[])
        current = InfraSnapshot(
            name="current",
            resources=[
                ResourceSnapshot(id="key-1", type="aws_kms_key", config={}),
            ],
        )

        differ = SnapshotDiffer()
        diff = differ.diff(baseline, current)

        assert diff.changes[0].severity == "high"

    def test_by_type_tracking(self):
        """Test changes grouped by resource type."""
        baseline = InfraSnapshot(
            name="baseline",
            resources=[
                ResourceSnapshot(id="vpc-1", type="aws_vpc", config={}),
            ],
        )
        current = InfraSnapshot(
            name="current",
            resources=[
                ResourceSnapshot(id="vpc-1", type="aws_vpc", config={"changed": True}),
                ResourceSnapshot(id="subnet-1", type="aws_subnet", config={}),
                ResourceSnapshot(id="subnet-2", type="aws_subnet", config={}),
            ],
        )

        differ = SnapshotDiffer()
        diff = differ.diff(baseline, current)

        assert "aws_vpc" in diff.by_type
        assert diff.by_type["aws_vpc"]["modified"] == 1
        assert diff.by_type["aws_subnet"]["added"] == 2


# =============================================================================
# SNAPSHOT REPORTER TESTS
# =============================================================================


class TestSnapshotReporter:
    """Test SnapshotReporter class."""

    def test_to_json(self):
        """Test JSON export."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "report"

            changes = [
                ResourceChange(
                    resource_id="vpc-1", resource_type="aws_vpc", change_type="added"
                ),
            ]
            diff = SnapshotDiff(
                baseline_name="baseline",
                baseline_date="2024-01-01T00:00:00Z",
                current_name="current",
                current_date="2024-01-02T00:00:00Z",
                total_added=1,
                changes=changes,
            )

            reporter = SnapshotReporter()
            path = reporter.to_json(diff, output_path)

            assert path.exists()
            assert path.suffix == ".json"

            import json

            data = json.loads(path.read_text())
            assert data["baseline"]["name"] == "baseline"
            assert data["summary"]["added"] == 1

    def test_to_markdown(self):
        """Test Markdown export."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "report"

            changes = [
                ResourceChange(
                    resource_id="vpc-1",
                    resource_type="aws_vpc",
                    change_type="added",
                    resource_name="my-vpc",
                ),
            ]
            diff = SnapshotDiff(
                baseline_name="baseline",
                baseline_date="2024-01-01T00:00:00Z",
                current_name="current",
                current_date="2024-01-02T00:00:00Z",
                total_added=1,
                changes=changes,
            )

            reporter = SnapshotReporter()
            path = reporter.to_markdown(diff, output_path)

            assert path.exists()
            assert path.suffix == ".md"

            content = path.read_text()
            assert "Infrastructure Change Report" in content
            assert "baseline" in content
            assert "SOC2" in content
            assert "CC7.1" in content

    def test_to_html(self):
        """Test HTML export."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "report"

            diff = SnapshotDiff(
                baseline_name="baseline",
                baseline_date="2024-01-01T00:00:00Z",
                current_name="current",
                current_date="2024-01-02T00:00:00Z",
                total_added=5,
                total_removed=2,
                by_type={
                    "aws_vpc": {"added": 2, "removed": 1, "modified": 0, "unchanged": 0}
                },
            )

            reporter = SnapshotReporter()
            path = reporter.to_html(diff, output_path)

            assert path.exists()
            assert path.suffix == ".html"

            content = path.read_text()
            assert "<!DOCTYPE html>" in content
            assert "Infrastructure Change Report" in content
            assert "tailwindcss" in content

    def test_markdown_with_critical_changes(self):
        """Test Markdown export includes critical changes section."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "report"

            critical_changes = [
                ResourceChange(
                    resource_id="role-1",
                    resource_type="aws_iam_role",
                    change_type="removed",
                    severity="critical",
                ),
            ]
            diff = SnapshotDiff(
                baseline_name="baseline",
                baseline_date="2024-01-01T00:00:00Z",
                current_name="current",
                current_date="2024-01-02T00:00:00Z",
                critical_changes=critical_changes,
            )

            reporter = SnapshotReporter()
            path = reporter.to_markdown(diff, output_path)

            content = path.read_text()
            assert "High Severity Changes" in content
            assert "aws_iam_role" in content

    def test_markdown_with_modified_resources(self):
        """Test Markdown export includes modified resource details."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "report"

            changes = [
                ResourceChange(
                    resource_id="sg-1",
                    resource_type="aws_security_group",
                    change_type="modified",
                    changed_attributes=["ingress"],
                    before={"ingress": "10.0.0.0/8"},
                    after={"ingress": "0.0.0.0/0"},
                    severity="high",
                ),
            ]
            diff = SnapshotDiff(
                baseline_name="baseline",
                baseline_date="2024-01-01T00:00:00Z",
                current_name="current",
                current_date="2024-01-02T00:00:00Z",
                total_modified=1,
                changes=changes,
            )

            reporter = SnapshotReporter()
            path = reporter.to_markdown(diff, output_path)

            content = path.read_text()
            assert "Modified Resources" in content
            assert "aws_security_group" in content
            assert "ingress" in content


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


class TestSnapshotIntegration:
    """Integration tests for the complete snapshot workflow."""

    def test_full_workflow(self):
        """Test complete save -> load -> diff -> report workflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = SnapshotStore(Path(tmpdir) / "snapshots")

            # Create and save baseline
            baseline_resources = [
                ResourceSnapshot(
                    id="vpc-1",
                    type="aws_vpc",
                    name="main-vpc",
                    config={"cidr_block": "10.0.0.0/16"},
                ),
                ResourceSnapshot(
                    id="subnet-1",
                    type="aws_subnet",
                    name="public-subnet",
                    config={"vpc_id": "vpc-1", "cidr_block": "10.0.1.0/24"},
                ),
            ]
            baseline = InfraSnapshot(
                name="baseline",
                region="us-east-1",
                resources=baseline_resources,
            )
            store.save(baseline)

            # Create and save current (with changes)
            current_resources = [
                ResourceSnapshot(
                    id="vpc-1",
                    type="aws_vpc",
                    name="main-vpc",
                    config={"cidr_block": "10.0.0.0/16"},  # Unchanged
                ),
                ResourceSnapshot(
                    id="subnet-1",
                    type="aws_subnet",
                    name="public-subnet",
                    config={"vpc_id": "vpc-1", "cidr_block": "10.0.2.0/24"},  # Modified
                ),
                ResourceSnapshot(
                    id="subnet-2",
                    type="aws_subnet",
                    name="private-subnet",
                    config={"vpc_id": "vpc-1", "cidr_block": "10.0.3.0/24"},  # Added
                ),
            ]
            current = InfraSnapshot(
                name="current",
                region="us-east-1",
                resources=current_resources,
            )
            store.save(current)

            # Load snapshots
            loaded_baseline = store.load("baseline")
            loaded_current = store.load("current")

            assert loaded_baseline is not None
            assert loaded_current is not None

            # Diff
            differ = SnapshotDiffer()
            diff = differ.diff(loaded_baseline, loaded_current)

            assert diff.total_added == 1
            assert diff.total_modified == 1
            assert diff.total_unchanged == 1

            # Report
            reporter = SnapshotReporter()
            report_path = Path(tmpdir) / "report"

            json_path = reporter.to_json(diff, report_path)
            md_path = reporter.to_markdown(diff, report_path)
            html_path = reporter.to_html(diff, report_path)

            assert json_path.exists()
            assert md_path.exists()
            assert html_path.exists()

    def test_store_cleanup_old(self):
        """Test cleanup of old snapshots."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = SnapshotStore(Path(tmpdir))

            # Save a snapshot with old date
            snapshot = InfraSnapshot(
                name="old-snapshot",
                created_at="2020-01-01T00:00:00+00:00",  # Very old
            )
            store.save(snapshot)

            # Cleanup with 30 day max age
            deleted = store.cleanup_old(max_age_days=30)

            assert deleted == 1
            assert not store.exists("old-snapshot")
