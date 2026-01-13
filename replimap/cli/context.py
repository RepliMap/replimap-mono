"""
GlobalContext - Unified CLI Context.

Integrates all V3 managers into a single context object that is
injected into every command via Typer's callback mechanism.

Contains:
- config: ConfigManager (profile-aware configuration)
- state: StateManager (runtime state)
- output: OutputManager (stdout/stderr separation)
- profile: str (current AWS profile)
- region: str (current AWS region)

Usage:
    @app.command()
    def my_command(ctx: typer.Context):
        output = ctx.obj.output
        config = ctx.obj.config
        state = ctx.obj.state

        output.progress("Working...")
        value = config.get("some.key")
        state.update(last_command="my_command")
        output.present({"result": "success"})
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from replimap.cli.config import ConfigManager, create_config_manager
from replimap.cli.output import OutputFormat, OutputManager, create_output_manager
from replimap.cli.state import StateManager, create_state_manager

if TYPE_CHECKING:
    import typer


@dataclass
class GlobalContext:
    """
    Unified context for CLI commands.

    This is assigned to ctx.obj by the app callback and provides
    access to all V3 managers from any command.

    Attributes:
        profile: Active AWS profile name
        region: Active AWS region
        config: Configuration manager (profile-aware)
        state: State manager (runtime persistence)
        output: Output manager (stdout hygiene)
    """

    profile: str
    region: str
    config: ConfigManager
    state: StateManager
    output: OutputManager
    _cli_overrides: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_cli(
        cls,
        profile: str | None = None,
        region: str | None = None,
        output_format: str = "text",
        verbose: int = 0,
        **cli_flags: Any,
    ) -> GlobalContext:
        """
        Create a GlobalContext from CLI arguments.

        This is the primary factory method used by the app callback.

        Args:
            profile: AWS profile (from --profile flag)
            region: AWS region (from --region flag)
            output_format: Output format (from --format flag)
            verbose: Verbosity level (from -v flags)
            **cli_flags: Additional CLI flags to store as overrides

        Returns:
            Configured GlobalContext instance
        """
        # Build CLI overrides dict
        cli_overrides: dict[str, Any] = dict(cli_flags)
        if profile is not None:
            cli_overrides["profile"] = profile
        if region is not None:
            cli_overrides["region"] = region

        # Create config manager with overrides
        config = create_config_manager(
            profile=profile or "default",
            cli_overrides=cli_overrides,
        )

        # Create state manager
        state = create_state_manager()

        # Determine effective profile and region
        effective_profile = profile or config.get("profile", "default")
        effective_region = region or config.get("region", "us-east-1")

        # If no profile/region specified, check state for last-used values
        if profile is None and state.state.last_profile:
            effective_profile = state.state.last_profile
        if region is None and state.state.last_region:
            effective_region = state.state.last_region

        # Create output manager
        output = create_output_manager(
            format=output_format,
            verbose=verbose,
        )

        return cls(
            profile=effective_profile,
            region=effective_region,
            config=config,
            state=state,
            output=output,
            _cli_overrides=cli_overrides,
        )

    def get_scan_config(self) -> dict[str, Any]:
        """Get all configuration values for the scan command."""
        return self.config.get_all_for_command("scan")

    def get_clone_config(self) -> dict[str, Any]:
        """Get all configuration values for the clone command."""
        return self.config.get_all_for_command("clone")

    def get_audit_config(self) -> dict[str, Any]:
        """Get all configuration values for the audit command."""
        return self.config.get_all_for_command("audit")

    def get_cost_config(self) -> dict[str, Any]:
        """Get all configuration values for the cost command."""
        return self.config.get_all_for_command("cost")

    def to_display_dict(self) -> dict[str, Any]:
        """
        Get context information for display.

        Returns:
            Dict suitable for display or JSON output
        """
        return {
            "profile": self.profile,
            "region": self.region,
            "output_format": self.output.format.value,
            "verbose": self.output.verbose,
            "config": self.config.to_display_dict(),
            "state": {
                "last_scan": self.state.get_last_scan_info(),
                "cache_exists": self.state.state.cache_exists,
            },
        }

    def explain_config(self, key: str) -> str:
        """Explain where a configuration value came from."""
        return self.config.explain(key)


def create_context_callback(app: typer.Typer) -> None:
    """
    Create and register the context callback for a Typer app.

    This sets up the @app.callback() that creates GlobalContext
    and assigns it to ctx.obj for all commands.

    Args:
        app: The Typer application to add the callback to
    """
    import typer

    @app.callback()
    def main_callback(
        ctx: typer.Context,
        profile: str | None = typer.Option(
            None,
            "--profile",
            "-p",
            help="AWS profile to use",
            envvar="AWS_PROFILE",
        ),
        region: str | None = typer.Option(
            None,
            "--region",
            "-r",
            help="AWS region to use",
            envvar="AWS_DEFAULT_REGION",
        ),
        output_format: str = typer.Option(
            "text",
            "--format",
            "-f",
            help="Output format: text, json, table, quiet",
        ),
        verbose: int = typer.Option(
            0,
            "--verbose",
            "-v",
            count=True,
            help="Increase verbosity (-v for verbose, -vv for debug)",
        ),
        quiet: bool = typer.Option(
            False,
            "--quiet",
            "-q",
            help="Suppress non-essential output",
        ),
    ) -> None:
        """RepliMap CLI - AWS Infrastructure Intelligence Engine."""
        # Handle quiet as format override
        effective_format = "quiet" if quiet else output_format

        # Validate format
        try:
            OutputFormat(effective_format)
        except ValueError:
            raise typer.BadParameter(
                f"Invalid format '{effective_format}'. "
                f"Choose from: text, json, table, quiet"
            ) from None

        # Create and assign global context
        ctx.obj = GlobalContext.from_cli(
            profile=profile,
            region=region,
            output_format=effective_format,
            verbose=verbose,
        )


def get_context(ctx: typer.Context) -> GlobalContext:
    """
    Get GlobalContext from Typer context.

    This is a convenience function for commands that need
    type-safe access to the context.

    Args:
        ctx: Typer context

    Returns:
        GlobalContext instance

    Raises:
        RuntimeError: If context is not properly initialized
    """
    if ctx.obj is None:
        raise RuntimeError(
            "GlobalContext not initialized. "
            "Ensure create_context_callback was called on the app."
        )

    if not isinstance(ctx.obj, GlobalContext):
        raise RuntimeError(
            f"Expected GlobalContext, got {type(ctx.obj).__name__}. "
            "Ensure create_context_callback was called on the app."
        )

    return ctx.obj


__all__ = [
    "GlobalContext",
    "create_context_callback",
    "get_context",
]
