"""
ConfigManager - Profile-Aware Configuration Management.

Configuration Resolution Priority (highest to lowest):
1. CLI Flags (--region us-west-2)
2. Environment Variables (REPLIMAP_REGION)
3. Profile Override ([profiles.prod])
4. Global Config ([global])
5. Hardcoded Defaults

TOML Structure Example:
    [global]
    region = "us-east-1"
    output_format = "terraform"

    [profiles.prod]
    region = "us-east-1"
    output_dir = "./outputs/prod"

    [profiles.prod.scan]
    parallel_scanners = 8

    [profiles.dev]
    region = "us-west-2"
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TypeVar

T = TypeVar("T")

# Default configuration values (lowest priority)
DEFAULTS: dict[str, Any] = {
    # AWS defaults
    "region": "us-east-1",
    "profile": "default",
    # Output defaults
    "output_format": "terraform",
    "output_dir": "./output",
    # Scan defaults
    "scan.parallel_scanners": 4,
    "scan.use_cache": False,
    "scan.cache_ttl_hours": 24,
    "scan.skip_services": [],
    # Clone defaults
    "clone.backend_type": "local",
    "clone.generate_imports": True,
    "clone.terraform_version": "1.5",
    # Audit defaults
    "audit.frameworks": ["CIS"],
    "audit.min_severity": "LOW",
    "audit.inline_comments": True,
    # Cost defaults
    "cost.ri_aware": False,
    "cost.show_breakdown": True,
}

# Environment variable prefix
ENV_PREFIX = "REPLIMAP"


@dataclass
class ConfigResolution:
    """Tracks how a configuration value was resolved."""

    key: str
    value: Any
    source: str  # "cli", "env", "profile.{name}", "global", "default"

    def __str__(self) -> str:
        return f"{self.key} = {self.value!r} (from {self.source})"


@dataclass
class ConfigManager:
    """
    Profile-aware configuration manager.

    Resolves configuration values by searching through multiple sources
    in order of priority.

    Attributes:
        profile: Active profile name
        cli_overrides: CLI flag values (highest priority)
        config_path: Path to config.toml file
    """

    profile: str = "default"
    cli_overrides: dict[str, Any] = field(default_factory=dict)
    config_path: Path = field(
        default_factory=lambda: Path.home() / ".replimap" / "config.toml"
    )
    _config: dict[str, Any] = field(default_factory=dict, init=False, repr=False)
    _resolution_log: dict[str, ConfigResolution] = field(
        default_factory=dict, init=False, repr=False
    )
    _loaded: bool = field(default=False, init=False, repr=False)

    def __post_init__(self) -> None:
        """Load configuration from file if it exists."""
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from TOML file."""
        if self._loaded:
            return

        if self.config_path.exists():
            try:
                # Use tomllib (Python 3.11+) or tomli as fallback
                try:
                    import tomllib
                except ImportError:
                    import tomli as tomllib  # type: ignore[import-not-found]

                with open(self.config_path, "rb") as f:
                    self._config = tomllib.load(f)
            except Exception:
                # Silently use empty config on parse error
                self._config = {}
        else:
            self._config = {}

        self._loaded = True

    def get(
        self,
        key: str,
        default: T | None = None,
        value_type: type[T] | None = None,
    ) -> T | Any:
        """
        Get a configuration value with priority resolution.

        Resolution order:
        1. CLI overrides (--key value)
        2. Environment (REPLIMAP_KEY)
        3. Profile config ([profiles.{profile}])
        4. Global config ([global])
        5. Hardcoded defaults
        6. Provided default parameter

        Args:
            key: Configuration key (e.g., "region" or "scan.parallel_scanners")
            default: Fallback value if not found anywhere
            value_type: Optional type for automatic conversion

        Returns:
            Resolved configuration value
        """
        # 1. CLI overrides (highest priority)
        if key in self.cli_overrides:
            value = self.cli_overrides[key]
            self._log_resolution(key, value, "cli")
            return self._convert_type(value, value_type)

        # 2. Environment variable
        env_key = self._key_to_env(key)
        env_value = os.environ.get(env_key)
        if env_value is not None:
            value = self._parse_env_value(env_value, value_type)
            self._log_resolution(key, value, f"env:{env_key}")
            return value

        # 3. Profile-specific config
        if self.profile != "default":
            profile_value = self._get_nested(
                self._config, f"profiles.{self.profile}.{key}"
            )
            if profile_value is not None:
                self._log_resolution(key, profile_value, f"profile:{self.profile}")
                return self._convert_type(profile_value, value_type)

        # 4. Global config
        global_value = self._get_nested(self._config, f"global.{key}")
        if global_value is not None:
            self._log_resolution(key, global_value, "global")
            return self._convert_type(global_value, value_type)

        # 5. Hardcoded defaults
        if key in DEFAULTS:
            value = DEFAULTS[key]
            self._log_resolution(key, value, "default")
            return self._convert_type(value, value_type)

        # 6. Provided default
        if default is not None:
            self._log_resolution(key, default, "parameter_default")
            return default

        return None

    def get_all_for_command(self, command: str) -> dict[str, Any]:
        """
        Get all configuration values for a specific command.

        Args:
            command: Command name (e.g., "scan", "clone", "audit")

        Returns:
            Dict of all config values for the command
        """
        result: dict[str, Any] = {}
        prefix = f"{command}."

        # Collect from defaults
        for key, value in DEFAULTS.items():
            if key.startswith(prefix):
                result[key[len(prefix) :]] = value

        # Override from global config
        global_cmd = self._get_nested(self._config, f"global.{command}")
        if isinstance(global_cmd, dict):
            result.update(global_cmd)

        # Override from profile config
        if self.profile != "default":
            profile_cmd = self._get_nested(
                self._config, f"profiles.{self.profile}.{command}"
            )
            if isinstance(profile_cmd, dict):
                result.update(profile_cmd)

        # Override from CLI flags
        for key, value in self.cli_overrides.items():
            if key.startswith(prefix):
                result[key[len(prefix) :]] = value

        return result

    def explain(self, key: str) -> str:
        """
        Explain where a configuration value came from.

        Args:
            key: Configuration key to explain

        Returns:
            Human-readable explanation string
        """
        # Force resolution to populate log
        self.get(key)

        if key in self._resolution_log:
            return str(self._resolution_log[key])

        return f"{key} = None (not configured)"

    def explain_all(self) -> list[str]:
        """Get explanations for all resolved values."""
        return [str(r) for r in self._resolution_log.values()]

    def to_display_dict(self) -> dict[str, Any]:
        """
        Get configuration for display (e.g., `replimap config show`).

        Returns:
            Dict suitable for display, including resolution sources
        """
        display: dict[str, Any] = {
            "active_profile": self.profile,
            "config_file": str(self.config_path),
            "config_exists": self.config_path.exists(),
            "resolved_values": {},
            "sources": {},
        }

        # Resolve common keys
        common_keys = [
            "region",
            "profile",
            "output_format",
            "output_dir",
            "scan.parallel_scanners",
            "scan.use_cache",
            "audit.frameworks",
            "cost.ri_aware",
        ]

        for key in common_keys:
            value = self.get(key)
            display["resolved_values"][key] = value
            if key in self._resolution_log:
                display["sources"][key] = self._resolution_log[key].source

        return display

    def set_cli_override(self, key: str, value: Any) -> None:
        """
        Set a CLI override value.

        Args:
            key: Configuration key
            value: Override value (None values are ignored)
        """
        if value is not None:
            self.cli_overrides[key] = value

    def _key_to_env(self, key: str) -> str:
        """
        Convert config key to environment variable name.

        Examples:
            "region" → "REPLIMAP_REGION"
            "scan.parallel_scanners" → "REPLIMAP_SCAN_PARALLEL_SCANNERS"
        """
        normalized = key.replace(".", "_").upper()
        return f"{ENV_PREFIX}_{normalized}"

    def _parse_env_value(
        self,
        value: str,
        value_type: type[T] | None = None,
    ) -> T | Any:
        """
        Parse environment variable value with type inference.

        Args:
            value: Raw string value from environment
            value_type: Optional target type

        Returns:
            Parsed value
        """
        # Handle explicit type conversion
        if value_type is not None:
            return self._convert_type(value, value_type)

        # Auto-detect type
        lower = value.lower()

        # Boolean
        if lower in ("true", "yes", "1", "on"):
            return True
        if lower in ("false", "no", "0", "off"):
            return False

        # Integer
        try:
            return int(value)
        except ValueError:
            pass

        # Float
        try:
            return float(value)
        except ValueError:
            pass

        # List (comma-separated)
        if "," in value:
            return [item.strip() for item in value.split(",")]

        return value

    def _convert_type(self, value: Any, value_type: type[T] | None) -> T | Any:
        """Convert value to specified type."""
        if value_type is None or value is None:
            return value

        if value_type is bool:
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                return value.lower() in ("true", "yes", "1", "on")
            return bool(value)

        if value_type is int:
            return int(value)

        if value_type is float:
            return float(value)

        if value_type is list:
            if isinstance(value, list):
                return value
            if isinstance(value, str):
                return [item.strip() for item in value.split(",")]
            return [value]

        return value_type(value)

    def _get_nested(self, data: dict[str, Any], key_path: str) -> Any:
        """
        Get nested value from dict using dot notation.

        Args:
            data: Source dictionary
            key_path: Dot-separated path (e.g., "profiles.prod.scan.parallel")

        Returns:
            Value at path or None if not found
        """
        parts = key_path.split(".")
        current: Any = data

        for part in parts:
            if not isinstance(current, dict):
                return None
            if part not in current:
                return None
            current = current[part]

        return current

    def _log_resolution(self, key: str, value: Any, source: str) -> None:
        """Log how a value was resolved."""
        self._resolution_log[key] = ConfigResolution(
            key=key, value=value, source=source
        )


def create_config_manager(
    profile: str = "default",
    cli_overrides: dict[str, Any] | None = None,
    config_path: Path | None = None,
) -> ConfigManager:
    """
    Factory function to create a ConfigManager.

    Args:
        profile: Active profile name
        cli_overrides: CLI flag values
        config_path: Custom config file path

    Returns:
        Configured ConfigManager instance
    """
    return ConfigManager(
        profile=profile,
        cli_overrides=cli_overrides or {},
        config_path=config_path or Path.home() / ".replimap" / "config.toml",
    )


__all__ = [
    "ConfigManager",
    "ConfigResolution",
    "DEFAULTS",
    "create_config_manager",
]
