"""
Cost estimate report formatting.

Generates console output, JSON, and HTML reports for cost analysis.
Includes prominent disclaimers about estimate accuracy.
"""

from __future__ import annotations

import json
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from replimap.cli.utils.console_links import get_console_url
from replimap.cost.models import (
    COST_DISCLAIMER_FULL,
    COST_DISCLAIMER_SHORT,
    EXCLUDED_FACTORS,
    CostConfidence,
    CostEstimate,
)

console = Console()


class CostReporter:
    """Generate cost estimate reports in various formats with disclaimers."""

    def to_console(self, estimate: CostEstimate) -> None:
        """Print cost estimate to console with prominent disclaimers."""
        # Header with warning
        console.print()
        console.print("[bold blue]💰 Cost Estimate[/bold blue]")
        console.print(f"[yellow]{COST_DISCLAIMER_SHORT}[/yellow]")
        console.print()

        # Confidence indicator
        confidence_color = self._get_confidence_color(estimate.confidence)

        # Summary panel with range
        summary = f"""
[bold]Monthly Estimate:[/bold] ${estimate.monthly_total:,.2f}
[dim]Range: ${estimate.estimated_range_low:,.2f} - ${estimate.estimated_range_high:,.2f} ({estimate.accuracy_range})[/dim]

[bold]Yearly Estimate:[/bold]  ${estimate.annual_total:,.2f}

[{confidence_color}]Confidence: {estimate.confidence.value} ({estimate.accuracy_range})[/{confidence_color}]
[dim]{estimate.confidence.description}[/dim]

[dim]Resources: {estimate.resource_count} total ({estimate.estimated_resources} priced)
Pricing: On-Demand (standard rates)[/dim]
"""
        console.print(
            Panel(summary.strip(), title="💰 Estimate Summary", border_style="blue")
        )

        # Warnings
        if estimate.warnings:
            console.print()
            for warning in estimate.warnings:
                console.print(f"[yellow]⚠️ {warning}[/yellow]")

        # Cost by category
        if estimate.by_category:
            console.print()
            console.print("[bold]Cost by Category:[/bold]")
            console.print()

            for breakdown in estimate.by_category:
                if breakdown.monthly_total > 0:
                    bar_width = int(breakdown.percentage / 2)  # Scale to max 50 chars
                    bar = "█" * bar_width + "░" * (50 - bar_width)
                    console.print(
                        f"  {breakdown.category.value:12} ${breakdown.monthly_total:>10,.2f} "
                        f"[dim]{bar}[/dim] {breakdown.percentage:5.1f}%"
                    )

        # Top resources table with confidence
        if estimate.top_resources:
            console.print()
            table = Table(title="Top 5 Estimated Costs")
            table.add_column("Resource", style="cyan", max_width=30)
            table.add_column("Type")
            table.add_column("Instance", max_width=15)
            table.add_column("Monthly Est.", justify="right", style="green")
            table.add_column("Confidence")

            for r in estimate.top_resources[:5]:
                conf_color = self._get_confidence_color(r.confidence)
                table.add_row(
                    self._truncate(r.resource_name, 30),
                    r.resource_type.replace("aws_", ""),
                    r.instance_type or "-",
                    f"${r.monthly_cost:,.2f}",
                    f"[{conf_color}]{r.confidence.value.lower()}[/{conf_color}]",
                )

            console.print(table)

        # Cost by region
        if len(estimate.by_region) > 1:
            console.print()
            console.print("[bold]Cost by Region:[/bold]")
            console.print()
            for region, cost in sorted(
                estimate.by_region.items(), key=lambda x: x[1], reverse=True
            ):
                pct = (
                    (cost / estimate.monthly_total * 100)
                    if estimate.monthly_total > 0
                    else 0
                )
                console.print(f"  {region:20} ${cost:>10,.2f} ({pct:5.1f}%)")

        # Optimization recommendations
        if estimate.recommendations:
            console.print()
            console.print("[bold]Optimization Recommendations:[/bold]")
            console.print()

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
                console.print(
                    f"     [green]Potential savings: ${rec.potential_savings:,.2f}/month[/green]"
                )
                console.print()

            if estimate.total_optimization_potential > 0:
                console.print(
                    f"[bold green]Total Optimization Potential: "
                    f"${estimate.total_optimization_potential:,.2f}/month "
                    f"({estimate.optimization_percentage:.1f}%)[/bold green]"
                )

        # Exclusions panel - always show
        self._print_exclusions()

        # Final disclaimer with links
        console.print()
        console.print(
            Panel(
                "[bold]For accurate cost projections, use:[/bold]\n"
                "• AWS Cost Explorer: https://console.aws.amazon.com/cost-management/\n"
                "• AWS Pricing Calculator: https://calculator.aws/",
                title="📊 Accurate Cost Tools",
                border_style="green",
            )
        )

    def _print_exclusions(self) -> None:
        """Print what's NOT included in the estimate."""
        console.print()
        console.print("[bold yellow]⚠️ NOT Included in This Estimate:[/bold yellow]")
        console.print()

        # Split into two columns
        half = len(EXCLUDED_FACTORS) // 2
        left = EXCLUDED_FACTORS[:half]
        right = EXCLUDED_FACTORS[half:]

        for i in range(max(len(left), len(right))):
            l_item = left[i] if i < len(left) else ""
            r_item = right[i] if i < len(right) else ""
            if l_item and r_item:
                console.print(f"  [dim]✗ {l_item:<35} ✗ {r_item}[/dim]")
            elif l_item:
                console.print(f"  [dim]✗ {l_item}[/dim]")
            elif r_item:
                console.print(f"  [dim]{' ' * 38} ✗ {r_item}[/dim]")

    def to_table(self, estimate: CostEstimate) -> None:
        """Print all resources as a table with disclaimer."""
        # Show disclaimer first
        console.print()
        console.print(f"[yellow]{COST_DISCLAIMER_SHORT}[/yellow]")
        console.print()

        table = Table(title="Resource Costs (Estimates Only)")
        table.add_column("Resource ID", style="cyan", max_width=35)
        table.add_column("Type", max_width=20)
        table.add_column("Category")
        table.add_column("Instance")
        table.add_column("Monthly Est.", justify="right", style="green")
        table.add_column("Annual Est.", justify="right")
        table.add_column("Confidence")

        for r in sorted(
            estimate.resource_costs, key=lambda x: x.monthly_cost, reverse=True
        ):
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

        # Show exclusions
        self._print_exclusions()

    def to_json(self, estimate: CostEstimate, output_path: Path) -> Path:
        """Export to JSON with full disclaimer."""
        data = estimate.to_dict()

        # Add full disclaimer at top level
        output = {
            "_disclaimer": COST_DISCLAIMER_FULL.strip(),
            "_generated_by": "RepliMap Cost Estimator",
            "_accuracy_note": f"Estimates are {estimate.accuracy_range} accurate",
            **data,
        }

        output_path.write_text(json.dumps(output, indent=2))
        console.print(f"[green]✓ Exported to {output_path}[/green]")
        console.print("[dim]Note: JSON includes full disclaimer[/dim]")
        return output_path

    def to_markdown(self, estimate: CostEstimate, output_path: Path) -> Path:
        """Export to Markdown with disclaimers."""
        conf = estimate.confidence

        md = f"""# Cost Estimate Report

> ⚠️ **DISCLAIMER:** {COST_DISCLAIMER_SHORT}

## Summary

| Metric | Value |
|--------|-------|
| **Monthly Estimate** | ${estimate.monthly_total:,.2f} |
| **Estimated Range** | ${estimate.estimated_range_low:,.2f} - ${estimate.estimated_range_high:,.2f} |
| **Confidence** | {conf.value} ({conf.accuracy_range}) |
| **Yearly Estimate** | ${estimate.annual_total:,.2f} |
| Resources | {estimate.resource_count} total |
| Pricing Model | On-Demand |

## Cost by Category

| Category | Monthly Est. | % of Total |
|----------|-------------|------------|
"""
        for b in estimate.by_category:
            if b.monthly_total > 0:
                md += f"| {b.category.value} | ${b.monthly_total:,.2f} | {b.percentage:.1f}% |\n"

        md += """
## Top 5 Costs

| Resource | Type | Monthly Est. | Confidence |
|----------|------|-------------|------------|
"""
        for r in estimate.top_resources[:5]:
            md += f"| {r.resource_name[:30]} | {r.resource_type.replace('aws_', '')} | ${r.monthly_cost:,.2f} | {r.confidence.value} |\n"

        md += """
## ⚠️ NOT Included in This Estimate

The following cost factors are **NOT** included and may significantly increase your actual bill:

"""
        for factor in EXCLUDED_FACTORS:
            md += f"- {factor}\n"

        # Add recommendations if any
        if estimate.recommendations:
            md += """
## Optimization Recommendations

"""
            for i, rec in enumerate(estimate.recommendations[:5], 1):
                md += f"### {i}. {rec.title}\n\n"
                md += f"{rec.description}\n\n"
                md += f"**Potential savings:** ${rec.potential_savings:,.2f}/month\n"
                md += f"**Effort:** {rec.effort}\n\n"

            if estimate.total_optimization_potential > 0:
                md += f"\n**Total potential savings:** ${estimate.total_optimization_potential:,.2f}/month ({estimate.optimization_percentage:.1f}%)\n"

        md += f"""
## Important Notes

1. This estimate is based on **standard on-demand pricing** only
2. Actual costs depend on your specific usage patterns
3. Data transfer costs alone can add 10-30% to your bill
4. Reserved Instances and Savings Plans may reduce costs significantly

## For Accurate Cost Projections

- **AWS Cost Explorer:** https://console.aws.amazon.com/cost-management/
- **AWS Pricing Calculator:** https://calculator.aws/

---

*Generated by RepliMap Cost Estimator*
*Confidence: {conf.value} ({conf.accuracy_range})*
*This is an estimate only and should not be used for financial planning without verification.*
"""

        output_path.write_text(md)
        console.print(f"[green]✓ Exported to {output_path}[/green]")
        return output_path

    def to_html(self, estimate: CostEstimate, output_path: Path) -> Path:
        """Export to HTML report with disclaimers."""
        html = self._generate_html(estimate)
        output_path.write_text(html)
        console.print(f"[green]✓ Exported to {output_path}[/green]")
        return output_path

    def to_csv(self, estimate: CostEstimate, output_path: Path) -> Path:
        """Export to CSV with disclaimer header."""
        lines = [
            f"# DISCLAIMER: {COST_DISCLAIMER_SHORT}",
            f"# Confidence: {estimate.confidence.value} ({estimate.accuracy_range})",
            f"# Monthly Total Estimate: ${estimate.monthly_total:,.2f}",
            f"# Range: ${estimate.estimated_range_low:,.2f} - ${estimate.estimated_range_high:,.2f}",
            "#",
            "resource_id,resource_type,category,instance_type,monthly_cost,annual_cost,confidence,accuracy_range",
        ]

        for r in estimate.resource_costs:
            lines.append(
                f'"{r.resource_id}",{r.resource_type},{r.category.value},'
                f"{r.instance_type},{r.monthly_cost:.2f},{r.annual_cost:.2f},"
                f"{r.confidence.value},{r.accuracy_range}"
            )

        output_path.write_text("\n".join(lines))
        console.print(f"[green]✓ Exported to {output_path}[/green]")
        console.print("[dim]Note: CSV includes disclaimer header[/dim]")
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

    def _generate_aws_console_link(
        self, resource_id: str, resource_type: str, region: str
    ) -> str:
        """Generate AWS Console deep link for a resource."""
        if not region:
            region = "us-east-1"
        return get_console_url(resource_type, resource_id, region)

    def _detect_environment(self, resource_name: str) -> str:
        """Detect environment from resource name."""
        name_lower = resource_name.lower()

        # Production indicators
        if any(p in name_lower for p in ["prod", "live", "production", "prd"]):
            return "PRODUCTION"
        # Non-production indicators
        elif any(
            p in name_lower
            for p in ["test", "dev", "stage", "uat", "qa", "sandbox", "demo"]
        ):
            return "NON-PRODUCTION"

        return "UNKNOWN"

    def _generate_html(self, estimate: CostEstimate) -> str:
        """Generate HTML report with disclaimers."""
        # Build category chart data for ECharts treemap
        category_data = []
        for b in estimate.by_category:
            if b.monthly_total > 0:
                # Get top 5 resources for drill-down
                top_res = sorted(
                    b.resources, key=lambda r: r.monthly_cost, reverse=True
                )[:5]
                children = [
                    {
                        "name": self._truncate(r.resource_name, 25),
                        "value": round(r.monthly_cost, 2),
                    }
                    for r in top_res
                ]
                category_data.append(
                    {
                        "name": b.category.value,
                        "value": round(b.monthly_total, 2),
                        "children": children,
                    }
                )

        # Calculate environment costs
        env_costs = {"PRODUCTION": 0.0, "NON-PRODUCTION": 0.0, "UNKNOWN": 0.0}
        for r in estimate.resource_costs:
            env = self._detect_environment(r.resource_name)
            env_costs[env] += r.monthly_cost

        # Count NAT gateways for estimator
        nat_gateways = [
            r for r in estimate.resource_costs if r.resource_type == "aws_nat_gateway"
        ]
        nat_count = len(nat_gateways)
        nat_hourly_total = sum(r.monthly_cost for r in nat_gateways)

        # Build recommendations HTML with filter buttons
        recommendations_html = ""
        for i, rec in enumerate(estimate.recommendations[:5], 1):
            effort_class = rec.effort.lower()
            affected_count = len(rec.affected_resources)
            # Determine filter keyword based on recommendation type
            filter_keyword = ""
            if "gp2" in rec.title.lower():
                filter_keyword = "gp2"
            elif "reserved" in rec.title.lower():
                filter_keyword = "instance"
            elif "nat" in rec.title.lower():
                filter_keyword = "nat_gateway"

            filter_btn = ""
            if filter_keyword and affected_count > 0:
                filter_btn = f"""
                <button class="btn-link" onclick="filterResources('{filter_keyword}')">
                    👉 View {affected_count} affected resources
                </button>
                """

            recommendations_html += f"""
            <div class="recommendation">
                <div class="rec-header">
                    <span class="rec-title">{i}. {rec.title}</span>
                    <span class="effort effort-{effort_class}">{rec.effort}</span>
                </div>
                <p>{rec.description}</p>
                <div class="savings">Potential savings: ${rec.potential_savings:,.2f}/month</div>
                {filter_btn}
            </div>
            """

        # Build warnings HTML
        warnings_html = ""
        if estimate.warnings:
            warnings_html = "\n".join(
                f'<div class="warning">{w}</div>' for w in estimate.warnings
            )

        # Build excluded factors list
        excluded_html = "\n".join(f"<li>{f}</li>" for f in EXCLUDED_FACTORS)

        # Build all resources table rows with console links
        all_resources_rows = ""
        for r in sorted(
            estimate.resource_costs, key=lambda x: x.monthly_cost, reverse=True
        ):
            console_link = self._generate_aws_console_link(
                r.resource_id, r.resource_type, r.region
            )
            env = self._detect_environment(r.resource_name)
            env_class = env.lower().replace("-", "")

            # Resource ID cell with optional link
            if console_link:
                resource_cell = f'<a href="{console_link}" target="_blank" title="{r.resource_id}">{self._truncate(r.resource_id, 35)} 🔗</a>'
            else:
                resource_cell = f'<span title="{r.resource_id}">{self._truncate(r.resource_id, 35)}</span>'

            all_resources_rows += f"""
                <tr>
                    <td class="resource-id">{resource_cell}</td>
                    <td>{r.resource_type.replace("aws_", "")}</td>
                    <td>{r.category.value}</td>
                    <td class="env-badge env-{env_class}">{env}</td>
                    <td>{r.instance_type or "-"}</td>
                    <td class="cost" style="text-align: right">${r.monthly_cost:,.2f}</td>
                    <td style="text-align: right">${r.annual_cost:,.2f}</td>
                    <td class="confidence-{r.confidence.value.lower()}">{r.confidence.value}</td>
                </tr>
            """

        # Calculate environment percentages
        prod_pct = (
            (env_costs["PRODUCTION"] / estimate.monthly_total * 100)
            if estimate.monthly_total > 0
            else 0
        )
        nonprod_pct = (
            (env_costs["NON-PRODUCTION"] / estimate.monthly_total * 100)
            if estimate.monthly_total > 0
            else 0
        )

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cost Estimate Report - RepliMap</title>
    <!-- DataTables CSS -->
    <link rel="stylesheet" href="https://cdn.datatables.net/1.13.7/css/dataTables.dataTables.min.css">
    <!-- ECharts -->
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
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
        .disclaimer-banner {{
            background: #fff3cd;
            border-bottom: 2px solid #ffc107;
            color: #856404;
            padding: 15px 30px;
            text-align: center;
            font-weight: 500;
        }}
        #header {{
            background: linear-gradient(135deg, #1a73e8 0%, #174ea6 100%);
            color: white;
            padding: 30px;
        }}
        #header h1 {{
            margin: 0 0 5px 0;
            font-size: 28px;
        }}
        #header .subtitle {{
            opacity: 0.8;
            font-size: 14px;
        }}
        .stats {{
            display: flex;
            gap: 30px;
            margin-top: 20px;
            flex-wrap: wrap;
            align-items: flex-start;
        }}
        .stat {{
            text-align: center;
        }}
        .stat-value {{
            font-size: 32px;
            font-weight: bold;
        }}
        .stat-label {{
            font-size: 12px;
            opacity: 0.8;
            text-transform: uppercase;
        }}
        .stat-range {{
            font-size: 12px;
            opacity: 0.7;
            margin-top: 4px;
        }}
        .stat.savings-highlight {{
            background: rgba(40, 167, 69, 0.3);
            padding: 15px 25px;
            border-radius: 8px;
            border: 2px solid #28a745;
        }}
        .stat.savings-highlight .stat-value {{
            color: #90EE90;
        }}
        .container {{
            max-width: 1400px;
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
        .exclusions {{
            background: #fef3e6;
            border: 1px solid #f0ad4e;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
        }}
        .exclusions h2 {{
            color: #856404;
            margin-top: 0;
        }}
        .exclusions ul {{
            columns: 2;
            list-style: none;
            padding: 0;
            margin: 0;
        }}
        .exclusions li {{
            padding: 4px 0;
            color: #856404;
        }}
        .exclusions li::before {{
            content: "✗ ";
            color: #dc3545;
        }}
        .grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }}
        .grid-3 {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
        }}
        @media (max-width: 1024px) {{
            .grid-3 {{
                grid-template-columns: 1fr 1fr;
            }}
        }}
        @media (max-width: 768px) {{
            .grid, .grid-3 {{
                grid-template-columns: 1fr;
            }}
            .exclusions ul {{
                columns: 1;
            }}
            .stats {{
                gap: 15px;
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
        .confidence-high {{
            color: #28a745;
        }}
        .confidence-medium {{
            color: #ffc107;
        }}
        .confidence-low {{
            color: #dc3545;
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
        .tools-box {{
            background: #d4edda;
            border: 1px solid #28a745;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            margin-bottom: 20px;
        }}
        .tools-box h2 {{
            color: #155724;
            margin-top: 0;
        }}
        .tools-box a {{
            color: #155724;
            font-weight: 500;
        }}
        footer {{
            text-align: center;
            padding: 30px;
            color: #666;
            font-size: 12px;
        }}
        /* Resource ID styling */
        .resource-id {{
            max-width: 280px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}
        .resource-id a {{
            color: #1a73e8;
            text-decoration: none;
        }}
        .resource-id a:hover {{
            text-decoration: underline;
        }}
        /* Environment badges */
        .env-badge {{
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
        }}
        .env-production {{
            background: #d4edda;
            color: #155724;
        }}
        .env-nonproduction {{
            background: #fff3cd;
            color: #856404;
        }}
        .env-unknown {{
            background: #e9ecef;
            color: #6c757d;
        }}
        /* Environment summary */
        .env-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
        }}
        .env-box {{
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }}
        .env-prod {{
            background: #e8f5e9;
            border: 1px solid #4caf50;
        }}
        .env-nonprod {{
            background: #fff3e0;
            border: 1px solid #ff9800;
        }}
        .env-value {{
            font-size: 24px;
            font-weight: bold;
            margin: 5px 0;
        }}
        .env-label {{
            font-size: 12px;
            text-transform: uppercase;
            color: #666;
        }}
        .env-percent {{
            font-size: 14px;
            color: #666;
        }}
        .env-warning {{
            color: #d32f2f;
            font-size: 12px;
            margin-top: 5px;
        }}
        /* NAT Calculator */
        .calculator-box {{
            background: #e3f2fd;
            border: 1px solid #2196f3;
            border-radius: 8px;
            padding: 15px;
            margin: 15px 0;
        }}
        .calculator-box h3 {{
            margin: 0 0 10px 0;
            color: #1565c0;
        }}
        .calc-input {{
            margin: 10px 0;
        }}
        .calc-input input {{
            width: 120px;
            padding: 8px;
            border: 1px solid #ccc;
            border-radius: 4px;
            font-size: 14px;
        }}
        .calc-result {{
            margin-top: 10px;
            padding: 10px;
            background: white;
            border-radius: 4px;
        }}
        .calc-total {{
            font-size: 18px;
            color: #1565c0;
            font-weight: bold;
        }}
        /* Button styles */
        .btn {{
            display: inline-block;
            padding: 8px 16px;
            background: #1a73e8;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            margin-right: 8px;
        }}
        .btn:hover {{
            background: #1557b0;
        }}
        .btn-link {{
            background: none;
            border: none;
            color: #1a73e8;
            cursor: pointer;
            padding: 5px 0;
            font-size: 13px;
            text-decoration: none;
        }}
        .btn-link:hover {{
            text-decoration: underline;
        }}
        .export-buttons {{
            margin-bottom: 15px;
        }}
        /* Table controls */
        .table-controls {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            flex-wrap: wrap;
            gap: 10px;
        }}
        .toggle-label {{
            display: flex;
            align-items: center;
            gap: 8px;
            cursor: pointer;
        }}
        /* DataTables overrides */
        .dataTables_wrapper .dataTables_filter input {{
            padding: 6px 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }}
        .dataTables_wrapper .dataTables_length select {{
            padding: 6px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }}
        /* Pagination styling */
        .dataTables_wrapper .dataTables_paginate {{
            margin-top: 15px;
            padding-top: 10px;
        }}
        .dataTables_wrapper .dataTables_paginate .paginate_button {{
            display: inline-block;
            padding: 6px 12px;
            margin: 0 3px;
            border: 1px solid #ddd;
            border-radius: 4px;
            background: #fff;
            color: #333 !important;
            cursor: pointer;
            text-decoration: none;
            font-size: 14px;
            min-width: 36px;
            text-align: center;
        }}
        .dataTables_wrapper .dataTables_paginate .paginate_button:hover {{
            background: #e9ecef;
            border-color: #adb5bd;
        }}
        .dataTables_wrapper .dataTables_paginate .paginate_button.current {{
            background: #1a73e8;
            border-color: #1a73e8;
            color: #fff !important;
            font-weight: 600;
        }}
        .dataTables_wrapper .dataTables_paginate .paginate_button.disabled {{
            color: #adb5bd !important;
            cursor: not-allowed;
            background: #f8f9fa;
            border-color: #e9ecef;
        }}
        .dataTables_wrapper .dataTables_paginate .paginate_button.disabled:hover {{
            background: #f8f9fa;
            border-color: #e9ecef;
        }}
        .dataTables_wrapper .dataTables_paginate .ellipsis {{
            padding: 6px 8px;
            color: #666;
        }}
        /* ECharts container */
        #treemapChart {{
            height: 350px;
        }}
        /* Dark Mode */
        @media (prefers-color-scheme: dark) {{
            body {{
                background: #121212;
                color: #e0e0e0;
            }}
            .card {{
                background: #1e1e1e;
                box-shadow: 0 2px 4px rgba(0,0,0,0.3);
            }}
            .card h2 {{
                color: #e0e0e0;
            }}
            table th {{
                color: #b0b0b0;
            }}
            table td {{
                border-bottom-color: #333;
            }}
            .cost {{
                color: #64b5f6;
            }}
            .disclaimer-banner {{
                background: #3e2723;
                border-bottom-color: #ff8f00;
                color: #ffcc80;
            }}
            .exclusions {{
                background: #3e2723;
                border-color: #ff8f00;
            }}
            .exclusions h2, .exclusions li {{
                color: #ffcc80;
            }}
            .recommendation {{
                background: #2d2d2d;
            }}
            .env-prod {{
                background: #1b5e20;
                border-color: #4caf50;
            }}
            .env-nonprod {{
                background: #e65100;
                border-color: #ff9800;
            }}
            #header {{
                background: linear-gradient(135deg, #0d47a1 0%, #1565c0 100%);
            }}
            a {{
                color: #90caf9;
            }}
            .resource-id a {{
                color: #90caf9;
            }}
            .tools-box {{
                background: #1b5e20;
                border-color: #4caf50;
            }}
            .tools-box h2, .tools-box a {{
                color: #a5d6a7;
            }}
            .calculator-box {{
                background: #0d47a1;
                border-color: #1976d2;
            }}
            .calculator-box h3 {{
                color: #90caf9;
            }}
            .calc-result {{
                background: #1e1e1e;
            }}
            .btn {{
                background: #1976d2;
            }}
            .dataTables_wrapper .dataTables_filter input,
            .dataTables_wrapper .dataTables_length select {{
                background: #2d2d2d;
                border-color: #444;
                color: #e0e0e0;
            }}
            .dataTables_wrapper .dataTables_paginate .paginate_button {{
                background: #2d2d2d;
                border-color: #444;
                color: #e0e0e0 !important;
            }}
            .dataTables_wrapper .dataTables_paginate .paginate_button:hover {{
                background: #3d3d3d;
                border-color: #555;
            }}
            .dataTables_wrapper .dataTables_paginate .paginate_button.current {{
                background: #1976d2;
                border-color: #1976d2;
                color: #fff !important;
            }}
            .dataTables_wrapper .dataTables_paginate .paginate_button.disabled {{
                background: #1e1e1e;
                border-color: #333;
                color: #555 !important;
            }}
        }}
        /* Print styles */
        @media print {{
            .disclaimer-banner {{
                background: #fff3cd !important;
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }}
            .export-buttons, .table-controls {{
                display: none;
            }}
            .card {{
                break-inside: avoid;
            }}
            #treemapChart {{
                height: 300px !important;
            }}
        }}
    </style>
</head>
<body>
    <div class="disclaimer-banner">
        ⚠️ ESTIMATE ONLY - Actual costs may vary significantly. Does not include data transfer, API calls, or usage-based fees.
    </div>

    <div id="header">
        <h1>💰 Cost Estimate Report</h1>
        <div class="subtitle">Confidence: {estimate.confidence.value} ({
            estimate.accuracy_range
        })</div>
        <div class="stats">
            <div class="stat">
                <div class="stat-value">${estimate.monthly_total:,.2f}</div>
                <div class="stat-label">Monthly Estimate</div>
                <div class="stat-range">${estimate.estimated_range_low:,.2f} - ${
            estimate.estimated_range_high:,.2f}</div>
            </div>
            <div class="stat">
                <div class="stat-value">${estimate.annual_total:,.2f}</div>
                <div class="stat-label">Annual Estimate</div>
            </div>
            <div class="stat">
                <div class="stat-value">{estimate.resource_count}</div>
                <div class="stat-label">Resources</div>
            </div>
            {
            f'''
            <div class="stat savings-highlight">
                <div class="stat-value">${estimate.total_optimization_potential:,.2f}</div>
                <div class="stat-label">Potential Savings</div>
                <div class="stat-range">{estimate.optimization_percentage:.1f}% of monthly cost</div>
            </div>
            '''
            if estimate.total_optimization_potential > 0
            else ""
        }
        </div>
    </div>

    {warnings_html}

    <div class="container">
        <!-- Environment Summary -->
        <div class="card">
            <h2>💼 Cost by Environment</h2>
            <div class="env-grid">
                <div class="env-box env-prod">
                    <div class="env-label">Production</div>
                    <div class="env-value">${env_costs["PRODUCTION"]:,.2f}</div>
                    <div class="env-percent">{prod_pct:.1f}% of total</div>
                </div>
                <div class="env-box env-nonprod">
                    <div class="env-label">Non-Production</div>
                    <div class="env-value">${env_costs["NON-PRODUCTION"]:,.2f}</div>
                    <div class="env-percent">{nonprod_pct:.1f}% of total</div>
                    {
            '<div class="env-warning">⚠️ High non-prod spend - review for waste</div>'
            if nonprod_pct > 20
            else ""
        }
                </div>
            </div>
        </div>

        <div class="grid">
            <div class="card">
                <h2>📊 Cost Distribution (Click to drill down)</h2>
                <div id="treemapChart"></div>
            </div>
            <div class="card">
                <h2>🎯 Optimization Recommendations</h2>
                {
            recommendations_html
            if recommendations_html
            else "<p>No optimization recommendations at this time.</p>"
        }
                {
            f'''
                <div class="total-savings" style="margin-top: 15px">
                    <div class="value">${estimate.total_optimization_potential:,.2f}</div>
                    <div class="label">Total Potential Savings ({estimate.optimization_percentage:.1f}%)</div>
                </div>
                '''
            if estimate.total_optimization_potential > 0
            else ""
        }
            </div>
        </div>

        <!-- NAT Gateway Calculator (if applicable) -->
        {
            f'''
        <div class="calculator-box">
            <h3>💡 NAT Gateway Data Processing Cost Estimator</h3>
            <p>Your infrastructure has <strong>{nat_count} NAT Gateway(s)</strong> at ${nat_hourly_total:,.2f}/mo (hourly charge only).</p>
            <p>Data processing is charged separately at <strong>$0.059/GB</strong>.</p>
            <div class="calc-input">
                <label>Estimated monthly data transfer (GB):
                    <input type="number" id="natDataGb" value="100" min="0" step="10">
                </label>
            </div>
            <div class="calc-result">
                <p>Additional NAT data processing cost: <strong>$<span id="natDataCost">5.90</span>/mo</strong></p>
                <p class="calc-total">Total estimated NAT cost: <strong>$<span id="natTotalCost">{nat_hourly_total + 5.90:,.2f}</span>/mo</strong></p>
            </div>
        </div>
        '''
            if nat_count > 0
            else ""
        }

        <div class="exclusions">
            <h2>⚠️ NOT Included in This Estimate</h2>
            <p>The following cost factors are not included and may significantly increase your actual bill:</p>
            <ul>
                {excluded_html}
            </ul>
        </div>

        <div class="tools-box">
            <h2>📊 For Accurate Cost Projections</h2>
            <p>
                <a href="https://console.aws.amazon.com/cost-management/" target="_blank">AWS Cost Explorer</a> |
                <a href="https://calculator.aws/" target="_blank">AWS Pricing Calculator</a>
            </p>
        </div>

        <div class="card">
            <h2>📋 All Resources</h2>
            <div class="export-buttons">
                <button class="btn" onclick="exportCSV()">📥 Export CSV</button>
                <button class="btn" onclick="window.print()">🖨️ Print / PDF</button>
                <button class="btn" onclick="clearFilter()">🔄 Clear Filter</button>
            </div>
            <div class="table-controls">
                <label class="toggle-label">
                    <input type="checkbox" id="showZeroCost">
                    Show zero-cost resources
                </label>
            </div>
            <table id="allResourcesTable">
                <thead>
                    <tr>
                        <th>Resource ID</th>
                        <th>Type</th>
                        <th>Category</th>
                        <th>Environment</th>
                        <th>Instance</th>
                        <th style="text-align: right">Monthly Est.</th>
                        <th style="text-align: right">Annual Est.</th>
                        <th>Confidence</th>
                    </tr>
                </thead>
                <tbody>
                    {all_resources_rows}
                </tbody>
            </table>
        </div>
    </div>

    <footer>
        <p>Generated by RepliMap Cost Estimator</p>
        <p><strong>This is an estimate only.</strong> Actual costs depend on your specific usage patterns and pricing agreements.</p>
    </footer>

    <!-- jQuery and DataTables -->
    <script src="https://code.jquery.com/jquery-3.7.0.min.js"></script>
    <script src="https://cdn.datatables.net/1.13.7/js/jquery.dataTables.min.js"></script>

    <script>
        // Category data for treemap
        const categoryData = {json.dumps(category_data)};
        const natHourlyTotal = {nat_hourly_total};

        // Initialize ECharts Treemap
        const treemapChart = echarts.init(document.getElementById('treemapChart'));

        const categoryColors = {{
            'DATABASE': '#1a73e8',
            'COMPUTE': '#34a853',
            'NETWORK': '#fbbc04',
            'STORAGE': '#ea4335',
            'MONITORING': '#9334e6',
            'SECURITY': '#00acc1',
            'OTHER': '#ff6f00'
        }};

        treemapChart.setOption({{
            tooltip: {{
                formatter: function(info) {{
                    return '<b>' + info.name + '</b><br/>$' + info.value.toLocaleString() + '/mo';
                }}
            }},
            series: [{{
                type: 'treemap',
                data: categoryData,
                leafDepth: 2,
                roam: false,
                nodeClick: 'zoomToNode',
                levels: [
                    {{
                        itemStyle: {{
                            borderColor: '#fff',
                            borderWidth: 2,
                            gapWidth: 2
                        }}
                    }},
                    {{
                        colorSaturation: [0.3, 0.6],
                        itemStyle: {{
                            borderColorSaturation: 0.7,
                            gapWidth: 1
                        }}
                    }}
                ],
                label: {{
                    show: true,
                    formatter: function(params) {{
                        return params.name + '\\n$' + params.value.toLocaleString();
                    }}
                }},
                upperLabel: {{
                    show: true,
                    height: 30
                }},
                itemStyle: {{
                    color: function(params) {{
                        if (params.data && params.data.name) {{
                            return categoryColors[params.data.name] || '#666';
                        }}
                        return '#666';
                    }}
                }}
            }}]
        }});

        // Responsive resize
        window.addEventListener('resize', () => treemapChart.resize());

        // Initialize DataTables
        let showZeroCost = false;

        // Custom filter function (doesn't pollute the search box)
        $.fn.dataTable.ext.search.push(function(settings, data, dataIndex) {{
            if (showZeroCost) return true;
            // Column 5 is Monthly Est. - check if it's $0.00
            const monthlyCost = data[5] || '';
            return monthlyCost !== '$0.00';
        }});

        $(document).ready(function() {{
            const table = $('#allResourcesTable').DataTable({{
                pageLength: 25,
                lengthMenu: [[25, 50, 100, -1], [25, 50, 100, "All"]],
                order: [[5, 'desc']], // Sort by Monthly Est. descending
                language: {{
                    search: "🔍 Filter:",
                    lengthMenu: "Show _MENU_ resources",
                    info: "Showing _START_ to _END_ of _TOTAL_ resources"
                }},
                columnDefs: [
                    {{ targets: [5, 6], type: 'num-fmt' }}
                ]
            }});

            // Toggle zero-cost resources
            $('#showZeroCost').on('change', function() {{
                showZeroCost = this.checked;
                table.draw();
            }});
        }});

        // Filter resources from recommendations
        function filterResources(keyword) {{
            const table = $('#allResourcesTable').DataTable();
            // Enable showing zero cost in case filter reveals them
            showZeroCost = true;
            document.getElementById('showZeroCost').checked = true;
            table.search(keyword).draw();
            document.getElementById('allResourcesTable').scrollIntoView({{
                behavior: 'smooth'
            }});
        }}

        function clearFilter() {{
            const table = $('#allResourcesTable').DataTable();
            document.getElementById('showZeroCost').checked = false;
            showZeroCost = false;
            table.search('').draw();
        }}

        // NAT Gateway calculator
        const natInput = document.getElementById('natDataGb');
        if (natInput) {{
            natInput.addEventListener('input', function(e) {{
                const gb = parseFloat(e.target.value) || 0;
                const dataProcessingCost = gb * 0.059;
                const totalCost = natHourlyTotal + dataProcessingCost;

                document.getElementById('natDataCost').textContent = dataProcessingCost.toFixed(2);
                document.getElementById('natTotalCost').textContent = totalCost.toLocaleString('en-US', {{
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                }});
            }});
        }}

        // CSV Export - exports ALL rows, not just visible page
        function exportCSV() {{
            let csv = [];

            // Add disclaimer header
            csv.push('# DISCLAIMER: ESTIMATE ONLY - Actual costs may vary');
            csv.push('# Generated by RepliMap Cost Estimator');
            csv.push('#');

            // Add header row
            const headers = ['RESOURCE ID', 'TYPE', 'CATEGORY', 'ENVIRONMENT', 'INSTANCE', 'MONTHLY EST.', 'ANNUAL EST.', 'CONFIDENCE'];
            csv.push(headers.map(h => '"' + h + '"').join(','));

            // Use DataTables API to get ALL rows (not just visible page)
            const dt = $('#allResourcesTable').DataTable();
            dt.rows({{ search: 'applied' }}).every(function() {{
                const data = this.data();
                // data is array: [resourceId, type, category, environment, instance, monthly, annual, confidence]
                const rowData = data.map(function(cell) {{
                    // Strip HTML tags and clean up
                    let text = String(cell).replace(/<[^>]*>/g, '').replace(/"/g, '""').trim();
                    return '"' + text + '"';
                }});
                csv.push(rowData.join(','));
            }});

            const blob = new Blob([csv.join('\\n')], {{ type: 'text/csv' }});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'replimap-cost-report.csv';
            a.click();
            URL.revokeObjectURL(url);
        }}
    </script>
</body>
</html>"""
