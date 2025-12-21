"""
Cost estimate report formatting.

Generates console output, JSON, and HTML reports for cost analysis.
"""

from __future__ import annotations

import json
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from replimap.cost.models import CostConfidence, CostEstimate

console = Console()


class CostReporter:
    """Generate cost estimate reports in various formats."""

    def to_console(self, estimate: CostEstimate) -> None:
        """Print cost estimate to console."""
        # Header
        console.print("\n[bold]Cost Estimate Report[/bold]\n")

        # Summary panel
        confidence_color = self._get_confidence_color(estimate.confidence)

        summary = f"""
[bold]Monthly Total:[/bold] ${estimate.monthly_total:,.2f}
[bold]Annual Total:[/bold] ${estimate.annual_total:,.2f}
[bold]Daily Average:[/bold] ${estimate.daily_average:,.2f}

[bold]Resources:[/bold] {estimate.resource_count} total
[bold]Estimated:[/bold] {estimate.estimated_resources} | [dim]Unestimated:[/dim] {estimate.unestimated_resources}
[{confidence_color}]Confidence: {estimate.confidence.value}[/{confidence_color}]
"""
        console.print(Panel(summary.strip(), title="Summary", border_style="blue"))

        # Warnings
        if estimate.warnings:
            console.print("\n[bold yellow]Warnings:[/bold yellow]")
            for warning in estimate.warnings:
                console.print(f"  [yellow]![/yellow] {warning}")

        # Cost by category
        console.print("\n[bold]Cost by Category:[/bold]\n")

        for breakdown in estimate.by_category:
            bar_width = int(breakdown.percentage / 2)  # Scale to max 50 chars
            bar = "█" * bar_width + "░" * (50 - bar_width)
            console.print(
                f"  {breakdown.category.value:12} ${breakdown.monthly_total:>10,.2f} "
                f"({breakdown.percentage:5.1f}%) [{bar}]"
            )

        # Top resources
        console.print("\n[bold]Top 10 Most Expensive Resources:[/bold]\n")

        table = Table()
        table.add_column("Resource", style="cyan", max_width=40)
        table.add_column("Type")
        table.add_column("Instance", max_width=15)
        table.add_column("Monthly", justify="right", style="green")
        table.add_column("Savings", justify="right", style="yellow")

        for r in estimate.top_resources[:10]:
            savings = f"${r.optimization_potential:,.0f}" if r.optimization_potential > 0 else "-"
            table.add_row(
                self._truncate(r.resource_name, 40),
                r.resource_type.replace("aws_", ""),
                r.instance_type or "-",
                f"${r.monthly_cost:,.2f}",
                savings,
            )

        console.print(table)

        # Cost by region
        if len(estimate.by_region) > 1:
            console.print("\n[bold]Cost by Region:[/bold]\n")
            for region, cost in sorted(
                estimate.by_region.items(), key=lambda x: x[1], reverse=True
            ):
                pct = (cost / estimate.monthly_total * 100) if estimate.monthly_total > 0 else 0
                console.print(f"  {region:20} ${cost:>10,.2f} ({pct:5.1f}%)")

        # Optimization recommendations
        if estimate.recommendations:
            console.print("\n[bold]Optimization Recommendations:[/bold]\n")

            for i, rec in enumerate(estimate.recommendations[:5], 1):
                effort_color = {
                    "LOW": "green",
                    "MEDIUM": "yellow",
                    "HIGH": "red",
                }.get(rec.effort, "white")

                console.print(
                    f"  [bold]{i}. {rec.title}[/bold] "
                    f"[{effort_color}]({rec.effort} effort)[/{effort_color}]"
                )
                console.print(f"     {rec.description}")
                console.print(f"     [green]Potential savings: ${rec.potential_savings:,.2f}/month[/green]")
                console.print()

            if estimate.total_optimization_potential > 0:
                console.print(
                    f"[bold green]Total Optimization Potential: "
                    f"${estimate.total_optimization_potential:,.2f}/month "
                    f"({estimate.optimization_percentage:.1f}%)[/bold green]"
                )

        # Assumptions
        if estimate.assumptions:
            console.print("\n[dim]Assumptions:[/dim]")
            for assumption in estimate.assumptions[:10]:
                console.print(f"  [dim]• {assumption}[/dim]")
            if len(estimate.assumptions) > 10:
                console.print(f"  [dim]• ... and {len(estimate.assumptions) - 10} more[/dim]")

    def to_table(self, estimate: CostEstimate) -> None:
        """Print all resources as a table."""
        table = Table(title="Resource Costs")
        table.add_column("Resource ID", style="cyan", max_width=35)
        table.add_column("Type", max_width=20)
        table.add_column("Category")
        table.add_column("Instance")
        table.add_column("Monthly", justify="right", style="green")
        table.add_column("Annual", justify="right")
        table.add_column("Confidence")

        for r in sorted(estimate.resource_costs, key=lambda x: x.monthly_cost, reverse=True):
            confidence_color = self._get_confidence_color(r.confidence)
            table.add_row(
                self._truncate(r.resource_id, 35),
                r.resource_type.replace("aws_", ""),
                r.category.value,
                r.instance_type or "-",
                f"${r.monthly_cost:,.2f}",
                f"${r.annual_cost:,.2f}",
                f"[{confidence_color}]{r.confidence.value}[/{confidence_color}]",
            )

        console.print(table)

    def to_json(self, estimate: CostEstimate, output_path: Path) -> Path:
        """Export to JSON."""
        data = estimate.to_dict()
        output_path.write_text(json.dumps(data, indent=2))
        console.print(f"[green]Exported to {output_path}[/green]")
        return output_path

    def to_html(self, estimate: CostEstimate, output_path: Path) -> Path:
        """Export to HTML report."""
        html = self._generate_html(estimate)
        output_path.write_text(html)
        console.print(f"[green]Exported to {output_path}[/green]")
        return output_path

    def to_csv(self, estimate: CostEstimate, output_path: Path) -> Path:
        """Export to CSV."""
        lines = [
            "resource_id,resource_type,category,instance_type,monthly_cost,annual_cost,confidence"
        ]

        for r in estimate.resource_costs:
            lines.append(
                f'"{r.resource_id}",{r.resource_type},{r.category.value},'
                f'{r.instance_type},{r.monthly_cost:.2f},{r.annual_cost:.2f},{r.confidence.value}'
            )

        output_path.write_text("\n".join(lines))
        console.print(f"[green]Exported to {output_path}[/green]")
        return output_path

    def _get_confidence_color(self, confidence: CostConfidence) -> str:
        """Get color for confidence level."""
        colors = {
            CostConfidence.HIGH: "green",
            CostConfidence.MEDIUM: "yellow",
            CostConfidence.LOW: "red",
            CostConfidence.UNKNOWN: "dim",
        }
        return colors.get(confidence, "white")

    def _truncate(self, text: str, max_len: int) -> str:
        """Truncate text with ellipsis."""
        if len(text) <= max_len:
            return text
        return text[: max_len - 3] + "..."

    def _generate_html(self, estimate: CostEstimate) -> str:
        """Generate HTML report."""
        # Build category chart data
        category_data = [
            {"name": b.category.value, "value": round(b.monthly_total, 2)}
            for b in estimate.by_category
        ]

        # Build top resources data
        top_data = [
            {
                "id": r.resource_id[:30],
                "type": r.resource_type,
                "cost": round(r.monthly_cost, 2),
            }
            for r in estimate.top_resources[:10]
        ]

        # Build recommendations HTML
        recommendations_html = ""
        for i, rec in enumerate(estimate.recommendations[:5], 1):
            effort_class = rec.effort.lower()
            recommendations_html += f"""
            <div class="recommendation">
                <div class="rec-header">
                    <span class="rec-title">{i}. {rec.title}</span>
                    <span class="effort effort-{effort_class}">{rec.effort}</span>
                </div>
                <p>{rec.description}</p>
                <div class="savings">Potential savings: ${rec.potential_savings:,.2f}/month</div>
            </div>
            """

        # Build warnings HTML
        warnings_html = ""
        if estimate.warnings:
            warnings_html = "\n".join(
                f'<div class="warning">{w}</div>' for w in estimate.warnings
            )

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cost Estimate Report</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            background: #f5f5f5;
            color: #333;
        }}
        #header {{
            background: linear-gradient(135deg, #1a73e8 0%, #174ea6 100%);
            color: white;
            padding: 30px;
        }}
        #header h1 {{
            margin: 0 0 10px 0;
            font-size: 28px;
        }}
        .stats {{
            display: flex;
            gap: 40px;
            margin-top: 20px;
        }}
        .stat {{
            text-align: center;
        }}
        .stat-value {{
            font-size: 36px;
            font-weight: bold;
        }}
        .stat-label {{
            font-size: 12px;
            opacity: 0.8;
            text-transform: uppercase;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        .card {{
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            padding: 20px;
            margin-bottom: 20px;
        }}
        .card h2 {{
            margin: 0 0 15px 0;
            font-size: 18px;
            color: #333;
        }}
        .warning {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            color: #856404;
            padding: 10px 15px;
            margin: 5px 0;
            font-size: 14px;
        }}
        .grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }}
        @media (max-width: 768px) {{
            .grid {{
                grid-template-columns: 1fr;
            }}
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th, td {{
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }}
        th {{
            font-weight: 600;
            color: #666;
            font-size: 12px;
            text-transform: uppercase;
        }}
        .cost {{
            color: #1a73e8;
            font-weight: 600;
        }}
        .recommendation {{
            background: #f8f9fa;
            border-radius: 6px;
            padding: 15px;
            margin-bottom: 10px;
        }}
        .rec-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }}
        .rec-title {{
            font-weight: 600;
        }}
        .effort {{
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
        }}
        .effort-low {{
            background: #d4edda;
            color: #155724;
        }}
        .effort-medium {{
            background: #fff3cd;
            color: #856404;
        }}
        .effort-high {{
            background: #f8d7da;
            color: #721c24;
        }}
        .savings {{
            color: #28a745;
            font-weight: 600;
            margin-top: 8px;
        }}
        #categoryChart {{
            max-height: 300px;
        }}
        .total-savings {{
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .total-savings .value {{
            font-size: 32px;
            font-weight: bold;
        }}
        .total-savings .label {{
            font-size: 14px;
            opacity: 0.9;
        }}
    </style>
</head>
<body>
    <div id="header">
        <h1>Cost Estimate Report</h1>
        <div class="stats">
            <div class="stat">
                <div class="stat-value">${estimate.monthly_total:,.2f}</div>
                <div class="stat-label">Monthly Total</div>
            </div>
            <div class="stat">
                <div class="stat-value">${estimate.annual_total:,.2f}</div>
                <div class="stat-label">Annual Total</div>
            </div>
            <div class="stat">
                <div class="stat-value">{estimate.resource_count}</div>
                <div class="stat-label">Resources</div>
            </div>
            <div class="stat">
                <div class="stat-value">{estimate.confidence.value}</div>
                <div class="stat-label">Confidence</div>
            </div>
        </div>
    </div>

    {warnings_html}

    <div class="container">
        <div class="grid">
            <div class="card">
                <h2>Cost by Category</h2>
                <canvas id="categoryChart"></canvas>
            </div>
            <div class="card">
                <h2>Top Resources</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Resource</th>
                            <th>Type</th>
                            <th style="text-align: right">Monthly</th>
                        </tr>
                    </thead>
                    <tbody>
                        {"".join(f'''
                        <tr>
                            <td>{r["id"]}</td>
                            <td>{r["type"].replace("aws_", "")}</td>
                            <td class="cost" style="text-align: right">${r["cost"]:,.2f}</td>
                        </tr>
                        ''' for r in top_data)}
                    </tbody>
                </table>
            </div>
        </div>

        <div class="card">
            <h2>Optimization Recommendations</h2>
            {recommendations_html if recommendations_html else '<p>No optimization recommendations at this time.</p>'}

            {f'''
            <div class="total-savings" style="margin-top: 20px">
                <div class="value">${estimate.total_optimization_potential:,.2f}</div>
                <div class="label">Potential Monthly Savings ({estimate.optimization_percentage:.1f}%)</div>
            </div>
            ''' if estimate.total_optimization_potential > 0 else ''}
        </div>

        <div class="card">
            <h2>All Resources</h2>
            <table>
                <thead>
                    <tr>
                        <th>Resource ID</th>
                        <th>Type</th>
                        <th>Category</th>
                        <th>Instance</th>
                        <th style="text-align: right">Monthly</th>
                        <th style="text-align: right">Annual</th>
                    </tr>
                </thead>
                <tbody>
                    {"".join(f'''
                    <tr>
                        <td>{r.resource_id[:40]}</td>
                        <td>{r.resource_type.replace("aws_", "")}</td>
                        <td>{r.category.value}</td>
                        <td>{r.instance_type or "-"}</td>
                        <td class="cost" style="text-align: right">${r.monthly_cost:,.2f}</td>
                        <td style="text-align: right">${r.annual_cost:,.2f}</td>
                    </tr>
                    ''' for r in sorted(estimate.resource_costs, key=lambda x: x.monthly_cost, reverse=True))}
                </tbody>
            </table>
        </div>
    </div>

    <script>
        const categoryData = {json.dumps(category_data)};

        new Chart(document.getElementById('categoryChart'), {{
            type: 'doughnut',
            data: {{
                labels: categoryData.map(d => d.name),
                datasets: [{{
                    data: categoryData.map(d => d.value),
                    backgroundColor: [
                        '#1a73e8',
                        '#34a853',
                        '#fbbc04',
                        '#ea4335',
                        '#9334e6',
                        '#00acc1',
                        '#ff6f00',
                    ]
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{
                        position: 'right'
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>"""
