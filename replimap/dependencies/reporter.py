"""
Dependency Explorer report formatting.

Generates console output, JSON, and HTML reports for dependency analysis.

IMPORTANT: All outputs include disclaimers about limitations.
This analysis is based on AWS API metadata only.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

from replimap.dependencies.models import (
    DISCLAIMER_FULL,
    DISCLAIMER_SHORT,
    DependencyExplorerResult,
    ImpactLevel,
    RelationshipCategory,
    ResourceNode,
    RESOURCE_CATEGORY_MAP,
)

console = Console()


# Category display configuration
CATEGORY_CONFIG: dict[RelationshipCategory, dict[str, str]] = {
    RelationshipCategory.MANAGER: {
        "label": "MANAGER",
        "color": "red bold",
        "icon": "!",
        "description": "Controls lifecycle (changes here override this resource)",
    },
    RelationshipCategory.IDENTITY: {
        "label": "IDENTITY",
        "color": "magenta",
        "icon": "I",
        "description": "IAM roles and permissions",
    },
    RelationshipCategory.NETWORK: {
        "label": "NETWORK",
        "color": "cyan",
        "icon": "N",
        "description": "Networking context (VPC, Subnet, Security Groups)",
    },
    RelationshipCategory.STORAGE: {
        "label": "STORAGE",
        "color": "yellow",
        "icon": "S",
        "description": "Attached storage and encryption",
    },
    RelationshipCategory.SOURCE: {
        "label": "SOURCE",
        "color": "blue",
        "icon": "A",
        "description": "Base image/template",
    },
    RelationshipCategory.ATTACHED: {
        "label": "ATTACHED",
        "color": "green",
        "icon": "D",
        "description": "Resources depending on this one",
    },
    RelationshipCategory.OTHER: {
        "label": "OTHER",
        "color": "dim",
        "icon": "?",
        "description": "Miscellaneous dependencies",
    },
}


def get_category(resource_type: str) -> RelationshipCategory:
    """Get the relationship category for a resource type."""
    return RESOURCE_CATEGORY_MAP.get(resource_type, RelationshipCategory.OTHER)


class DependencyExplorerReporter:
    """Generate dependency exploration reports in various formats."""

    def to_console(self, result: DependencyExplorerResult) -> None:
        """Print dependency exploration to console with grouped dependencies."""
        console.print("\n[bold blue]Dependency Explorer[/bold blue]")
        console.print(f"[dim]{DISCLAIMER_SHORT}[/dim]\n")

        # Show ASG warning FIRST if applicable (P0 - most important)
        if result.asg_info:
            console.print(
                Panel(
                    f"[red bold]WARNING: This instance is managed by Auto Scaling Group![/red bold]\n\n"
                    f"[yellow]ASG Name:[/yellow] {result.asg_info.name}\n\n"
                    f"[red]Any manual changes to this instance may be overwritten by the ASG![/red]\n"
                    f"[red]To make persistent changes, modify the Launch Template instead.[/red]\n\n"
                    f"[bold]Next Best Action:[/bold]\n"
                    f"  1. Find the Launch Template for ASG '{result.asg_info.name}'\n"
                    f"  2. Modify the Launch Template configuration\n"
                    f"  3. Trigger an instance refresh on the ASG",
                    title="[red bold]! ASG-MANAGED INSTANCE ![/red bold]",
                    border_style="red",
                )
            )
            console.print()

        # Resource context panel
        config = result.center_config
        context_lines = []

        # Build context info for EC2 instances
        if result.center_resource.type == "aws_instance":
            if config.get("vpc_id"):
                context_lines.append(f"[cyan]VPC:[/cyan] {config['vpc_id']}")
            if config.get("subnet_id"):
                context_lines.append(f"[cyan]Subnet:[/cyan] {config['subnet_id']}")
            if config.get("availability_zone"):
                context_lines.append(f"[cyan]AZ:[/cyan] {config['availability_zone']}")
            if config.get("instance_type"):
                context_lines.append(
                    f"[cyan]Instance Type:[/cyan] {config['instance_type']}"
                )
            if config.get("iam_instance_profile"):
                profile = config["iam_instance_profile"]
                if isinstance(profile, dict):
                    context_lines.append(
                        f"[magenta]IAM Profile:[/magenta] {profile.get('name', 'N/A')}"
                    )

        # Summary panel with context
        impact_color = self._get_impact_color(result.estimated_impact)
        summary = f"""[bold]Center Resource:[/bold] {result.center_resource.id}
[bold]Type:[/bold] {result.center_resource.type}
[bold]Name:[/bold] {result.center_resource.name}

[{impact_color}]Estimated Impact: {result.estimated_impact.value} ({result.estimated_score}/100)[/{impact_color}]
[bold]Resources Found:[/bold] {result.total_affected}
"""
        if context_lines:
            summary += "\n[bold]Context:[/bold]\n  " + "\n  ".join(context_lines)

        console.print(
            Panel(summary.strip(), title="Summary", border_style=impact_color)
        )

        # Categorize resources
        upstream = [r for r in result.affected_resources if r.depth < 0]
        downstream = [r for r in result.affected_resources if r.depth > 0]

        # Group upstream by category
        if upstream:
            self._print_categorized_dependencies(
                upstream,
                "Dependencies (Resources This Resource Uses)",
                is_upstream=True,
            )

        # Group downstream by category
        if downstream:
            self._print_categorized_dependencies(
                downstream,
                "Dependents (Resources That Use This Resource)",
                is_upstream=False,
            )

        # Warnings section
        if result.warnings:
            console.print("\n[bold yellow]Warnings:[/bold yellow]")
            for warning in result.warnings:
                if "ASG" in warning or "CRITICAL" in warning:
                    console.print(f"  [red bold]![/red bold] [red]{warning}[/red]")
                else:
                    console.print(f"  [yellow]![/yellow] {warning}")

        # Next Best Actions
        self._print_next_actions(result)

        # Always end with disclaimer
        console.print()
        console.print(
            Panel(
                DISCLAIMER_FULL.strip(),
                title="Important Disclaimer",
                border_style="yellow",
            )
        )

    def _print_categorized_dependencies(
        self,
        resources: list[ResourceNode],
        title: str,
        is_upstream: bool,
    ) -> None:
        """Print dependencies grouped by relationship category."""
        # Group by category
        by_category: dict[RelationshipCategory, list[ResourceNode]] = {}
        for r in resources:
            cat = get_category(r.type)
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(r)

        console.print(f"\n[bold]{title}[/bold]")

        # Priority order for categories
        category_order = [
            RelationshipCategory.MANAGER,
            RelationshipCategory.IDENTITY,
            RelationshipCategory.NETWORK,
            RelationshipCategory.STORAGE,
            RelationshipCategory.SOURCE,
            RelationshipCategory.ATTACHED,
            RelationshipCategory.OTHER,
        ]

        for cat in category_order:
            if cat not in by_category:
                continue

            cat_resources = by_category[cat]
            cfg = CATEGORY_CONFIG[cat]
            color = cfg["color"]
            label = cfg["label"]
            desc = cfg["description"]

            console.print(
                f"\n  [{color}][{label}][/{color}] [dim]({desc})[/dim]"
            )

            for r in cat_resources:
                impact_color = self._get_impact_color(r.impact_level)
                # Show resource type in a more readable format
                type_short = r.type.replace("aws_", "")
                console.print(
                    f"    [{color}]{cfg['icon']}[/{color}] "
                    f"[{impact_color}]{type_short}[/{impact_color}]: {r.id}"
                )

    def _print_next_actions(self, result: DependencyExplorerResult) -> None:
        """Print suggested next actions based on the analysis."""
        console.print("\n[bold green]Next Best Actions:[/bold green]")

        actions = []

        # ASG-specific actions
        if result.asg_info:
            actions.append(
                f"Review ASG '{result.asg_info.name}' and its Launch Template"
            )
            actions.append("Modify Launch Template instead of this instance directly")

        # Security Group actions
        sg_resources = [
            r for r in result.affected_resources if r.type == "aws_security_group"
        ]
        if sg_resources:
            sg_count = len(sg_resources)
            actions.append(
                f"Review {sg_count} Security Group(s) for blast radius implications"
            )

        # General actions
        if result.total_affected > 1:
            actions.append(
                f"Validate all {result.total_affected} affected resources before changes"
            )

        actions.append("Check application logs and configs for hidden dependencies")

        for i, action in enumerate(actions, 1):
            console.print(f"  {i}. {action}")

    def to_tree(self, result: DependencyExplorerResult) -> None:
        """Print dependency exploration as a hierarchical tree."""
        # Show ASG warning first
        if result.asg_info:
            console.print(
                f"\n[red bold]! ASG-MANAGED: {result.asg_info.name}[/red bold]"
            )

        console.print(f"\n[dim]{DISCLAIMER_SHORT}[/dim]")

        center = result.center_resource
        config = result.center_config

        # Build center label with context
        center_label = f"[bold cyan]{center.type}[/bold cyan]: {center.id}"
        if center.name and center.name != center.id:
            center_label += f" ({center.name})"

        tree = Tree(center_label)

        # Add upstream dependencies (what this resource uses)
        upstream = [r for r in result.affected_resources if r.depth < 0]
        if upstream:
            upstream_branch = tree.add("[magenta]Uses (upstream dependencies)[/magenta]")
            self._build_categorized_tree(upstream_branch, upstream)

        # Add context info for EC2
        if center.type == "aws_instance" and config:
            context_branch = tree.add("[dim]Context[/dim]")
            if config.get("vpc_id"):
                context_branch.add(f"[cyan]VPC:[/cyan] {config['vpc_id']}")
            if config.get("subnet_id"):
                context_branch.add(f"[cyan]Subnet:[/cyan] {config['subnet_id']}")
            if config.get("availability_zone"):
                context_branch.add(f"[cyan]AZ:[/cyan] {config['availability_zone']}")
            if config.get("asg_name"):
                context_branch.add(
                    f"[red bold]ASG:[/red bold] {config['asg_name']} [red](manages this instance)[/red]"
                )

        # Add downstream dependencies (what uses this resource)
        downstream = [r for r in result.affected_resources if r.depth > 0]
        if downstream:
            downstream_branch = tree.add(
                "[yellow]Used by (downstream dependencies)[/yellow]"
            )
            self._build_categorized_tree(downstream_branch, downstream)

        console.print("\n[bold]Dependency Tree:[/bold]\n")
        console.print(tree)

        # Next actions
        self._print_next_actions(result)

        # Disclaimer at end
        console.print()
        console.print(
            "[yellow]Note: This tree shows AWS API-detected dependencies only.[/yellow]"
        )
        console.print("[yellow]Application-level dependencies are NOT shown.[/yellow]")

    def _build_categorized_tree(
        self,
        parent: Tree,
        resources: list[ResourceNode],
    ) -> None:
        """Build tree branches organized by category."""
        # Group by category
        by_category: dict[RelationshipCategory, list[ResourceNode]] = {}
        for r in resources:
            cat = get_category(r.type)
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(r)

        # Priority order for categories
        category_order = [
            RelationshipCategory.MANAGER,
            RelationshipCategory.IDENTITY,
            RelationshipCategory.NETWORK,
            RelationshipCategory.STORAGE,
            RelationshipCategory.SOURCE,
            RelationshipCategory.ATTACHED,
            RelationshipCategory.OTHER,
        ]

        for cat in category_order:
            if cat not in by_category:
                continue

            cat_resources = by_category[cat]
            cfg = CATEGORY_CONFIG[cat]
            color = cfg["color"]
            label = cfg["label"]

            cat_branch = parent.add(f"[{color}][{label}][/{color}]")
            for r in cat_resources:
                type_short = r.type.replace("aws_", "")
                cat_branch.add(f"[{color}]{type_short}[/{color}]: {r.id}")

    def _build_tree(
        self,
        parent: Tree,
        resource_id: str,
        result: DependencyExplorerResult,
        visited: set[str],
    ) -> None:
        """Recursively build tree (legacy method for backward compatibility)."""
        if resource_id in visited:
            return
        visited.add(resource_id)

        # Find dependents (resources that depend on this one)
        for resource in result.affected_resources:
            if resource_id in resource.depends_on:
                color = self._get_impact_color(resource.impact_level)
                label = f"[{color}]{resource.type}[/{color}]: {resource.id}"
                branch = parent.add(label)
                self._build_tree(branch, resource.id, result, visited)

    def to_json(self, result: DependencyExplorerResult, output_path: Path) -> Path:
        """Export to JSON with disclaimer."""
        data = result.to_dict()
        output_path.write_text(json.dumps(data, indent=2))
        console.print(f"[green]Exported to {output_path}[/green]")
        console.print(f"[dim]{DISCLAIMER_SHORT}[/dim]")
        return output_path

    def to_html(self, result: DependencyExplorerResult, output_path: Path) -> Path:
        """Export to HTML with D3.js visualization and prominent disclaimers."""
        html = self._generate_html(result)
        output_path.write_text(html)
        console.print(f"[green]Exported to {output_path}[/green]")
        console.print(f"[dim]{DISCLAIMER_SHORT}[/dim]")
        return output_path

    def to_table(self, result: DependencyExplorerResult) -> None:
        """Print affected resources as a table."""
        # Show disclaimer first
        console.print(f"\n[dim]{DISCLAIMER_SHORT}[/dim]\n")

        table = Table(title="Potentially Affected Resources (AWS API metadata only)")
        table.add_column("Depth", justify="center")
        table.add_column("Resource ID", style="cyan")
        table.add_column("Type")
        table.add_column("Name")
        table.add_column("Est. Impact", justify="center")
        table.add_column("Score", justify="right")

        for resource in sorted(result.affected_resources, key=lambda r: r.depth):
            color = self._get_impact_color(resource.impact_level)
            table.add_row(
                str(resource.depth),
                resource.id[:40] + ("..." if len(resource.id) > 40 else ""),
                resource.type,
                resource.name[:30] + ("..." if len(resource.name) > 30 else ""),
                f"[{color}]{resource.impact_level.value}[/{color}]",
                str(resource.impact_score),
            )

        console.print(table)

        # Disclaimer after table
        console.print()
        console.print("[yellow]Note: Impact levels are estimates only.[/yellow]")

    def _get_impact_color(self, level: ImpactLevel) -> str:
        """Get color for impact level."""
        colors = {
            ImpactLevel.CRITICAL: "red bold",
            ImpactLevel.HIGH: "red",
            ImpactLevel.MEDIUM: "yellow",
            ImpactLevel.LOW: "blue",
            ImpactLevel.NONE: "dim",
            ImpactLevel.UNKNOWN: "dim italic",
        }
        return colors.get(level, "white")

    def _generate_html(self, result: DependencyExplorerResult) -> str:
        """Generate HTML report with D3.js visualization and prominent disclaimers."""
        # Prepare nodes for D3.js
        nodes_js = []
        for resource in result.affected_resources:
            color = {
                ImpactLevel.CRITICAL: "#e74c3c",
                ImpactLevel.HIGH: "#e67e22",
                ImpactLevel.MEDIUM: "#f1c40f",
                ImpactLevel.LOW: "#3498db",
                ImpactLevel.NONE: "#95a5a6",
                ImpactLevel.UNKNOWN: "#7f8c8d",
            }.get(resource.impact_level, "#95a5a6")

            size = 10 + (resource.impact_score / 10)

            nodes_js.append(
                {
                    "id": resource.id,
                    "type": resource.type,
                    "name": resource.name,
                    "impact": resource.impact_level.value,
                    "score": resource.impact_score,
                    "depth": resource.depth,
                    "color": color,
                    "size": size,
                    "isCenter": resource.depth == 0,
                }
            )

        # Prepare edges for D3.js
        edges_js = []
        affected_ids = {r.id for r in result.affected_resources}
        for resource in result.affected_resources:
            for dep_id in resource.depends_on:
                if dep_id in affected_ids:
                    edges_js.append(
                        {
                            "source": resource.id,
                            "target": dep_id,
                        }
                    )

        # Generate warnings HTML
        warnings_html = ""
        if result.warnings:
            warnings_html = "\n".join(
                f'<div class="warning">{w}</div>' for w in result.warnings
            )

        # Generate limitations HTML
        limitations_html = "\n".join(f"<li>{lim}</li>" for lim in result.limitations)

        # Generate zone summary
        zones_html = ""
        for zone in result.zones:
            zone_class = "zone-center" if zone.depth == 0 else ""
            zones_html += f"""
            <div class="zone {zone_class}">
                <strong>Depth {zone.depth}</strong>: {len(zone.resources)} resources
                (Est. Score: {zone.total_impact_score})
            </div>
            """

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dependency Explorer: {result.center_resource.id}</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        * {{
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            background: #1a1a2e;
            color: #eee;
        }}
        #header {{
            background: linear-gradient(135deg, #16213e 0%, #1a1a2e 100%);
            padding: 20px 30px;
            border-bottom: 1px solid #333;
        }}
        #header h1 {{
            margin: 0 0 10px 0;
            font-size: 24px;
            color: #3498db;
        }}
        #header .subtitle {{
            color: #888;
            font-size: 14px;
        }}
        .disclaimer {{
            background: #44350a;
            border: 2px solid #f1c40f;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 30px;
        }}
        .disclaimer-title {{
            color: #f1c40f;
            font-weight: bold;
            font-size: 18px;
            margin-bottom: 15px;
        }}
        .disclaimer p {{
            color: #ffeeba;
            margin: 10px 0;
        }}
        .disclaimer ul {{
            color: #ffeeba;
            margin: 10px 0;
            padding-left: 20px;
        }}
        .disclaimer li {{
            margin: 5px 0;
        }}
        .disclaimer-critical {{
            font-weight: bold;
            color: #fff;
            background: #856404;
            padding: 10px;
            border-radius: 4px;
            margin-top: 15px;
        }}
        .stats {{
            display: flex;
            gap: 30px;
            margin-top: 15px;
        }}
        .stat {{
            text-align: center;
        }}
        .stat-value {{
            font-size: 28px;
            font-weight: bold;
        }}
        .stat-label {{
            font-size: 12px;
            color: #888;
            text-transform: uppercase;
        }}
        .stat-note {{
            font-size: 10px;
            color: #666;
            font-style: italic;
        }}
        .stat-critical {{ color: #e74c3c; }}
        .stat-high {{ color: #e67e22; }}
        .stat-medium {{ color: #f1c40f; }}
        .stat-unknown {{ color: #7f8c8d; }}
        .warning {{
            background: #44350a;
            border-left: 4px solid #f1c40f;
            color: #f1c40f;
            padding: 10px 15px;
            margin: 5px 30px;
            font-size: 14px;
        }}
        .zones {{
            padding: 15px 30px;
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }}
        .zone {{
            background: #222;
            padding: 10px 15px;
            border-radius: 5px;
            font-size: 13px;
        }}
        .zone-center {{
            border: 2px solid #3498db;
        }}
        #graph {{
            width: 100%;
            height: calc(100vh - 450px);
            min-height: 400px;
        }}
        .tooltip {{
            position: absolute;
            background: #333;
            border: 1px solid #555;
            padding: 10px;
            border-radius: 5px;
            font-size: 12px;
            pointer-events: none;
            z-index: 100;
        }}
        .node text {{
            font-size: 10px;
            fill: #ccc;
        }}
        .link {{
            stroke: #555;
            stroke-opacity: 0.6;
        }}
        .node-center circle {{
            stroke: #fff;
            stroke-width: 3px;
        }}
        #review-order {{
            padding: 20px 30px;
            background: #16213e;
        }}
        #review-order h3 {{
            margin: 0 0 5px 0;
            font-size: 16px;
        }}
        #review-order .note {{
            color: #f1c40f;
            font-size: 13px;
            margin-bottom: 15px;
        }}
        #review-order ol {{
            margin: 0;
            padding-left: 20px;
            columns: 2;
        }}
        #review-order li {{
            font-size: 13px;
            color: #aaa;
            margin-bottom: 5px;
        }}
        .footer-disclaimer {{
            background: #44350a;
            border-top: 2px solid #f1c40f;
            padding: 20px 30px;
            margin-top: 20px;
        }}
        .footer-disclaimer p {{
            color: #ffeeba;
            margin: 5px 0;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div id="header">
        <h1>Dependency Explorer</h1>
        <div class="subtitle">
            <strong>{result.center_resource.type}</strong>: {result.center_resource.id}
            ({result.center_resource.name})
        </div>
        <div class="stats">
            <div class="stat">
                <div class="stat-value stat-{result.estimated_impact.value.lower()}">{result.estimated_impact.value}</div>
                <div class="stat-label">Est. Impact</div>
                <div class="stat-note">(estimate only)</div>
            </div>
            <div class="stat">
                <div class="stat-value">{result.total_affected}</div>
                <div class="stat-label">Resources Found</div>
                <div class="stat-note">(via AWS API)</div>
            </div>
            <div class="stat">
                <div class="stat-value">{result.max_depth}</div>
                <div class="stat-label">Max Depth</div>
            </div>
            <div class="stat">
                <div class="stat-value">{result.estimated_score}/100</div>
                <div class="stat-label">Est. Score</div>
                <div class="stat-note">(estimate only)</div>
            </div>
        </div>
    </div>

    <!-- Prominent disclaimer at top -->
    <div class="disclaimer">
        <div class="disclaimer-title">Important Disclaimer</div>
        <p>This analysis is based on <strong>AWS API metadata only</strong>.</p>
        <p>The following dependencies <strong>CANNOT</strong> be detected:</p>
        <ul>
            {limitations_html}
        </ul>
        <div class="disclaimer-critical">
            ALWAYS review application logs, code, and configuration before making any infrastructure changes.
            RepliMap provides suggestions only.
        </div>
    </div>

    {warnings_html}
    <div class="zones">{zones_html}</div>
    <div id="graph"></div>

    <div id="review-order">
        <h3>Suggested Review Order</h3>
        <div class="note">This is a SUGGESTION only. Validate all dependencies before making any changes.</div>
        <ol>
            {"".join(f"<li>{rid}</li>" for rid in result.suggested_review_order[:20])}
            {f"<li>... and {len(result.suggested_review_order) - 20} more</li>" if len(result.suggested_review_order) > 20 else ""}
        </ol>
    </div>

    <!-- Disclaimer at bottom too -->
    <div class="footer-disclaimer">
        <p><strong>RepliMap provides suggestions only.</strong></p>
        <p>You are responsible for validating all dependencies before making changes to your infrastructure.</p>
        <p>This analysis cannot detect application-level dependencies, hardcoded IPs, DNS references, or configuration file dependencies.</p>
    </div>

    <div class="tooltip" style="display: none;"></div>

    <script>
        const nodes = {json.dumps(nodes_js)};
        const links = {json.dumps(edges_js)};

        const width = window.innerWidth;
        const height = Math.max(400, window.innerHeight - 500);

        const svg = d3.select("#graph")
            .append("svg")
            .attr("width", "100%")
            .attr("height", height)
            .attr("viewBox", [0, 0, width, height]);

        // Add arrow marker for edges
        svg.append("defs").append("marker")
            .attr("id", "arrow")
            .attr("viewBox", "0 -5 10 10")
            .attr("refX", 20)
            .attr("refY", 0)
            .attr("markerWidth", 6)
            .attr("markerHeight", 6)
            .attr("orient", "auto")
            .append("path")
            .attr("d", "M0,-5L10,0L0,5")
            .attr("fill", "#555");

        const simulation = d3.forceSimulation(nodes)
            .force("link", d3.forceLink(links).id(d => d.id).distance(120))
            .force("charge", d3.forceManyBody().strength(-300))
            .force("center", d3.forceCenter(width / 2, height / 2))
            .force("collision", d3.forceCollide().radius(d => d.size + 10));

        const link = svg.append("g")
            .selectAll("line")
            .data(links)
            .join("line")
            .attr("class", "link")
            .attr("marker-end", "url(#arrow)");

        const node = svg.append("g")
            .selectAll("g")
            .data(nodes)
            .join("g")
            .attr("class", d => d.isCenter ? "node node-center" : "node")
            .call(d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended));

        node.append("circle")
            .attr("r", d => d.size)
            .attr("fill", d => d.color);

        node.append("text")
            .text(d => d.id.substring(0, 20))
            .attr("x", d => d.size + 5)
            .attr("y", 3);

        // Tooltip
        const tooltip = d3.select(".tooltip");

        node.on("mouseover", (event, d) => {{
            tooltip.style("display", "block")
                .html(`
                    <strong>${{d.type}}</strong><br/>
                    ID: ${{d.id}}<br/>
                    Name: ${{d.name}}<br/>
                    Est. Impact: ${{d.impact}} (${{d.score}}/100)<br/>
                    Depth: ${{d.depth}}<br/>
                    <em style="color: #888; font-size: 10px;">Impact is an estimate only</em>
                `)
                .style("left", (event.pageX + 15) + "px")
                .style("top", (event.pageY - 10) + "px");
        }})
        .on("mouseout", () => {{
            tooltip.style("display", "none");
        }});

        simulation.on("tick", () => {{
            link
                .attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);

            node.attr("transform", d => `translate(${{d.x}},${{d.y}})`);
        }});

        function dragstarted(event) {{
            if (!event.active) simulation.alphaTarget(0.3).restart();
            event.subject.fx = event.subject.x;
            event.subject.fy = event.subject.y;
        }}

        function dragged(event) {{
            event.subject.fx = event.x;
            event.subject.fy = event.y;
        }}

        function dragended(event) {{
            if (!event.active) simulation.alphaTarget(0);
            event.subject.fx = null;
            event.subject.fy = null;
        }}
    </script>
</body>
</html>"""


# Backward compatibility alias
BlastRadiusReporter = DependencyExplorerReporter
