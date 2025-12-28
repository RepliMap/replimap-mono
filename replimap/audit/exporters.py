"""
Export utilities for Trust Center reports.

Supports multiple output formats:
- JSON: Full report with optional detailed records
- CSV: Tabular format for spreadsheet analysis
- Text: Human-readable compliance statement
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from .models import AuditSession, TrustCenterReport


def export_json(
    report: TrustCenterReport,
    output_path: Path | str,
    include_records: bool = False,
) -> None:
    """
    Export report as JSON.

    Args:
        report: TrustCenterReport instance
        output_path: Output file path
        include_records: If True, include detailed API call records
    """
    output_path = Path(output_path)
    data = report.to_dict()

    if not include_records:
        # Remove detailed records from session summaries
        for session in data.get("sessions", []):
            session.pop("records", None)

    with open(output_path, "w") as f:
        json.dump(data, f, indent=2, default=str)


def export_csv(
    sessions: list[AuditSession],
    output_path: Path | str,
) -> None:
    """
    Export API call records as CSV.

    Args:
        sessions: List of AuditSession instances
        output_path: Output file path
    """
    output_path = Path(output_path)

    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)

        # Header
        writer.writerow(
            [
                "Session ID",
                "Session Name",
                "Timestamp",
                "Service",
                "Operation",
                "Region",
                "Category",
                "Duration (ms)",
                "HTTP Status",
                "Is Read-Only",
                "Is Success",
                "Error Code",
                "Request ID",
                "Account ID",
            ]
        )

        # Records
        for session in sessions:
            for record in session.records:
                writer.writerow(
                    [
                        session.session_id,
                        session.session_name or "",
                        record.timestamp.isoformat(),
                        record.service,
                        record.operation,
                        record.region,
                        record.category.value,
                        record.duration_ms,
                        record.http_status,
                        record.is_read_only,
                        record.is_success,
                        record.error_code or "",
                        record.request_id,
                        record.account_id or "",
                    ]
                )


def export_summary_csv(
    report: TrustCenterReport,
    output_path: Path | str,
) -> None:
    """
    Export report summary as CSV.

    Args:
        report: TrustCenterReport instance
        output_path: Output file path
    """
    output_path = Path(output_path)

    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)

        # Header section
        writer.writerow(["Trust Center Audit Report"])
        writer.writerow(["Report ID", report.report_id])
        writer.writerow(["Generated", report.generated_at.isoformat()])
        writer.writerow(["Period Start", report.report_period_start.isoformat()])
        writer.writerow(["Period End", report.report_period_end.isoformat()])
        writer.writerow(["Tool", f"{report.tool_name} v{report.tool_version}"])
        writer.writerow([])

        # Summary section
        writer.writerow(["Summary"])
        writer.writerow(["Total Sessions", report.total_sessions])
        writer.writerow(["Total API Calls", report.total_api_calls])
        writer.writerow(
            ["Total Duration (seconds)", f"{report.total_duration_seconds:.2f}"]
        )
        writer.writerow(
            ["Read-Only Percentage", f"{report.read_only_percentage:.1f}%"]
        )
        writer.writerow(
            ["Fully Read-Only", "Yes" if report.is_fully_read_only else "No"]
        )
        writer.writerow(["Total Errors", report.total_errors])
        writer.writerow(
            ["Error Rate", f"{report.error_rate_percentage:.2f}%"]
        )
        writer.writerow([])

        # Calls by category
        writer.writerow(["Calls by Category"])
        writer.writerow(["Category", "Count"])
        for category, count in sorted(report.calls_by_category.items()):
            writer.writerow([category, count])
        writer.writerow([])

        # Calls by service
        writer.writerow(["Calls by Service"])
        writer.writerow(["Service", "Count"])
        for service, count in sorted(
            report.calls_by_service.items(), key=lambda x: -x[1]
        ):
            writer.writerow([service, count])
        writer.writerow([])

        # Non-read operations (if any)
        if report.write_operations:
            writer.writerow(["Non-Read Operations"])
            for op in report.write_operations:
                writer.writerow([op])
            writer.writerow([])

        # Sessions
        writer.writerow(["Sessions"])
        writer.writerow(
            [
                "Session ID",
                "Name",
                "Start Time",
                "Duration (s)",
                "Total Calls",
                "Read-Only %",
            ]
        )
        for session in report.session_summaries:
            writer.writerow(
                [
                    session.get("session_id", ""),
                    session.get("session_name", ""),
                    session.get("start_time", ""),
                    session.get("duration_seconds", ""),
                    session.get("total_calls", 0),
                    f"{session.get('read_only_percentage', 100):.1f}%",
                ]
            )
        writer.writerow([])

        # Compliance statement
        writer.writerow(["Compliance Statement"])
        writer.writerow([report.compliance_statement])


def generate_compliance_text(report: TrustCenterReport) -> str:
    """
    Generate a plain-text compliance statement.

    Args:
        report: TrustCenterReport instance

    Returns:
        Formatted compliance text suitable for printing or saving
    """
    separator = "=" * 72
    subseparator = "-" * 72

    lines = [
        separator,
        "TRUST CENTER COMPLIANCE REPORT",
        separator,
        "",
        f"Tool: {report.tool_name} v{report.tool_version}",
        f"Report ID: {report.report_id}",
        f"Generated: {report.generated_at.isoformat()}",
        f"Audit Period: {report.report_period_start.date()} to {report.report_period_end.date()}",
        "",
        subseparator,
        "EXECUTIVE SUMMARY",
        subseparator,
        "",
        f"  Total Audit Sessions:  {report.total_sessions}",
        f"  Total AWS API Calls:   {report.total_api_calls:,}",
        f"  Total Duration:        {report.total_duration_seconds:.1f} seconds",
        "",
        f"  Read-Only Operations:  {report.read_only_percentage:.1f}%",
        f"  Fully Read-Only:       {'YES' if report.is_fully_read_only else 'NO'}",
        "",
        f"  Total Errors:          {report.total_errors}",
        f"  Error Rate:            {report.error_rate_percentage:.2f}%",
        "",
        subseparator,
        "OPERATIONS BY CATEGORY",
        subseparator,
        "",
    ]

    # Category breakdown
    for category, count in sorted(report.calls_by_category.items()):
        pct = (count / report.total_api_calls * 100) if report.total_api_calls > 0 else 0
        lines.append(f"  {category.upper():12} {count:>8,} ({pct:>5.1f}%)")

    lines.extend(
        [
            "",
            subseparator,
            "AWS SERVICES ACCESSED",
            subseparator,
            "",
        ]
    )

    # Service breakdown (top 10)
    sorted_services = sorted(
        report.calls_by_service.items(), key=lambda x: -x[1]
    )[:10]
    for service, count in sorted_services:
        lines.append(f"  {service:20} {count:>8,} calls")

    if len(report.calls_by_service) > 10:
        lines.append(f"  ... and {len(report.calls_by_service) - 10} more services")

    # Non-read operations (if any)
    if report.write_operations:
        lines.extend(
            [
                "",
                subseparator,
                "NON-READ OPERATIONS DETECTED",
                subseparator,
                "",
            ]
        )
        for op in report.write_operations:
            lines.append(f"  - {op}")

    lines.extend(
        [
            "",
            subseparator,
            "COMPLIANCE STATEMENT",
            subseparator,
            "",
        ]
    )

    # Word-wrap compliance statement
    statement = report.compliance_statement
    words = statement.split()
    current_line = "  "
    for word in words:
        if len(current_line) + len(word) + 1 > 70:
            lines.append(current_line)
            current_line = "  " + word
        else:
            current_line += " " + word if current_line != "  " else word
    if current_line.strip():
        lines.append(current_line)

    lines.extend(
        [
            "",
            separator,
            "",
            "This report was automatically generated by RepliMap Trust Center.",
            "For questions, contact your RepliMap administrator.",
            "",
        ]
    )

    return "\n".join(lines)


def save_compliance_text(
    report: TrustCenterReport,
    output_path: Path | str,
) -> None:
    """
    Save compliance text to a file.

    Args:
        report: TrustCenterReport instance
        output_path: Output file path
    """
    output_path = Path(output_path)
    text = generate_compliance_text(report)
    output_path.write_text(text)
