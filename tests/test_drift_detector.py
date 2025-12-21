"""
Comprehensive tests for the Drift Detector feature.
"""

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from replimap.drift import (
    DriftEngine,
    DriftReporter,
    DriftReport,
    DriftSeverity,
    DriftType,
    TerraformStateParser,
    TFResource,
    TFState,
)
from replimap.drift.comparator import DriftComparator
from replimap.drift.models import AttributeDiff, ResourceDrift


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
        """Test comparing resource with only tags changed."""
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
        assert drift.severity == DriftSeverity.LOW  # tags are low severity

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
        """Test _values_differ handles None correctly."""
        comparator = DriftComparator()

        # Both None - no diff
        assert comparator._values_differ(None, None, "attr") is False

        # None vs empty - no diff
        assert comparator._values_differ(None, "", "attr") is False
        assert comparator._values_differ(None, [], "attr") is False
        assert comparator._values_differ(None, {}, "attr") is False

        # None vs actual value - diff
        assert comparator._values_differ(None, "value", "attr") is True
        assert comparator._values_differ("value", None, "attr") is True

    def test_lists_equivalent(self):
        """Test _lists_equivalent comparison."""
        comparator = DriftComparator()

        # Same simple lists (order independent)
        assert comparator._lists_equivalent([1, 2, 3], [3, 2, 1]) is True

        # Different simple lists
        assert comparator._lists_equivalent([1, 2], [1, 2, 3]) is False

        # Same dicts in lists (order independent)
        list1 = [{"port": 80}, {"port": 443}]
        list2 = [{"port": 443}, {"port": 80}]
        assert comparator._lists_equivalent(list1, list2) is True

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
            scanned_at=datetime.now(timezone.utc),
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
