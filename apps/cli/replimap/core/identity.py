"""
Identity Guard - Protects against unauthorized AWS identity switches.

Core Safety Rules:
1. NEVER silently switch AWS profile
2. CI mode = Fail Fast for sensitive operations
3. Explicit profiles require explicit confirmation to switch

This module ensures that AWS credential changes are always visible
and approved by the user before execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from replimap.cli.utils.console import console
from replimap.core.context import (
    ConfigSource,
    ExecutionEnvironment,
    GlobalContext,
)

if TYPE_CHECKING:
    from rich.console import Console


class IdentitySource(Enum):
    """Source of AWS identity specification."""

    CLI_ARGUMENT = "cli"  # --profile flag
    ENVIRONMENT = "env"  # AWS_PROFILE environment variable
    CONFIG_FILE = "config"  # Config file default
    DEFAULT = "default"  # No explicit specification


@dataclass
class IdentityContext:
    """Current AWS identity context with source tracking."""

    profile: str
    source: IdentitySource
    is_explicit: bool
    arn: str | None = None
    account_id: str | None = None
    user_id: str | None = None

    def describe(self) -> str:
        """Human-readable description of identity."""
        return f"{self.profile} (via {self.source.value})"

    def describe_full(self) -> str:
        """Full description including ARN if available."""
        if self.arn:
            return f"{self.profile} ({self.arn})"
        return self.describe()


class IdentityGuard:
    """
    Guards against unauthorized identity switches.

    Behavior by environment:
    - Interactive: Prompt for confirmation before switching
    - CI: Fail fast with detailed fix instructions
    - Non-Interactive: Reject switch with error message

    Usage:
        guard = IdentityGuard(ctx)
        identity = guard.resolve_identity()

        # Before switching profile
        if guard.can_switch_identity("new-profile", "permission denied"):
            # Switch is allowed
            pass
    """

    def __init__(
        self,
        ctx: GlobalContext,
        output_console: Console | None = None,
    ):
        """
        Initialize IdentityGuard.

        Args:
            ctx: Global context with environment and configuration
            output_console: Optional console for output (defaults to global)
        """
        self.ctx = ctx
        self.console = output_console or console
        self._current_identity: IdentityContext | None = None

    def resolve_identity(self) -> IdentityContext:
        """
        Resolve and validate the current AWS identity.

        Returns:
            IdentityContext with profile info, ARN, and account details

        Note:
            Does not raise on credential errors - caller should check
            if arn is None to detect invalid credentials.
        """
        profile = self.ctx.profile.value
        source = self._map_source(self.ctx.profile.source)
        is_explicit = self.ctx.is_explicit_profile()

        # Attempt to validate credentials
        arn = None
        account_id = None
        user_id = None

        try:
            session = boto3.Session(profile_name=profile)
            sts = session.client("sts")
            identity = sts.get_caller_identity()
            arn = identity.get("Arn")
            account_id = identity.get("Account")
            user_id = identity.get("UserId")
        except (ClientError, NoCredentialsError):
            pass  # Invalid credentials - arn will be None

        self._current_identity = IdentityContext(
            profile=profile,
            source=source,
            is_explicit=is_explicit,
            arn=arn,
            account_id=account_id,
            user_id=user_id,
        )

        return self._current_identity

    def get_current_identity(self) -> IdentityContext | None:
        """Get the current identity without re-resolving."""
        return self._current_identity

    def can_switch_identity(self, new_profile: str, reason: str) -> bool:
        """
        Request permission to switch AWS identity.

        This is the core safety method. It ensures that any profile
        switch is either:
        - Confirmed by the user (interactive mode)
        - Explicitly rejected with fix instructions (CI mode)
        - Rejected with error message (non-interactive mode)

        Args:
            new_profile: Target profile name to switch to
            reason: Human-readable reason why the switch is needed

        Returns:
            True if switch is allowed, False otherwise
        """
        if not self._current_identity:
            self.resolve_identity()

        assert self._current_identity is not None

        # Same profile - no switch needed
        if new_profile == self._current_identity.profile:
            return True

        # CI environment: Fail fast with detailed instructions
        if self.ctx.environment == ExecutionEnvironment.CI:
            self._fail_fast_ci(new_profile, reason)
            return False

        # Non-interactive (but not CI): Reject with error
        if not self.ctx.is_interactive():
            self._reject_non_interactive(new_profile, reason)
            return False

        # Interactive: Ask for confirmation
        return self._confirm_interactive(new_profile, reason)

    def _fail_fast_ci(self, new_profile: str, reason: str) -> None:
        """
        Fail fast in CI environment with detailed fix instructions.

        Provides actionable guidance on how to fix the issue in CI.
        """
        ci_name = self.ctx.ci_name or "CI"
        current = self._current_identity
        assert current is not None

        self.console.print()
        self.console.print(
            f"[red bold]❌ Error [RM-E003]: Sensitive Operation in {ci_name}[/red bold]"
        )
        self.console.print()
        self.console.print(
            "RepliMap detected a sensitive operation that requires user\n"
            "confirmation, but is running in a CI environment without TTY."
        )
        self.console.print()
        self.console.print("[yellow]Operation:[/yellow] Switch AWS Profile")
        self.console.print(f"  From: {current.describe()}")
        self.console.print(f"  To:   {new_profile}")
        self.console.print(f"[yellow]Reason:[/yellow] {reason}")
        self.console.print()
        self.console.print("[green bold]🔧 To fix this in CI:[/green bold]")
        self.console.print()
        self.console.print("  [bold]Option 1:[/bold] Use explicit profile in command")
        self.console.print(
            f"    [cyan]replimap scan --profile {new_profile} --region us-east-1[/cyan]"
        )
        self.console.print()
        self.console.print("  [bold]Option 2:[/bold] Set environment variable")
        self.console.print(f"    [cyan]export AWS_PROFILE={new_profile}[/cyan]")
        self.console.print()
        self.console.print(
            "  [bold]Option 3:[/bold] Configure in .replimap/config.toml"
        )
        self.console.print(f'    [cyan]default_profile = "{new_profile}"[/cyan]')
        self.console.print()
        self.console.print("[dim]For more information: replimap explain RM-E003[/dim]")

    def _reject_non_interactive(self, new_profile: str, reason: str) -> None:
        """Reject switch in non-interactive mode with clear error."""
        current = self._current_identity
        assert current is not None

        self.console.print()
        self.console.print(
            "[red]❌ Cannot switch identity in non-interactive mode[/red]"
        )
        self.console.print(f"  Current: {current.describe()}")
        self.console.print(f"  Target:  {new_profile}")
        self.console.print(f"  Reason:  {reason}")
        self.console.print()
        self.console.print(
            f"[yellow]Fix: Run with --profile {new_profile} explicitly[/yellow]"
        )

    def _confirm_interactive(self, new_profile: str, reason: str) -> bool:
        """Ask for confirmation in interactive mode."""
        current = self._current_identity
        assert current is not None

        self.console.print()
        self.console.print("[yellow bold]⚠️  Identity Switch Required[/yellow bold]")
        self.console.print(f"   Current: {current.describe()}")
        self.console.print(f"   Target:  {new_profile}")
        self.console.print(f"   Reason:  {reason}")

        # Extra warning if current profile was explicitly specified
        if current.is_explicit:
            self.console.print()
            self.console.print(
                f"[red]⚠️  Warning: You explicitly specified '{current.profile}'.[/red]"
            )
            self.console.print(
                "[red]   Switching may have unintended consequences.[/red]"
            )

        try:
            response = (
                self.console.input(f"\n   Switch to '{new_profile}'? [y/N]: ")
                .strip()
                .lower()
            )
            return response == "y"
        except (EOFError, KeyboardInterrupt):
            self.console.print("\n   [dim]Switch cancelled[/dim]")
            return False

    def _map_source(self, source: ConfigSource) -> IdentitySource:
        """Map ConfigSource to IdentitySource."""
        mapping = {
            ConfigSource.CLI: IdentitySource.CLI_ARGUMENT,
            ConfigSource.ENVIRONMENT: IdentitySource.ENVIRONMENT,
            ConfigSource.CONFIG_FILE: IdentitySource.CONFIG_FILE,
            ConfigSource.DEFAULT: IdentitySource.DEFAULT,
        }
        return mapping.get(source, IdentitySource.DEFAULT)


def create_identity_guard(
    ctx: GlobalContext,
    output_console: Console | None = None,
) -> IdentityGuard:
    """
    Factory function to create an IdentityGuard.

    Args:
        ctx: Global context
        output_console: Optional console for output

    Returns:
        Configured IdentityGuard instance
    """
    return IdentityGuard(ctx, output_console)


__all__ = [
    "IdentityContext",
    "IdentityGuard",
    "IdentitySource",
    "create_identity_guard",
]
