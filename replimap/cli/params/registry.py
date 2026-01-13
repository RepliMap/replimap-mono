"""
ChoiceRegistry - Dynamic Options Resolution.

Resolves string references in Parameter schemas to actual values.

Namespaces:
- aws:profiles → Available AWS profiles
- aws:regions → Available AWS regions
- config:* → Configuration values
- state:* → Runtime state values
- output:formats → Output format options
- audit:frameworks → Audit framework options
- audit:severity → Severity level options

Usage:
    # Register a custom provider
    ChoiceRegistry.register("custom:values", lambda: ["a", "b", "c"])

    # Resolve a reference
    regions = ChoiceRegistry.resolve("aws:regions")

    # Resolve with caching disabled
    fresh_profiles = ChoiceRegistry.resolve("aws:profiles", use_cache=False)
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

# Type alias for provider functions
Provider = Callable[[], Any]


class ChoiceRegistry:
    """
    Registry for resolving dynamic choice references.

    This is a class-level (not instance-level) registry that maps
    string references to provider functions.

    The separation of schema (string references) from resolution
    (this registry) enables:
    - JSON-serializable schemas
    - Lazy loading of expensive choices (like AWS profiles)
    - Caching of resolved values
    - Easy mocking in tests
    """

    _providers: dict[str, Provider] = {}
    _cache: dict[str, Any] = {}
    _cache_enabled: bool = True

    @classmethod
    def register(cls, key: str, provider: Provider) -> None:
        """
        Register a choice provider.

        Args:
            key: Reference key (e.g., "aws:regions")
            provider: Callable that returns the choices
        """
        cls._providers[key] = provider
        # Clear cache for this key
        if key in cls._cache:
            del cls._cache[key]

    @classmethod
    def resolve(cls, key: str, use_cache: bool = True) -> Any:
        """
        Resolve a reference to actual values.

        Args:
            key: Reference key (e.g., "aws:regions")
            use_cache: Whether to use cached values

        Returns:
            Resolved value from provider

        Raises:
            KeyError: If reference is not registered
        """
        # Check cache first
        if use_cache and cls._cache_enabled and key in cls._cache:
            return cls._cache[key]

        # Look up provider
        if key not in cls._providers:
            raise KeyError(f"No provider registered for '{key}'")

        # Resolve
        provider = cls._providers[key]
        value = provider()

        # Cache result
        if use_cache and cls._cache_enabled:
            cls._cache[key] = value

        return value

    @classmethod
    def resolve_or_default(cls, key: str, default: Any = None) -> Any:
        """
        Resolve a reference, returning default if not found.

        Args:
            key: Reference key
            default: Value to return if not found

        Returns:
            Resolved value or default
        """
        try:
            return cls.resolve(key)
        except KeyError:
            return default

    @classmethod
    def is_registered(cls, key: str) -> bool:
        """Check if a reference is registered."""
        return key in cls._providers

    @classmethod
    def clear_cache(cls) -> None:
        """Clear all cached values."""
        cls._cache.clear()

    @classmethod
    def clear_cache_for(cls, key: str) -> None:
        """Clear cached value for a specific key."""
        if key in cls._cache:
            del cls._cache[key]

    @classmethod
    def disable_cache(cls) -> None:
        """Disable caching (useful for testing)."""
        cls._cache_enabled = False
        cls._cache.clear()

    @classmethod
    def enable_cache(cls) -> None:
        """Enable caching."""
        cls._cache_enabled = True

    @classmethod
    def list_providers(cls) -> list[str]:
        """List all registered provider keys."""
        return list(cls._providers.keys())


# ============================================================================
# BUILT-IN PROVIDERS
# ============================================================================


def _get_aws_profiles() -> list[str]:
    """Get available AWS profiles."""
    try:
        import boto3

        session = boto3.Session()
        profiles = session.available_profiles
        return list(profiles) if profiles else ["default"]
    except Exception:
        return ["default"]


def _get_aws_regions() -> list[str]:
    """Get commonly used AWS regions."""
    return [
        "us-east-1",
        "us-east-2",
        "us-west-1",
        "us-west-2",
        "eu-west-1",
        "eu-west-2",
        "eu-west-3",
        "eu-central-1",
        "eu-north-1",
        "ap-southeast-1",
        "ap-southeast-2",
        "ap-northeast-1",
        "ap-northeast-2",
        "ap-south-1",
        "sa-east-1",
        "ca-central-1",
        "me-south-1",
        "af-south-1",
    ]


def _get_output_formats() -> list[str]:
    """Get available output formats for IaC generation."""
    return [
        "terraform",
        "cloudformation",
        "pulumi",
    ]


def _get_cli_output_formats() -> list[str]:
    """Get available CLI output formats."""
    return [
        "text",
        "json",
        "table",
        "quiet",
    ]


def _get_audit_frameworks() -> list[str]:
    """Get available audit frameworks."""
    return [
        "CIS",
        "SOC2",
        "PCI-DSS",
        "HIPAA",
        "GDPR",
        "NIST",
        "ISO27001",
    ]


def _get_audit_severity() -> list[str]:
    """Get audit severity levels."""
    return [
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL",
    ]


def _get_report_formats() -> list[str]:
    """Get available report formats."""
    return [
        "console",
        "html",
        "json",
        "csv",
        "markdown",
        "sarif",
    ]


def _get_terraform_versions() -> list[str]:
    """Get supported Terraform versions."""
    return [
        "1.5",
        "1.6",
        "1.7",
        "1.8",
        "1.9",
    ]


def _get_backend_types() -> list[str]:
    """Get Terraform backend types."""
    return [
        "local",
        "s3",
        "gcs",
        "azurerm",
    ]


def _get_true() -> bool:
    """Return True (for condition resolution)."""
    return True


def _get_false() -> bool:
    """Return False (for condition resolution)."""
    return False


def _register_builtins() -> None:
    """Register all built-in providers."""
    # AWS
    ChoiceRegistry.register("aws:profiles", _get_aws_profiles)
    ChoiceRegistry.register("aws:regions", _get_aws_regions)

    # Output
    ChoiceRegistry.register("output:formats", _get_cli_output_formats)
    ChoiceRegistry.register("output:iac_formats", _get_output_formats)
    ChoiceRegistry.register("output:report_formats", _get_report_formats)

    # Audit
    ChoiceRegistry.register("audit:frameworks", _get_audit_frameworks)
    ChoiceRegistry.register("audit:severity", _get_audit_severity)

    # Terraform
    ChoiceRegistry.register("terraform:versions", _get_terraform_versions)
    ChoiceRegistry.register("terraform:backends", _get_backend_types)

    # Conditions (for state-based visibility)
    ChoiceRegistry.register("condition:true", _get_true)
    ChoiceRegistry.register("condition:false", _get_false)


# Register built-ins on module load
_register_builtins()


__all__ = [
    "ChoiceRegistry",
]
