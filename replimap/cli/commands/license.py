"""
License commands - License management for RepliMap.
"""

from __future__ import annotations

import typer
from rich.panel import Panel
from rich.table import Table

from replimap.cli.utils import console
from replimap.licensing import Feature, LicenseStatus, LicenseValidationError
from replimap.licensing.manager import get_license_manager
from replimap.licensing.tracker import get_usage_tracker


def create_license_app() -> typer.Typer:
    """Create the license sub-command group."""
    license_app = typer.Typer(
        name="license",
        help="License management commands",
        rich_markup_mode="rich",
        context_settings={"help_option_names": ["-h", "--help"]},
    )

    @license_app.command("activate")
    def license_activate(
        license_key: str = typer.Argument(
            ...,
            help="License key (format: RM-XXXX-XXXX-XXXX-XXXX)",
        ),
    ) -> None:
        """
        Activate a license key.

        Examples:
            replimap license activate RM-7P0A-QB0G-ADFS-2TWU
        """
        manager = get_license_manager()

        try:
            license_obj = manager.activate(license_key)
            console.print(
                Panel(
                    f"[green]License activated successfully![/]\n\n"
                    f"Plan: [bold cyan]{license_obj.plan.value.upper()}[/]\n"
                    f"Email: {license_obj.email}\n"
                    f"Expires: {license_obj.expires_at.strftime('%Y-%m-%d') if license_obj.expires_at else 'Never'}",
                    title="License Activated",
                    border_style="green",
                )
            )
        except LicenseValidationError as e:
            console.print(
                Panel(
                    f"[red]License activation failed:[/]\n{e}",
                    title="Activation Error",
                    border_style="red",
                )
            )
            raise typer.Exit(1)

    @license_app.command("status")
    def license_status() -> None:
        """
        Show current license status.

        Examples:
            replimap license status
        """
        manager = get_license_manager()
        status, message = manager.validate()
        license_obj = manager.current_license
        features = manager.current_features

        # Status panel
        if status == LicenseStatus.VALID:
            status_color = "green"
            status_icon = "[green]Valid[/]"
        elif status == LicenseStatus.EXPIRED:
            status_color = "red"
            status_icon = "[red]Expired[/]"
        else:
            status_color = "yellow"
            status_icon = f"[yellow]{status.value}[/]"

        plan_name = manager.current_plan.value.upper()
        if license_obj:
            info = (
                f"Plan: [bold cyan]{plan_name}[/]\n"
                f"Status: {status_icon}\n"
                f"Email: {license_obj.email}\n"
                f"Expires: "
                f"{license_obj.expires_at.strftime('%Y-%m-%d') if license_obj.expires_at else 'Never'}"
            )
        else:
            info = (
                f"Plan: [bold cyan]{plan_name}[/]\n"
                f"Status: {status_icon}\n"
                f"[dim]No license key activated. Using free tier.[/]"
            )

        console.print(
            Panel(
                info,
                title="License Status",
                border_style=status_color,
            )
        )

        # Features table
        console.print()
        table = Table(title="Plan Features", show_header=True, header_style="bold cyan")
        table.add_column("Feature", style="dim")
        table.add_column("Available", justify="center")

        feature_display = [
            (Feature.UNLIMITED_RESOURCES, "Unlimited Resources"),
            (Feature.ASYNC_SCANNING, "Async Scanning"),
            (Feature.MULTI_ACCOUNT, "Multi-Account Support"),
            (Feature.CUSTOM_TEMPLATES, "Custom Templates"),
            (Feature.WEB_DASHBOARD, "Web Dashboard"),
            (Feature.COLLABORATION, "Team Collaboration"),
            (Feature.SSO, "SSO Integration"),
            (Feature.AUDIT_LOGS, "Audit Logs"),
        ]

        for feature, display_name in feature_display:
            available = features.has_feature(feature)
            icon = "[green]Yes[/]" if available else "[dim]No[/]"
            table.add_row(display_name, icon)

        console.print(table)

        # Limits
        console.print()
        limits_table = Table(
            title="Usage Limits", show_header=True, header_style="bold cyan"
        )
        limits_table.add_column("Limit", style="dim")
        limits_table.add_column("Value", justify="right")

        limits_table.add_row(
            "Resources per Scan",
            str(features.max_resources_per_scan)
            if features.max_resources_per_scan
            else "Unlimited",
        )
        limits_table.add_row(
            "Scans per Month",
            str(features.max_scans_per_month)
            if features.max_scans_per_month
            else "Unlimited",
        )
        limits_table.add_row(
            "AWS Accounts",
            str(features.max_aws_accounts)
            if features.max_aws_accounts
            else "Unlimited",
        )

        console.print(limits_table)

        # Usage stats
        tracker = get_usage_tracker()
        stats = tracker.get_stats()

        if stats.total_scans > 0:
            console.print()
            usage_table = Table(
                title="Usage This Month",
                show_header=True,
                header_style="bold cyan",
            )
            usage_table.add_column("Metric", style="dim")
            usage_table.add_column("Value", justify="right")

            usage_table.add_row("Scans", str(stats.scans_this_month))
            usage_table.add_row("Resources Scanned", str(stats.resources_this_month))
            usage_table.add_row("Regions Used", str(len(stats.unique_regions)))

            console.print(usage_table)

        console.print()

    @license_app.command("deactivate")
    def license_deactivate(
        confirm: bool = typer.Option(
            False,
            "--yes",
            "-y",
            help="Skip confirmation",
        ),
    ) -> None:
        """
        Deactivate the current license.

        Examples:
            replimap license deactivate --yes
        """
        manager = get_license_manager()

        if manager.current_license is None:
            console.print("[yellow]No license is currently active.[/]")
            raise typer.Exit(0)

        if not confirm:
            confirm = typer.confirm("Are you sure you want to deactivate your license?")
            if not confirm:
                console.print("[dim]Cancelled.[/]")
                raise typer.Exit(0)

        manager.deactivate()
        console.print("[green]License deactivated.[/] You are now on the free tier.")

    @license_app.command("usage")
    def license_usage() -> None:
        """
        Show detailed usage statistics.

        Examples:
            replimap license usage
        """
        tracker = get_usage_tracker()
        stats = tracker.get_stats()

        console.print(
            Panel(
                f"Total Scans: [bold]{stats.total_scans}[/]\n"
                f"Total Resources Scanned: [bold]{stats.total_resources_scanned}[/]\n"
                f"Unique Regions: [bold]{len(stats.unique_regions)}[/]\n"
                f"Last Scan: [bold]"
                f"{stats.last_scan.strftime('%Y-%m-%d %H:%M') if stats.last_scan else 'Never'}"
                f"[/]",
                title="Usage Overview",
                border_style="cyan",
            )
        )

        # Recent scans
        recent = tracker.get_recent_scans(10)
        if recent:
            console.print()
            table = Table(
                title="Recent Scans", show_header=True, header_style="bold cyan"
            )
            table.add_column("Date", style="dim")
            table.add_column("Region")
            table.add_column("Resources", justify="right")
            table.add_column("Duration", justify="right")

            for scan in recent:
                table.add_row(
                    scan.timestamp.strftime("%Y-%m-%d %H:%M"),
                    scan.region,
                    str(scan.resource_count),
                    f"{scan.duration_seconds:.1f}s",
                )

            console.print(table)

        # Resource type breakdown
        if stats.resource_type_counts:
            console.print()
            type_table = Table(
                title="Resources by Type",
                show_header=True,
                header_style="bold cyan",
            )
            type_table.add_column("Resource Type", style="dim")
            type_table.add_column("Count", justify="right")

            for rtype, count in sorted(
                stats.resource_type_counts.items(),
                key=lambda x: x[1],
                reverse=True,
            ):
                type_table.add_row(rtype, str(count))

            console.print(type_table)

        console.print()

    return license_app


def register(app: typer.Typer) -> None:
    """Register license commands with the app."""
    app.add_typer(create_license_app(), name="license")
