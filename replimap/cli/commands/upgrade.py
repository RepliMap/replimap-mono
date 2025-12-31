"""Upgrade command group for RepliMap CLI."""

from __future__ import annotations

import webbrowser

import typer
from rich.panel import Panel

from replimap.cli.utils import console

# Constants
PRICING_URL = "https://replimap.dev/pricing"
CHECKOUT_URLS = {
    "solo": "https://replimap.dev/checkout/solo",
    "pro": "https://replimap.dev/checkout/pro",
    "team": "https://replimap.dev/checkout/team",
    "enterprise": "https://replimap.dev/contact",
}


def _show_upgrade_info(plan_name: str) -> None:
    """Show upgrade information and open browser."""
    from replimap.licensing.models import Plan, get_plan_features

    plan_map = {
        "solo": Plan.SOLO,
        "pro": Plan.PRO,
        "team": Plan.TEAM,
        "enterprise": Plan.ENTERPRISE,
    }

    plan = plan_map.get(plan_name.lower())
    if not plan:
        console.print(f"[red]Unknown plan: {plan_name}[/]")
        raise typer.Exit(1)

    config = get_plan_features(plan)

    console.print()
    console.print(
        Panel(
            f"[bold blue]{config.plan.value.upper()} Plan[/bold blue]\n\n"
            f"[dim]Price:[/] ${config.price_monthly}/month\n"
            f"       ${config.price_annual_monthly}/month (billed annually)",
            border_style="blue",
        )
    )

    console.print("\n[bold]Features:[/bold]\n")

    if config.max_scans_per_month is None:
        console.print("  [green]✓[/] Unlimited scans")

    if config.clone_download_enabled:
        console.print("  [green]✓[/] Download Terraform code")

    if config.audit_visible_findings is None:
        console.print("  [green]✓[/] Full audit reports")

    if config.audit_ci_mode:
        console.print("  [green]✓[/] CI/CD integration")

    if config.drift_enabled:
        console.print("  [green]✓[/] Drift detection")

    if config.drift_watch_enabled:
        console.print("  [green]✓[/] Drift watch mode")

    if config.drift_alerts_enabled:
        console.print("  [green]✓[/] Alert notifications")

    if config.cost_enabled:
        console.print("  [green]✓[/] Cost estimation")

    if config.deps_enabled:
        console.print("  [green]✓[/] Dependency exploration")

    if config.max_aws_accounts is None or config.max_aws_accounts > 1:
        accounts = (
            "Unlimited"
            if config.max_aws_accounts is None
            else str(config.max_aws_accounts)
        )
        console.print(f"  [green]✓[/] {accounts} AWS accounts")

    console.print()

    url = CHECKOUT_URLS.get(plan_name.lower(), PRICING_URL)
    console.print(f"[dim]Opening {url}...[/dim]")
    webbrowser.open(url)


def create_upgrade_app() -> typer.Typer:
    """Create and return the upgrade subcommand app."""
    upgrade_app = typer.Typer(
        help="Upgrade your RepliMap plan",
        no_args_is_help=True,
    )

    @upgrade_app.command("solo")
    def upgrade_solo() -> None:
        """Upgrade to Solo plan ($29/mo)."""
        _show_upgrade_info("solo")

    @upgrade_app.command("pro")
    def upgrade_pro() -> None:
        """Upgrade to Pro plan ($79/mo)."""
        _show_upgrade_info("pro")

    @upgrade_app.command("team")
    def upgrade_team() -> None:
        """Upgrade to Team plan ($149/mo)."""
        _show_upgrade_info("team")

    @upgrade_app.command("enterprise")
    def upgrade_enterprise() -> None:
        """Contact us for Enterprise plan."""
        _show_upgrade_info("enterprise")

    @upgrade_app.callback(invoke_without_command=True)
    def upgrade_default(ctx: typer.Context) -> None:
        """Show available plans."""
        if ctx.invoked_subcommand is None:
            console.print()
            console.print(
                Panel(
                    "[bold blue]RepliMap Plans[/bold blue]\n\n"
                    "[dim]Solo[/]     $29/mo  - Download code, full reports\n"
                    "[dim]Pro[/]      $79/mo  - Drift detection, CI/CD mode\n"
                    "[dim]Team[/]    $149/mo  - Watch mode, alerts, dependency explorer\n"
                    "[dim]Enterprise[/] Custom - SSO, audit logs, SLA",
                    border_style="blue",
                )
            )
            console.print()
            console.print("Usage: [bold]replimap upgrade <plan>[/]\n")
            console.print("  [dim]replimap upgrade solo[/]")
            console.print("  [dim]replimap upgrade pro[/]")
            console.print("  [dim]replimap upgrade team[/]")
            console.print()
            console.print(f"[dim]Opening {PRICING_URL}...[/dim]")
            webbrowser.open(PRICING_URL)

    return upgrade_app


def register(app: typer.Typer) -> None:
    """Register the upgrade command group with the Typer app."""
    upgrade_app = create_upgrade_app()
    app.add_typer(upgrade_app, name="upgrade")
