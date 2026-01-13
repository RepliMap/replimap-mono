"""
Error Catalog - Detailed information for all RepliMap error codes.

This catalog provides comprehensive information about each error code
including root causes, fix commands, and documentation links.

Error codes follow the format: RM-EXXX where XXX is a numeric code.
"""

from __future__ import annotations

from typing import Any, TypedDict


class ErrorEntry(TypedDict, total=False):
    """Type definition for error catalog entries."""

    summary: str
    fix_command: str
    fix_description: str
    root_cause: str
    docs: list[str]
    examples: list[str]
    related_codes: list[str]


# The main error catalog
# Each entry provides comprehensive information for the `replimap explain` command
ERROR_CATALOG: dict[str, ErrorEntry] = {
    # ==============================
    # Authentication Errors (E001-E099)
    # ==============================
    "RM-E001": {
        "summary": "No AWS credentials found",
        "fix_command": "aws configure",
        "fix_description": "Configure AWS credentials using the AWS CLI",
        "root_cause": (
            "RepliMap could not find valid AWS credentials. This happens when:\n"
            "  1. AWS CLI is not configured\n"
            "  2. Environment variables (AWS_ACCESS_KEY_ID, etc.) are not set\n"
            "  3. ~/.aws/credentials file is missing or empty"
        ),
        "docs": [
            "https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-quickstart.html"
        ],
        "examples": [
            "aws configure                    # Configure default profile",
            "aws configure --profile myprof   # Configure named profile",
            "export AWS_PROFILE=myprof        # Use specific profile",
        ],
        "related_codes": ["RM-E002", "RM-E004"],
    },
    "RM-E002": {
        "summary": "AWS profile not found",
        "fix_command": "aws configure --profile <name>",
        "fix_description": "Create or configure the specified AWS profile",
        "root_cause": (
            "The specified AWS profile does not exist in your configuration. "
            "Profiles are stored in ~/.aws/credentials and ~/.aws/config."
        ),
        "docs": [
            "https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-profiles.html"
        ],
        "examples": [
            "aws configure --profile prod     # Create prod profile",
            "replimap profiles                # List available profiles",
        ],
        "related_codes": ["RM-E001"],
    },
    "RM-E003": {
        "summary": "Sensitive operation blocked in CI environment",
        "fix_command": "replimap scan --profile <name>",
        "fix_description": "Specify the profile explicitly to avoid interactive prompts",
        "root_cause": (
            "RepliMap detected an operation that requires user confirmation "
            "(like switching AWS profiles), but the command is running in a CI "
            "environment where interactive prompts are not possible.\n\n"
            "To fix this, explicitly specify all sensitive options via CLI flags "
            "or environment variables."
        ),
        "docs": [
            "https://github.com/RepliMap/replimap/wiki/CI-Integration"
        ],
        "examples": [
            "replimap scan --profile prod --region us-east-1",
            "export AWS_PROFILE=prod && replimap scan",
        ],
        "related_codes": ["RM-E001", "RM-E002"],
    },
    "RM-E004": {
        "summary": "AWS credentials expired",
        "fix_command": "replimap cache clear && aws sso login",
        "fix_description": "Clear cached credentials and re-authenticate",
        "root_cause": (
            "Your AWS session token has expired. This commonly happens with:\n"
            "  1. AWS SSO sessions (typically expire after 8-12 hours)\n"
            "  2. MFA-based temporary credentials\n"
            "  3. Assumed role credentials"
        ),
        "docs": [
            "https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-sso.html"
        ],
        "examples": [
            "replimap cache clear",
            "aws sso login --profile myprof",
        ],
        "related_codes": ["RM-E001"],
    },
    # ==============================
    # Permission Errors (E100-E199)
    # ==============================
    "RM-E100": {
        "summary": "Access denied - insufficient IAM permissions",
        "fix_command": "replimap iam --generate-policy > policy.json",
        "fix_description": "Generate the minimum IAM policy required for RepliMap",
        "root_cause": (
            "The AWS credentials you're using don't have permission to perform "
            "the requested operation. RepliMap requires read-only access to "
            "various AWS services to scan your infrastructure."
        ),
        "docs": [
            "https://github.com/RepliMap/replimap/wiki/IAM-Permissions"
        ],
        "examples": [
            "replimap iam --generate-policy > policy.json",
            "aws iam put-user-policy --user-name replimap --policy-name RepliMapPolicy --policy-document file://policy.json",
        ],
        "related_codes": ["RM-E101", "RM-E102"],
    },
    "RM-E101": {
        "summary": "Service-specific access denied",
        "fix_command": "replimap scan --skip-service <service>",
        "fix_description": "Skip the service you don't have access to",
        "root_cause": (
            "You don't have permission to access a specific AWS service. "
            "You can either request the necessary permissions or skip "
            "scanning that service."
        ),
        "docs": [],
        "examples": [
            "replimap scan --skip-service s3",
            "replimap scan --skip-service rds,lambda",
        ],
        "related_codes": ["RM-E100"],
    },
    "RM-E102": {
        "summary": "STS AssumeRole failed",
        "fix_command": "aws sts get-caller-identity",
        "fix_description": "Verify your current identity and role trust policy",
        "root_cause": (
            "Failed to assume the specified IAM role. Common causes:\n"
            "  1. Role trust policy doesn't allow your identity\n"
            "  2. Role doesn't exist\n"
            "  3. External ID mismatch (for cross-account roles)"
        ),
        "docs": [
            "https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_use.html"
        ],
        "examples": [
            "aws sts get-caller-identity  # Check current identity",
            "aws sts assume-role --role-arn <arn> --role-session-name test",
        ],
        "related_codes": ["RM-E100"],
    },
    # ==============================
    # Rate Limiting Errors (E200-E299)
    # ==============================
    "RM-E200": {
        "summary": "AWS API rate limit exceeded (throttled)",
        "fix_command": "replimap scan --concurrency 3",
        "fix_description": "Reduce the number of concurrent API calls",
        "root_cause": (
            "AWS has rate-limited your API calls because too many requests "
            "were made in a short period. This is common when scanning large "
            "accounts with many resources."
        ),
        "docs": [
            "https://docs.aws.amazon.com/general/latest/gr/api-retries.html"
        ],
        "examples": [
            "replimap scan --concurrency 3   # Reduce concurrency",
            "replimap scan --cache           # Use cached data when possible",
        ],
        "related_codes": ["RM-E201"],
    },
    "RM-E201": {
        "summary": "Service quota exceeded",
        "fix_command": "aws service-quotas list-service-quotas --service-code <service>",
        "fix_description": "Check and request quota increases if needed",
        "root_cause": (
            "You've exceeded a service-specific quota or limit. This is "
            "different from API rate limiting - it means you've hit an "
            "account-level limit."
        ),
        "docs": [
            "https://docs.aws.amazon.com/servicequotas/latest/userguide/intro.html"
        ],
        "examples": [],
        "related_codes": ["RM-E200"],
    },
    # ==============================
    # Network Errors (E300-E399)
    # ==============================
    "RM-E300": {
        "summary": "Network connectivity error",
        "fix_command": "replimap doctor",
        "fix_description": "Run diagnostics to identify connectivity issues",
        "root_cause": (
            "Could not establish a connection to AWS. Possible causes:\n"
            "  1. No internet connection\n"
            "  2. Firewall blocking AWS endpoints\n"
            "  3. Proxy misconfiguration\n"
            "  4. VPN issues"
        ),
        "docs": [],
        "examples": [
            "replimap doctor",
            "curl -I https://sts.amazonaws.com  # Test connectivity",
        ],
        "related_codes": ["RM-E301"],
    },
    "RM-E301": {
        "summary": "Request timeout",
        "fix_command": "replimap scan --timeout 60",
        "fix_description": "Increase the request timeout",
        "root_cause": (
            "The AWS API request timed out before completing. This can happen "
            "with slow network connections or when listing very large numbers "
            "of resources."
        ),
        "docs": [],
        "examples": [
            "replimap scan --timeout 60       # 60 second timeout",
            "replimap scan --concurrency 3    # Reduce load",
        ],
        "related_codes": ["RM-E300"],
    },
    # ==============================
    # Configuration Errors (E400-E499)
    # ==============================
    "RM-E400": {
        "summary": "Invalid configuration",
        "fix_command": "replimap doctor",
        "fix_description": "Run diagnostics to identify configuration issues",
        "root_cause": (
            "The RepliMap configuration file contains invalid settings. "
            "Check ~/.replimap/config.toml for syntax errors."
        ),
        "docs": [],
        "examples": [
            "replimap doctor",
            "cat ~/.replimap/config.toml",
        ],
        "related_codes": [],
    },
    "RM-E401": {
        "summary": "Output directory not writable",
        "fix_command": "mkdir -p ./terraform && chmod 755 ./terraform",
        "fix_description": "Create the output directory with proper permissions",
        "root_cause": (
            "RepliMap cannot write to the specified output directory. "
            "This could be due to missing directory or permission issues."
        ),
        "docs": [],
        "examples": [
            "replimap clone --output ./my-terraform",
        ],
        "related_codes": [],
    },
    # ==============================
    # Decision Errors (E500-E599)
    # ==============================
    "RM-E500": {
        "summary": "Decision expired",
        "fix_command": "replimap decisions renew <decision_id>",
        "fix_description": "Renew the expired decision or make a new choice",
        "root_cause": (
            "A previously saved decision has expired. Decisions have TTL "
            "(Time To Live) to prevent stale configurations from persisting "
            "indefinitely."
        ),
        "docs": [],
        "examples": [
            "replimap decisions list --expired",
            "replimap decisions renew scan.permissions.skip_s3",
        ],
        "related_codes": ["RM-E501"],
    },
    "RM-E501": {
        "summary": "Decision conflict",
        "fix_command": "replimap decisions clear --scope <scope>",
        "fix_description": "Clear conflicting decisions and start fresh",
        "root_cause": (
            "Multiple decisions conflict with each other. This can happen "
            "when importing decisions or after configuration changes."
        ),
        "docs": [],
        "examples": [
            "replimap decisions list",
            "replimap decisions clear --scope extraction",
        ],
        "related_codes": ["RM-E500"],
    },
    # ==============================
    # Terraform Errors (E600-E699)
    # ==============================
    "RM-E600": {
        "summary": "Terraform not installed",
        "fix_command": "brew install terraform",
        "fix_description": "Install Terraform (optional, only needed for validation)",
        "root_cause": (
            "Terraform is not installed or not in PATH. While RepliMap doesn't "
            "require Terraform to generate code, some features like validation "
            "need it."
        ),
        "docs": [
            "https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli"
        ],
        "examples": [
            "brew install terraform          # macOS",
            "apt-get install terraform       # Ubuntu/Debian",
            "terraform --version             # Verify installation",
        ],
        "related_codes": [],
    },
}


def get_error_info(code: str) -> ErrorEntry | None:
    """
    Get error information by code.

    Args:
        code: Error code (e.g., "RM-E001")

    Returns:
        Error entry or None if not found
    """
    return ERROR_CATALOG.get(code)


def search_errors(query: str) -> list[tuple[str, ErrorEntry]]:
    """
    Search error catalog by keyword.

    Args:
        query: Search term

    Returns:
        List of (code, entry) tuples matching the query
    """
    query_lower = query.lower()
    results = []

    for code, entry in ERROR_CATALOG.items():
        # Search in code, summary, and root_cause
        searchable = f"{code} {entry.get('summary', '')} {entry.get('root_cause', '')}"
        if query_lower in searchable.lower():
            results.append((code, entry))

    return results


def list_all_codes() -> list[str]:
    """Get all error codes in the catalog."""
    return sorted(ERROR_CATALOG.keys())


def format_error_for_display(code: str) -> str:
    """
    Format an error entry for display (explain command).

    Args:
        code: Error code

    Returns:
        Formatted string for display
    """
    entry = ERROR_CATALOG.get(code)
    if not entry:
        return f"Unknown error code: {code}"

    lines = [
        f"╭─ {code} ─╮",
        "",
        f"Summary: {entry.get('summary', 'No description')}",
        "",
    ]

    if entry.get("root_cause"):
        lines.append("Root Cause:")
        for line in entry["root_cause"].split("\n"):
            lines.append(f"  {line}")
        lines.append("")

    if entry.get("fix_command"):
        lines.append("Fix:")
        lines.append(f"  $ {entry['fix_command']}")
        if entry.get("fix_description"):
            lines.append(f"  {entry['fix_description']}")
        lines.append("")

    if entry.get("examples"):
        lines.append("Examples:")
        for example in entry["examples"]:
            lines.append(f"  $ {example}")
        lines.append("")

    if entry.get("docs"):
        lines.append("Documentation:")
        for doc in entry["docs"]:
            lines.append(f"  • {doc}")
        lines.append("")

    if entry.get("related_codes"):
        lines.append(f"Related: {', '.join(entry['related_codes'])}")

    return "\n".join(lines)


__all__ = [
    "ERROR_CATALOG",
    "format_error_for_display",
    "get_error_info",
    "list_all_codes",
    "search_errors",
]
