"""
Pre-defined Parameter Schemas.

All command parameter definitions are centralized here.
Uses choices_ref string references - NO CALLABLES.

This module defines:
- SCAN_PARAMETERS: Parameters for the scan command
- CLONE_PARAMETERS: Parameters for the clone command
- AUDIT_PARAMETERS: Parameters for the audit command
- COST_PARAMETERS: Parameters for the cost command

All schemas are JSON-serializable for:
- Documentation generation
- API schema export
- Interactive form rendering
"""

from __future__ import annotations

from typing import Any

from replimap.cli.params.schema import Parameter, ParameterGroup, ParameterType

# ============================================================================
# SCAN COMMAND PARAMETERS
# ============================================================================

SCAN_PARAMETERS = ParameterGroup(
    name="scan",
    description="AWS Infrastructure Scan - Discover resources and build dependency graph",
    parameters=[
        Parameter(
            key="profile",
            label="AWS Profile",
            type=ParameterType.SELECT,
            help_text="AWS profile to use for authentication",
            choices_ref="aws:profiles",
            default_ref="config:profile",
            required=False,
            cli_flag="--profile",
            cli_short="-p",
        ),
        Parameter(
            key="region",
            label="AWS Region",
            type=ParameterType.SELECT,
            help_text="AWS region to scan",
            choices_ref="aws:regions",
            default_ref="config:region",
            required=False,
            cli_flag="--region",
            cli_short="-r",
        ),
        Parameter(
            key="output",
            label="Output Path",
            type=ParameterType.PATH,
            help_text="Path to save the graph (JSON or SQLite .db)",
            required=False,
            cli_flag="--output",
            cli_short="-o",
        ),
        Parameter(
            key="scope",
            label="Selection Scope",
            type=ParameterType.TEXT,
            help_text="Selection scope: vpc:<id>, vpc-name:<pattern>, or VPC ID",
            required=False,
            cli_flag="--scope",
            cli_short="-s",
        ),
        Parameter(
            key="entry",
            label="Entry Point",
            type=ParameterType.TEXT,
            help_text="Entry point: tag:Key=Value, <type>:<name>, or resource ID",
            required=False,
            cli_flag="--entry",
            cli_short="-e",
        ),
        Parameter(
            key="vpc_filter",
            label="VPC Filter",
            type=ParameterType.TEXT,
            help_text="Filter by VPC ID(s), comma-separated",
            required=False,
            cli_flag="--vpc",
        ),
        Parameter(
            key="use_cache",
            label="Use Scan Cache",
            type=ParameterType.CONFIRM,
            help_text="Use cached scan results for faster incremental scans",
            default_static=False,
            required=False,
            cli_flag="--cache",
        ),
        Parameter(
            key="refresh_cache",
            label="Refresh Cache",
            type=ParameterType.CONFIRM,
            help_text="Force refresh of scan cache",
            default_static=False,
            required=False,
            cli_flag="--refresh-cache",
            condition_ref="state:cache_exists",
        ),
        Parameter(
            key="incremental",
            label="Incremental Scan",
            type=ParameterType.CONFIRM,
            help_text="Use incremental scanning (only detect changes)",
            default_static=False,
            required=False,
            cli_flag="--incremental",
        ),
        Parameter(
            key="trust_center",
            label="Trust Center Auditing",
            type=ParameterType.CONFIRM,
            help_text="Enable Trust Center API auditing for compliance",
            default_static=False,
            required=False,
            cli_flag="--trust-center",
        ),
        Parameter(
            key="interactive",
            label="Interactive Mode",
            type=ParameterType.CONFIRM,
            help_text="Prompt for missing options interactively",
            default_static=False,
            required=False,
            cli_flag="--interactive",
            cli_short="-i",
        ),
    ],
)


# ============================================================================
# CLONE COMMAND PARAMETERS
# ============================================================================

CLONE_PARAMETERS = ParameterGroup(
    name="clone",
    description="Clone Infrastructure - Generate IaC from scanned resources",
    parameters=[
        Parameter(
            key="profile",
            label="AWS Profile",
            type=ParameterType.SELECT,
            help_text="AWS profile to use for authentication",
            choices_ref="aws:profiles",
            default_ref="config:profile",
            required=False,
            cli_flag="--profile",
            cli_short="-p",
        ),
        Parameter(
            key="region",
            label="AWS Region",
            type=ParameterType.SELECT,
            help_text="AWS region to clone",
            choices_ref="aws:regions",
            default_ref="config:region",
            required=False,
            cli_flag="--region",
            cli_short="-r",
        ),
        Parameter(
            key="format",
            label="Output Format",
            type=ParameterType.SELECT,
            help_text="Infrastructure-as-Code format to generate",
            choices_ref="output:iac_formats",
            default_static="terraform",
            required=False,
            cli_flag="--format",
            cli_short="-f",
        ),
        Parameter(
            key="output_dir",
            label="Output Directory",
            type=ParameterType.PATH,
            help_text="Directory to write generated files",
            default_ref="config:output_dir",
            required=False,
            cli_flag="--output-dir",
            cli_short="-o",
        ),
        Parameter(
            key="backend_type",
            label="Backend Type",
            type=ParameterType.SELECT,
            help_text="Terraform backend type for state storage",
            choices_ref="terraform:backends",
            default_static="local",
            required=False,
            cli_flag="--backend",
        ),
        Parameter(
            key="backend_bucket",
            label="Backend S3 Bucket",
            type=ParameterType.TEXT,
            help_text="S3 bucket for remote state (if using S3 backend)",
            required=False,
            cli_flag="--backend-bucket",
        ),
        Parameter(
            key="terraform_version",
            label="Terraform Version",
            type=ParameterType.SELECT,
            help_text="Target Terraform version for generated code",
            choices_ref="terraform:versions",
            default_static="1.5",
            required=False,
            cli_flag="--tf-version",
        ),
        Parameter(
            key="generate_imports",
            label="Generate Import Blocks",
            type=ParameterType.CONFIRM,
            help_text="Generate import blocks for existing resources",
            default_static=True,
            required=False,
            cli_flag="--imports/--no-imports",
        ),
        Parameter(
            key="dry_run",
            label="Dry Run",
            type=ParameterType.CONFIRM,
            help_text="Preview what would be generated without writing files",
            default_static=False,
            required=False,
            cli_flag="--dry-run",
        ),
        Parameter(
            key="force",
            label="Force Overwrite",
            type=ParameterType.CONFIRM,
            help_text="Overwrite existing files without prompting",
            default_static=False,
            required=False,
            cli_flag="--force",
        ),
    ],
)


# ============================================================================
# AUDIT COMMAND PARAMETERS
# ============================================================================

AUDIT_PARAMETERS = ParameterGroup(
    name="audit",
    description="Security Audit - Check infrastructure against compliance frameworks",
    parameters=[
        Parameter(
            key="profile",
            label="AWS Profile",
            type=ParameterType.SELECT,
            help_text="AWS profile to use for authentication",
            choices_ref="aws:profiles",
            default_ref="config:profile",
            required=False,
            cli_flag="--profile",
            cli_short="-p",
        ),
        Parameter(
            key="region",
            label="AWS Region",
            type=ParameterType.SELECT,
            help_text="AWS region to audit",
            choices_ref="aws:regions",
            default_ref="config:region",
            required=False,
            cli_flag="--region",
            cli_short="-r",
        ),
        Parameter(
            key="framework",
            label="Compliance Framework",
            type=ParameterType.MULTISELECT,
            help_text="Compliance frameworks to check against",
            choices_ref="audit:frameworks",
            default_static=["CIS"],
            required=False,
            cli_flag="--framework",
        ),
        Parameter(
            key="min_severity",
            label="Minimum Severity",
            type=ParameterType.SELECT,
            help_text="Minimum severity level to report",
            choices_ref="audit:severity",
            default_static="LOW",
            required=False,
            cli_flag="--severity",
        ),
        Parameter(
            key="output_format",
            label="Output Format",
            type=ParameterType.SELECT,
            help_text="Report output format",
            choices_ref="output:report_formats",
            default_static="console",
            required=False,
            cli_flag="--format",
            cli_short="-f",
        ),
        Parameter(
            key="output_path",
            label="Output Path",
            type=ParameterType.PATH,
            help_text="Path to write the audit report",
            required=False,
            cli_flag="--output",
            cli_short="-o",
        ),
        Parameter(
            key="fail_on_findings",
            label="Fail on Findings",
            type=ParameterType.CONFIRM,
            help_text="Exit with error code if findings are detected (for CI/CD)",
            default_static=False,
            required=False,
            cli_flag="--fail-on-findings",
        ),
        Parameter(
            key="inline_comments",
            label="Add Inline Comments",
            type=ParameterType.CONFIRM,
            help_text="Add audit findings as inline comments in generated IaC",
            default_static=True,
            required=False,
            cli_flag="--inline/--no-inline",
        ),
    ],
)


# ============================================================================
# COST COMMAND PARAMETERS
# ============================================================================

COST_PARAMETERS = ParameterGroup(
    name="cost",
    description="Cost Analysis - Estimate infrastructure costs",
    parameters=[
        Parameter(
            key="profile",
            label="AWS Profile",
            type=ParameterType.SELECT,
            help_text="AWS profile to use for authentication",
            choices_ref="aws:profiles",
            default_ref="config:profile",
            required=False,
            cli_flag="--profile",
            cli_short="-p",
        ),
        Parameter(
            key="region",
            label="AWS Region",
            type=ParameterType.SELECT,
            help_text="AWS region to analyze",
            choices_ref="aws:regions",
            default_ref="config:region",
            required=False,
            cli_flag="--region",
            cli_short="-r",
        ),
        Parameter(
            key="output_format",
            label="Output Format",
            type=ParameterType.SELECT,
            help_text="Report output format",
            choices_ref="output:report_formats",
            default_static="console",
            required=False,
            cli_flag="--format",
            cli_short="-f",
        ),
        Parameter(
            key="ri_aware",
            label="RI-Aware Pricing",
            type=ParameterType.CONFIRM,
            help_text="Use Reserved Instance pricing where applicable",
            default_static=False,
            required=False,
            cli_flag="--ri-aware",
        ),
        Parameter(
            key="show_breakdown",
            label="Show Breakdown",
            type=ParameterType.CONFIRM,
            help_text="Show detailed cost breakdown by resource type",
            default_static=True,
            required=False,
            cli_flag="--breakdown/--no-breakdown",
        ),
        Parameter(
            key="output_path",
            label="Output Path",
            type=ParameterType.PATH,
            help_text="Path to write the cost report",
            required=False,
            cli_flag="--output",
            cli_short="-o",
        ),
    ],
)


# ============================================================================
# EXPORT FUNCTIONS
# ============================================================================


def export_all_schemas() -> dict[str, Any]:
    """
    Export all parameter schemas as a JSON-serializable dict.

    Returns:
        Dict containing all schemas, suitable for JSON serialization
    """
    return {
        "version": "1.0",
        "schemas": {
            "scan": SCAN_PARAMETERS.to_dict(),
            "clone": CLONE_PARAMETERS.to_dict(),
            "audit": AUDIT_PARAMETERS.to_dict(),
            "cost": COST_PARAMETERS.to_dict(),
        },
    }


def get_schema(command: str) -> ParameterGroup | None:
    """
    Get the parameter schema for a command.

    Args:
        command: Command name (scan, clone, audit, cost)

    Returns:
        ParameterGroup if found, None otherwise
    """
    schemas = {
        "scan": SCAN_PARAMETERS,
        "clone": CLONE_PARAMETERS,
        "audit": AUDIT_PARAMETERS,
        "cost": COST_PARAMETERS,
    }
    return schemas.get(command)


__all__ = [
    "AUDIT_PARAMETERS",
    "CLONE_PARAMETERS",
    "COST_PARAMETERS",
    "SCAN_PARAMETERS",
    "export_all_schemas",
    "get_schema",
]
