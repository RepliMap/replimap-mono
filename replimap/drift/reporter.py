"""Drift report generation."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from jinja2 import Environment, PackageLoader, select_autoescape
from markupsafe import Markup

from replimap.drift.models import (
    DriftReason,
    DriftReport,
    DriftSeverity,
    DriftType,
    ResourceDrift,
)

if TYPE_CHECKING:
    pass


def _get_drift_classification(drift: ResourceDrift) -> str:
    """Classify drift as semantic or cosmetic for UI styling.

    Returns:
        'semantic' if any diff is functional/semantic OR if ADDED/REMOVED
        'cosmetic' if all diffs are tag/ordering/default changes
        'none' if UNSCANNED (no action possible)
    """
    # ADDED and REMOVED always require action
    if drift.drift_type in (DriftType.ADDED, DriftType.REMOVED):
        return "semantic"
    # UNSCANNED has no action
    if drift.drift_type == DriftType.UNSCANNED:
        return "none"
    # MODIFIED - check the diffs
    if not drift.diffs:
        return "none"
    # If ANY diff is semantic, the whole drift is semantic
    if any(d.is_semantic for d in drift.diffs):
        return "semantic"
    return "cosmetic"


def _sanitize_tf_resource_name(resource_id: str) -> str:
    """Sanitize a resource ID to create a valid Terraform resource name.

    Terraform resource names must:
    - Start with a letter or underscore
    - Contain only letters, digits, underscores, and dashes
    - Not be empty

    Args:
        resource_id: The raw resource ID to sanitize

    Returns:
        A valid Terraform resource name
    """
    import re

    if not resource_id:
        return "unknown"

    # Replace all invalid characters with underscore
    safe_name = resource_id
    for char in [
        "-",
        ".",
        "/",
        ":",
        " ",
        "@",
        "#",
        "$",
        "%",
        "^",
        "&",
        "*",
        "(",
        ")",
        "[",
        "]",
        "{",
        "}",
        "|",
        "\\",
        "'",
        '"',
        "<",
        ">",
        ",",
        "?",
        "!",
        "=",
        "+",
        "~",
        "`",
    ]:
        safe_name = safe_name.replace(char, "_")

    # Collapse consecutive underscores into single underscore
    safe_name = re.sub(r"_+", "_", safe_name)

    # Strip leading/trailing underscores
    safe_name = safe_name.strip("_")

    # If empty after sanitization, use fallback
    if not safe_name:
        return "imported"

    # Terraform names can't start with a digit - prefix with 'r_'
    if safe_name[0].isdigit():
        safe_name = f"r_{safe_name}"

    # Limit length (TF has no hard limit but keep it reasonable)
    return safe_name[:60]


def _shell_quote(value: str) -> str:
    """Quote a value for safe shell usage if it contains special characters.

    Args:
        value: The value to potentially quote

    Returns:
        The value, quoted with single quotes if necessary
    """
    # Characters that need quoting in shell
    needs_quoting = set(" \t\n'\"\\$`!&|;<>(){}[]#*?~")

    if any(c in needs_quoting for c in value):
        # Use single quotes, escaping any single quotes in the value
        escaped = value.replace("'", "'\"'\"'")
        return f"'{escaped}'"
    return value


def _generate_remediation_cmd(drift: ResourceDrift) -> str:
    """Generate a remediation command for the drift.

    Returns terraform command appropriate for the drift type.
    """
    # Build resource address
    if drift.tf_address:
        resource_addr = drift.tf_address
    else:
        # Generate a valid TF resource name from the ID
        safe_name = _sanitize_tf_resource_name(drift.resource_id)
        resource_addr = f"{drift.resource_type}.{safe_name}"

    if drift.drift_type == DriftType.MODIFIED:
        return f"terraform apply -target={resource_addr}"
    elif drift.drift_type == DriftType.ADDED:
        # Resource exists in AWS but not in TF - import it
        # Quote the resource ID for shell safety
        quoted_id = _shell_quote(drift.resource_id)
        return f"terraform import {resource_addr} {quoted_id}"
    elif drift.drift_type == DriftType.REMOVED:
        # Resource in TF but deleted from AWS - recreate it
        # Alternative: terraform state rm {resource_addr} (to accept deletion)
        return f"terraform apply -target={resource_addr}"
    elif drift.drift_type == DriftType.UNSCANNED:
        return ""  # No command for unscanned
    return ""


def _format_value(val: Any) -> str:
    """Format a value for display with semantic empty handling.

    Returns HTML-safe string with appropriate styling for empty values.
    """
    if val is None:
        return '<span class="text-gray-400 italic">(not set)</span>'
    if val == "":
        return '<span class="text-gray-400 italic">(empty)</span>'
    if val == [] or val == {}:
        type_name = "list" if isinstance(val, list) else "object"
        return f'<span class="text-gray-400 italic">(empty {type_name})</span>'
    if isinstance(val, bool):
        return str(val).lower()
    if isinstance(val, (dict, list)):
        # Truncate long JSON
        json_str = json.dumps(val, default=str)
        if len(json_str) > 100:
            return json_str[:97] + "..."
        return json_str
    # Regular value
    str_val = str(val)
    if len(str_val) > 100:
        return str_val[:97] + "..."
    return str_val


def _format_diff_value(expected: Any, actual: Any, which: str) -> str:
    """Format expected/actual value with semantic context.

    Adds visual cues for additions and removals.
    """
    if which == "expected":
        if expected is None and actual is not None:
            return '<span class="text-gray-400 italic">(not set)</span>'
        return _format_value(expected)
    else:  # actual
        if actual is None and expected is not None:
            return '<span class="text-red-400 italic">(removed)</span>'
        return _format_value(actual)


class DriftReporter:
    """Generate drift reports in various formats."""

    def __init__(self) -> None:
        """Initialize the reporter with Jinja2 environment."""
        self.env = Environment(
            loader=PackageLoader("replimap.drift", "templates"),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        # Register custom filters
        self.env.filters["format_value"] = _format_value
        self.env.filters["format_diff_expected"] = lambda e, a: _format_diff_value(
            e, a, "expected"
        )
        self.env.filters["format_diff_actual"] = lambda e, a: _format_diff_value(
            e, a, "actual"
        )
        self.env.filters["drift_classification"] = _get_drift_classification
        self.env.filters["remediation_cmd"] = _generate_remediation_cmd
        # Make Markup available for safe HTML rendering
        self.env.globals["Markup"] = Markup

    def to_console(self, report: DriftReport) -> str:
        """Generate console-friendly output."""
        lines = []

        # Header
        lines.append("")
        if report.has_drift:
            lines.append("DRIFT DETECTED")
        else:
            lines.append("NO DRIFT")
        lines.append("=" * 50)

        # Summary
        lines.append(f"Total resources: {report.total_resources}")
        lines.append(f"Drifted: {report.drifted_resources}")
        if report.added_resources:
            lines.append(f"  - Added (not in TF): {report.added_resources}")
        if report.removed_resources:
            lines.append(f"  - Removed (deleted from AWS): {report.removed_resources}")
        if report.modified_resources:
            lines.append(f"  - Modified: {report.modified_resources}")
        if report.unscanned_resources:
            lines.append(f"Unscanned (no scanner): {report.unscanned_resources}")
        lines.append("")

        # Critical/High drifts first
        critical_high = report.critical_drifts + report.high_drifts
        if critical_high:
            lines.append("HIGH PRIORITY DRIFTS:")
            lines.append("-" * 50)
            for drift in critical_high[:10]:  # Limit to 10
                lines.append(self._format_drift(drift))
            if len(critical_high) > 10:
                lines.append(f"  ... and {len(critical_high) - 10} more")
            lines.append("")

        # Other drifts
        other = [
            d
            for d in report.drifts
            if d.severity not in (DriftSeverity.CRITICAL, DriftSeverity.HIGH)
        ]
        if other:
            lines.append("OTHER DRIFTS:")
            lines.append("-" * 50)
            for drift in other[:10]:
                lines.append(self._format_drift(drift))
            if len(other) > 10:
                lines.append(f"  ... and {len(other) - 10} more")

        lines.append("")
        lines.append(f"Scan completed in {report.scan_duration_seconds}s")

        return "\n".join(lines)

    def _format_drift(self, drift: ResourceDrift) -> str:
        """Format a single drift for console output."""
        icon = {
            DriftType.ADDED: "[+]",
            DriftType.REMOVED: "[-]",
            DriftType.MODIFIED: "[~]",
            DriftType.UNSCANNED: "[?]",
        }.get(drift.drift_type, "[?]")

        severity_label = {
            DriftSeverity.CRITICAL: "[CRITICAL]",
            DriftSeverity.HIGH: "[HIGH]",
            DriftSeverity.MEDIUM: "[MEDIUM]",
            DriftSeverity.LOW: "[LOW]",
        }.get(drift.severity, "[INFO]")

        line = f"{severity_label} {icon} {drift.resource_type}: {drift.resource_id}"

        if drift.tf_address:
            line += f" ({drift.tf_address})"

        # Show diffs for modified resources
        if drift.drift_type == DriftType.MODIFIED and drift.diffs:
            # Separate semantic vs noise diffs
            semantic_diffs = [d for d in drift.diffs if d.is_semantic]
            other_diffs = [d for d in drift.diffs if not d.is_semantic]

            for diff in semantic_diffs[:3]:  # Limit to 3
                line += (
                    f"\n      {diff.attribute}: {diff.expected!r} -> {diff.actual!r}"
                )
            if len(semantic_diffs) > 3:
                line += (
                    f"\n      ... and {len(semantic_diffs) - 3} more semantic changes"
                )

            # Summarize non-semantic diffs
            if other_diffs:
                tag_count = sum(
                    1 for d in other_diffs if d.reason == DriftReason.TAG_ONLY
                )
                if tag_count:
                    line += f"\n      + {tag_count} tag change(s)"

        return line

    def to_json(self, report: DriftReport, output_path: Path) -> Path:
        """Export report as JSON."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report.to_dict(), indent=2, default=str))
        return output_path

    def to_html(self, report: DriftReport, output_path: Path) -> Path:
        """Generate HTML report."""
        template = self.env.get_template("drift_report.html.j2")

        # Pre-process drifts to add classification
        processed_drifts = []
        for drift in report.drifts:
            # Add computed properties for template
            drift._classification = _get_drift_classification(drift)
            drift._remediation_cmd = _generate_remediation_cmd(drift)
            drift._semantic_count = sum(1 for d in drift.diffs if d.is_semantic)
            drift._tag_count = sum(
                1 for d in drift.diffs if d.reason == DriftReason.TAG_ONLY
            )
            processed_drifts.append(drift)

        # Group drifts by resource type
        drifts_by_type: dict[str, list[ResourceDrift]] = {}
        for drift in processed_drifts:
            if drift.drift_type == DriftType.UNSCANNED:
                continue  # Handle separately
            if drift.resource_type not in drifts_by_type:
                drifts_by_type[drift.resource_type] = []
            drifts_by_type[drift.resource_type].append(drift)

        # Sort groups by count (most drifts first)
        sorted_groups = sorted(
            drifts_by_type.items(), key=lambda x: len(x[1]), reverse=True
        )

        html = template.render(
            report=report,
            generated_at=datetime.now(UTC).isoformat(),
            drifts_by_type=sorted_groups,
            DriftType=DriftType,
            DriftSeverity=DriftSeverity,
            DriftReason=DriftReason,
        )

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html)
        return output_path
