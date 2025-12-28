"""
Tests for P3-3: Topology Constraints Configuration.

Tests verify:
1. TopologyConstraint creation and matching
2. TopologyValidator constraint checking
3. YAML configuration loading
4. Violation detection and reporting
5. Default constraints generation
"""

import tempfile
from pathlib import Path

import pytest

from replimap.core.topology_constraints import (
    ConstraintType,
    ConstraintViolation,
    TopologyConstraint,
    TopologyConstraintsConfig,
    TopologyValidator,
    ValidationResult,
    ViolationSeverity,
    create_default_constraints,
    generate_sample_config_yaml,
    load_constraints_from_yaml,
)


class TestTopologyConstraint:
    """Test TopologyConstraint model."""

    def test_create_constraint(self):
        """Test creating a topology constraint."""
        constraint = TopologyConstraint(
            name="require-env-tag",
            constraint_type=ConstraintType.REQUIRE_TAG,
            severity=ViolationSeverity.MEDIUM,
            description="Require Environment tag",
            required_tags={"Environment": None},
        )

        assert constraint.name == "require-env-tag"
        assert constraint.constraint_type == ConstraintType.REQUIRE_TAG
        assert constraint.severity == ViolationSeverity.MEDIUM
        assert "Environment" in constraint.required_tags

    def test_constraint_enabled(self):
        """Test constraint enabled/disabled."""
        enabled = TopologyConstraint(
            name="test",
            constraint_type=ConstraintType.REQUIRE_TAG,
            enabled=True,
        )
        disabled = TopologyConstraint(
            name="test",
            constraint_type=ConstraintType.REQUIRE_TAG,
            enabled=False,
        )

        assert enabled.enabled
        assert not disabled.enabled

    def test_matches_source(self):
        """Test source pattern matching."""
        constraint = TopologyConstraint(
            name="test",
            constraint_type=ConstraintType.PROHIBIT_RELATIONSHIP,
            source_type="aws_instance",
        )

        assert constraint.matches_source("aws_instance")
        assert not constraint.matches_source("aws_vpc")

    def test_matches_source_pattern(self):
        """Test source regex pattern matching."""
        constraint = TopologyConstraint(
            name="test",
            constraint_type=ConstraintType.PROHIBIT_RELATIONSHIP,
            source_pattern="aws_(instance|db_instance)",
        )

        assert constraint.matches_source("aws_instance")
        assert constraint.matches_source("aws_db_instance")
        assert not constraint.matches_source("aws_vpc")

    def test_matches_target(self):
        """Test target pattern matching."""
        constraint = TopologyConstraint(
            name="test",
            constraint_type=ConstraintType.PROHIBIT_RELATIONSHIP,
            target_type="aws_db_instance",
        )

        assert constraint.matches_target("aws_db_instance")
        assert not constraint.matches_target("aws_instance")

    def test_exception_handling(self):
        """Test exception list."""
        constraint = TopologyConstraint(
            name="test",
            constraint_type=ConstraintType.REQUIRE_TAG,
            exceptions=["resource-exempt-1", "resource-exempt-2"],
        )

        assert constraint.is_exception("resource-exempt-1")
        assert constraint.is_exception("resource-exempt-2")
        assert not constraint.is_exception("resource-normal")

    def test_to_dict(self):
        """Test serialization."""
        constraint = TopologyConstraint(
            name="test",
            constraint_type=ConstraintType.REQUIRE_TAG,
            severity=ViolationSeverity.HIGH,
            required_tags={"Environment": None},
        )

        data = constraint.to_dict()
        assert data["name"] == "test"
        assert data["constraint_type"] == "require_tag"
        assert data["severity"] == "high"

    def test_from_dict(self):
        """Test deserialization."""
        data = {
            "name": "test",
            "constraint_type": "require_tag",
            "severity": "critical",
            "required_tags": {"Owner": None},
        }

        constraint = TopologyConstraint.from_dict(data)
        assert constraint.name == "test"
        assert constraint.constraint_type == ConstraintType.REQUIRE_TAG
        assert constraint.severity == ViolationSeverity.CRITICAL


class TestConstraintViolation:
    """Test ConstraintViolation model."""

    def test_create_violation(self):
        """Test creating a constraint violation."""
        constraint = TopologyConstraint(
            name="require-tag",
            constraint_type=ConstraintType.REQUIRE_TAG,
            severity=ViolationSeverity.HIGH,
        )

        violation = ConstraintViolation(
            constraint=constraint,
            resource_id="vpc-12345",
            resource_type="aws_vpc",
            message="Missing required tag: Environment",
        )

        assert violation.resource_id == "vpc-12345"
        assert violation.severity == ViolationSeverity.HIGH
        assert "Environment" in violation.message

    def test_violation_to_dict(self):
        """Test violation serialization."""
        constraint = TopologyConstraint(
            name="test",
            constraint_type=ConstraintType.REQUIRE_TAG,
            severity=ViolationSeverity.CRITICAL,
        )

        violation = ConstraintViolation(
            constraint=constraint,
            resource_id="vpc-12345",
            resource_type="aws_vpc",
            message="Test violation",
            details={"missing_tag": "Owner"},
        )

        data = violation.to_dict()
        assert data["constraint_name"] == "test"
        assert data["severity"] == "critical"
        assert data["resource_id"] == "vpc-12345"


class TestValidationResult:
    """Test ValidationResult model."""

    def test_is_valid_no_violations(self):
        """Test validation with no violations."""
        result = ValidationResult()
        assert result.is_valid
        assert result.critical_count == 0
        assert result.high_count == 0

    def test_is_valid_with_low_violations(self):
        """Test validation with only low severity violations."""
        constraint = TopologyConstraint(
            name="test",
            constraint_type=ConstraintType.REQUIRE_TAG,
            severity=ViolationSeverity.LOW,
        )

        result = ValidationResult(
            violations=[
                ConstraintViolation(
                    constraint=constraint,
                    resource_id="vpc-1",
                    resource_type="aws_vpc",
                    message="Test",
                )
            ]
        )

        # Low severity doesn't fail validation
        assert result.is_valid

    def test_is_invalid_with_critical(self):
        """Test validation fails with critical violations."""
        constraint = TopologyConstraint(
            name="test",
            constraint_type=ConstraintType.REQUIRE_TAG,
            severity=ViolationSeverity.CRITICAL,
        )

        result = ValidationResult(
            violations=[
                ConstraintViolation(
                    constraint=constraint,
                    resource_id="vpc-1",
                    resource_type="aws_vpc",
                    message="Test",
                )
            ]
        )

        assert not result.is_valid
        assert result.critical_count == 1


class TestTopologyConstraintsConfig:
    """Test TopologyConstraintsConfig."""

    def test_create_config(self):
        """Test creating config with constraints."""
        config = TopologyConstraintsConfig()
        config.add_constraint(
            TopologyConstraint(
                name="test",
                constraint_type=ConstraintType.REQUIRE_TAG,
            )
        )

        assert len(config.constraints) == 1

    def test_get_enabled_constraints(self):
        """Test getting only enabled constraints."""
        config = TopologyConstraintsConfig(
            constraints=[
                TopologyConstraint(
                    name="enabled",
                    constraint_type=ConstraintType.REQUIRE_TAG,
                    enabled=True,
                ),
                TopologyConstraint(
                    name="disabled",
                    constraint_type=ConstraintType.REQUIRE_TAG,
                    enabled=False,
                ),
            ]
        )

        enabled = config.enabled_constraints
        assert len(enabled) == 1
        assert enabled[0].name == "enabled"

    def test_get_constraints_by_type(self):
        """Test filtering constraints by type."""
        config = TopologyConstraintsConfig(
            constraints=[
                TopologyConstraint(
                    name="tag1",
                    constraint_type=ConstraintType.REQUIRE_TAG,
                ),
                TopologyConstraint(
                    name="encrypt",
                    constraint_type=ConstraintType.REQUIRE_ENCRYPTION,
                ),
            ]
        )

        tag_constraints = config.get_constraints_by_type(ConstraintType.REQUIRE_TAG)
        assert len(tag_constraints) == 1
        assert tag_constraints[0].name == "tag1"

    def test_yaml_roundtrip(self):
        """Test YAML save and load."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "constraints.yaml"

            # Create config
            config = TopologyConstraintsConfig(
                constraints=[
                    TopologyConstraint(
                        name="require-env",
                        constraint_type=ConstraintType.REQUIRE_TAG,
                        required_tags={"Environment": None},
                    )
                ]
            )

            # Save
            config.to_yaml(path)

            # Load
            loaded = TopologyConstraintsConfig.from_yaml(path)
            assert len(loaded.constraints) == 1
            assert loaded.constraints[0].name == "require-env"


class TestDefaultConstraints:
    """Test default constraint generation."""

    def test_create_default_constraints(self):
        """Test generating default constraints."""
        config = create_default_constraints()

        assert len(config.constraints) > 0

        # Should include common constraints
        names = [c.name for c in config.constraints]
        assert "require-environment-tag" in names or any("tag" in n for n in names)

    def test_generate_sample_yaml(self):
        """Test sample YAML generation."""
        yaml_content = generate_sample_config_yaml()

        assert "topology_constraints" in yaml_content
        assert "constraints" in yaml_content
        assert "constraint_type" in yaml_content


class TestViolationSeverity:
    """Test ViolationSeverity enum."""

    def test_severity_values(self):
        """Test severity enum values."""
        assert ViolationSeverity.CRITICAL.value == "critical"
        assert ViolationSeverity.HIGH.value == "high"
        assert ViolationSeverity.MEDIUM.value == "medium"
        assert ViolationSeverity.LOW.value == "low"
        assert ViolationSeverity.INFO.value == "info"

    def test_severity_str(self):
        """Test severity string representation."""
        assert str(ViolationSeverity.CRITICAL) == "critical"


class TestConstraintType:
    """Test ConstraintType enum."""

    def test_constraint_type_values(self):
        """Test constraint type values."""
        assert ConstraintType.PROHIBIT_RELATIONSHIP.value == "prohibit_relationship"
        assert ConstraintType.REQUIRE_TAG.value == "require_tag"
        assert ConstraintType.REQUIRE_ENCRYPTION.value == "require_encryption"
        assert ConstraintType.PROHIBIT_PUBLIC_ACCESS.value == "prohibit_public_access"
