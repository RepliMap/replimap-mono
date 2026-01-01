"""Cost trends analysis command for RepliMap CLI."""

from __future__ import annotations

import json as json_module
from pathlib import Path

import typer
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from replimap.cli.utils import console, get_aws_session, get_profile_region


def trends_command(
    profile: str | None = typer.Option(
        None,
        "--profile",
        "-p",
        help="AWS profile name",
    ),
    days: int = typer.Option(
        30,
        "--days",
        "-d",
        help="Number of days to analyze (default: 30)",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path (JSON or Markdown)",
    ),
    output_format: str = typer.Option(
        "console",
        "--format",
        "-f",
        help="Output format: console, json, markdown",
    ),
    no_cache: bool = typer.Option(
        False,
        "--no-cache",
        help="Don't use cached credentials",
    ),
) -> None:
    """
    Analyze AWS cost trends and detect anomalies.

    Uses AWS Cost Explorer to analyze historical spending patterns.

    Examples:
        replimap trends
        replimap trends --days 90
        replimap trends -f json -o trends.json
    """
    from replimap.cost.trends import CostTrendAnalyzer
    from replimap.licensing import check_cost_allowed

    cost_gate = check_cost_allowed()
    if not cost_gate.allowed:
        console.print(cost_gate.prompt)
        raise typer.Exit(1)

    effective_profile = profile or "default"

    # Cost Explorer is a global service, typically accessed via us-east-1
    # but we still respect profile region if set
    effective_region = get_profile_region(profile) or "us-east-1"

    console.print(
        Panel(
            f"[bold cyan]Cost Trend Analyzer[/bold cyan]\n\n"
            f"Profile: [cyan]{effective_profile}[/]\n"
            f"Period: [cyan]Last {days} days[/]",
            border_style="cyan",
        )
    )

    session = get_aws_session(
        effective_profile, effective_region, use_cache=not no_cache
    )

    # Global signal handler handles Ctrl-C
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(
                "Fetching cost data from Cost Explorer...", total=None
            )
            analyzer = CostTrendAnalyzer(session)
            result = analyzer.analyze(days=days)
            progress.update(task, completed=True)
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/]")
        console.print("[dim]Note: Cost Explorer must be enabled in your AWS account[/]")
        raise typer.Exit(1)

    console.print()

    if output_format == "console":
        console.print("[bold]Trend Analysis[/bold]")
        trend = result.trend
        direction_style = {
            "increasing": "red",
            "decreasing": "green",
            "stable": "dim",
            "volatile": "yellow",
        }.get(trend.direction.value, "dim")

        console.print(
            f"  Direction: [{direction_style}]{trend.direction.value.upper()}[/]"
        )
        console.print(f"  Rate: ${abs(trend.slope):.2f}/day")
        console.print(
            f"  Period change: {trend.period_change_pct:+.1f}% (${trend.period_change_amount:+.2f})"
        )
        console.print(f"  Projected monthly: ${trend.projected_monthly:.2f}")
        console.print()

        if result.anomalies:
            console.print(
                f"[bold yellow]Anomalies Detected ({len(result.anomalies)})[/bold yellow]"
            )
            for a in result.anomalies[:5]:
                console.print(
                    f"  • {a.date}: {a.anomaly_type.value} - ${a.amount:.2f} ({a.description})"
                )
            console.print()

        if result.service_breakdown:
            console.print("[bold]Top Services by Cost[/bold]")
            for svc, cost in list(result.service_breakdown.items())[:5]:
                console.print(f"  • {svc}: ${cost:.2f}")
            console.print()

        if result.forecast:
            console.print("[bold]Forecast[/bold]")
            console.print(f"  Next 7 days: ${result.forecast.next_7_days:.2f}")
            console.print(f"  Next 30 days: ${result.forecast.next_30_days:.2f}")

    elif output_format == "json":
        output_path = output or Path("cost_trends.json")
        with open(output_path, "w") as f:
            json_module.dump(result.to_dict(), f, indent=2)
        console.print(f"[green]✓ Saved to {output_path}[/]")

    elif output_format in ("md", "markdown"):
        output_path = output or Path("cost_trends.md")
        with open(output_path, "w") as f:
            f.write("# Cost Trend Analysis\n\n")
            f.write(f"- Period: Last {days} days\n")
            f.write(f"- Direction: {result.trend.direction.value}\n")
            f.write(f"- Rate: ${abs(result.trend.slope):.2f}/day\n")
            f.write(f"- Projected monthly: ${result.trend.projected_monthly:.2f}\n")
        console.print(f"[green]✓ Saved to {output_path}[/]")

    console.print()


def register(app: typer.Typer) -> None:
    """Register the trends command with the Typer app."""
    app.command(name="trends")(trends_command)
