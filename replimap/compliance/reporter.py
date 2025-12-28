"""
Compliance Report Generator.

Generates compliance reports in various formats:
- Console (human-readable text)
- JSON (machine-readable)
- HTML (rich interactive report)
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from .models import ComplianceResults, RuleFinding, Severity

logger = logging.getLogger(__name__)


class ComplianceReporter:
    """
    Generates compliance reports in multiple formats.

    Usage:
        reporter = ComplianceReporter()
        reporter.print_console(results)
        reporter.write_json(results, Path("report.json"))
        reporter.write_html(results, Path("report.html"))
    """

    def print_console(
        self,
        results: ComplianceResults,
        show_passed: bool = False,
        max_findings: int = 50,
    ) -> None:
        """
        Print compliance report to console.

        Args:
            results: Compliance evaluation results
            show_passed: If True, show passed rules as well
            max_findings: Maximum number of findings to show per rule
        """
        summary = results.get_summary()

        # Header
        print("\n" + "=" * 60)
        print("COMPLIANCE REPORT")
        print("=" * 60)

        # Score
        print(f"\nScore: {summary['score']}% (Grade: {summary['grade']})")
        print(f"Resources: {summary['total_resources']}")
        print(f"Rules: {summary['total_rules']}")
        print(f"Passed: {summary['total_passed']} | Failed: {summary['total_failed']}")

        # Severity breakdown
        if summary["findings_by_severity"]:
            print("\nFindings by Severity:")
            for severity in ["critical", "high", "medium", "low", "info"]:
                count = summary["findings_by_severity"].get(severity, 0)
                if count > 0:
                    print(f"  {severity.upper()}: {count}")

        # Critical and High findings
        critical = results.get_critical_findings()
        high = results.get_high_findings()

        if critical:
            print("\n" + "-" * 60)
            print("CRITICAL FINDINGS:")
            print("-" * 60)
            for finding in critical[:max_findings]:
                self._print_finding(finding)
            if len(critical) > max_findings:
                print(f"  ... and {len(critical) - max_findings} more")

        if high:
            print("\n" + "-" * 60)
            print("HIGH FINDINGS:")
            print("-" * 60)
            for finding in high[:max_findings]:
                self._print_finding(finding)
            if len(high) > max_findings:
                print(f"  ... and {len(high) - max_findings} more")

        # Per-rule summary
        print("\n" + "-" * 60)
        print("RULE SUMMARY:")
        print("-" * 60)

        for result in results.results:
            status = "PASS" if result.failed_count == 0 else "FAIL"
            if not show_passed and status == "PASS":
                continue

            severity_icon = self._severity_icon(result.rule.severity)
            print(
                f"  [{status}] {severity_icon} {result.rule.id}: {result.rule.name}"
            )
            if result.failed_count > 0:
                print(f"        {result.failed_count} failures / {result.total_evaluated} resources")

        print("\n" + "=" * 60)

    def _print_finding(self, finding: RuleFinding) -> None:
        """Print a single finding."""
        print(f"\n  [{finding.rule.id}] {finding.resource_name}")
        print(f"    Resource: {finding.resource_id} ({finding.resource_type})")
        print(f"    Region: {finding.region}")
        if finding.rule.remediation:
            print(f"    Remediation: {finding.rule.remediation}")

    def _severity_icon(self, severity: Severity) -> str:
        """Get icon for severity level."""
        icons = {
            Severity.CRITICAL: "[!!!]",
            Severity.HIGH: "[!!]",
            Severity.MEDIUM: "[!]",
            Severity.LOW: "[.]",
            Severity.INFO: "[i]",
        }
        return icons.get(severity, "[?]")

    def write_json(
        self,
        results: ComplianceResults,
        path: Path,
        indent: int = 2,
    ) -> Path:
        """
        Write compliance report as JSON.

        Args:
            results: Compliance evaluation results
            path: Output file path
            indent: JSON indentation

        Returns:
            Path to written file
        """
        data = results.to_dict()

        with open(path, "w") as f:
            json.dump(data, f, indent=indent)

        logger.info(f"Wrote JSON report to {path}")
        return path

    def write_html(
        self,
        results: ComplianceResults,
        path: Path,
        title: str = "Compliance Report",
    ) -> Path:
        """
        Write compliance report as HTML.

        Args:
            results: Compliance evaluation results
            path: Output file path
            title: Report title

        Returns:
            Path to written file
        """
        summary = results.get_summary()

        html = self._generate_html(results, summary, title)

        with open(path, "w") as f:
            f.write(html)

        logger.info(f"Wrote HTML report to {path}")
        return path

    def _generate_html(
        self,
        results: ComplianceResults,
        summary: dict[str, Any],
        title: str,
    ) -> str:
        """Generate HTML report content."""
        grade_color = {
            "A": "#28a745",
            "B": "#5cb85c",
            "C": "#f0ad4e",
            "D": "#d9534f",
            "F": "#c9302c",
        }

        severity_colors = {
            "critical": "#c9302c",
            "high": "#d9534f",
            "medium": "#f0ad4e",
            "low": "#5bc0de",
            "info": "#5cb85c",
        }

        # Build findings HTML
        findings_html = ""
        for result in results.results:
            if result.failed_count == 0:
                continue

            findings_html += f"""
            <div class="rule-section">
                <h3>{result.rule.id}: {result.rule.name}</h3>
                <p class="rule-description">{result.rule.description}</p>
                <p class="severity-badge" style="background-color: {severity_colors.get(str(result.rule.severity), '#999')}">
                    {str(result.rule.severity).upper()}
                </p>
                <p><strong>Failed:</strong> {result.failed_count} / {result.total_evaluated}</p>
                <table class="findings-table">
                    <thead>
                        <tr>
                            <th>Resource</th>
                            <th>Type</th>
                            <th>Region</th>
                        </tr>
                    </thead>
                    <tbody>
            """

            for finding in result.findings[:20]:  # Limit to 20 per rule
                findings_html += f"""
                        <tr>
                            <td>{finding.resource_name}</td>
                            <td>{finding.resource_type}</td>
                            <td>{finding.region}</td>
                        </tr>
                """

            if len(result.findings) > 20:
                findings_html += f"""
                        <tr>
                            <td colspan="3" class="more">... and {len(result.findings) - 20} more</td>
                        </tr>
                """

            findings_html += """
                    </tbody>
                </table>
            """

            if result.rule.remediation:
                findings_html += f"""
                <div class="remediation">
                    <strong>Remediation:</strong> {result.rule.remediation}
                </div>
                """

            findings_html += "</div>"

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{ box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        h1 {{ color: #333; border-bottom: 2px solid #0066cc; padding-bottom: 10px; }}
        h2 {{ color: #444; margin-top: 30px; }}
        h3 {{ color: #555; margin-top: 20px; }}
        .summary-box {{
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .score-display {{
            font-size: 3em;
            font-weight: bold;
            text-align: center;
            color: {grade_color.get(summary['grade'], '#333')};
        }}
        .grade-badge {{
            display: inline-block;
            background: {grade_color.get(summary['grade'], '#333')};
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 1.2em;
            margin-left: 10px;
        }}
        .stats {{ display: flex; justify-content: space-around; margin: 20px 0; }}
        .stat {{ text-align: center; padding: 15px; }}
        .stat-value {{ font-size: 2em; font-weight: bold; color: #333; }}
        .stat-label {{ color: #666; }}
        .severity-summary {{
            display: flex;
            justify-content: center;
            gap: 20px;
            margin: 20px 0;
        }}
        .severity-item {{
            padding: 10px 20px;
            border-radius: 5px;
            color: white;
            text-align: center;
        }}
        .rule-section {{
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .rule-description {{ color: #666; }}
        .severity-badge {{
            display: inline-block;
            color: white;
            padding: 3px 10px;
            border-radius: 3px;
            font-size: 0.9em;
        }}
        .findings-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }}
        .findings-table th, .findings-table td {{
            border: 1px solid #ddd;
            padding: 10px;
            text-align: left;
        }}
        .findings-table th {{
            background: #f8f9fa;
        }}
        .findings-table tr:nth-child(even) {{
            background: #f8f9fa;
        }}
        .more {{ color: #666; font-style: italic; }}
        .remediation {{
            background: #e7f3ff;
            padding: 15px;
            border-radius: 5px;
            margin-top: 15px;
            border-left: 4px solid #0066cc;
        }}
        .timestamp {{ color: #999; font-size: 0.9em; }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <p class="timestamp">Generated: {summary['timestamp']}</p>

    <div class="summary-box">
        <div class="score-display">
            {summary['score']}%
            <span class="grade-badge">{summary['grade']}</span>
        </div>

        <div class="stats">
            <div class="stat">
                <div class="stat-value">{summary['total_resources']}</div>
                <div class="stat-label">Resources</div>
            </div>
            <div class="stat">
                <div class="stat-value">{summary['total_rules']}</div>
                <div class="stat-label">Rules</div>
            </div>
            <div class="stat">
                <div class="stat-value">{summary['total_passed']}</div>
                <div class="stat-label">Passed</div>
            </div>
            <div class="stat">
                <div class="stat-value">{summary['total_failed']}</div>
                <div class="stat-label">Failed</div>
            </div>
        </div>

        <div class="severity-summary">
            {"".join(f'''
            <div class="severity-item" style="background-color: {severity_colors.get(sev, '#999')}">
                <strong>{count}</strong><br>{sev.upper()}
            </div>
            ''' for sev, count in summary['findings_by_severity'].items())}
        </div>
    </div>

    <h2>Findings</h2>
    {findings_html if findings_html else '<p>No findings - all rules passed!</p>'}

</body>
</html>"""

    def get_summary_text(self, results: ComplianceResults) -> str:
        """
        Get a brief text summary.

        Args:
            results: Compliance evaluation results

        Returns:
            Brief summary string
        """
        summary = results.get_summary()
        return (
            f"Compliance: {summary['score']}% ({summary['grade']}) - "
            f"{summary['total_findings']} findings across {summary['total_resources']} resources"
        )
