"""
Parameter Schema - Pure Data Definitions.

CRITICAL CONSTRAINT: NO CALLABLES!
- choices_ref: str (NOT choices: Callable)
- default_ref: str (NOT default: Callable)
- condition_ref: str (NOT condition: Callable)

This ensures Schema can be:
- JSON serialized for API transport
- Used for automatic documentation generation
- Validated without execution

Examples:
    # CORRECT - using string references
    Parameter(
        key="region",
        type=ParameterType.SELECT,
        choices_ref="aws:regions",  # Resolved by ChoiceRegistry
        default_ref="config:region",
    )

    # WRONG - using callables (will break serialization)
    Parameter(
        key="region",
        type=ParameterType.SELECT,
        choices=lambda: get_regions(),  # ❌ NOT ALLOWED
        default=lambda: get_default_region(),  # ❌ NOT ALLOWED
    )
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ParameterType(str, Enum):
    """Types of parameters for interactive prompts."""

    TEXT = "text"  # Free-form text input
    SELECT = "select"  # Single selection from choices
    MULTISELECT = "multiselect"  # Multiple selections from choices
    CONFIRM = "confirm"  # Yes/No confirmation
    INTEGER = "integer"  # Integer number input
    FLOAT = "float"  # Floating point number input
    PATH = "path"  # File/directory path input
    PASSWORD = "password"  # Hidden text input (for sensitive data)


@dataclass
class Parameter:
    """
    A pure-data parameter definition.

    This class defines a parameter that can be used for:
    - CLI argument generation
    - Interactive prompt rendering
    - Documentation generation
    - API schema export

    All fields are JSON-serializable - no Callable objects allowed.

    Attributes:
        key: Parameter identifier (e.g., "region", "output_format")
        label: Human-readable label for prompts
        type: Parameter type (TEXT, SELECT, etc.)
        help_text: Description shown in help/prompts
        choices_ref: String reference to choices provider (e.g., "aws:regions")
        choices_static: Static list of choices (mutually exclusive with choices_ref)
        default_ref: String reference to default value provider (e.g., "config:region")
        default_static: Static default value (mutually exclusive with default_ref)
        required: Whether the parameter is required
        condition_ref: String reference to condition that must be true to show parameter
        cli_flag: CLI flag name override (defaults to --key)
        cli_short: Short CLI flag (e.g., "-r" for region)
        env_var: Environment variable name (auto-generated if not specified)
        validators: List of validator references (e.g., "validators:not_empty")
    """

    key: str
    label: str
    type: ParameterType = ParameterType.TEXT
    help_text: str = ""
    # Choices - use ONLY ONE of these
    choices_ref: str | None = None  # e.g., "aws:regions"
    choices_static: list[str] | None = None
    # Default - use ONLY ONE of these
    default_ref: str | None = None  # e.g., "config:region"
    default_static: Any = None
    # Behavior
    required: bool = True
    condition_ref: str | None = None  # e.g., "state:cache_exists"
    # CLI integration
    cli_flag: str | None = None  # Defaults to --{key}
    cli_short: str | None = None  # e.g., "-r"
    env_var: str | None = None  # e.g., "REPLIMAP_REGION"
    # Validation
    validators: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate parameter definition."""
        # Ensure type is enum
        if isinstance(self.type, str):
            self.type = ParameterType(self.type)

        # Validate mutually exclusive fields
        if self.choices_ref and self.choices_static:
            raise ValueError(
                f"Parameter '{self.key}': choices_ref and choices_static are "
                f"mutually exclusive. Use only one."
            )

        if self.default_ref and self.default_static is not None:
            raise ValueError(
                f"Parameter '{self.key}': default_ref and default_static are "
                f"mutually exclusive. Use only one."
            )

    @property
    def effective_cli_flag(self) -> str:
        """Get the effective CLI flag name."""
        if self.cli_flag:
            return self.cli_flag
        return f"--{self.key.replace('_', '-')}"

    @property
    def effective_env_var(self) -> str:
        """Get the effective environment variable name."""
        if self.env_var:
            return self.env_var
        return f"REPLIMAP_{self.key.upper().replace('.', '_')}"

    def to_dict(self) -> dict[str, Any]:
        """
        Convert to JSON-serializable dict.

        Returns:
            Dict suitable for JSON serialization
        """
        result: dict[str, Any] = {
            "key": self.key,
            "label": self.label,
            "type": self.type.value,
            "help_text": self.help_text,
            "required": self.required,
        }

        # Only include non-None optional fields
        if self.choices_ref:
            result["choices_ref"] = self.choices_ref
        if self.choices_static:
            result["choices_static"] = self.choices_static
        if self.default_ref:
            result["default_ref"] = self.default_ref
        if self.default_static is not None:
            result["default_static"] = self.default_static
        if self.condition_ref:
            result["condition_ref"] = self.condition_ref
        if self.cli_flag:
            result["cli_flag"] = self.cli_flag
        if self.cli_short:
            result["cli_short"] = self.cli_short
        if self.env_var:
            result["env_var"] = self.env_var
        if self.validators:
            result["validators"] = self.validators

        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Parameter:
        """
        Create Parameter from dict.

        Args:
            data: Dict loaded from JSON

        Returns:
            Parameter instance
        """
        return cls(
            key=data["key"],
            label=data["label"],
            type=ParameterType(data.get("type", "text")),
            help_text=data.get("help_text", ""),
            choices_ref=data.get("choices_ref"),
            choices_static=data.get("choices_static"),
            default_ref=data.get("default_ref"),
            default_static=data.get("default_static"),
            required=data.get("required", True),
            condition_ref=data.get("condition_ref"),
            cli_flag=data.get("cli_flag"),
            cli_short=data.get("cli_short"),
            env_var=data.get("env_var"),
            validators=data.get("validators", []),
        )

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class ParameterGroup:
    """
    A group of related parameters.

    Used to organize parameters for a command or feature.

    Attributes:
        name: Group identifier (e.g., "scan", "clone")
        description: Human-readable description
        parameters: List of parameters in the group
    """

    name: str
    description: str
    parameters: list[Parameter] = field(default_factory=list)

    def get(self, key: str) -> Parameter | None:
        """
        Get a parameter by key.

        Args:
            key: Parameter key to find

        Returns:
            Parameter if found, None otherwise
        """
        for param in self.parameters:
            if param.key == key:
                return param
        return None

    def keys(self) -> list[str]:
        """Get all parameter keys."""
        return [p.key for p in self.parameters]

    def required_keys(self) -> list[str]:
        """Get keys of required parameters."""
        return [p.key for p in self.parameters if p.required]

    def optional_keys(self) -> list[str]:
        """Get keys of optional parameters."""
        return [p.key for p in self.parameters if not p.required]

    def to_dict(self) -> dict[str, Any]:
        """
        Convert to JSON-serializable dict.

        Returns:
            Dict suitable for JSON serialization
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": [p.to_dict() for p in self.parameters],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ParameterGroup:
        """
        Create ParameterGroup from dict.

        Args:
            data: Dict loaded from JSON

        Returns:
            ParameterGroup instance
        """
        return cls(
            name=data["name"],
            description=data["description"],
            parameters=[Parameter.from_dict(p) for p in data.get("parameters", [])],
        )

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


def validate_schema_purity(param: Parameter) -> list[str]:
    """
    Validate that a parameter contains no callable objects.

    This is used by tests to ensure schema purity.

    Args:
        param: Parameter to validate

    Returns:
        List of validation errors (empty if valid)
    """
    errors: list[str] = []

    # Check for callable in any field
    if callable(param.choices_ref):
        errors.append(f"Parameter '{param.key}': choices_ref is callable")
    if callable(param.choices_static):
        errors.append(f"Parameter '{param.key}': choices_static is callable")
    if callable(param.default_ref):
        errors.append(f"Parameter '{param.key}': default_ref is callable")
    if callable(param.default_static):
        errors.append(f"Parameter '{param.key}': default_static is callable")
    if callable(param.condition_ref):
        errors.append(f"Parameter '{param.key}': condition_ref is callable")

    return errors


def validate_group_purity(group: ParameterGroup) -> list[str]:
    """
    Validate that all parameters in a group are pure.

    Args:
        group: ParameterGroup to validate

    Returns:
        List of validation errors (empty if valid)
    """
    errors: list[str] = []
    for param in group.parameters:
        errors.extend(validate_schema_purity(param))
    return errors


__all__ = [
    "Parameter",
    "ParameterGroup",
    "ParameterType",
    "validate_group_purity",
    "validate_schema_purity",
]
