"""
Schema Purity Tests.

Ensures all Parameter schemas are JSON-serializable and contain no Callable objects.
This prevents "dirty schemas" with embedded functions from entering the codebase.

If these tests fail, a developer has added a Callable to a Parameter definition,
which breaks JSON serialization and API schema export.
"""

from __future__ import annotations

import json

import pytest

from replimap.cli.params.definitions import (
    AUDIT_PARAMETERS,
    CLONE_PARAMETERS,
    COST_PARAMETERS,
    SCAN_PARAMETERS,
    export_all_schemas,
)
from replimap.cli.params.schema import (
    Parameter,
    ParameterGroup,
    ParameterType,
    validate_group_purity,
    validate_schema_purity,
)


class TestSchemaPurity:
    """Tests that schemas contain no callable objects."""

    def test_scan_params_serializable(self) -> None:
        """SCAN_PARAMETERS must be JSON serializable."""
        data = SCAN_PARAMETERS.to_dict()
        # If this contains a Callable, json.dumps will raise TypeError
        json_str = json.dumps(data)
        assert json_str is not None
        assert len(json_str) > 0

    def test_clone_params_serializable(self) -> None:
        """CLONE_PARAMETERS must be JSON serializable."""
        data = CLONE_PARAMETERS.to_dict()
        json_str = json.dumps(data)
        assert json_str is not None
        assert len(json_str) > 0

    def test_audit_params_serializable(self) -> None:
        """AUDIT_PARAMETERS must be JSON serializable."""
        data = AUDIT_PARAMETERS.to_dict()
        json_str = json.dumps(data)
        assert json_str is not None
        assert len(json_str) > 0

    def test_cost_params_serializable(self) -> None:
        """COST_PARAMETERS must be JSON serializable."""
        data = COST_PARAMETERS.to_dict()
        json_str = json.dumps(data)
        assert json_str is not None
        assert len(json_str) > 0

    def test_all_schemas_export(self) -> None:
        """All schemas export must succeed."""
        all_schemas = export_all_schemas()
        json_str = json.dumps(all_schemas)
        assert json_str is not None

        # Verify structure
        assert "schemas" in all_schemas
        assert "scan" in all_schemas["schemas"]
        assert "clone" in all_schemas["schemas"]
        assert "audit" in all_schemas["schemas"]
        assert "cost" in all_schemas["schemas"]

    def test_no_callable_in_scan_parameters(self) -> None:
        """SCAN_PARAMETERS must contain no callable objects."""
        errors = validate_group_purity(SCAN_PARAMETERS)
        assert errors == [], f"Callable objects found: {errors}"

    def test_no_callable_in_clone_parameters(self) -> None:
        """CLONE_PARAMETERS must contain no callable objects."""
        errors = validate_group_purity(CLONE_PARAMETERS)
        assert errors == [], f"Callable objects found: {errors}"

    def test_no_callable_in_audit_parameters(self) -> None:
        """AUDIT_PARAMETERS must contain no callable objects."""
        errors = validate_group_purity(AUDIT_PARAMETERS)
        assert errors == [], f"Callable objects found: {errors}"

    def test_no_callable_in_cost_parameters(self) -> None:
        """COST_PARAMETERS must contain no callable objects."""
        errors = validate_group_purity(COST_PARAMETERS)
        assert errors == [], f"Callable objects found: {errors}"


class TestParameterValidation:
    """Tests for parameter definition validation."""

    def test_mutually_exclusive_choices(self) -> None:
        """choices_ref and choices_static are mutually exclusive."""
        with pytest.raises(ValueError, match="mutually exclusive"):
            Parameter(
                key="test",
                label="Test",
                choices_ref="aws:regions",
                choices_static=["a", "b"],
            )

    def test_mutually_exclusive_defaults(self) -> None:
        """default_ref and default_static are mutually exclusive."""
        with pytest.raises(ValueError, match="mutually exclusive"):
            Parameter(
                key="test",
                label="Test",
                default_ref="config:region",
                default_static="us-east-1",
            )

    def test_parameter_roundtrip(self) -> None:
        """Parameter should survive JSON roundtrip."""
        original = Parameter(
            key="region",
            label="AWS Region",
            type=ParameterType.SELECT,
            help_text="Select a region",
            choices_ref="aws:regions",
            default_ref="config:region",
            required=True,
            cli_flag="--region",
            cli_short="-r",
        )

        # Serialize
        json_str = original.to_json()

        # Deserialize
        data = json.loads(json_str)
        restored = Parameter.from_dict(data)

        # Verify
        assert restored.key == original.key
        assert restored.label == original.label
        assert restored.type == original.type
        assert restored.choices_ref == original.choices_ref
        assert restored.default_ref == original.default_ref

    def test_parameter_group_roundtrip(self) -> None:
        """ParameterGroup should survive JSON roundtrip."""
        original = ParameterGroup(
            name="test",
            description="Test parameters",
            parameters=[
                Parameter(key="a", label="A", type=ParameterType.TEXT),
                Parameter(key="b", label="B", type=ParameterType.CONFIRM),
            ],
        )

        # Serialize
        json_str = original.to_json()

        # Deserialize
        data = json.loads(json_str)
        restored = ParameterGroup.from_dict(data)

        # Verify
        assert restored.name == original.name
        assert len(restored.parameters) == len(original.parameters)
        assert restored.parameters[0].key == "a"
        assert restored.parameters[1].key == "b"


class TestSchemaUtilities:
    """Tests for schema utility methods."""

    def test_effective_cli_flag(self) -> None:
        """effective_cli_flag should generate correct flag names."""
        # With explicit flag
        param1 = Parameter(key="region", label="Region", cli_flag="--aws-region")
        assert param1.effective_cli_flag == "--aws-region"

        # Without explicit flag (auto-generated)
        param2 = Parameter(key="output_dir", label="Output Dir")
        assert param2.effective_cli_flag == "--output-dir"

    def test_effective_env_var(self) -> None:
        """effective_env_var should generate correct env var names."""
        # With explicit env var
        param1 = Parameter(key="region", label="Region", env_var="AWS_REGION")
        assert param1.effective_env_var == "AWS_REGION"

        # Without explicit env var (auto-generated)
        param2 = Parameter(key="output_dir", label="Output Dir")
        assert param2.effective_env_var == "REPLIMAP_OUTPUT_DIR"

    def test_parameter_group_get(self) -> None:
        """ParameterGroup.get should find parameters by key."""
        group = ParameterGroup(
            name="test",
            description="Test",
            parameters=[
                Parameter(key="a", label="A"),
                Parameter(key="b", label="B"),
            ],
        )

        assert group.get("a") is not None
        assert group.get("a").label == "A"
        assert group.get("c") is None

    def test_parameter_group_keys(self) -> None:
        """ParameterGroup should list all keys correctly."""
        group = ParameterGroup(
            name="test",
            description="Test",
            parameters=[
                Parameter(key="a", label="A", required=True),
                Parameter(key="b", label="B", required=False),
                Parameter(key="c", label="C", required=True),
            ],
        )

        assert group.keys() == ["a", "b", "c"]
        assert group.required_keys() == ["a", "c"]
        assert group.optional_keys() == ["b"]
