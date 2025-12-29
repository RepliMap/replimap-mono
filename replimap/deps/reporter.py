"""
Dependency Analysis Reporter.

Formats and displays DependencyAnalysis results with:
- Categorized dependency display
- Blast radius visualization
- Progress feedback for large queries
- Rich console output
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

from replimap.deps.models import (
    Dependency,
    DependencyAnalysis,
    RelationType,
    Severity,
)
from replimap.deps.blast_radius import get_risk_color, get_severity_color

console = Console()


# Relation type display configuration
RELATION_CONFIG: dict[RelationType, dict[str, str]] = {
    RelationType.MANAGER: {
        "label": "MANAGER",
        "color": "red bold",
        "icon": "!",
        "description": "Controls lifecycle (changes may be overwritten)",
    },
    RelationType.CONSUMER: {
        "label": "CONSUMERS",
        "color": "yellow",
        "icon": "⬆",
        "description": "Resources affected by changes to this resource",
    },
    RelationType.DEPENDENCY: {
        "label": "DEPENDENCIES",
        "color": "cyan",
        "icon": "⬇",
        "description": "Resources this depends on",
    },
    RelationType.MANAGED: {
        "label": "MANAGED",
        "color": "green",
        "icon": "M",
        "description": "Resources controlled by this one",
    },
    RelationType.NETWORK: {
        "label": "NETWORK",
        "color": "blue",
        "icon": "N",
        "description": "Network context",
    },
    RelationType.IDENTITY: {
        "label": "IDENTITY",
        "color": "magenta",
        "icon": "I",
        "description": "Permissions and encryption",
    },
    RelationType.TRUST: {
        "label": "TRUST",
        "color": "magenta",
        "icon": "T",
        "description": "Who can assume this role",
    },
    RelationType.REPLICATION: {
        "label": "REPLICATION",
        "color": "dim",
        "icon": "R",
        "description": "Replication relationships",
    },
    RelationType.TRIGGER: {
        "label": "TRIGGERS",
        "color": "dim",
        "icon": "⚡",
        "description": "Event triggers",
    },
}


class DependencyAnalysisReporter:
    """Reporter for DependencyAnalysis results."""

    def to_console(self, analysis: DependencyAnalysis) -> None:
        """Print dependency analysis to console."""
        console.print("\n[bold blue]Dependency Analysis[/bold blue]")
        console.print("[dim]Based on AWS API metadata only[/dim]\n")

        # Show warnings first (especially MANAGER warnings)
        self._print_manager_warnings(analysis)

        # Blast radius summary
        self._print_blast_radius(analysis)

        # Center resource info
        self._print_center_resource(analysis)

        # Dependencies by category
        self._print_categorized_dependencies(analysis)

        # IaC status
        if analysis.iac_status:
            self._print_iac_status(analysis.iac_status)

        # Next best actions
        self._print_next_actions(analysis)

        # Warnings footer
        if analysis.warnings:
            self._print_warnings(analysis.warnings)

    def _print_manager_warnings(self, analysis: DependencyAnalysis) -> None:
        """Print critical MANAGER warnings first."""
        managers = analysis.dependencies.get(RelationType.MANAGER, [])

        for manager in managers:
            if manager.resource_type == "aws_autoscaling_group":
                console.print(
                    Panel(
                        f"[red bold]WARNING: Resource managed by Auto Scaling Group![/red bold]\n\n"
                        f"[yellow]ASG Name:[/yellow] {manager.resource_name}\n\n"
                        f"[red]Manual changes will be REVERTED by Auto Scaling![/red]\n"
                        f"[red]Modify the Launch Template instead.[/red]\n\n"
                        f"[bold]To update:[/bold]\n"
                        f"  1. Find the Launch Template for ASG '{manager.resource_name}'\n"
                        f"  2. Modify the Launch Template configuration\n"
                        f"  3. Trigger instance refresh: aws autoscaling start-instance-refresh",
                        title="[red bold]! ASG-MANAGED RESOURCE ![/red bold]",
                        border_style="red",
                    )
                )
                console.print()
            elif manager.resource_type == "aws_cloudformation_stack":
                console.print(
                    Panel(
                        f"[yellow]This resource is managed by CloudFormation.[/yellow]\n\n"
                        f"[bold]Stack:[/bold] {manager.resource_name}\n\n"
                        f"Direct modifications may cause stack drift.\n"
                        f"Consider updating the CloudFormation template instead.",
                        title="[yellow]CloudFormation Managed[/yellow]",
                        border_style="yellow",
                    )
                )
                console.print()

    def _print_blast_radius(self, analysis: DependencyAnalysis) -> None:
        """Print blast radius assessment."""
        if not analysis.blast_radius:
            return

        br = analysis.blast_radius
        color = get_risk_color(br.level)

        # Build breakdown display
        breakdown_lines = []
        for rt, info in br.breakdown.items():
            rt_short = rt.replace("aws_", "")
            breakdown_lines.append(
                f"  {rt_short}: {info['count']} (weight: {info['weight']}) = {info['impact']} impact"
            )

        breakdown_text = "\n".join(breakdown_lines) if breakdown_lines else "  No consumers found"

        panel_content = f"""[{color}]Impact Score: {br.score}/100 [{br.level}][/{color}]

[bold]Affected Resources:[/bold] {br.affected_count} total
[bold]Weighted Impact:[/bold] {br.weighted_impact}

[bold]Breakdown:[/bold]
{breakdown_text}

[{color}]{br.summary}[/{color}]"""

        console.print(
            Panel(
                panel_content,
                title="Blast Radius Analysis",
                border_style=color.split()[0],  # Remove 'bold' for border
            )
        )
        console.print()

    def _print_center_resource(self, analysis: DependencyAnalysis) -> None:
        """Print center resource info with context."""
        center = analysis.center_resource
        context = analysis.context

        lines = [
            f"[bold]Resource:[/bold] {center.resource_id}",
            f"[bold]Type:[/bold] {center.resource_type}",
        ]

        if center.resource_name and center.resource_name != center.resource_id:
            lines.append(f"[bold]Name:[/bold] {center.resource_name}")

        # Add context info
        if context:
            lines.append("")
            lines.append("[bold]Context:[/bold]")
            for key, value in context.items():
                if value and key not in ("role_name", "group_name"):  # Skip redundant
                    key_display = key.replace("_", " ").title()
                    lines.append(f"  [cyan]{key_display}:[/cyan] {value}")

        console.print(Panel("\n".join(lines), title="Center Resource"))
        console.print()

    def _print_categorized_dependencies(self, analysis: DependencyAnalysis) -> None:
        """Print dependencies grouped by relation type."""
        # Order of display
        display_order = [
            RelationType.MANAGER,
            RelationType.CONSUMER,
            RelationType.TRUST,
            RelationType.DEPENDENCY,
            RelationType.NETWORK,
            RelationType.IDENTITY,
            RelationType.MANAGED,
            RelationType.REPLICATION,
            RelationType.TRIGGER,
        ]

        for rel_type in display_order:
            deps = analysis.dependencies.get(rel_type)
            if not deps:
                continue

            config = RELATION_CONFIG.get(rel_type, {})
            label = config.get("label", rel_type.value.upper())
            color = config.get("color", "white")
            desc = config.get("description", "")
            icon = config.get("icon", "•")

            console.print(
                f"[{color}][{label}][/{color}] [dim]({desc})[/dim]"
            )

            for dep in deps:
                self._print_dependency(dep, color, icon, indent=2)

            console.print()

    def _print_dependency(
        self,
        dep: Dependency,
        color: str,
        icon: str,
        indent: int = 0,
    ) -> None:
        """Print a single dependency with optional nesting."""
        prefix = " " * indent
        sev_color = get_severity_color(dep.severity.value)

        type_short = dep.resource_type.replace("aws_", "")
        name = dep.resource_name or dep.resource_id

        line = f"{prefix}[{color}]{icon}[/{color}] [{sev_color}]{dep.severity.value.upper():8}[/{sev_color}] "
        line += f"{type_short}: {name}"

        if dep.resource_id != name:
            line += f" [dim]({dep.resource_id})[/dim]"

        console.print(line)

        if dep.warning:
            console.print(f"{prefix}   [dim]└── {dep.warning}[/dim]")

        # Print children
        for child in dep.children:
            self._print_dependency(child, color, "└─", indent=indent + 4)

    def _print_iac_status(self, iac_status: dict[str, Any]) -> None:
        """Print IaC management status."""
        if iac_status.get("managed"):
            tool = iac_status.get("tool", "Unknown")
            stack = iac_status.get("stack")

            status_line = f"[green]✓[/green] Managed by {tool}"
            if stack:
                status_line += f" ({stack})"
        else:
            status_line = "[yellow]?[/yellow] No IaC management detected"

        console.print(f"[bold]IaC Status:[/bold] {status_line}")

        # Signs of manual modification
        signs = iac_status.get("signs_of_manual_modification", [])
        for sign in signs:
            console.print(f"  [dim]! {sign}[/dim]")

        console.print()

    def _print_next_actions(self, analysis: DependencyAnalysis) -> None:
        """Print suggested next actions."""
        actions = []

        # MANAGER-specific actions
        managers = analysis.dependencies.get(RelationType.MANAGER, [])
        for manager in managers:
            if manager.resource_type == "aws_autoscaling_group":
                actions.append(
                    f"Review ASG '{manager.resource_name}' and its Launch Template"
                )
                actions.append("Modify Launch Template, not this resource directly")
            elif manager.resource_type == "aws_cloudformation_stack":
                actions.append(
                    f"Update CloudFormation stack '{manager.resource_name}' instead"
                )

        # High blast radius actions
        if analysis.blast_radius and analysis.blast_radius.level in ("CRITICAL", "HIGH"):
            actions.append(
                f"Review all {analysis.blast_radius.affected_count} affected resources before changes"
            )

        # SG chain warning
        consumers = analysis.dependencies.get(RelationType.CONSUMER, [])
        sg_refs = [c for c in consumers if c.resource_type == "aws_security_group"]
        if sg_refs:
            actions.append(
                f"Check {len(sg_refs)} Security Group(s) that reference this resource"
            )

        # Cross-account warning
        trust = analysis.dependencies.get(RelationType.TRUST, [])
        cross_account = [t for t in trust if t.metadata.get("type") == "cross_account"]
        if cross_account:
            actions.append("Coordinate with external account owners before changes")

        # Generic actions
        actions.append("Check application logs and configs for hidden dependencies")

        if actions:
            console.print("[bold green]Next Best Actions:[/bold green]")
            for i, action in enumerate(actions, 1):
                console.print(f"  {i}. {action}")
            console.print()

    def _print_warnings(self, warnings: list[str]) -> None:
        """Print warnings."""
        console.print("[bold yellow]Warnings:[/bold yellow]")
        for warning in warnings:
            if "CRITICAL" in warning or "CROSS-ACCOUNT" in warning:
                console.print(f"  [red]! {warning}[/red]")
            else:
                console.print(f"  [yellow]! {warning}[/yellow]")
        console.print()

    def to_tree(self, analysis: DependencyAnalysis) -> None:
        """Print as a hierarchical tree."""
        center = analysis.center_resource

        # Build center label
        center_label = f"[bold cyan]{center.resource_type}[/bold cyan]: {center.resource_id}"
        if center.resource_name and center.resource_name != center.resource_id:
            center_label += f" ({center.resource_name})"

        tree = Tree(center_label)

        # Add branches by relation type
        display_order = [
            RelationType.MANAGER,
            RelationType.CONSUMER,
            RelationType.TRUST,
            RelationType.DEPENDENCY,
            RelationType.NETWORK,
            RelationType.IDENTITY,
        ]

        for rel_type in display_order:
            deps = analysis.dependencies.get(rel_type)
            if not deps:
                continue

            config = RELATION_CONFIG.get(rel_type, {})
            label = config.get("label", rel_type.value.upper())
            color = config.get("color", "white")

            branch = tree.add(f"[{color}][{label}][/{color}]")

            for dep in deps:
                type_short = dep.resource_type.replace("aws_", "")
                dep_label = f"[{color}]{type_short}[/{color}]: {dep.resource_name or dep.resource_id}"
                child_branch = branch.add(dep_label)

                for child in dep.children:
                    child_type = child.resource_type.replace("aws_", "")
                    child_branch.add(f"[dim]{child_type}: {child.resource_name}[/dim]")

        console.print("\n[bold]Dependency Tree:[/bold]\n")
        console.print(tree)

        # Print next actions
        self._print_next_actions(analysis)

    def to_json(self, analysis: DependencyAnalysis, output_path: Path) -> Path:
        """Export to JSON."""
        data = analysis.to_dict()
        output_path.write_text(json.dumps(data, indent=2, default=str))
        console.print(f"[green]Exported to {output_path}[/green]")
        return output_path

    def to_table(self, analysis: DependencyAnalysis) -> None:
        """Print as a table."""
        table = Table(title="Dependency Analysis")
        table.add_column("Relation", style="cyan")
        table.add_column("Severity", justify="center")
        table.add_column("Type")
        table.add_column("ID / Name")
        table.add_column("Warning")

        for rel_type, deps in analysis.dependencies.items():
            config = RELATION_CONFIG.get(rel_type, {})
            label = config.get("label", rel_type.value)
            color = config.get("color", "white")

            for dep in deps:
                sev_color = get_severity_color(dep.severity.value)
                table.add_row(
                    f"[{color}]{label}[/{color}]",
                    f"[{sev_color}]{dep.severity.value.upper()}[/{sev_color}]",
                    dep.resource_type.replace("aws_", ""),
                    dep.resource_name or dep.resource_id,
                    dep.warning or "",
                )

        console.print(table)
