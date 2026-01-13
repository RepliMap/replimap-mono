"""
Decisions CLI commands - Manage user decisions with TTL.

Commands:
- list: Show all decisions
- clear: Remove decisions
- renew: Extend TTL for a decision
- export: Export decisions for team sharing
- import: Import shared decisions
"""

from __future__ import annotations

from pathlib import Path

import typer
import yaml
from rich.prompt import Confirm
from rich.table import Table

from replimap.cli.errors import enhanced_cli_error_handler
from replimap.cli.utils import console
from replimap.decisions.manager import DecisionManager
from replimap.decisions.models import DecisionType


def create_decisions_app() -> typer.Typer:
    """Create the decisions sub-command group."""
    decisions_app = typer.Typer(
        name="decisions",
        help="Manage user decisions (suppression, extraction, etc.)",
        rich_markup_mode="rich",
        context_settings={"help_option_names": ["-h", "--help"]},
    )

    @decisions_app.command("list")
    @enhanced_cli_error_handler
    def decisions_list(
        scope: str | None = typer.Option(
            None,
            "--scope",
            "-s",
            help="Filter by scope (e.g., 'scan.permissions')",
        ),
        show_expired: bool = typer.Option(
            False,
            "--expired",
            help="Include expired decisions",
        ),
        decision_type: str | None = typer.Option(
            None,
            "--type",
            "-t",
            help="Filter by type (suppress, extraction, preference, permanent)",
        ),
    ) -> None:
        """
        List all decisions.

        Shows decisions with their status, TTL, and expiration info.

        Examples:
            replimap decisions list
            replimap decisions list --scope scan.permissions
            replimap decisions list --type suppress
            replimap decisions list --expired
        """
        manager = DecisionManager()
        decisions = manager.list_all()

        # Filter by scope
        if scope:
            decisions = [d for d in decisions if d.scope == scope]

        # Filter by type
        if decision_type:
            try:
                dt = DecisionType(decision_type)
                decisions = [d for d in decisions if d.decision_type == dt.value]
            except ValueError:
                console.print(
                    f"[red]Invalid decision type: {decision_type}[/red]\n"
                    "Valid types: suppress, extraction, preference, permanent"
                )
                raise typer.Exit(1)

        # Filter expired unless --expired flag
        if not show_expired:
            valid_decisions = [d for d in decisions if not d.is_expired()]
            expired_count = len(decisions) - len(valid_decisions)
            decisions = valid_decisions
        else:
            expired_count = 0

        if not decisions:
            console.print("[dim]No decisions found.[/dim]")
            if expired_count > 0:
                console.print(
                    f"[dim]({expired_count} expired decisions hidden, "
                    "use --expired to show)[/dim]"
                )
            return

        # Build table
        table = Table(
            title="User Decisions",
            show_header=True,
            header_style="bold",
        )
        table.add_column("Scope", style="cyan")
        table.add_column("Rule", style="green")
        table.add_column("Value")
        table.add_column("Type")
        table.add_column("Status")
        table.add_column("Reason", max_width=40)

        for d in decisions:
            # Determine status
            if d.is_expired():
                status = "[red]EXPIRED[/red]"
            elif d.is_expiring_soon():
                days = d.days_until_expiry()
                status = f"[yellow]{days}d left[/yellow]"
            elif d.is_permanent():
                status = "[dim]permanent[/dim]"
            else:
                days = d.days_until_expiry()
                status = f"[green]{days}d[/green]"

            table.add_row(
                d.scope,
                d.rule,
                str(d.value),
                d.decision_type,
                status,
                d.reason[:40] + "..." if len(d.reason) > 40 else d.reason,
            )

        console.print(table)

        # Summary
        counts = manager.count()
        console.print()
        console.print(
            f"[dim]Total: {counts['total']} | "
            f"Valid: {counts['valid']} | "
            f"Expired: {counts['expired']} | "
            f"Expiring soon: {counts['expiring_soon']} | "
            f"Permanent: {counts['permanent']}[/dim]"
        )

    @decisions_app.command("clear")
    @enhanced_cli_error_handler
    def decisions_clear(
        scope: str | None = typer.Option(
            None,
            "--scope",
            "-s",
            help="Clear only decisions in this scope",
        ),
        expired_only: bool = typer.Option(
            False,
            "--expired",
            help="Clear only expired decisions",
        ),
        all_decisions: bool = typer.Option(
            False,
            "--all",
            help="Clear all decisions",
        ),
        yes: bool = typer.Option(
            False,
            "--yes",
            "-y",
            help="Skip confirmation",
        ),
    ) -> None:
        """
        Clear decisions.

        By default, requires --scope, --expired, or --all to specify what to clear.

        Examples:
            replimap decisions clear --expired
            replimap decisions clear --scope scan.permissions
            replimap decisions clear --all
        """
        manager = DecisionManager()

        if not (scope or expired_only or all_decisions):
            console.print(
                "[red]Specify what to clear:[/red]\n"
                "  --scope <scope>  Clear decisions in scope\n"
                "  --expired        Clear only expired decisions\n"
                "  --all            Clear all decisions"
            )
            raise typer.Exit(1)

        # Determine what we're clearing
        if expired_only:
            to_clear = manager.get_expired()
            description = "expired decisions"
        elif scope:
            to_clear = manager.get_by_scope(scope)
            description = f"decisions in scope '{scope}'"
        else:
            to_clear = manager.list_all()
            description = "all decisions"

        if not to_clear:
            console.print(f"[dim]No {description} to clear.[/dim]")
            return

        # Confirm
        if not yes:
            confirm = Confirm.ask(f"Clear {len(to_clear)} {description}?")
            if not confirm:
                console.print("[dim]Cancelled.[/dim]")
                raise typer.Exit(0)

        # Clear
        if expired_only:
            removed = manager.remove_expired()
        elif scope:
            removed = manager.clear(scope=scope)
        else:
            removed = manager.clear()

        console.print(f"[green]Cleared {removed} {description}.[/green]")

    @decisions_app.command("renew")
    @enhanced_cli_error_handler
    def decisions_renew(
        decision_id: str = typer.Argument(
            ...,
            help="Decision to renew (format: scope.rule)",
        ),
    ) -> None:
        """
        Renew a decision's TTL.

        Extends the expiration by the original TTL period.

        Examples:
            replimap decisions renew scan.permissions.skip_s3
        """
        # Parse decision_id
        parts = decision_id.rsplit(".", 1)
        if len(parts) != 2:
            console.print(
                "[red]Invalid decision ID format.[/red]\n"
                "Use: scope.rule (e.g., scan.permissions.skip_s3)"
            )
            raise typer.Exit(1)

        scope, rule = parts

        manager = DecisionManager()
        decision = manager.get_decision(scope, rule, check_expiry=False)

        if not decision:
            console.print(f"[red]Decision not found: {decision_id}[/red]")
            raise typer.Exit(1)

        if decision.is_permanent():
            console.print(
                f"[yellow]Decision '{decision_id}' is permanent and "
                "does not need renewal.[/yellow]"
            )
            return

        if manager.renew_decision(scope, rule):
            decision = manager.get_decision(scope, rule)
            assert decision is not None
            console.print(
                f"[green]Renewed '{decision_id}'.[/green]\n"
                f"New expiration: {decision.days_until_expiry()} days"
            )
        else:
            console.print(f"[red]Failed to renew '{decision_id}'.[/red]")
            raise typer.Exit(1)

    @decisions_app.command("export")
    @enhanced_cli_error_handler
    def decisions_export(
        output: Path = typer.Option(
            Path("decisions-export.yaml"),
            "--output",
            "-o",
            help="Output file path",
        ),
    ) -> None:
        """
        Export decisions for team sharing.

        Exports user decisions (not auto-generated) that haven't expired.

        Examples:
            replimap decisions export
            replimap decisions export --output team-decisions.yaml
        """
        manager = DecisionManager()
        data = manager.export_shareable()

        if not data.get("decisions"):
            console.print("[dim]No decisions to export.[/dim]")
            return

        with open(output, "w") as f:
            yaml.dump(
                data,
                f,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )

        console.print(
            f"[green]Exported {len(data['decisions'])} decisions to {output}[/green]"
        )

    @decisions_app.command("import")
    @enhanced_cli_error_handler
    def decisions_import(
        file: Path = typer.Argument(
            ...,
            help="File to import",
            exists=True,
        ),
        overwrite: bool = typer.Option(
            False,
            "--overwrite",
            help="Overwrite existing decisions",
        ),
        yes: bool = typer.Option(
            False,
            "--yes",
            "-y",
            help="Skip confirmation",
        ),
    ) -> None:
        """
        Import shared decisions.

        Imports decisions from an export file.

        Examples:
            replimap decisions import team-decisions.yaml
            replimap decisions import team-decisions.yaml --overwrite
        """
        with open(file) as f:
            data = yaml.safe_load(f)

        if not data or not data.get("decisions"):
            console.print("[dim]No decisions to import.[/dim]")
            return

        count = len(data["decisions"])

        if not yes:
            msg = f"Import {count} decisions"
            if overwrite:
                msg += " (overwriting existing)"
            msg += "?"
            if not Confirm.ask(msg):
                console.print("[dim]Cancelled.[/dim]")
                raise typer.Exit(0)

        manager = DecisionManager()
        imported = manager.import_shared(data, overwrite=overwrite)

        console.print(f"[green]Imported {imported} decisions.[/green]")
        if imported < count:
            console.print(
                f"[dim]({count - imported} skipped - already exist, "
                "use --overwrite to replace)[/dim]"
            )

    return decisions_app


def register(app: typer.Typer) -> None:
    """Register the decisions command group with the main app."""
    app.add_typer(create_decisions_app())


__all__ = ["create_decisions_app", "register"]
