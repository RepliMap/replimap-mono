"""DR readiness command group for RepliMap CLI."""

from __future__ import annotations

import json as json_module
import os
import webbrowser
from pathlib import Path

import typer
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from replimap.cli.utils import console, get_aws_session
from replimap.core import GraphEngine
from replimap.scanners.base import run_all_scanners


def create_dr_app() -> typer.Typer:
    """Create and return the DR subcommand app."""
    dr_app = typer.Typer(help="Disaster Recovery readiness assessment")

    @dr_app.command("assess")
    def dr_assess(
        profile: str | None = typer.Option(
            None, "--profile", "-p", help="AWS profile name"
        ),
        region: str | None = typer.Option(
            None, "--region", "-r", help="Primary AWS region to assess"
        ),
        dr_region: str | None = typer.Option(
            None, "--dr-region", help="DR region to check for replicas"
        ),
        output: Path | None = typer.Option(
            None, "--output", "-o", help="Output file path"
        ),
        output_format: str = typer.Option(
            "console",
            "--format",
            "-f",
            help="Output format: console, json, markdown, html",
        ),
        target_tier: str = typer.Option(
            "tier_2", "--target-tier", "-t", help="Target DR tier"
        ),
        no_cache: bool = typer.Option(
            False, "--no-cache", help="Don't use cached credentials"
        ),
    ) -> None:
        """Assess disaster recovery readiness for your infrastructure."""
        from replimap.dr.readiness import DRReadinessAssessor, DRTier

        effective_region = region or os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
        effective_profile = profile or "default"

        tier_map = {
            "tier_0": DRTier.TIER_0,
            "tier_1": DRTier.TIER_1,
            "tier_2": DRTier.TIER_2,
            "tier_3": DRTier.TIER_3,
            "tier_4": DRTier.TIER_4,
        }
        target = tier_map.get(target_tier.lower(), DRTier.TIER_2)

        console.print(
            Panel(
                f"[bold cyan]DR Readiness Assessment[/bold cyan]\n\n"
                f"Primary Region: [cyan]{effective_region}[/]\n"
                f"DR Region: [cyan]{dr_region or 'Auto-detect'}[/]\n"
                f"Target Tier: [cyan]{target.display_name}[/]",
                border_style="cyan",
            )
        )

        session = get_aws_session(
            effective_profile, effective_region, use_cache=not no_cache
        )

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Scanning primary region...", total=None)

            try:
                graph = GraphEngine()
                run_all_scanners(session, effective_region, graph)
                progress.update(task, description="Assessing DR readiness...")
                assessor = DRReadinessAssessor(
                    session,
                    primary_region=effective_region,
                    dr_region=dr_region,
                )
                result = assessor.assess(graph, target_tier=target)
                progress.update(task, completed=True)
            except Exception as e:
                console.print(f"[red]Error: {e}[/]")
                raise typer.Exit(1)

        console.print()

        if output_format == "console":
            score_color = (
                "green"
                if result.score >= 80
                else "yellow"
                if result.score >= 60
                else "red"
            )
            console.print(
                f"[bold]DR Readiness Score: [{score_color}]{result.score}/100[/][/bold]"
            )
            console.print(
                f"Current Tier: [bold]{result.current_tier.display_name}[/bold]"
            )
            console.print(f"Target Tier: {target.display_name}")
            console.print()

            console.print("[bold]Recovery Objectives[/bold]")
            console.print(f"  Estimated RTO: {result.estimated_rto_minutes} minutes")
            console.print(f"  Estimated RPO: {result.estimated_rpo_minutes} minutes")
            console.print()

            console.print("[bold]Coverage Analysis[/bold]")
            for category, coverage in result.coverage.items():
                pct = coverage.percentage
                bar = "█" * int(pct / 10) + "░" * (10 - int(pct / 10))
                color = "green" if pct >= 80 else "yellow" if pct >= 50 else "red"
                console.print(f"  {category}: [{color}]{bar}[/] {pct:.0f}%")
            console.print()

            if result.gaps:
                console.print(
                    f"[bold yellow]Gaps Identified ({len(result.gaps)})[/bold yellow]"
                )
                for gap in result.gaps[:5]:
                    console.print(f"  ⚠ {gap.description}")
                    console.print(f"    [dim]Impact: {gap.impact}[/dim]")
                console.print()

            if result.recommendations:
                console.print(
                    f"[bold green]Recommendations ({len(result.recommendations)})[/bold green]"
                )
                for rec in result.recommendations[:5]:
                    console.print(f"  ✓ {rec.description}")
                    if rec.estimated_cost:
                        console.print(
                            f"    [dim]Est. cost: ${rec.estimated_cost}/mo[/dim]"
                        )

        elif output_format == "json":
            output_path = output or Path("dr_assessment.json")
            with open(output_path, "w") as f:
                json_module.dump(result.to_dict(), f, indent=2)
            console.print(f"[green]✓ Saved to {output_path}[/]")

        elif output_format in ("md", "markdown"):
            output_path = output or Path("dr_assessment.md")
            with open(output_path, "w") as f:
                f.write("# DR Readiness Assessment\n\n")
                f.write(f"- Score: {result.score}/100\n")
                f.write(f"- Current Tier: {result.current_tier.display_name}\n")
                f.write(f"- Estimated RTO: {result.estimated_rto_minutes} minutes\n")
                f.write(f"- Estimated RPO: {result.estimated_rpo_minutes} minutes\n")
            console.print(f"[green]✓ Saved to {output_path}[/]")

        elif output_format == "html":
            output_path = output or Path("dr_assessment.html")
            html_content = f"""<!DOCTYPE html>
<html>
<head><title>DR Readiness Report</title>
<style>
body {{ font-family: -apple-system, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
.score {{ font-size: 48px; color: {"green" if result.score >= 80 else "orange" if result.score >= 60 else "red"}; }}
.metric {{ background: #f5f5f5; padding: 10px; margin: 10px 0; border-radius: 4px; }}
</style>
</head>
<body>
<h1>DR Readiness Assessment</h1>
<p class="score">{result.score}/100</p>
<div class="metric"><strong>Current Tier:</strong> {result.current_tier.display_name}</div>
<div class="metric"><strong>Estimated RTO:</strong> {result.estimated_rto_minutes} minutes</div>
<div class="metric"><strong>Estimated RPO:</strong> {result.estimated_rpo_minutes} minutes</div>
<h2>Coverage</h2>
{"".join(f'<div class="metric">{cat}: {cov.percentage:.0f}%</div>' for cat, cov in result.coverage.items())}
</body>
</html>"""
            with open(output_path, "w") as f:
                f.write(html_content)
            console.print(f"[green]✓ Saved to {output_path}[/]")
            webbrowser.open(f"file://{output_path.absolute()}")

        console.print()

    @dr_app.command("scorecard")
    def dr_scorecard(
        profile: str | None = typer.Option(None, "--profile", "-p"),
        output: Path | None = typer.Option(None, "--output", "-o"),
    ) -> None:
        """Generate DR readiness scorecard for all regions."""
        console.print("[dim]Generating multi-region DR scorecard...[/dim]")
        console.print(
            "[yellow]This feature requires scanning multiple regions.[/yellow]"
        )
        console.print(
            "Use 'replimap dr assess -r <region>' for single-region assessment."
        )

    return dr_app


def register(app: typer.Typer) -> None:
    """Register the dr command group with the Typer app."""
    dr_app = create_dr_app()
    app.add_typer(dr_app, name="dr")
