"""Trust Center command group for RepliMap CLI."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.prompt import Confirm
from rich.table import Table

from replimap.cli.utils import console


def create_trust_center_app() -> typer.Typer:
    """Create and return the trust_center subcommand app."""
    trust_center_app = typer.Typer(help="Trust Center API auditing for compliance")

    @trust_center_app.command("report")
    def trust_center_report(
        output: Path | None = typer.Option(
            None, "--output", "-o", help="Output file path (JSON, CSV, or TXT)"
        ),
        format_type: str = typer.Option(
            "text", "--format", "-f", help="Output format: json, csv, text"
        ),
        include_records: bool = typer.Option(
            False,
            "--include-records",
            help="Include detailed API call records in JSON output",
        ),
    ) -> None:
        """Generate Trust Center compliance report."""
        from replimap.audit import TrustCenter

        tc = TrustCenter.get_instance()
        tc.load_sessions_from_disk()

        if tc.session_count == 0:
            console.print(
                "[yellow]No audit sessions found.[/]\n"
                "Run a scan with --trust-center to enable API auditing:\n"
                "  replimap scan --profile prod --trust-center"
            )
            raise typer.Exit(0)

        report = tc.generate_report()

        if format_type == "json":
            output_path = output or Path("trust_center_report.json")
            tc.export_json(report, output_path, include_records=include_records)
            console.print(f"[green]✓ Saved JSON report: {output_path}[/]")

        elif format_type == "csv":
            output_path = output or Path("trust_center_records.csv")
            sessions = tc.list_sessions()
            tc.export_csv(sessions, output_path)
            console.print(f"[green]✓ Saved CSV report: {output_path}[/]")

        elif format_type == "text":
            if output:
                tc.save_compliance_text(report, output)
                console.print(f"[green]✓ Saved compliance report: {output}[/]")
            else:
                text = tc.generate_compliance_text(report)
                console.print(text)

        else:
            console.print(f"[red]Unknown format: {format_type}[/]")
            raise typer.Exit(1)

    @trust_center_app.command("status")
    def trust_center_status() -> None:
        """Show Trust Center status and session summary."""
        from replimap.audit import TrustCenter

        tc = TrustCenter.get_instance()
        tc.load_sessions_from_disk()

        console.print("[bold]Trust Center Status[/bold]\n")
        console.print(f"Active Sessions: {tc.session_count}")

        sessions = tc.list_sessions()
        if sessions:
            console.print("\n[bold]Recent Sessions:[/bold]")
            table = Table(show_header=True)
            table.add_column("Session ID", style="cyan")
            table.add_column("Name")
            table.add_column("API Calls", justify="right")
            table.add_column("Read-Only %", justify="right")
            table.add_column("Status")

            for session in sessions[-5:]:
                status = (
                    "[green]✓ Read-Only[/]"
                    if session.is_read_only
                    else "[yellow]⚠ Has Writes[/]"
                )
                table.add_row(
                    session.session_id[:12] + "...",
                    session.session_name or "-",
                    str(session.total_calls),
                    f"{session.read_only_percentage:.1f}%",
                    status,
                )
            console.print(table)
        else:
            console.print("\n[dim]No sessions recorded yet.[/]")

    @trust_center_app.command("clear")
    def trust_center_clear(
        force: bool = typer.Option(
            False, "--force", "-f", help="Skip confirmation prompt"
        ),
    ) -> None:
        """Clear all Trust Center audit sessions."""
        from replimap.audit import TrustCenter

        tc = TrustCenter.get_instance()
        tc.load_sessions_from_disk()

        if tc.session_count == 0:
            console.print("[dim]No sessions to clear.[/]")
            raise typer.Exit(0)

        if not force:
            if not Confirm.ask(f"Clear {tc.session_count} audit sessions?"):
                console.print("[dim]Cancelled[/]")
                raise typer.Exit(0)

        tc.clear_sessions()

        session_files = list(tc._storage_dir.glob("session_*.json"))
        for f in session_files:
            f.unlink()

        console.print(
            f"[green]✓ Cleared all audit sessions ({len(session_files)} files removed)[/]"
        )

    return trust_center_app


def register(app: typer.Typer) -> None:
    """Register the trust_center command group with the Typer app."""
    trust_center_app = create_trust_center_app()
    app.add_typer(trust_center_app, name="trust-center")
