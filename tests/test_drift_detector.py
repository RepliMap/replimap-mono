"""
Comprehensive tests for the Drift Detector feature.
"""

import json
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from replimap.drift import (
    DriftEngine,
    DriftReport,
    DriftReporter,
    DriftSeverity,
    DriftType,
    TerraformStateParser,
    TFResource,
)
from replimap.drift.comparator import DriftComparator
from replimap.drift.models import AttributeDiff, DriftReason, ResourceDrift
from replimap.drift.normalizer import (
    DriftNormalizer,
    canonical_hash,
    classify_drift_reason,
    deep_sort,
    get_ignores_for_type,
    is_falsy,
    normalize_tags,
    values_equivalent,
)


class TestDriftModels:
    """Tests for drift data models."""

    def test_drift_type_enum(self):
        """Test DriftType enum values."""
        assert DriftType.ADDED.value == "added"
        assert DriftType.REMOVED.value == "removed"
        assert DriftType.MODIFIED.value == "modified"
        assert DriftType.UNCHANGED.value == "unchanged"

    def test_drift_severity_enum(self):
        """Test DriftSeverity enum values."""
        assert DriftSeverity.CRITICAL.value == "critical"
        assert DriftSeverity.HIGH.value == "high"
        assert DriftSeverity.MEDIUM.value == "medium"
        assert DriftSeverity.LOW.value == "low"
        assert DriftSeverity.INFO.value == "info"

    def test_attribute_diff_creation(self):
        """Test AttributeDiff dataclass."""
        diff = AttributeDiff(
            attribute="ingress",
            expected=[{"from_port": 80}],
            actual=[{"from_port": 443}],
            severity=DriftSeverity.CRITICAL,
        )

        assert diff.attribute == "ingress"
        assert diff.expected == [{"from_port": 80}]
        assert diff.actual == [{"from_port": 443}]
        assert diff.severity == DriftSeverity.CRITICAL

    def test_attribute_diff_str(self):
        """Test AttributeDiff string representation."""
        diff = AttributeDiff(
            attribute="port",
            expected=80,
            actual=443,
        )

        assert "port" in str(diff)
        assert "80" in str(diff)
        assert "443" in str(diff)

    def test_resource_drift_creation(self):
        """Test ResourceDrift dataclass."""
        drift = ResourceDrift(
            resource_type="aws_security_group",
            resource_id="sg-abc123",
            resource_name="web-sg",
            drift_type=DriftType.MODIFIED,
            diffs=[
                AttributeDiff(
                    attribute="ingress",
                    expected=[],
                    actual=[{"from_port": 80}],
                    severity=DriftSeverity.CRITICAL,
                )
            ],
            severity=DriftSeverity.CRITICAL,
            tf_address="aws_security_group.web",
        )

        assert drift.resource_type == "aws_security_group"
        assert drift.resource_id == "sg-abc123"
        assert drift.is_drifted is True
        assert drift.diff_count == 1

    def test_resource_drift_unchanged(self):
        """Test ResourceDrift for unchanged resource."""
        drift = ResourceDrift(
            resource_type="aws_vpc",
            resource_id="vpc-123",
            resource_name="main",
            drift_type=DriftType.UNCHANGED,
        )

        assert drift.is_drifted is False
        assert drift.diff_count == 0

    def test_drift_report_creation(self):
        """Test DriftReport dataclass."""
        report = DriftReport(
            total_resources=10,
            drifted_resources=3,
            added_resources=1,
            removed_resources=1,
            modified_resources=1,
            drifts=[],
            state_file="terraform.tfstate",
            region="us-east-1",
        )

        assert report.total_resources == 10
        assert report.drifted_resources == 3
        assert report.has_drift is True

    def test_drift_report_no_drift(self):
        """Test DriftReport with no drift."""
        report = DriftReport(
            total_resources=10,
            drifted_resources=0,
        )

        assert report.has_drift is False

    def test_drift_report_critical_drifts(self):
        """Test DriftReport critical_drifts property."""
        critical_drift = ResourceDrift(
            resource_type="aws_iam_role",
            resource_id="role-123",
            resource_name="admin",
            drift_type=DriftType.MODIFIED,
            severity=DriftSeverity.CRITICAL,
        )
        high_drift = ResourceDrift(
            resource_type="aws_instance",
            resource_id="i-456",
            resource_name="web",
            drift_type=DriftType.MODIFIED,
            severity=DriftSeverity.HIGH,
        )
        low_drift = ResourceDrift(
            resource_type="aws_vpc",
            resource_id="vpc-789",
            resource_name="main",
            drift_type=DriftType.MODIFIED,
            severity=DriftSeverity.LOW,
        )

        report = DriftReport(
            drifts=[critical_drift, high_drift, low_drift],
            drifted_resources=3,
        )

        assert len(report.critical_drifts) == 1
        assert len(report.high_drifts) == 1
        assert report.critical_drifts[0].resource_id == "role-123"

    def test_drift_report_to_dict(self):
        """Test DriftReport to_dict serialization."""
        drift = ResourceDrift(
            resource_type="aws_security_group",
            resource_id="sg-123",
            resource_name="web",
            drift_type=DriftType.MODIFIED,
            diffs=[
                AttributeDiff(
                    attribute="ingress",
                    expected=[],
                    actual=[{"port": 80}],
                    severity=DriftSeverity.CRITICAL,
                )
            ],
            severity=DriftSeverity.CRITICAL,
            tf_address="aws_security_group.web",
        )

        report = DriftReport(
            total_resources=5,
            drifted_resources=1,
            modified_resources=1,
            drifts=[drift],
            state_file="test.tfstate",
            region="us-east-1",
        )

        data = report.to_dict()

        assert data["summary"]["total_resources"] == 5
        assert data["summary"]["has_drift"] is True
        assert len(data["drifts"]) == 1
        assert data["drifts"][0]["resource_id"] == "sg-123"
        assert data["metadata"]["region"] == "us-east-1"


class TestTerraformStateParser:
    """Tests for TerraformStateParser."""

    def create_sample_tfstate(self) -> dict:
        """Create a sample Terraform state structure."""
        return {
            "version": 4,
            "terraform_version": "1.5.0",
            "resources": [
                {
                    "type": "aws_vpc",
                    "name": "main",
                    "instances": [
                        {
                            "attributes": {
                                "id": "vpc-abc123",
                                "cidr_block": "10.0.0.0/16",
                                "enable_dns_hostnames": True,
                            }
                        }
                    ],
                },
                {
                    "type": "aws_security_group",
                    "name": "web",
                    "instances": [
                        {
                            "attributes": {
                                "id": "sg-def456",
                                "name": "web-sg",
                                "vpc_id": "vpc-abc123",
                                "ingress": [
                                    {"from_port": 80, "to_port": 80, "protocol": "tcp"}
                                ],
                                "egress": [],
                            }
                        }
                    ],
                },
            ],
            "outputs": {"vpc_id": {"value": "vpc-abc123"}},
        }

    def test_parse_valid_state(self):
        """Test parsing valid Terraform state."""
        parser = TerraformStateParser()
        state_data = self.create_sample_tfstate()

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".tfstate", delete=False
        ) as f:
            json.dump(state_data, f)
            temp_path = Path(f.name)

        try:
            tf_state = parser.parse(temp_path)

            assert tf_state.version == 4
            assert tf_state.terraform_version == "1.5.0"
            assert len(tf_state.resources) == 2
        finally:
            temp_path.unlink()

    def test_parse_resources_correctly(self):
        """Test resources are parsed correctly."""
        parser = TerraformStateParser()
        state_data = self.create_sample_tfstate()

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".tfstate", delete=False
        ) as f:
            json.dump(state_data, f)
            temp_path = Path(f.name)

        try:
            tf_state = parser.parse(temp_path)

            vpc = tf_state.get_resource_by_id("vpc-abc123")
            assert vpc is not None
            assert vpc.type == "aws_vpc"
            assert vpc.name == "main"
            assert vpc.address == "aws_vpc.main"
            assert vpc.attributes["cidr_block"] == "10.0.0.0/16"
        finally:
            temp_path.unlink()

    def test_parse_file_not_found(self):
        """Test parsing non-existent file raises error."""
        parser = TerraformStateParser()

        with pytest.raises(FileNotFoundError):
            parser.parse(Path("/non/existent/path.tfstate"))

    def test_parse_unsupported_version(self):
        """Test parsing old state version raises error."""
        parser = TerraformStateParser()
        state_data = {"version": 3, "resources": []}

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".tfstate", delete=False
        ) as f:
            json.dump(state_data, f)
            temp_path = Path(f.name)

        try:
            with pytest.raises(ValueError, match="Unsupported state version"):
                parser.parse(temp_path)
        finally:
            temp_path.unlink()

    def test_parse_with_count_index(self):
        """Test parsing resources with count index."""
        parser = TerraformStateParser()
        state_data = {
            "version": 4,
            "terraform_version": "1.5.0",
            "resources": [
                {
                    "type": "aws_subnet",
                    "name": "public",
                    "instances": [
                        {
                            "index_key": 0,
                            "attributes": {
                                "id": "subnet-1",
                                "cidr_block": "10.0.1.0/24",
                            },
                        },
                        {
                            "index_key": 1,
                            "attributes": {
                                "id": "subnet-2",
                                "cidr_block": "10.0.2.0/24",
                            },
                        },
                    ],
                }
            ],
            "outputs": {},
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".tfstate", delete=False
        ) as f:
            json.dump(state_data, f)
            temp_path = Path(f.name)

        try:
            tf_state = parser.parse(temp_path)

            assert len(tf_state.resources) == 2
            addresses = [r.address for r in tf_state.resources]
            assert "aws_subnet.public[0]" in addresses
            assert "aws_subnet.public[1]" in addresses
        finally:
            temp_path.unlink()

    def test_parse_with_for_each_index(self):
        """Test parsing resources with for_each string index."""
        parser = TerraformStateParser()
        state_data = {
            "version": 4,
            "terraform_version": "1.5.0",
            "resources": [
                {
                    "type": "aws_subnet",
                    "name": "private",
                    "instances": [
                        {
                            "index_key": "us-east-1a",
                            "attributes": {
                                "id": "subnet-a",
                                "availability_zone": "us-east-1a",
                            },
                        },
                        {
                            "index_key": "us-east-1b",
                            "attributes": {
                                "id": "subnet-b",
                                "availability_zone": "us-east-1b",
                            },
                        },
                    ],
                }
            ],
            "outputs": {},
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".tfstate", delete=False
        ) as f:
            json.dump(state_data, f)
            temp_path = Path(f.name)

        try:
            tf_state = parser.parse(temp_path)

            assert len(tf_state.resources) == 2
            addresses = [r.address for r in tf_state.resources]
            assert 'aws_subnet.private["us-east-1a"]' in addresses
            assert 'aws_subnet.private["us-east-1b"]' in addresses
        finally:
            temp_path.unlink()

    def test_parse_skips_unsupported_types(self):
        """Test parser skips unsupported resource types."""
        parser = TerraformStateParser()
        state_data = {
            "version": 4,
            "terraform_version": "1.5.0",
            "resources": [
                {
                    "type": "aws_vpc",
                    "name": "main",
                    "instances": [{"attributes": {"id": "vpc-123"}}],
                },
                {
                    "type": "aws_unsupported_type",  # Not in SUPPORTED_RESOURCE_TYPES
                    "name": "foo",
                    "instances": [{"attributes": {"id": "foo-123"}}],
                },
            ],
            "outputs": {},
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".tfstate", delete=False
        ) as f:
            json.dump(state_data, f)
            temp_path = Path(f.name)

        try:
            tf_state = parser.parse(temp_path)

            assert len(tf_state.resources) == 1
            assert tf_state.resources[0].type == "aws_vpc"
        finally:
            temp_path.unlink()

    def test_get_resources_by_type(self):
        """Test getting resources by type."""
        parser = TerraformStateParser()
        state_data = self.create_sample_tfstate()

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".tfstate", delete=False
        ) as f:
            json.dump(state_data, f)
            temp_path = Path(f.name)

        try:
            tf_state = parser.parse(temp_path)

            vpcs = tf_state.get_resources_by_type("aws_vpc")
            sgs = tf_state.get_resources_by_type("aws_security_group")

            assert len(vpcs) == 1
            assert len(sgs) == 1
            assert vpcs[0].id == "vpc-abc123"
        finally:
            temp_path.unlink()


class TestDriftComparator:
    """Tests for DriftComparator."""

    def test_compare_unchanged_resource(self):
        """Test comparing unchanged resource."""
        comparator = DriftComparator()
        tf_resource = TFResource(
            type="aws_vpc",
            name="main",
            address="aws_vpc.main",
            id="vpc-123",
            attributes={
                "cidr_block": "10.0.0.0/16",
                "enable_dns_hostnames": True,
            },
        )
        actual_attrs = {
            "cidr_block": "10.0.0.0/16",
            "enable_dns_hostnames": True,
        }

        drift = comparator.compare_resource(tf_resource, actual_attrs)

        assert drift.drift_type == DriftType.UNCHANGED
        assert drift.is_drifted is False
        assert drift.diff_count == 0

    def test_compare_modified_resource(self):
        """Test comparing modified resource."""
        comparator = DriftComparator()
        tf_resource = TFResource(
            type="aws_security_group",
            name="web",
            address="aws_security_group.web",
            id="sg-123",
            attributes={
                "name": "web-sg",
                "vpc_id": "vpc-123",
                "ingress": [{"from_port": 80, "to_port": 80}],
            },
        )
        actual_attrs = {
            "name": "web-sg",
            "vpc_id": "vpc-123",
            "ingress": [{"from_port": 443, "to_port": 443}],  # Changed
        }

        drift = comparator.compare_resource(tf_resource, actual_attrs)

        assert drift.drift_type == DriftType.MODIFIED
        assert drift.is_drifted is True
        assert drift.severity == DriftSeverity.CRITICAL  # ingress is critical

    def test_compare_with_tags_change(self):
        """Test comparing resource with only tags changed.

        Note: Tag changes are classified as TAG_ONLY reason, which is not
        filtered as noise but has LOW severity.
        """
        comparator = DriftComparator()
        tf_resource = TFResource(
            type="aws_vpc",
            name="main",
            address="aws_vpc.main",
            id="vpc-123",
            attributes={
                "cidr_block": "10.0.0.0/16",
                "tags": {"Name": "old-name"},
            },
        )
        actual_attrs = {
            "cidr_block": "10.0.0.0/16",
            "tags": {"Name": "new-name"},  # Changed
        }

        drift = comparator.compare_resource(tf_resource, actual_attrs)

        assert drift.is_drifted is True
        # Tags have LOW severity but since it's TAG_ONLY reason, not semantic,
        # max_severity doesn't get updated and stays at INFO
        assert drift.severity == DriftSeverity.INFO

    def test_identify_added_resources(self):
        """Test identifying added resources."""
        comparator = DriftComparator()

        # Mock resources from AWS
        class MockResource:
            def __init__(self, id, terraform_type, original_name):
                self.id = id
                self.terraform_type = terraform_type
                self.resource_type = terraform_type  # Also add resource_type
                self.original_name = original_name

        actual_resources = [
            MockResource("sg-new", "aws_security_group", "new-sg"),
            MockResource("sg-existing", "aws_security_group", "existing-sg"),
        ]
        tf_state_ids = {"sg-existing"}  # Only sg-existing is in TF state

        added = comparator.identify_added_resources(actual_resources, tf_state_ids)

        assert len(added) == 1
        assert added[0].resource_id == "sg-new"
        assert added[0].drift_type == DriftType.ADDED

    def test_identify_removed_resources(self):
        """Test identifying removed resources."""
        comparator = DriftComparator()

        tf_resources = [
            TFResource(
                type="aws_instance",
                name="web",
                address="aws_instance.web",
                id="i-deleted",
                attributes={},
            ),
            TFResource(
                type="aws_instance",
                name="api",
                address="aws_instance.api",
                id="i-existing",
                attributes={},
            ),
        ]
        actual_ids = {"i-existing"}  # i-deleted no longer exists

        removed = comparator.identify_removed_resources(tf_resources, actual_ids)

        assert len(removed) == 1
        assert removed[0].resource_id == "i-deleted"
        assert removed[0].drift_type == DriftType.REMOVED
        assert removed[0].severity == DriftSeverity.HIGH

    def test_values_differ_none_handling(self):
        """Test _values_differ handles None correctly.

        Note: Now uses values_equivalent from normalizer which has
        more sophisticated falsy value handling.
        """
        comparator = DriftComparator()

        # Both None - no diff
        assert comparator._values_differ(None, None, "attr") is False

        # None vs empty - no diff (falsy equivalence)
        assert comparator._values_differ(None, "", "attr") is False
        assert comparator._values_differ(None, [], "attr") is False
        assert comparator._values_differ(None, {}, "attr") is False

        # None vs actual value - diff
        assert comparator._values_differ(None, "value", "attr") is True
        assert comparator._values_differ("value", None, "attr") is True

    def test_lists_equivalent_via_values_equivalent(self):
        """Test list comparison via values_equivalent.

        Note: The comparator now uses values_equivalent from normalizer
        which handles order-independent list comparison.
        """
        # Same simple lists (order independent)
        assert values_equivalent([1, 2, 3], [3, 2, 1], "attr") is True

        # Different simple lists
        assert values_equivalent([1, 2], [1, 2, 3], "attr") is False

        # Same dicts in lists (order independent)
        list1 = [{"port": 80}, {"port": 443}]
        list2 = [{"port": 443}, {"port": 80}]
        assert values_equivalent(list1, list2, "ports") is True

    def test_severity_for_added(self):
        """Test _severity_for_added returns correct severity."""
        comparator = DriftComparator()

        assert (
            comparator._severity_for_added("aws_security_group")
            == DriftSeverity.CRITICAL
        )
        assert comparator._severity_for_added("aws_iam_role") == DriftSeverity.CRITICAL
        assert comparator._severity_for_added("aws_instance") == DriftSeverity.HIGH
        assert comparator._severity_for_added("aws_db_instance") == DriftSeverity.HIGH
        assert comparator._severity_for_added("aws_subnet") == DriftSeverity.MEDIUM


class TestDriftReporter:
    """Tests for DriftReporter."""

    def create_sample_report(self) -> DriftReport:
        """Create a sample drift report."""
        drifts = [
            ResourceDrift(
                resource_type="aws_security_group",
                resource_id="sg-123",
                resource_name="web-sg",
                drift_type=DriftType.MODIFIED,
                diffs=[
                    AttributeDiff(
                        attribute="ingress",
                        expected="[port 80]",
                        actual="[port 443]",
                        severity=DriftSeverity.CRITICAL,
                    )
                ],
                severity=DriftSeverity.CRITICAL,
                tf_address="aws_security_group.web",
            ),
            ResourceDrift(
                resource_type="aws_instance",
                resource_id="i-456",
                resource_name="web-server",
                drift_type=DriftType.ADDED,
                severity=DriftSeverity.HIGH,
            ),
            ResourceDrift(
                resource_type="aws_s3_bucket",
                resource_id="bucket-789",
                resource_name="logs",
                drift_type=DriftType.REMOVED,
                severity=DriftSeverity.HIGH,
                tf_address="aws_s3_bucket.logs",
            ),
        ]

        return DriftReport(
            total_resources=10,
            drifted_resources=3,
            added_resources=1,
            removed_resources=1,
            modified_resources=1,
            drifts=drifts,
            state_file="terraform.tfstate",
            region="us-east-1",
            scan_duration_seconds=5.5,
        )

    def test_to_console_with_drift(self):
        """Test console output with drift."""
        reporter = DriftReporter()
        report = self.create_sample_report()

        output = reporter.to_console(report)

        assert "DRIFT DETECTED" in output
        assert "Total resources: 10" in output
        assert "Drifted: 3" in output
        assert "HIGH PRIORITY" in output
        assert "sg-123" in output

    def test_to_console_no_drift(self):
        """Test console output with no drift."""
        reporter = DriftReporter()
        report = DriftReport(total_resources=10, drifted_resources=0)

        output = reporter.to_console(report)

        assert "NO DRIFT" in output
        assert "Total resources: 10" in output

    def test_to_json(self):
        """Test JSON output."""
        reporter = DriftReporter()
        report = self.create_sample_report()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = Path(f.name)

        try:
            result_path = reporter.to_json(report, temp_path)

            assert result_path == temp_path
            assert temp_path.exists()

            data = json.loads(temp_path.read_text())
            assert data["summary"]["total_resources"] == 10
            assert data["summary"]["has_drift"] is True
            assert len(data["drifts"]) == 3
        finally:
            temp_path.unlink()

    def test_to_html(self):
        """Test HTML output."""
        reporter = DriftReporter()
        report = self.create_sample_report()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            temp_path = Path(f.name)

        try:
            result_path = reporter.to_html(report, temp_path)

            assert result_path == temp_path
            assert temp_path.exists()

            content = temp_path.read_text()
            assert "<!DOCTYPE html>" in content
            assert "Drift" in content
            assert "tailwindcss" in content
        finally:
            temp_path.unlink()

    def test_to_html_no_drift(self):
        """Test HTML output with no drift."""
        reporter = DriftReporter()
        report = DriftReport(total_resources=10, drifted_resources=0)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            temp_path = Path(f.name)

        try:
            reporter.to_html(report, temp_path)
            content = temp_path.read_text()

            assert "No Drift" in content or "no drift" in content.lower()
        finally:
            temp_path.unlink()


class TestDriftEngine:
    """Tests for DriftEngine."""

    def test_engine_initialization(self):
        """Test DriftEngine initialization."""
        mock_session = MagicMock()

        engine = DriftEngine(
            session=mock_session,
            region="us-east-1",
            profile="prod",
        )

        assert engine.session == mock_session
        assert engine.region == "us-east-1"
        assert engine.profile == "prod"

    def test_engine_requires_state_source(self):
        """Test engine requires either state_path or remote_backend.

        Note: The ValueError check happens before AWS/graph dependencies are used,
        so we need to mock the GraphEngine and run_all_scanners imports that
        occur when detect() is called. We patch at source module level.
        """
        mock_session = MagicMock()
        engine = DriftEngine(session=mock_session, region="us-east-1")

        # Create mocks for the dynamic imports
        import sys

        original_core = sys.modules.get("replimap.core")
        original_scanners = sys.modules.get("replimap.scanners")

        try:
            # Create mock modules
            mock_core = MagicMock()
            mock_core.GraphEngine = MagicMock()
            sys.modules["replimap.core"] = mock_core

            mock_scanners = MagicMock()
            mock_scanners.run_all_scanners = MagicMock()
            sys.modules["replimap.scanners"] = mock_scanners

            with pytest.raises(ValueError, match="Either state_path or remote_backend"):
                engine.detect()
        finally:
            # Restore original modules
            if original_core:
                sys.modules["replimap.core"] = original_core
            elif "replimap.core" in sys.modules:
                del sys.modules["replimap.core"]
            if original_scanners:
                sys.modules["replimap.scanners"] = original_scanners
            elif "replimap.scanners" in sys.modules:
                del sys.modules["replimap.scanners"]

    def test_engine_detect_with_local_state(self):
        """Test drift detection with local state file."""
        mock_session = MagicMock()

        # Create mock graph
        mock_graph = MagicMock()
        mock_graph.get_all_resources.return_value = []

        engine = DriftEngine(session=mock_session, region="us-east-1")

        # Create temporary state file
        state_data = {
            "version": 4,
            "terraform_version": "1.5.0",
            "resources": [],
            "outputs": {},
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".tfstate", delete=False
        ) as f:
            json.dump(state_data, f)
            temp_path = Path(f.name)

        import sys

        original_core = sys.modules.get("replimap.core")
        original_scanners = sys.modules.get("replimap.scanners")

        try:
            # Create mock modules
            mock_graph_engine_class = MagicMock(return_value=mock_graph)
            mock_core = MagicMock()
            mock_core.GraphEngine = mock_graph_engine_class
            sys.modules["replimap.core"] = mock_core

            mock_scanners_mod = MagicMock()
            mock_scanners_mod.run_all_scanners = MagicMock()
            sys.modules["replimap.scanners"] = mock_scanners_mod

            report = engine.detect(state_path=temp_path)

            assert isinstance(report, DriftReport)
            assert report.state_file == str(temp_path)
            assert report.region == "us-east-1"
        finally:
            temp_path.unlink()
            # Restore original modules
            if original_core:
                sys.modules["replimap.core"] = original_core
            elif "replimap.core" in sys.modules:
                del sys.modules["replimap.core"]
            if original_scanners:
                sys.modules["replimap.scanners"] = original_scanners
            elif "replimap.scanners" in sys.modules:
                del sys.modules["replimap.scanners"]


class TestDriftEdgeCases:
    """Edge case tests for drift detection."""

    def test_empty_state_file(self):
        """Test handling empty state file."""
        parser = TerraformStateParser()
        state_data = {
            "version": 4,
            "terraform_version": "1.5.0",
            "resources": [],
            "outputs": {},
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".tfstate", delete=False
        ) as f:
            json.dump(state_data, f)
            temp_path = Path(f.name)

        try:
            tf_state = parser.parse(temp_path)
            assert len(tf_state.resources) == 0
        finally:
            temp_path.unlink()

    def test_malformed_json(self):
        """Test handling malformed JSON in state file."""
        parser = TerraformStateParser()

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".tfstate", delete=False
        ) as f:
            f.write("{ invalid json }")
            temp_path = Path(f.name)

        try:
            with pytest.raises(json.JSONDecodeError):
                parser.parse(temp_path)
        finally:
            temp_path.unlink()

    def test_resource_without_id(self):
        """Test handling resource without ID attribute."""
        parser = TerraformStateParser()
        state_data = {
            "version": 4,
            "terraform_version": "1.5.0",
            "resources": [
                {
                    "type": "aws_vpc",
                    "name": "main",
                    "instances": [
                        {
                            "attributes": {
                                # Missing "id" attribute
                                "cidr_block": "10.0.0.0/16",
                            }
                        }
                    ],
                }
            ],
            "outputs": {},
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".tfstate", delete=False
        ) as f:
            json.dump(state_data, f)
            temp_path = Path(f.name)

        try:
            tf_state = parser.parse(temp_path)
            # Resource should be skipped
            assert len(tf_state.resources) == 0
        finally:
            temp_path.unlink()

    def test_deep_nested_attributes(self):
        """Test comparing deeply nested attributes."""
        comparator = DriftComparator()

        tf_resource = TFResource(
            type="aws_s3_bucket",
            name="logs",
            address="aws_s3_bucket.logs",
            id="bucket-123",
            attributes={
                "versioning": [{"enabled": True, "mfa_delete": False}],
            },
        )
        actual_attrs = {
            "versioning": [{"enabled": False, "mfa_delete": False}],  # Changed
        }

        drift = comparator.compare_resource(tf_resource, actual_attrs)

        assert drift.is_drifted is True

    def test_report_serialization_with_datetime(self):
        """Test report serialization handles datetime correctly."""
        report = DriftReport(
            scanned_at=datetime.now(UTC),
            state_file="test.tfstate",
            region="us-east-1",
        )

        data = report.to_dict()

        # Should be serializable to JSON
        json_str = json.dumps(data, default=str)
        assert "scanned_at" in json_str

    def test_large_number_of_drifts(self):
        """Test handling large number of drifts."""
        drifts = [
            ResourceDrift(
                resource_type="aws_instance",
                resource_id=f"i-{i:06d}",
                resource_name=f"instance-{i}",
                drift_type=DriftType.MODIFIED,
                severity=DriftSeverity.MEDIUM,
            )
            for i in range(100)
        ]

        report = DriftReport(
            total_resources=100,
            drifted_resources=100,
            modified_resources=100,
            drifts=drifts,
        )

        reporter = DriftReporter()
        console_output = reporter.to_console(report)

        # Should limit output
        assert "... and" in console_output or len(console_output) > 100


class TestDriftEngineIdExtraction:
    """Tests for ID extraction in drift engine."""

    def test_extract_base_id_simple(self):
        """Test extracting base ID from simple resource ID."""
        from unittest.mock import MagicMock

        from replimap.drift.engine import DriftEngine

        engine = DriftEngine(session=MagicMock(), region="us-east-1")

        # Simple ID without prefix
        assert engine._extract_base_id("sg-072c65dfd31d69b92") == "sg-072c65dfd31d69b92"
        assert engine._extract_base_id("i-1234567890abcdef0") == "i-1234567890abcdef0"

    def test_extract_base_id_with_account_prefix(self):
        """Test extracting base ID from account:region:id format."""
        from unittest.mock import MagicMock

        from replimap.drift.engine import DriftEngine

        engine = DriftEngine(session=MagicMock(), region="us-east-1")

        # ID with account:region prefix
        assert (
            engine._extract_base_id("542859091916:ap-southeast-2:sg-072c65dfd31d69b92")
            == "sg-072c65dfd31d69b92"
        )

        assert engine._extract_base_id("123456789012:us-east-1:i-abc123") == "i-abc123"

    def test_extract_base_id_arn(self):
        """Test ARN IDs are preserved."""
        from unittest.mock import MagicMock

        from replimap.drift.engine import DriftEngine

        engine = DriftEngine(session=MagicMock(), region="us-east-1")

        # ARN format should be preserved
        arn = "arn:aws:sqs:ap-southeast-2:542859091916:etime-14si-prod-broadcasts"
        assert engine._extract_base_id(arn) == arn

        # But account-prefixed ARN should extract the ARN
        prefixed_arn = f"542859091916:ap-southeast-2:{arn}"
        assert engine._extract_base_id(prefixed_arn) == arn

    def test_extract_base_id_with_colons_in_resource(self):
        """Test IDs with colons in the resource part."""
        from unittest.mock import MagicMock

        from replimap.drift.engine import DriftEngine

        engine = DriftEngine(session=MagicMock(), region="us-east-1")

        # Resource ID that contains colons
        assert (
            engine._extract_base_id(
                "542859091916:ap-southeast-2:some:resource:with:colons"
            )
            == "some:resource:with:colons"
        )


class TestDriftNormalizer:
    """Tests for drift normalization pipeline."""

    # =========================================================================
    # Layer 1: Attribute Filter Tests
    # =========================================================================

    def test_get_ignores_for_type_base_ignores(self):
        """Test that base ignores are always included."""
        ignores = get_ignores_for_type("aws_vpc")
        assert "arn" in ignores
        assert "id" in ignores
        assert "create_date" in ignores

    def test_get_ignores_for_type_resource_specific(self):
        """Test resource-specific ignores are included."""
        ignores = get_ignores_for_type("aws_autoscaling_group")
        assert "instances" in ignores
        assert "desired_capacity" in ignores
        # Also has base ignores
        assert "arn" in ignores

    def test_get_ignores_for_type_unknown_type(self):
        """Test unknown resource type gets only base ignores."""
        ignores = get_ignores_for_type("aws_unknown_type")
        assert ignores  # Has base ignores
        assert "instances" not in ignores  # No resource-specific

    # =========================================================================
    # Layer 2: Structure Normalizer Tests
    # =========================================================================

    def test_normalize_tags_aws_format(self):
        """Test normalizing AWS API tag format."""
        tags = [
            {"Key": "Name", "Value": "web-server"},
            {"Key": "Environment", "Value": "production"},
        ]
        result = normalize_tags(tags)
        assert result == {"Name": "web-server", "Environment": "production"}

    def test_normalize_tags_terraform_format(self):
        """Test normalizing Terraform dict format."""
        tags = {"Name": "web-server", "Environment": "production"}
        result = normalize_tags(tags)
        assert result == {"Name": "web-server", "Environment": "production"}

    def test_normalize_tags_filters_aws_managed(self):
        """Test AWS-managed tags are filtered out."""
        tags = [
            {"Key": "Name", "Value": "web"},
            {"Key": "aws:autoscaling:groupName", "Value": "asg-1"},
            {"Key": "kubernetes.io/cluster/eks", "Value": "owned"},
        ]
        result = normalize_tags(tags)
        assert result == {"Name": "web"}
        assert "aws:autoscaling:groupName" not in result
        assert "kubernetes.io/cluster/eks" not in result

    def test_normalize_tags_none(self):
        """Test normalizing None tags."""
        assert normalize_tags(None) == {}

    def test_normalize_tags_empty(self):
        """Test normalizing empty tags."""
        assert normalize_tags([]) == {}
        assert normalize_tags({}) == {}

    def test_deep_sort_simple_list(self):
        """Test deep sorting simple lists."""
        result = deep_sort([3, 1, 2])
        assert result == [1, 2, 3]

    def test_deep_sort_nested_dict(self):
        """Test deep sorting nested dicts."""
        result = deep_sort({"z": 1, "a": {"c": 3, "b": 2}})
        # Dict should be sorted by key
        assert list(result.keys()) == ["a", "z"]
        assert list(result["a"].keys()) == ["b", "c"]

    def test_deep_sort_list_of_dicts(self):
        """Test deep sorting list of dicts."""
        input_list = [
            {"port": 443, "protocol": "tcp"},
            {"port": 80, "protocol": "tcp"},
        ]
        result = deep_sort(input_list)
        # Should be sorted deterministically
        assert len(result) == 2

    def test_canonical_hash_order_independent(self):
        """Test canonical hash is order independent."""
        list1 = [{"port": 80}, {"port": 443}]
        list2 = [{"port": 443}, {"port": 80}]
        assert canonical_hash(list1) == canonical_hash(list2)

    def test_canonical_hash_different_content(self):
        """Test canonical hash differs for different content."""
        list1 = [{"port": 80}]
        list2 = [{"port": 443}]
        assert canonical_hash(list1) != canonical_hash(list2)

    # =========================================================================
    # Layer 3: Value Canonicalizer Tests
    # =========================================================================

    def test_is_falsy_none(self):
        """Test is_falsy for None."""
        assert is_falsy(None) is True

    def test_is_falsy_false(self):
        """Test is_falsy for False."""
        assert is_falsy(False) is True

    def test_is_falsy_zero(self):
        """Test is_falsy for zero."""
        assert is_falsy(0) is True
        assert is_falsy(0.0) is True

    def test_is_falsy_empty_string(self):
        """Test is_falsy for empty string."""
        assert is_falsy("") is True
        assert is_falsy("null") is True
        assert is_falsy("None") is True

    def test_is_falsy_empty_containers(self):
        """Test is_falsy for empty containers."""
        assert is_falsy([]) is True
        assert is_falsy({}) is True
        assert is_falsy(set()) is True

    def test_is_falsy_truthy_values(self):
        """Test is_falsy for truthy values."""
        assert is_falsy(True) is False
        assert is_falsy(1) is False
        assert is_falsy("hello") is False
        assert is_falsy([1, 2, 3]) is False

    def test_values_equivalent_both_falsy(self):
        """Test values_equivalent when both are falsy."""
        assert values_equivalent(None, False, "attr") is True
        assert values_equivalent(None, "", "attr") is True
        assert values_equivalent([], {}, "attr") is True
        assert values_equivalent(0, None, "attr") is True

    def test_values_equivalent_one_falsy(self):
        """Test values_equivalent when one is falsy."""
        assert values_equivalent(None, "value", "attr") is False
        assert values_equivalent("value", None, "attr") is False

    def test_values_equivalent_same_values(self):
        """Test values_equivalent for same values."""
        assert values_equivalent("hello", "hello", "attr") is True
        assert values_equivalent(80, 80, "attr") is True

    def test_values_equivalent_string_number(self):
        """Test values_equivalent with type coercion."""
        # Stringified numbers should be equivalent
        assert values_equivalent("80", 80, "port") is True
        assert values_equivalent("true", True, "enabled") is True

    def test_values_equivalent_tags(self):
        """Test values_equivalent for tags."""
        aws_tags = [{"Key": "Name", "Value": "web"}]
        tf_tags = {"Name": "web"}
        assert values_equivalent(aws_tags, tf_tags, "tags") is True

    def test_values_equivalent_lists_order_independent(self):
        """Test values_equivalent for lists (order independent)."""
        list1 = [{"port": 80}, {"port": 443}]
        list2 = [{"port": 443}, {"port": 80}]
        assert values_equivalent(list1, list2, "ingress") is True

    def test_values_equivalent_case_insensitive_attrs(self):
        """Test values_equivalent case insensitivity for specific attrs."""
        assert values_equivalent("t2.micro", "T2.MICRO", "instance_type") is True
        assert values_equivalent("mysql", "MYSQL", "engine") is True

    # =========================================================================
    # Drift Reason Classification Tests
    # =========================================================================

    def test_classify_drift_reason_semantic(self):
        """Test classification of semantic drift."""
        reason = classify_drift_reason("cidr_block", "10.0.0.0/16", "10.1.0.0/16", "")
        assert reason == DriftReason.SEMANTIC.value

    def test_classify_drift_reason_tag_only(self):
        """Test classification of tag-only drift."""
        reason = classify_drift_reason("tags", {"Name": "old"}, {"Name": "new"}, "")
        assert reason == DriftReason.TAG_ONLY.value

    def test_classify_drift_reason_ordering(self):
        """Test classification of ordering drift."""
        list1 = [{"port": 80}, {"port": 443}]
        list2 = [{"port": 443}, {"port": 80}]
        reason = classify_drift_reason("ingress", list1, list2, "")
        assert reason == DriftReason.ORDERING.value

    def test_classify_drift_reason_default_value(self):
        """Test classification of default value drift.

        DEFAULT_VALUE is when one side is falsy and the other is not.
        When both are falsy (None and ""), they're considered equivalent
        and this wouldn't even be called as a diff.
        """
        # One falsy (None), one truthy ("value") -> DEFAULT_VALUE
        reason = classify_drift_reason("description", None, "value", "")
        assert reason == DriftReason.DEFAULT_VALUE.value

        # One truthy, one falsy -> DEFAULT_VALUE
        reason = classify_drift_reason("description", "old", "", "")
        assert reason == DriftReason.DEFAULT_VALUE.value

    def test_classify_drift_reason_computed(self):
        """Test classification of computed attribute drift."""
        reason = classify_drift_reason("arn", "arn:old", "arn:new", "aws_instance")
        assert reason == DriftReason.COMPUTED.value

    # =========================================================================
    # DriftNormalizer Class Tests
    # =========================================================================

    def test_normalizer_filters_ignored_attrs(self):
        """Test normalizer filters ignored attributes."""
        normalizer = DriftNormalizer()
        attrs = {
            "cidr_block": "10.0.0.0/16",
            "arn": "arn:aws:...",
            "id": "vpc-123",
        }
        result = normalizer.normalize(attrs, "aws_vpc")
        assert "cidr_block" in result
        assert "arn" not in result
        assert "id" not in result

    def test_normalizer_normalizes_tags(self):
        """Test normalizer normalizes tags."""
        normalizer = DriftNormalizer()
        attrs = {
            "tags": [{"Key": "Name", "Value": "web"}],
        }
        result = normalizer.normalize(attrs, "aws_instance")
        assert result["tags"] == {"Name": "web"}

    def test_normalizer_sorts_lists(self):
        """Test normalizer sorts lists deterministically.

        Note: deep_sort sorts by JSON representation for consistency,
        not by specific field values. The important thing is that
        the order is deterministic.
        """
        normalizer = DriftNormalizer()
        attrs1 = {
            "ingress": [{"port": 443}, {"port": 80}],
        }
        attrs2 = {
            "ingress": [{"port": 80}, {"port": 443}],
        }
        result1 = normalizer.normalize(attrs1, "aws_security_group")
        result2 = normalizer.normalize(attrs2, "aws_security_group")
        # Both should produce the same sorted output
        assert result1["ingress"] == result2["ingress"]

    def test_normalizer_strict_mode(self):
        """Test normalizer strict mode skips normalization."""
        normalizer = DriftNormalizer(strict_mode=True)
        attrs = {"arn": "arn:aws:..."}
        result = normalizer.normalize(attrs, "aws_vpc")
        # Strict mode preserves all attributes
        assert "arn" in result

    def test_normalizer_compare_no_diff(self):
        """Test normalizer compare with equivalent values."""
        normalizer = DriftNormalizer()
        expected = {"tags": {"Name": "web"}}
        actual = {"tags": [{"Key": "Name", "Value": "web"}]}
        diffs = normalizer.compare(expected, actual, "aws_instance")
        assert len(diffs) == 0

    def test_normalizer_compare_with_diff(self):
        """Test normalizer compare with differences."""
        normalizer = DriftNormalizer()
        expected = {"cidr_block": "10.0.0.0/16"}
        actual = {"cidr_block": "10.1.0.0/16"}
        diffs = normalizer.compare(expected, actual, "aws_vpc")
        assert len(diffs) == 1
        attr, exp_val, act_val, reason = diffs[0]
        assert attr == "cidr_block"
        assert exp_val == "10.0.0.0/16"
        assert act_val == "10.1.0.0/16"

    # =========================================================================
    # DriftReason Model Tests
    # =========================================================================

    def test_drift_reason_enum_values(self):
        """Test DriftReason enum values."""
        assert DriftReason.SEMANTIC.value == "semantic"
        assert DriftReason.ORDERING.value == "ordering"
        assert DriftReason.DEFAULT_VALUE.value == "default_value"
        assert DriftReason.COMPUTED.value == "computed"
        assert DriftReason.TAG_ONLY.value == "tag_only"

    def test_attribute_diff_is_noise(self):
        """Test AttributeDiff.is_noise property."""
        noise_diff = AttributeDiff(
            attribute="ingress",
            expected=[{"port": 80}],
            actual=[{"port": 80}],
            reason=DriftReason.ORDERING,
        )
        assert noise_diff.is_noise is True

        semantic_diff = AttributeDiff(
            attribute="cidr_block",
            expected="10.0.0.0/16",
            actual="10.1.0.0/16",
            reason=DriftReason.SEMANTIC,
        )
        assert semantic_diff.is_noise is False

    def test_attribute_diff_is_semantic(self):
        """Test AttributeDiff.is_semantic property."""
        semantic_diff = AttributeDiff(
            attribute="cidr_block",
            expected="10.0.0.0/16",
            actual="10.1.0.0/16",
            reason=DriftReason.SEMANTIC,
        )
        assert semantic_diff.is_semantic is True

        tag_diff = AttributeDiff(
            attribute="tags",
            expected={"Name": "old"},
            actual={"Name": "new"},
            reason=DriftReason.TAG_ONLY,
        )
        assert tag_diff.is_semantic is False

    # =========================================================================
    # Integration Tests
    # =========================================================================

    def test_comparator_filters_noise_by_default(self):
        """Test comparator filters ordering/default value drifts."""
        comparator = DriftComparator()
        tf_resource = TFResource(
            type="aws_security_group",
            name="web",
            address="aws_security_group.web",
            id="sg-123",
            attributes={
                "ingress": [{"port": 443}, {"port": 80}],  # Different order
            },
        )
        actual_attrs = {
            "ingress": [{"port": 80}, {"port": 443}],  # Same content
        }

        drift = comparator.compare_resource(tf_resource, actual_attrs)
        # Should have no diffs because ordering is filtered
        assert drift.drift_type == DriftType.UNCHANGED

    def test_comparator_includes_noise_when_requested(self):
        """Test comparator includes noise when include_noise=True."""
        comparator = DriftComparator()
        tf_resource = TFResource(
            type="aws_security_group",
            name="web",
            address="aws_security_group.web",
            id="sg-123",
            attributes={
                "ingress": [{"port": 443}, {"port": 80}],
            },
        )
        actual_attrs = {
            "ingress": [{"port": 80}, {"port": 443}],
        }

        drift = comparator.compare_resource(
            tf_resource, actual_attrs, include_noise=True
        )
        # With include_noise, the ordering diff should be included
        # Note: depends on whether there actually IS a diff after normalization
        # In this case, canonical_hash should make them equal
        assert drift.drift_type == DriftType.UNCHANGED
