"""
Lightweight Field Hints - 5KB alternative to 500MB provider schema.

Uses a curated list of field hints instead of full provider schema
for determining which fields should be extracted as Terraform variables.

Key Features:
- 5KB hints file vs 500MB provider schema
- Covers 95% of common scenarios
- Context-specific overrides for edge cases
- Conservative fallback for unknown fields
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class FieldHint:
    """
    Hint for how to handle a field during extraction.

    Attributes:
        action: What to do with the field ("extract", "keep", "ask")
        reason: Human-readable explanation
    """

    action: str  # "extract" | "keep" | "ask"
    reason: str

    @property
    def should_extract(self) -> bool:
        """Check if field should be extracted as variable."""
        return self.action == "extract"

    @property
    def should_keep(self) -> bool:
        """Check if field should be kept hardcoded."""
        return self.action == "keep"

    @property
    def needs_decision(self) -> bool:
        """Check if field needs user decision."""
        return self.action == "ask"


class LightweightFieldHints:
    """
    Lightweight field hints registry.

    Loads a small YAML file with curated hints for common fields
    instead of requiring the full 500MB Terraform provider schema.

    Usage:
        hints = LightweightFieldHints()

        # Get hint for a field
        hint = hints.get_hint("vpc_id")
        if hint.should_extract:
            # Extract as variable
            pass

        # With resource context for overrides
        hint = hints.get_hint("cidr_block", resource_type="aws_vpc")
        # Returns "extract" due to context override
    """

    DEFAULT_HINTS_PATH = Path(__file__).parent.parent / "data" / "field_hints.yaml"

    def __init__(self, hints_path: Path | None = None):
        """
        Initialize LightweightFieldHints.

        Args:
            hints_path: Path to hints YAML file (uses bundled default if not specified)
        """
        self._hints_path = hints_path or self.DEFAULT_HINTS_PATH
        self._extract: set[str] = set()
        self._keep: set[str] = set()
        self._ask: set[str] = set()
        self._overrides: dict[str, dict[str, str]] = {}
        self._fallback: dict[str, str] = {}
        self._loaded = False

        self._load()

    def _load(self) -> None:
        """Load hints from YAML file."""
        if self._loaded:
            return

        if not self._hints_path.exists():
            # Use built-in defaults if file doesn't exist
            self._use_builtin_defaults()
            self._loaded = True
            return

        try:
            with open(self._hints_path) as f:
                data = yaml.safe_load(f) or {}

            self._extract = set(data.get("extract", []))
            self._keep = set(data.get("keep", []))
            self._ask = set(data.get("ask", []))
            self._overrides = data.get("context_overrides", {})
            self._fallback = data.get("fallback", {})
            self._loaded = True

        except (yaml.YAMLError, OSError):
            self._use_builtin_defaults()
            self._loaded = True

    def _use_builtin_defaults(self) -> None:
        """Use built-in default hints when file is unavailable."""
        # Resource IDs - always extract (environment-specific)
        self._extract = {
            "vpc_id",
            "subnet_id",
            "subnet_ids",
            "security_group_id",
            "security_group_ids",
            "instance_id",
            "db_subnet_group_name",
            "target_group_arn",
            "load_balancer_arn",
            "role_arn",
            "execution_role_arn",
            "task_role_arn",
            "kms_key_id",
            "kms_key_arn",
            "certificate_arn",
            "hosted_zone_id",
            "zone_id",
            "cluster_identifier",
            "ami",
            "image_id",
            "account_id",
        }

        # Standard values - always keep hardcoded
        self._keep = {
            "port",
            "from_port",
            "to_port",
            "protocol",
            "type",
            "engine",
            "engine_version",
            "enabled",
            "encrypted",
            "multi_az",
            "publicly_accessible",
        }

        # Context-dependent - ask user
        self._ask = {
            "cidr_block",
            "instance_type",
            "instance_class",
            "allocated_storage",
            "volume_size",
            "name",
            "bucket",
        }

        # Context overrides
        self._overrides = {
            "aws_vpc": {"cidr_block": "extract"},
            "aws_subnet": {"cidr_block": "extract", "availability_zone": "extract"},
            "aws_security_group": {"cidr_blocks": "keep"},
            "aws_security_group_rule": {"cidr_blocks": "keep"},
        }

        # Fallback behavior
        self._fallback = {
            "unknown_field": "keep",
            "unknown_resource": "ask",
        }

    def get_hint(
        self,
        field_name: str,
        resource_type: str | None = None,
    ) -> FieldHint:
        """
        Get extraction hint for a field.

        Args:
            field_name: Field name (e.g., "vpc_id", "from_port")
            resource_type: Optional resource type for context overrides

        Returns:
            FieldHint with action and reason
        """
        if not self._loaded:
            self._load()

        # Clean field name (remove array indices like "ingress.0.cidr_blocks")
        clean = self._clean_field_name(field_name)

        # Check context overrides first (most specific)
        if resource_type and resource_type in self._overrides:
            override = self._overrides[resource_type].get(clean)
            if override:
                return FieldHint(
                    action=override,
                    reason=f"Context override for {resource_type}.{clean}",
                )

        # Check main lists
        if clean in self._extract:
            return FieldHint(
                action="extract",
                reason=f"Field '{clean}' typically varies between environments",
            )

        if clean in self._keep:
            return FieldHint(
                action="keep",
                reason=f"Field '{clean}' is typically static across environments",
            )

        if clean in self._ask:
            return FieldHint(
                action="ask",
                reason=f"Field '{clean}' may vary - user decision needed",
            )

        # Fallback behavior
        fallback_action = self._fallback.get("unknown_field", "keep")
        return FieldHint(
            action=fallback_action,
            reason=f"Unknown field '{clean}' - using conservative fallback",
        )

    def _clean_field_name(self, field_name: str) -> str:
        """
        Clean field name by removing array indices and nested paths.

        Examples:
            "ingress.0.cidr_blocks" → "cidr_blocks"
            "tags.Name" → "Name"
            "vpc_id" → "vpc_id"
        """
        parts = field_name.split(".")

        # Remove numeric indices
        parts = [p for p in parts if not p.isdigit()]

        # Return the last meaningful part
        return parts[-1] if parts else field_name

    def get_all_extract_fields(self) -> set[str]:
        """Get all fields marked for extraction."""
        return set(self._extract)

    def get_all_keep_fields(self) -> set[str]:
        """Get all fields marked to keep hardcoded."""
        return set(self._keep)

    def get_all_ask_fields(self) -> set[str]:
        """Get all fields that need user decision."""
        return set(self._ask)

    def get_overrides_for_resource(
        self,
        resource_type: str,
    ) -> dict[str, str]:
        """Get all overrides for a specific resource type."""
        return dict(self._overrides.get(resource_type, {}))

    def add_custom_hint(
        self,
        field_name: str,
        action: str,
        resource_type: str | None = None,
    ) -> None:
        """
        Add a custom hint (runtime override).

        Args:
            field_name: Field name
            action: Action ("extract", "keep", "ask")
            resource_type: Optional resource type for context-specific hint
        """
        if resource_type:
            if resource_type not in self._overrides:
                self._overrides[resource_type] = {}
            self._overrides[resource_type][field_name] = action
        else:
            # Add to appropriate set
            # Remove from other sets first
            self._extract.discard(field_name)
            self._keep.discard(field_name)
            self._ask.discard(field_name)

            if action == "extract":
                self._extract.add(field_name)
            elif action == "keep":
                self._keep.add(field_name)
            elif action == "ask":
                self._ask.add(field_name)

    def to_dict(self) -> dict[str, Any]:
        """Convert current hints to dictionary (for debugging/export)."""
        return {
            "extract": sorted(self._extract),
            "keep": sorted(self._keep),
            "ask": sorted(self._ask),
            "context_overrides": self._overrides,
            "fallback": self._fallback,
        }


def create_field_hints(hints_path: Path | None = None) -> LightweightFieldHints:
    """
    Factory function to create LightweightFieldHints.

    Args:
        hints_path: Optional custom path to hints file

    Returns:
        Configured LightweightFieldHints instance
    """
    return LightweightFieldHints(hints_path)


__all__ = [
    "FieldHint",
    "LightweightFieldHints",
    "create_field_hints",
]
