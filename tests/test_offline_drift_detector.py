"""Comprehensive tests for Offline Drift Detection."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from replimap.core.drift.detector import (
    AttributeChange,
    AttributeComparator,
    AttributeNormalizer,
    DriftFilter,
    DriftFinding,
    DriftIgnoreRule,
    DriftReport,
    DriftSeverity,
    DriftType,
    OfflineDriftDetector,
    ScanComparator,
    TerraformStateLoader,
)


class TestTerraformStateLoader:
    """Test TF state parsing."""

    def test_parse_v4_state(self, tmp_path: Path) -> None:
        """Parse TF State v4 format."""
        state = {
            "version": 4,
            "resources": [
                {
                    "type": "aws_instance",
                    "name": "web",
                    "mode": "managed",
                    "instances": [
                        {
                            "attributes": {
                                "id": "i-1234567890abcdef0",
                                "instance_type": "t3.micro",
                                "tags": {"Name": "web"},
                            }
                        }
                    ],
                }
            ],
        }

        state_file = tmp_path / "terraform.tfstate"
        state_file.write_text(json.dumps(state))

        loader = TerraformStateLoader()
        result = loader.load(state_file)

        assert "i-1234567890abcdef0" in result
        assert result["i-1234567890abcdef0"]["type"] == "aws_instance"
        assert result["i-1234567890abcdef0"]["address"] == "aws_instance.web"

    def test_parse_count_for_each(self, tmp_path: Path) -> None:
        """Parse resources with count/for_each."""
        state = {
            "version": 4,
            "resources": [
                {
                    "type": "aws_instance",
                    "name": "web",
                    "mode": "managed",
                    "instances": [
                        {"index_key": 0, "attributes": {"id": "i-001"}},
                        {"index_key": 1, "attributes": {"id": "i-002"}},
                    ],
                },
                {
                    "type": "aws_instance",
                    "name": "api",
                    "mode": "managed",
                    "instances": [
                        {"index_key": "east", "attributes": {"id": "i-003"}},
                        {"index_key": "west", "attributes": {"id": "i-004"}},
                    ],
                },
            ],
        }

        state_file = tmp_path / "terraform.tfstate"
        state_file.write_text(json.dumps(state))

        loader = TerraformStateLoader()
        result = loader.load(state_file)

        assert result["i-001"]["address"] == "aws_instance.web[0]"
        assert result["i-002"]["address"] == "aws_instance.web[1]"
        assert result["i-003"]["address"] == 'aws_instance.api["east"]'
        assert result["i-004"]["address"] == 'aws_instance.api["west"]'

    def test_parse_module_resources(self, tmp_path: Path) -> None:
        """Parse module-nested resources."""
        state = {
            "version": 4,
            "resources": [
                {
                    "type": "aws_instance",
                    "name": "web",
                    "module": "module.vpc",
                    "mode": "managed",
                    "instances": [{"attributes": {"id": "i-123"}}],
                }
            ],
        }

        state_file = tmp_path / "terraform.tfstate"
        state_file.write_text(json.dumps(state))

        loader = TerraformStateLoader()
        result = loader.load(state_file)

        assert result["i-123"]["address"] == "module.vpc.aws_instance.web"
        assert result["i-123"]["module"] == "module.vpc"

    def test_skip_data_sources(self, tmp_path: Path) -> None:
        """Should skip data source resources."""
        state = {
            "version": 4,
            "resources": [
                {
                    "type": "aws_ami",
                    "name": "ubuntu",
                    "mode": "data",  # Data source
                    "instances": [{"attributes": {"id": "ami-123"}}],
                },
                {
                    "type": "aws_instance",
                    "name": "web",
                    "mode": "managed",
                    "instances": [{"attributes": {"id": "i-123"}}],
                },
            ],
        }

        state_file = tmp_path / "terraform.tfstate"
        state_file.write_text(json.dumps(state))

        loader = TerraformStateLoader()
        result = loader.load(state_file)

        assert "ami-123" not in result
        assert "i-123" in result

    def test_skip_non_aws_resources(self, tmp_path: Path) -> None:
        """Should skip non-AWS resources."""
        state = {
            "version": 4,
            "resources": [
                {
                    "type": "google_compute_instance",
                    "name": "gcp_vm",
                    "mode": "managed",
                    "instances": [{"attributes": {"id": "gcp-123"}}],
                },
                {
                    "type": "aws_instance",
                    "name": "web",
                    "mode": "managed",
                    "instances": [{"attributes": {"id": "i-123"}}],
                },
            ],
        }

        state_file = tmp_path / "terraform.tfstate"
        state_file.write_text(json.dumps(state))

        loader = TerraformStateLoader()
        result = loader.load(state_file)

        assert "gcp-123" not in result
        assert "i-123" in result


class TestAttributeNormalizer:
    """Test attribute normalization."""

    def test_normalize_tags_array_to_object(self) -> None:
        """Convert AWS tags [{Key, Value}] to TF format {key: value}."""
        normalizer = AttributeNormalizer()

        attrs: dict[str, Any] = {
            "tags": [
                {"Key": "Name", "Value": "web"},
                {"Key": "Env", "Value": "prod"},
            ]
        }

        result = normalizer.normalize_aws_attributes("aws_instance", attrs)

        assert result["tags"] == {"Name": "web", "Env": "prod"}
        assert result["tags_all"] == {"Name": "web", "Env": "prod"}

    def test_normalize_camel_to_snake(self) -> None:
        """Convert CamelCase to snake_case."""
        normalizer = AttributeNormalizer()

        attrs: dict[str, Any] = {
            "InstanceType": "t3.micro",
            "PublicIpAddress": "1.2.3.4",
        }

        result = normalizer.normalize_aws_attributes("aws_instance", attrs)

        assert "instance_type" in result
        # PublicIpAddress maps to public_ip via FIELD_NAME_MAP
        assert "public_ip" in result

    def test_normalize_known_field_mappings(self) -> None:
        """Test known field name mappings."""
        normalizer = AttributeNormalizer()

        attrs: dict[str, Any] = {
            "ImageId": "ami-123",
            "SubnetId": "subnet-456",
        }

        result = normalizer.normalize_aws_attributes("aws_instance", attrs)

        assert result.get("ami") == "ami-123"
        assert result.get("subnet_id") == "subnet-456"

    def test_normalize_boolean_strings(self) -> None:
        """Convert string booleans to actual booleans."""
        normalizer = AttributeNormalizer()

        attrs: dict[str, Any] = {
            "enabled": "true",
            "disabled": "false",
        }

        result = normalizer.normalize_aws_attributes("aws_instance", attrs)

        assert result["enabled"] is True
        assert result["disabled"] is False

    def test_ignore_global_fields(self) -> None:
        """Check global field ignore logic."""
        normalizer = AttributeNormalizer()

        assert normalizer.should_ignore_field("aws_instance", "arn") is True
        assert normalizer.should_ignore_field("aws_instance", "creation_date") is True
        assert normalizer.should_ignore_field("aws_instance", "owner_id") is True

    def test_ignore_resource_specific_fields(self) -> None:
        """Check resource-specific field ignore logic."""
        normalizer = AttributeNormalizer()

        assert (
            normalizer.should_ignore_field("aws_lambda_function", "invoke_arn") is True
        )
        assert (
            normalizer.should_ignore_field("aws_autoscaling_group", "desired_capacity")
            is True
        )
        assert (
            normalizer.should_ignore_field("aws_ecs_service", "desired_count") is True
        )

    def test_not_ignore_important_fields(self) -> None:
        """Important fields should NOT be ignored."""
        normalizer = AttributeNormalizer()

        assert normalizer.should_ignore_field("aws_instance", "instance_type") is False
        assert normalizer.should_ignore_field("aws_security_group", "ingress") is False


class TestDriftFilter:
    """Test drift filtering."""

    def test_default_rules_exist(self) -> None:
        """Verify default rules are loaded."""
        filter = DriftFilter()

        # Should have default rules for K8s, AWS tags, ASG
        assert len(filter.rules) > 0

    def test_ignore_kubernetes_resources(self) -> None:
        """Ignore K8s-managed resources."""
        filter = DriftFilter()

        change = AttributeChange(
            field="tags",
            expected={},
            actual={},
            severity=DriftSeverity.LOW,
        )

        # Should NOT ignore (no K8s tags)
        result = filter.should_ignore_change(
            "aws_instance",
            "i-123",
            change,
            tags={"Name": "web"},
        )
        assert result is False

        # Should ignore (has K8s tags)
        result = filter.should_ignore_change(
            "aws_instance",
            "i-123",
            change,
            tags={"kubernetes.io/cluster/main": "owned"},
        )
        assert result is True

    def test_ignore_asg_desired_capacity(self) -> None:
        """Ignore ASG auto-scaling changes."""
        filter = DriftFilter()

        change = AttributeChange(
            field="desired_capacity",
            expected=2,
            actual=5,
            severity=DriftSeverity.MEDIUM,
        )

        result = filter.should_ignore_change(
            "aws_autoscaling_group", "asg-123", change, {}
        )
        assert result is True

    def test_load_from_config(self, tmp_path: Path) -> None:
        """Load ignore rules from config file."""
        config = tmp_path / ".replimapignore"
        config.write_text(
            """
# Ignore all CloudWatch logs
aws_cloudwatch_log_group

# Ignore specific field
aws_instance:user_data

# Ignore specific resource
i-abcdef123
"""
        )

        filter = DriftFilter.from_config(config)

        # Check rules loaded
        assert any(r.resource_type == "aws_cloudwatch_log_group" for r in filter.rules)
        assert any(
            r.resource_type == "aws_instance" and r.field == "user_data"
            for r in filter.rules
        )
        assert any(r.resource_id == "i-abcdef123" for r in filter.rules)

    def test_filter_findings(self) -> None:
        """Test filtering a list of findings."""
        filter = DriftFilter(
            custom_rules=[
                DriftIgnoreRule(resource_type="aws_cloudwatch_log_group"),
            ]
        )

        findings = [
            DriftFinding(
                resource_id="log-1",
                resource_type="aws_cloudwatch_log_group",
                resource_name="log1",
                drift_type=DriftType.UNMANAGED,
            ),
            DriftFinding(
                resource_id="i-123",
                resource_type="aws_instance",
                resource_name="web",
                drift_type=DriftType.DRIFTED,
            ),
        ]

        filtered = filter.filter_findings(findings)

        assert len(filtered) == 1
        assert filtered[0].resource_type == "aws_instance"


class TestAttributeComparator:
    """Test attribute comparison."""

    def test_compare_equal_values(self) -> None:
        """Equal values should not produce changes."""
        normalizer = AttributeNormalizer()
        comparator = AttributeComparator(normalizer)

        expected = {"instance_type": "t3.micro", "ami": "ami-123"}
        actual = {"instance_type": "t3.micro", "ami": "ami-123"}

        changes = comparator.compare("aws_instance", expected, actual)

        assert len(changes) == 0

    def test_compare_different_values(self) -> None:
        """Different values should produce changes."""
        normalizer = AttributeNormalizer()
        comparator = AttributeComparator(normalizer)

        expected = {"instance_type": "t3.micro"}
        actual = {"instance_type": "t3.large"}

        changes = comparator.compare("aws_instance", expected, actual)

        assert len(changes) == 1
        assert changes[0].field == "instance_type"
        assert changes[0].expected == "t3.micro"
        assert changes[0].actual == "t3.large"

    def test_security_fields_critical_severity(self) -> None:
        """Security fields should have CRITICAL severity."""
        normalizer = AttributeNormalizer()
        comparator = AttributeComparator(normalizer)

        expected = {"ingress": [{"from_port": 22, "cidr_blocks": ["10.0.0.0/8"]}]}
        actual = {"ingress": [{"from_port": 22, "cidr_blocks": ["0.0.0.0/0"]}]}

        changes = comparator.compare("aws_security_group", expected, actual)

        assert len(changes) == 1
        assert changes[0].severity == DriftSeverity.CRITICAL

    def test_infrastructure_fields_high_severity(self) -> None:
        """Infrastructure fields should have HIGH severity."""
        normalizer = AttributeNormalizer()
        comparator = AttributeComparator(normalizer)

        expected = {"instance_type": "t3.micro"}
        actual = {"instance_type": "t3.large"}

        changes = comparator.compare("aws_instance", expected, actual)

        assert len(changes) == 1
        assert changes[0].severity == DriftSeverity.HIGH

    def test_empty_values_equivalent(self) -> None:
        """None, empty string, empty list should be equivalent."""
        normalizer = AttributeNormalizer()
        comparator = AttributeComparator(normalizer)

        expected = {"description": None}
        actual = {"description": ""}

        changes = comparator.compare("aws_instance", expected, actual)

        assert len(changes) == 0

    def test_list_order_insensitive(self) -> None:
        """Lists should be compared order-insensitively."""
        normalizer = AttributeNormalizer()
        comparator = AttributeComparator(normalizer)

        expected = {"items": ["a", "b", "c"]}
        actual = {"items": ["c", "a", "b"]}

        changes = comparator.compare("aws_instance", expected, actual)

        assert len(changes) == 0


class TestOfflineDriftDetector:
    """Test drift detection."""

    @pytest.fixture
    def detector(self) -> OfflineDriftDetector:
        return OfflineDriftDetector()

    def test_detect_unmanaged(
        self, detector: OfflineDriftDetector, tmp_path: Path
    ) -> None:
        """Detect resources in AWS but not in TF State."""
        live_resources = [
            {"id": "i-123", "type": "aws_instance", "name": "web", "attributes": {}},
            {"id": "i-456", "type": "aws_instance", "name": "api", "attributes": {}},
        ]

        state = {
            "version": 4,
            "resources": [
                {
                    "type": "aws_instance",
                    "name": "web",
                    "mode": "managed",
                    "instances": [{"attributes": {"id": "i-123"}}],
                }
            ],
        }

        state_file = tmp_path / "terraform.tfstate"
        state_file.write_text(json.dumps(state))

        report = detector.detect(live_resources, state_file)

        unmanaged = [f for f in report.findings if f.drift_type == DriftType.UNMANAGED]
        assert len(unmanaged) == 1
        assert unmanaged[0].resource_id == "i-456"
        assert "import" in unmanaged[0].remediation_hint.lower()

    def test_detect_missing(
        self, detector: OfflineDriftDetector, tmp_path: Path
    ) -> None:
        """Detect resources in TF State but not in AWS."""
        live_resources = [
            {"id": "i-123", "type": "aws_instance", "name": "web", "attributes": {}},
        ]

        state = {
            "version": 4,
            "resources": [
                {
                    "type": "aws_instance",
                    "name": "web",
                    "mode": "managed",
                    "instances": [{"attributes": {"id": "i-123"}}],
                },
                {
                    "type": "aws_instance",
                    "name": "api",
                    "mode": "managed",
                    "instances": [{"attributes": {"id": "i-456"}}],
                },
            ],
        }

        state_file = tmp_path / "terraform.tfstate"
        state_file.write_text(json.dumps(state))

        report = detector.detect(live_resources, state_file)

        missing = [f for f in report.findings if f.drift_type == DriftType.MISSING]
        assert len(missing) == 1
        assert missing[0].resource_id == "i-456"
        assert "apply" in missing[0].remediation_hint.lower()

    def test_detect_drifted(
        self, detector: OfflineDriftDetector, tmp_path: Path
    ) -> None:
        """Detect resources with changed attributes."""
        live_resources = [
            {
                "id": "i-123",
                "type": "aws_instance",
                "name": "web",
                "attributes": {"instance_type": "t3.large"},  # Changed!
            }
        ]

        state = {
            "version": 4,
            "resources": [
                {
                    "type": "aws_instance",
                    "name": "web",
                    "mode": "managed",
                    "instances": [
                        {
                            "attributes": {
                                "id": "i-123",
                                "instance_type": "t3.micro",  # Original
                            }
                        }
                    ],
                }
            ],
        }

        state_file = tmp_path / "terraform.tfstate"
        state_file.write_text(json.dumps(state))

        report = detector.detect(live_resources, state_file)

        drifted = [f for f in report.findings if f.drift_type == DriftType.DRIFTED]
        assert len(drifted) == 1
        assert drifted[0].resource_id == "i-123"

        # Check changes
        changes = drifted[0].changes
        assert len(changes) == 1
        assert changes[0].field == "instance_type"
        assert changes[0].expected == "t3.micro"
        assert changes[0].actual == "t3.large"
        assert changes[0].severity == DriftSeverity.HIGH

    def test_security_severity(
        self, detector: OfflineDriftDetector, tmp_path: Path
    ) -> None:
        """Security changes should be CRITICAL severity."""
        live_resources = [
            {
                "id": "sg-123",
                "type": "aws_security_group",
                "name": "web-sg",
                "attributes": {
                    "ingress": [
                        {"from_port": 22, "to_port": 22, "cidr_blocks": ["0.0.0.0/0"]}
                    ]
                },
            }
        ]

        state = {
            "version": 4,
            "resources": [
                {
                    "type": "aws_security_group",
                    "name": "web-sg",
                    "mode": "managed",
                    "instances": [
                        {
                            "attributes": {
                                "id": "sg-123",
                                "ingress": [
                                    {
                                        "from_port": 22,
                                        "to_port": 22,
                                        "cidr_blocks": ["10.0.0.0/8"],
                                    }
                                ],
                            }
                        }
                    ],
                }
            ],
        }

        state_file = tmp_path / "terraform.tfstate"
        state_file.write_text(json.dumps(state))

        report = detector.detect(live_resources, state_file)

        assert report.critical_count >= 1
        drifted = [f for f in report.findings if f.drift_type == DriftType.DRIFTED]
        assert drifted[0].max_change_severity == DriftSeverity.CRITICAL

    def test_no_drift(self, detector: OfflineDriftDetector, tmp_path: Path) -> None:
        """No drift when resources match."""
        live_resources = [
            {
                "id": "i-123",
                "type": "aws_instance",
                "name": "web",
                "attributes": {"instance_type": "t3.micro"},
            }
        ]

        state = {
            "version": 4,
            "resources": [
                {
                    "type": "aws_instance",
                    "name": "web",
                    "mode": "managed",
                    "instances": [
                        {
                            "attributes": {
                                "id": "i-123",
                                "instance_type": "t3.micro",
                            }
                        }
                    ],
                }
            ],
        }

        state_file = tmp_path / "terraform.tfstate"
        state_file.write_text(json.dumps(state))

        report = detector.detect(live_resources, state_file)

        assert not report.has_drift
        assert len(report.findings) == 0


class TestScanComparator:
    """Test scan comparison."""

    def test_detect_new_resources(self) -> None:
        """Detect resources added since last scan."""
        comparator = ScanComparator()

        current = [
            {"id": "i-123", "type": "aws_instance", "name": "web", "attributes": {}},
            {"id": "i-456", "type": "aws_instance", "name": "api", "attributes": {}},
        ]
        previous = [
            {"id": "i-123", "type": "aws_instance", "name": "web", "attributes": {}},
        ]

        report = comparator.compare(current, previous)

        assert report.summary["added"] == 1
        added = [f for f in report.findings if f.drift_type == DriftType.UNMANAGED]
        assert len(added) == 1
        assert added[0].resource_id == "i-456"

    def test_detect_removed_resources(self) -> None:
        """Detect resources removed since last scan."""
        comparator = ScanComparator()

        current = [
            {"id": "i-123", "type": "aws_instance", "name": "web", "attributes": {}},
        ]
        previous = [
            {"id": "i-123", "type": "aws_instance", "name": "web", "attributes": {}},
            {"id": "i-456", "type": "aws_instance", "name": "api", "attributes": {}},
        ]

        report = comparator.compare(current, previous)

        assert report.summary["removed"] == 1
        removed = [f for f in report.findings if f.drift_type == DriftType.MISSING]
        assert len(removed) == 1
        assert removed[0].resource_id == "i-456"

    def test_detect_modified_resources(self) -> None:
        """Detect resources modified since last scan."""
        comparator = ScanComparator()

        current = [
            {
                "id": "i-123",
                "type": "aws_instance",
                "name": "web",
                "attributes": {"instance_type": "t3.large"},
            },
        ]
        previous = [
            {
                "id": "i-123",
                "type": "aws_instance",
                "name": "web",
                "attributes": {"instance_type": "t3.micro"},
            },
        ]

        report = comparator.compare(current, previous)

        assert report.summary["modified"] == 1
        modified = [f for f in report.findings if f.drift_type == DriftType.DRIFTED]
        assert len(modified) == 1
        assert modified[0].resource_id == "i-123"

    def test_no_changes(self) -> None:
        """No changes when scans are identical."""
        comparator = ScanComparator()

        resources = [
            {
                "id": "i-123",
                "type": "aws_instance",
                "name": "web",
                "attributes": {"instance_type": "t3.micro"},
            },
        ]

        report = comparator.compare(resources, resources)

        assert not report.has_drift
        assert report.summary["added"] == 0
        assert report.summary["removed"] == 0
        assert report.summary["modified"] == 0


class TestDriftReport:
    """Test DriftReport model."""

    def test_to_dict(self) -> None:
        """Test serialization to dict."""
        finding = DriftFinding(
            resource_id="i-123",
            resource_type="aws_instance",
            resource_name="web",
            drift_type=DriftType.DRIFTED,
            changes=[
                AttributeChange(
                    field="instance_type",
                    expected="t3.micro",
                    actual="t3.large",
                    severity=DriftSeverity.HIGH,
                )
            ],
        )

        report = DriftReport(
            findings=[finding],
            scan_timestamp="2024-01-01T00:00:00Z",
            state_file_path="terraform.tfstate",
        )

        data = report.to_dict()

        assert data["has_drift"] is True
        assert data["findings_count"] == 1
        assert len(data["findings"]) == 1
        assert data["findings"][0]["resource_id"] == "i-123"

    def test_to_json(self) -> None:
        """Test JSON serialization."""
        report = DriftReport(
            findings=[],
            scan_timestamp="2024-01-01T00:00:00Z",
        )

        json_str = report.to_json()

        # Should be valid JSON
        data = json.loads(json_str)
        assert data["has_drift"] is False

    def test_severity_counts(self) -> None:
        """Test critical and high counts."""
        report = DriftReport(
            findings=[
                DriftFinding(
                    resource_id="sg-1",
                    resource_type="aws_security_group",
                    resource_name="sg1",
                    drift_type=DriftType.DRIFTED,
                    severity=DriftSeverity.CRITICAL,
                ),
                DriftFinding(
                    resource_id="i-1",
                    resource_type="aws_instance",
                    resource_name="web",
                    drift_type=DriftType.DRIFTED,
                    severity=DriftSeverity.HIGH,
                ),
                DriftFinding(
                    resource_id="i-2",
                    resource_type="aws_instance",
                    resource_name="api",
                    drift_type=DriftType.MISSING,
                    severity=DriftSeverity.HIGH,
                ),
            ]
        )

        assert report.critical_count == 1
        assert report.high_count == 2


class TestDriftFinding:
    """Test DriftFinding model."""

    def test_remediation_for_unmanaged(self) -> None:
        """Unmanaged resources suggest import."""
        finding = DriftFinding(
            resource_id="i-123",
            resource_type="aws_instance",
            resource_name="web",
            drift_type=DriftType.UNMANAGED,
        )

        from replimap.core.drift.detector import Remediation

        assert finding.remediation == Remediation.IMPORT
        assert "import" in finding.remediation_hint.lower()

    def test_remediation_for_missing(self) -> None:
        """Missing resources suggest apply."""
        finding = DriftFinding(
            resource_id="i-123",
            resource_type="aws_instance",
            resource_name="web",
            drift_type=DriftType.MISSING,
        )

        from replimap.core.drift.detector import Remediation

        assert finding.remediation == Remediation.APPLY
        assert "apply" in finding.remediation_hint.lower()

    def test_remediation_for_critical_drift(self) -> None:
        """Critical drift suggests investigation."""
        finding = DriftFinding(
            resource_id="sg-123",
            resource_type="aws_security_group",
            resource_name="web-sg",
            drift_type=DriftType.DRIFTED,
            changes=[
                AttributeChange(
                    field="ingress",
                    expected=[],
                    actual=[{"from_port": 22}],
                    severity=DriftSeverity.CRITICAL,
                )
            ],
        )

        from replimap.core.drift.detector import Remediation

        assert finding.remediation == Remediation.INVESTIGATE

    def test_max_change_severity(self) -> None:
        """Max severity is calculated from changes."""
        finding = DriftFinding(
            resource_id="i-123",
            resource_type="aws_instance",
            resource_name="web",
            drift_type=DriftType.DRIFTED,
            changes=[
                AttributeChange(
                    field="tags",
                    expected={},
                    actual={"foo": "bar"},
                    severity=DriftSeverity.LOW,
                ),
                AttributeChange(
                    field="instance_type",
                    expected="t3.micro",
                    actual="t3.large",
                    severity=DriftSeverity.HIGH,
                ),
            ],
        )

        assert finding.max_change_severity == DriftSeverity.HIGH
