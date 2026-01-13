"""
Global Configuration Context and Environment Detection.

Provides unified access to configuration with source tracking,
and execution environment detection for CI/interactive mode handling.

Configuration Hierarchy (highest to lowest priority):
1. CLI arguments
2. Environment variables
3. Config file (~/.replimap/config.toml)
4. Default values
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from replimap.cli.config import ConfigManager


class ExecutionEnvironment(Enum):
    """Execution environment type."""

    INTERACTIVE = "interactive"  # Has TTY, can prompt user
    CI = "ci"  # CI/CD environment, no TTY
    NON_INTERACTIVE = "non_interactive"  # No TTY but not CI


class ConfigSource(Enum):
    """Configuration value source."""

    CLI = "cli"  # Command line argument
    ENVIRONMENT = "env"  # Environment variable
    CONFIG_FILE = "config"  # Configuration file
    DEFAULT = "default"  # Default value


@dataclass
class ConfigValue:
    """A configuration value with its source."""

    value: Any
    source: ConfigSource

    def __str__(self) -> str:
        return f"{self.value} (from {self.source.value})"


class EnvironmentDetector:
    """
    Detects the current execution environment.

    Supports detection of 15+ CI platforms including GitHub Actions,
    GitLab CI, CircleCI, Jenkins, and more.
    """

    # Specific CI platforms first, generic CI last (order matters for detection)
    CI_INDICATORS: dict[str, str] = {
        "GITHUB_ACTIONS": "GitHub Actions",
        "GITLAB_CI": "GitLab CI",
        "CIRCLECI": "CircleCI",
        "JENKINS_URL": "Jenkins",
        "TRAVIS": "Travis CI",
        "BUILDKITE": "Buildkite",
        "CODEBUILD_BUILD_ID": "AWS CodeBuild",
        "TF_BUILD": "Azure Pipelines",
        "TEAMCITY_VERSION": "TeamCity",
        "BITBUCKET_BUILD_NUMBER": "Bitbucket Pipelines",
        "DRONE": "Drone CI",
        "BUDDY": "Buddy CI",
        "APPVEYOR": "AppVeyor",
        "SEMAPHORE": "Semaphore CI",
        "HARNESS_BUILD_ID": "Harness CI",
        "RENDER": "Render",
        "CI": "Generic CI",  # Generic fallback - must be last
    }

    @classmethod
    def detect(cls) -> ExecutionEnvironment:
        """Detect the current execution environment."""
        if cls.is_ci():
            return ExecutionEnvironment.CI
        if cls.has_tty():
            return ExecutionEnvironment.INTERACTIVE
        return ExecutionEnvironment.NON_INTERACTIVE

    @classmethod
    def is_ci(cls) -> bool:
        """Check if running in a CI environment."""
        return any(os.environ.get(var) for var in cls.CI_INDICATORS)

    @classmethod
    def has_tty(cls) -> bool:
        """Check if running in an interactive terminal."""
        try:
            return sys.stdin.isatty() and sys.stdout.isatty()
        except Exception:
            return False

    @classmethod
    def get_ci_name(cls) -> str | None:
        """Get the name of the CI platform, if any."""
        for var, name in cls.CI_INDICATORS.items():
            if os.environ.get(var):
                return name
        return None

    @classmethod
    def is_interactive(cls) -> bool:
        """Check if user interaction is possible."""
        return cls.detect() == ExecutionEnvironment.INTERACTIVE


@dataclass
class GlobalContext:
    """
    Global configuration context with source tracking.

    Integrates with existing ConfigManager while adding:
    - Source tracking for configuration values
    - Environment detection (CI vs interactive)
    - Identity tracking for AWS operations

    Usage:
        ctx = GlobalContext.from_cli(profile="prod", region="us-east-1")
        profile = ctx.profile  # ConfigValue with source
        if ctx.is_interactive():
            # Can prompt user
            pass
    """

    # Core settings with source tracking
    profile: ConfigValue = field(
        default_factory=lambda: ConfigValue("default", ConfigSource.DEFAULT)
    )
    region: ConfigValue = field(
        default_factory=lambda: ConfigValue(None, ConfigSource.DEFAULT)
    )
    output_dir: ConfigValue = field(
        default_factory=lambda: ConfigValue("./output", ConfigSource.DEFAULT)
    )

    # Behavior settings
    verbose: bool = False
    debug: bool = False
    non_interactive: bool = False
    dry_run: bool = False

    # Environment
    environment: ExecutionEnvironment = field(
        default_factory=EnvironmentDetector.detect
    )
    ci_name: str | None = field(default_factory=EnvironmentDetector.get_ci_name)

    # Paths
    config_path: Path = field(
        default_factory=lambda: Path.home() / ".replimap" / "config.toml"
    )
    decisions_path: Path = field(
        default_factory=lambda: Path.home() / ".replimap" / "decisions.yaml"
    )

    # Internal
    _config_manager: ConfigManager | None = field(default=None, init=False, repr=False)

    @classmethod
    def from_cli(
        cls,
        profile: str | None = None,
        region: str | None = None,
        output: str | None = None,
        verbose: bool = False,
        debug: bool = False,
        non_interactive: bool = False,
        dry_run: bool = False,
        config_path: Path | None = None,
    ) -> GlobalContext:
        """
        Create context from CLI arguments with full hierarchy resolution.

        Resolution order for each setting:
        1. CLI argument (if provided)
        2. Environment variable
        3. Config file
        4. Default value
        """
        ctx = cls()

        # Set config path first
        if config_path:
            ctx.config_path = config_path

        # Create config manager for resolution
        ctx._config_manager = ConfigManager(
            profile=profile or "default",
            config_path=ctx.config_path,
        )

        # Resolve profile
        if profile:
            ctx.profile = ConfigValue(profile, ConfigSource.CLI)
        elif os.environ.get("AWS_PROFILE"):
            ctx.profile = ConfigValue(
                os.environ["AWS_PROFILE"], ConfigSource.ENVIRONMENT
            )
        else:
            resolved = ctx._config_manager.get("profile")
            source = cls._determine_source(ctx._config_manager, "profile")
            ctx.profile = ConfigValue(resolved or "default", source)

        # Resolve region
        if region:
            ctx.region = ConfigValue(region, ConfigSource.CLI)
        elif os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION"):
            env_region = os.environ.get("AWS_REGION") or os.environ.get(
                "AWS_DEFAULT_REGION"
            )
            ctx.region = ConfigValue(env_region, ConfigSource.ENVIRONMENT)
        else:
            resolved = ctx._config_manager.get("region")
            source = cls._determine_source(ctx._config_manager, "region")
            ctx.region = ConfigValue(resolved, source)

        # Resolve output directory
        if output:
            ctx.output_dir = ConfigValue(output, ConfigSource.CLI)
        elif os.environ.get("REPLIMAP_OUTPUT_DIR"):
            ctx.output_dir = ConfigValue(
                os.environ["REPLIMAP_OUTPUT_DIR"], ConfigSource.ENVIRONMENT
            )
        else:
            resolved = ctx._config_manager.get("output_dir")
            source = cls._determine_source(ctx._config_manager, "output_dir")
            ctx.output_dir = ConfigValue(resolved or "./output", source)

        # Set behavior flags
        ctx.verbose = verbose
        ctx.debug = debug
        ctx.dry_run = dry_run

        # Non-interactive is forced in CI
        ctx.non_interactive = non_interactive or (
            ctx.environment == ExecutionEnvironment.CI
        )

        return ctx

    @staticmethod
    def _determine_source(config_manager: ConfigManager, key: str) -> ConfigSource:
        """Determine the source of a configuration value."""
        # Force resolution and check log
        config_manager.get(key)
        if key in config_manager._resolution_log:
            source_str = config_manager._resolution_log[key].source
            if source_str == "cli":
                return ConfigSource.CLI
            if source_str.startswith("env:"):
                return ConfigSource.ENVIRONMENT
            if source_str in ("global", "profile:"):
                return ConfigSource.CONFIG_FILE
        return ConfigSource.DEFAULT

    def is_interactive(self) -> bool:
        """Check if user interaction is allowed."""
        if self.non_interactive:
            return False
        return self.environment == ExecutionEnvironment.INTERACTIVE

    def is_explicit_profile(self) -> bool:
        """Check if profile was explicitly specified (CLI or ENV)."""
        return self.profile.source in (ConfigSource.CLI, ConfigSource.ENVIRONMENT)

    def is_ci(self) -> bool:
        """Check if running in CI environment."""
        return self.environment == ExecutionEnvironment.CI

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get a configuration value using the internal ConfigManager."""
        if self._config_manager:
            return self._config_manager.get(key, default)
        return default

    def to_dict(self) -> dict[str, Any]:
        """Convert context to dictionary for serialization."""
        return {
            "profile": self.profile.value,
            "profile_source": self.profile.source.value,
            "region": self.region.value,
            "region_source": self.region.source.value,
            "output_dir": self.output_dir.value,
            "environment": self.environment.value,
            "ci_name": self.ci_name,
            "verbose": self.verbose,
            "debug": self.debug,
            "non_interactive": self.non_interactive,
            "dry_run": self.dry_run,
        }


__all__ = [
    "ConfigSource",
    "ConfigValue",
    "EnvironmentDetector",
    "ExecutionEnvironment",
    "GlobalContext",
]
