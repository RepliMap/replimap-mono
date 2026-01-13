"""
Parameter System - Pure Data Parameter Definitions.

This module provides a schema-based parameter system that is
completely JSON-serializable (no Callable objects).

Key Components:
- ParameterType: Enum of parameter types (TEXT, SELECT, etc.)
- Parameter: Pure data class for parameter definitions
- ParameterGroup: Collection of related parameters
- ChoiceRegistry: Resolves string references to actual choices

Key Constraint: NO CALLABLE OBJECTS
- Use choices_ref: "aws:regions" instead of choices: lambda: get_regions()
- Use default_ref: "config:region" instead of default: lambda: get_config()
- Use condition_ref: "state:cache_exists" instead of condition: callable

This ensures schemas can be:
- JSON serialized for documentation generation
- Sent over API for dynamic form generation
- Validated statically
"""

from replimap.cli.params.definitions import (
    AUDIT_PARAMETERS,
    CLONE_PARAMETERS,
    COST_PARAMETERS,
    SCAN_PARAMETERS,
    export_all_schemas,
)
from replimap.cli.params.registry import ChoiceRegistry
from replimap.cli.params.schema import Parameter, ParameterGroup, ParameterType

__all__ = [
    # Schema
    "Parameter",
    "ParameterGroup",
    "ParameterType",
    # Registry
    "ChoiceRegistry",
    # Pre-defined schemas
    "SCAN_PARAMETERS",
    "CLONE_PARAMETERS",
    "AUDIT_PARAMETERS",
    "COST_PARAMETERS",
    "export_all_schemas",
]
