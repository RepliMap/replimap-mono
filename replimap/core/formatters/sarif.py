"""
Robust SARIF (Static Analysis Results Interchange Format) Generator.

Production-grade SARIF 2.1.0 generator for GitHub Security integration with:
- Dynamic Rule Registry with predefined and fallback rules
- Stable fingerprinting for GitHub deduplication
- Hybrid locations (file + cloud resources)
- Rich Markdown support for GitHub display
- Full GitHub Advanced Security compatibility

SARIF 2.1.0 specification: https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from replimap.core.drift.detector import DriftReport


# ============================================================
# SARIF ENUMS AND DATA MODELS
# ============================================================


class SARIFLevel(Enum):
    """SARIF result levels mapping to GitHub severity."""

    ERROR = "error"  # Maps to Critical/High findings
    WARNING = "warning"  # Maps to Medium findings
    NOTE = "note"  # Maps to Low findings
    NONE = "none"  # Maps to Info findings


@dataclass
class SARIFRule:
    """
    SARIF rule definition with full metadata.

    Each unique finding type maps to a rule that GitHub displays
    in the Security tab's rule index.
    """

    id: str
    name: str
    short_description: str
    full_description: str
    help_uri: str = "https://replimap.dev/docs"
    help_text: str = ""
    default_level: SARIFLevel = SARIFLevel.WARNING
    security_severity: float = 5.0
    tags: list[str] = field(default_factory=list)
    cwe_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to SARIF reportingDescriptor format."""
        rule = {
            "id": self.id,
            "name": self.name,
            "shortDescription": {"text": self.short_description},
            "fullDescription": {"text": self.full_description},
            "helpUri": self.help_uri,
            "defaultConfiguration": {"level": self.default_level.value},
            "properties": {
                "security-severity": str(self.security_severity),
                "tags": self.tags or ["infrastructure", "cloud", "security"],
            },
        }

        # Add help markdown if provided
        if self.help_text:
            rule["help"] = {
                "text": self.help_text,
                "markdown": self.help_text,
            }

        # Add CWE relationships if provided
        if self.cwe_ids:
            rule["relationships"] = [
                {
                    "target": {"id": cwe_id, "toolComponent": {"name": "CWE"}},
                    "kinds": ["superset"],
                }
                for cwe_id in self.cwe_ids
            ]

        return rule


@dataclass
class SARIFLocation:
    """
    Hybrid SARIF location supporting both file and cloud resources.

    Supports:
    - Physical location (file + line/column)
    - Logical location (resource address, cloud path)
    - Region with line numbers or URI-based addressing
    """

    # Physical location (file-based)
    artifact_uri: str | None = None
    artifact_uri_base_id: str = "%SRCROOT%"
    start_line: int | None = None
    start_column: int | None = None
    end_line: int | None = None
    end_column: int | None = None

    # Logical location (cloud resource-based)
    logical_name: str | None = None
    logical_kind: str = "resource"
    fully_qualified_name: str | None = None
    decorated_name: str | None = None

    # Cloud-specific properties
    cloud_provider: str = "aws"
    resource_arn: str | None = None
    resource_id: str | None = None
    region: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to SARIF location format."""
        location: dict[str, Any] = {}

        # Physical location
        if self.artifact_uri:
            physical: dict[str, Any] = {
                "artifactLocation": {
                    "uri": self.artifact_uri,
                }
            }

            if self.artifact_uri_base_id:
                physical["artifactLocation"]["uriBaseId"] = self.artifact_uri_base_id

            # Add region if line info provided
            if self.start_line is not None:
                physical["region"] = {"startLine": self.start_line}
                if self.start_column is not None:
                    physical["region"]["startColumn"] = self.start_column
                if self.end_line is not None:
                    physical["region"]["endLine"] = self.end_line
                if self.end_column is not None:
                    physical["region"]["endColumn"] = self.end_column

            location["physicalLocation"] = physical

        # Logical locations (can have multiple)
        logical_locations = []

        if self.logical_name or self.fully_qualified_name:
            logical = {
                "name": self.logical_name or self.fully_qualified_name,
                "kind": self.logical_kind,
            }
            if self.fully_qualified_name:
                logical["fullyQualifiedName"] = self.fully_qualified_name
            if self.decorated_name:
                logical["decoratedName"] = self.decorated_name

            logical_locations.append(logical)

        # Add cloud resource location
        if self.resource_arn or self.resource_id:
            cloud_logical = {
                "name": self.resource_id or self.resource_arn,
                "kind": "cloudResource",
            }
            if self.resource_arn:
                cloud_logical["fullyQualifiedName"] = self.resource_arn
            if self.region:
                cloud_logical["decoratedName"] = f"{self.cloud_provider}:{self.region}"

            logical_locations.append(cloud_logical)

        if logical_locations:
            location["logicalLocations"] = logical_locations

        # Add cloud properties
        if self.resource_arn or self.resource_id or self.region:
            location["properties"] = {}
            if self.cloud_provider:
                location["properties"]["cloudProvider"] = self.cloud_provider
            if self.resource_arn:
                location["properties"]["resourceArn"] = self.resource_arn
            if self.resource_id:
                location["properties"]["resourceId"] = self.resource_id
            if self.region:
                location["properties"]["region"] = self.region

        return location


@dataclass
class SARIFResult:
    """
    SARIF result with stable fingerprinting.

    Fingerprints are critical for GitHub's deduplication:
    - Same fingerprint = same issue (won't create duplicate alert)
    - Different fingerprint = new issue
    """

    rule_id: str
    level: SARIFLevel
    message_text: str
    message_markdown: str | None = None
    locations: list[SARIFLocation] = field(default_factory=list)
    fingerprint_components: list[str] = field(default_factory=list)
    properties: dict[str, Any] = field(default_factory=dict)
    fixes: list[dict[str, Any]] = field(default_factory=list)
    code_flows: list[dict[str, Any]] = field(default_factory=list)
    related_locations: list[SARIFLocation] = field(default_factory=list)

    def fingerprint(self) -> str:
        """
        Generate stable fingerprint for deduplication.

        Uses SHA-256 of concatenated components:
        - Rule ID (finding type)
        - Resource ID (specific instance)
        - Custom components (e.g., field name for drift)

        This ensures:
        - Same issue on same resource = same fingerprint
        - Different issues = different fingerprints
        - Resource changes don't break tracking
        """
        components = [self.rule_id] + self.fingerprint_components
        raw = "|".join(str(c) for c in components if c)
        return hashlib.sha256(raw.encode()).hexdigest()[:32]

    def to_dict(self) -> dict[str, Any]:
        """Convert to SARIF result format."""
        result: dict[str, Any] = {
            "ruleId": self.rule_id,
            "level": self.level.value,
            "message": {"text": self.message_text},
        }

        # Add markdown message if provided
        if self.message_markdown:
            result["message"]["markdown"] = self.message_markdown

        # Add locations
        if self.locations:
            result["locations"] = [loc.to_dict() for loc in self.locations]

        # Add fingerprints
        result["fingerprints"] = {
            "replimap/v1": self.fingerprint(),
        }

        # Add partial fingerprints for hierarchical deduplication
        result["partialFingerprints"] = {
            "ruleId/v1": hashlib.sha256(self.rule_id.encode()).hexdigest()[:16],
        }
        if self.fingerprint_components:
            result["partialFingerprints"]["primaryResource/v1"] = hashlib.sha256(
                self.fingerprint_components[0].encode()
                if self.fingerprint_components
                else b""
            ).hexdigest()[:16]

        # Add fixes if provided
        if self.fixes:
            result["fixes"] = self.fixes

        # Add code flows (for attack path visualization)
        if self.code_flows:
            result["codeFlows"] = self.code_flows

        # Add related locations (for context)
        if self.related_locations:
            result["relatedLocations"] = [
                {"id": i, **loc.to_dict()}
                for i, loc in enumerate(self.related_locations)
            ]

        # Add custom properties
        if self.properties:
            result["properties"] = self.properties

        return result


# ============================================================
# MARKDOWN BUILDER
# ============================================================


class MarkdownBuilder:
    """
    Helper for building rich Markdown content for GitHub display.

    GitHub's Security tab renders markdown in:
    - Rule help text
    - Result messages
    - Fix descriptions
    """

    @staticmethod
    def header(text: str, level: int = 2) -> str:
        """Create markdown header."""
        return f"{'#' * level} {text}\n\n"

    @staticmethod
    def paragraph(text: str) -> str:
        """Create paragraph."""
        return f"{text}\n\n"

    @staticmethod
    def bullet_list(items: list[str]) -> str:
        """Create bullet list."""
        return "\n".join(f"- {item}" for item in items) + "\n\n"

    @staticmethod
    def numbered_list(items: list[str]) -> str:
        """Create numbered list."""
        return "\n".join(f"{i}. {item}" for i, item in enumerate(items, 1)) + "\n\n"

    @staticmethod
    def code_block(code: str, lang: str = "") -> str:
        """Create fenced code block."""
        return f"```{lang}\n{code}\n```\n\n"

    @staticmethod
    def inline_code(code: str) -> str:
        """Create inline code."""
        return f"`{code}`"

    @staticmethod
    def bold(text: str) -> str:
        """Create bold text."""
        return f"**{text}**"

    @staticmethod
    def italic(text: str) -> str:
        """Create italic text."""
        return f"*{text}*"

    @staticmethod
    def link(text: str, url: str) -> str:
        """Create link."""
        return f"[{text}]({url})"

    @staticmethod
    def table(headers: list[str], rows: list[list[str]]) -> str:
        """Create markdown table."""
        lines = []
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("| " + " | ".join("---" for _ in headers) + " |")
        for row in rows:
            lines.append("| " + " | ".join(str(cell) for cell in row) + " |")
        return "\n".join(lines) + "\n\n"

    @staticmethod
    def collapsible(summary: str, content: str) -> str:
        """Create collapsible section."""
        return f"<details>\n<summary>{summary}</summary>\n\n{content}\n</details>\n\n"

    @staticmethod
    def badge(label: str, value: str, color: str = "blue") -> str:
        """Create shield.io badge (rendered by GitHub)."""
        label_enc = label.replace(" ", "%20")
        value_enc = value.replace(" ", "%20")
        return (
            f"![{label}](https://img.shields.io/badge/{label_enc}-{value_enc}-{color})"
        )

    @staticmethod
    def severity_badge(severity: str) -> str:
        """Create severity badge with appropriate color."""
        colors = {
            "critical": "red",
            "high": "orange",
            "medium": "yellow",
            "low": "blue",
            "info": "gray",
        }
        color = colors.get(severity.lower(), "gray")
        return MarkdownBuilder.badge("severity", severity, color)


# ============================================================
# RULE REGISTRY
# ============================================================


class RuleRegistry:
    """
    Dynamic rule registry with predefined and fallback rules.

    Predefined rules provide consistent, well-documented rule definitions
    for known finding types. Fallback rules are generated dynamically
    for unexpected finding types.
    """

    # Predefined rules with full metadata
    PREDEFINED_RULES: dict[str, SARIFRule] = {
        # ============ AUDIT RULES ============
        "AUDIT001": SARIFRule(
            id="AUDIT001",
            name="PubliclyAccessibleResource",
            short_description="Resource is publicly accessible",
            full_description=(
                "A cloud resource has been configured with public access enabled. "
                "This could expose sensitive data or functionality to unauthorized users. "
                "Public access should be restricted unless explicitly required."
            ),
            help_uri="https://replimap.dev/docs/rules/AUDIT001",
            help_text=(
                "## Publicly Accessible Resource\n\n"
                "### Impact\n"
                "Resources with public access can be discovered and accessed by anyone "
                "on the internet, potentially leading to data breaches or unauthorized access.\n\n"
                "### Remediation\n"
                "1. Review if public access is truly required\n"
                "2. Restrict access using security groups, NACLs, or IAM policies\n"
                "3. Enable logging to monitor access patterns\n"
            ),
            default_level=SARIFLevel.ERROR,
            security_severity=8.0,
            tags=["security", "public-access", "cloud"],
            cwe_ids=["CWE-284", "CWE-200"],
        ),
        "AUDIT002": SARIFRule(
            id="AUDIT002",
            name="UnencryptedResource",
            short_description="Resource lacks encryption",
            full_description=(
                "A cloud resource storing or transmitting data does not have encryption "
                "enabled. This could lead to data exposure if the resource is compromised. "
                "Enable encryption at rest and in transit."
            ),
            help_uri="https://replimap.dev/docs/rules/AUDIT002",
            help_text=(
                "## Unencrypted Resource\n\n"
                "### Impact\n"
                "Data stored without encryption can be read by anyone with access to "
                "the underlying storage, including cloud provider employees or attackers.\n\n"
                "### Remediation\n"
                "1. Enable server-side encryption (SSE)\n"
                "2. Use KMS managed keys for additional control\n"
                "3. Enable encryption in transit (TLS/HTTPS)\n"
            ),
            default_level=SARIFLevel.ERROR,
            security_severity=7.5,
            tags=["security", "encryption", "compliance"],
            cwe_ids=["CWE-311", "CWE-312"],
        ),
        "AUDIT003": SARIFRule(
            id="AUDIT003",
            name="OverlyPermissiveIAM",
            short_description="IAM permissions are overly permissive",
            full_description=(
                "An IAM policy or role grants more permissions than necessary, violating "
                "the principle of least privilege. This increases the blast radius of "
                "potential security incidents."
            ),
            help_uri="https://replimap.dev/docs/rules/AUDIT003",
            help_text=(
                "## Overly Permissive IAM\n\n"
                "### Impact\n"
                "Excessive permissions allow compromised credentials to access resources "
                "beyond what's needed for their intended function.\n\n"
                "### Remediation\n"
                "1. Review and remove unused permissions\n"
                "2. Use resource-level permissions instead of wildcards\n"
                "3. Implement permission boundaries\n"
                "4. Enable CloudTrail to audit permission usage\n"
            ),
            default_level=SARIFLevel.ERROR,
            security_severity=8.5,
            tags=["security", "iam", "least-privilege"],
            cwe_ids=["CWE-732", "CWE-269"],
        ),
        "AUDIT004": SARIFRule(
            id="AUDIT004",
            name="InsecureSecurityGroup",
            short_description="Security group allows unrestricted access",
            full_description=(
                "A security group rule allows inbound or outbound traffic from 0.0.0.0/0 "
                "(all IP addresses) on sensitive ports. This exposes resources to the "
                "entire internet."
            ),
            help_uri="https://replimap.dev/docs/rules/AUDIT004",
            help_text=(
                "## Insecure Security Group\n\n"
                "### Impact\n"
                "Open security groups expose services to potential attacks from anywhere "
                "on the internet, including port scanning and exploitation attempts.\n\n"
                "### Remediation\n"
                "1. Restrict CIDR ranges to known IP addresses\n"
                "2. Use security group references instead of IP ranges\n"
                "3. Implement network segmentation\n"
                "4. Use VPN or bastion hosts for remote access\n"
            ),
            default_level=SARIFLevel.ERROR,
            security_severity=9.0,
            tags=["security", "network", "firewall"],
            cwe_ids=["CWE-284", "CWE-668"],
        ),
        "AUDIT005": SARIFRule(
            id="AUDIT005",
            name="MissingLogging",
            short_description="Resource lacks audit logging",
            full_description=(
                "A resource does not have audit logging enabled. This prevents detection "
                "and investigation of security incidents. Enable appropriate logging for "
                "all sensitive resources."
            ),
            help_uri="https://replimap.dev/docs/rules/AUDIT005",
            help_text=(
                "## Missing Audit Logging\n\n"
                "### Impact\n"
                "Without logging, security incidents may go undetected and forensic "
                "investigation becomes impossible.\n\n"
                "### Remediation\n"
                "1. Enable CloudTrail for API call logging\n"
                "2. Enable access logging for S3 buckets\n"
                "3. Enable VPC flow logs for network monitoring\n"
                "4. Configure log retention policies\n"
            ),
            default_level=SARIFLevel.WARNING,
            security_severity=5.0,
            tags=["security", "logging", "monitoring"],
            cwe_ids=["CWE-778"],
        ),
        "AUDIT006": SARIFRule(
            id="AUDIT006",
            name="CrossAccountAccess",
            short_description="Resource allows cross-account access",
            full_description=(
                "A resource policy allows access from external AWS accounts. While this "
                "may be intentional for legitimate sharing, it should be reviewed to "
                "ensure only trusted accounts have access."
            ),
            help_uri="https://replimap.dev/docs/rules/AUDIT006",
            help_text=(
                "## Cross-Account Access\n\n"
                "### Impact\n"
                "Cross-account access can lead to data exfiltration if the external "
                "account is compromised or malicious.\n\n"
                "### Remediation\n"
                "1. Verify all external account IDs are trusted\n"
                "2. Use external ID for third-party access\n"
                "3. Implement resource-based policy conditions\n"
                "4. Monitor cross-account access with CloudTrail\n"
            ),
            default_level=SARIFLevel.WARNING,
            security_severity=6.0,
            tags=["security", "cross-account", "trust"],
            cwe_ids=["CWE-284"],
        ),
        "AUDIT007": SARIFRule(
            id="AUDIT007",
            name="DefaultVPCUsage",
            short_description="Resource uses default VPC",
            full_description=(
                "A resource is deployed in the default VPC. Default VPCs have less "
                "restrictive network controls and should be avoided for production "
                "workloads."
            ),
            help_uri="https://replimap.dev/docs/rules/AUDIT007",
            help_text=(
                "## Default VPC Usage\n\n"
                "### Impact\n"
                "Default VPCs may have overly permissive security groups and routing "
                "that don't follow security best practices.\n\n"
                "### Remediation\n"
                "1. Create custom VPCs with appropriate CIDR ranges\n"
                "2. Implement network segmentation (public/private subnets)\n"
                "3. Delete or modify default VPC security groups\n"
                "4. Migrate workloads to custom VPCs\n"
            ),
            default_level=SARIFLevel.NOTE,
            security_severity=3.0,
            tags=["security", "network", "vpc"],
            cwe_ids=["CWE-1188"],
        ),
        "AUDIT008": SARIFRule(
            id="AUDIT008",
            name="UntaggedResource",
            short_description="Resource lacks required tags",
            full_description=(
                "A resource is missing required tags for cost allocation, ownership, "
                "or compliance tracking. Proper tagging is essential for governance."
            ),
            help_uri="https://replimap.dev/docs/rules/AUDIT008",
            help_text=(
                "## Untagged Resource\n\n"
                "### Impact\n"
                "Untagged resources cannot be properly tracked for cost allocation, "
                "ownership, or compliance reporting.\n\n"
                "### Remediation\n"
                "1. Apply required tags (Environment, Owner, CostCenter)\n"
                "2. Use AWS Config rules to enforce tagging\n"
                "3. Implement tag policies in AWS Organizations\n"
            ),
            default_level=SARIFLevel.NOTE,
            security_severity=1.0,
            tags=["governance", "tagging", "compliance"],
            cwe_ids=[],
        ),
        # ============ DRIFT RULES ============
        "DRIFT001": SARIFRule(
            id="DRIFT001",
            name="UnmanagedResource",
            short_description="Unmanaged resource detected",
            full_description=(
                "An AWS resource exists that is not managed by Terraform. This could be "
                "a resource created manually via the AWS Console, CLI, or another tool. "
                "Unmanaged resources can lead to configuration inconsistencies."
            ),
            help_uri="https://replimap.dev/docs/rules/DRIFT001",
            help_text=(
                "## Unmanaged Resource\n\n"
                "### Impact\n"
                "Unmanaged resources exist outside your Infrastructure as Code, making "
                "them difficult to track, replicate, and secure.\n\n"
                "### Remediation\n"
                "1. Import into Terraform: `terraform import <resource_type>.<name> <id>`\n"
                "2. Or delete if no longer needed\n"
                "3. Update runbooks to prevent manual creation\n"
            ),
            default_level=SARIFLevel.WARNING,
            security_severity=5.0,
            tags=["infrastructure", "drift", "terraform"],
            cwe_ids=[],
        ),
        "DRIFT002": SARIFRule(
            id="DRIFT002",
            name="MissingResource",
            short_description="Terraform resource missing from AWS",
            full_description=(
                "A resource defined in Terraform state no longer exists in AWS. This "
                "indicates the resource was deleted outside of Terraform, which can "
                "cause terraform apply failures or unexpected recreations."
            ),
            help_uri="https://replimap.dev/docs/rules/DRIFT002",
            help_text=(
                "## Missing Resource\n\n"
                "### Impact\n"
                "Terraform state is out of sync with reality. Running `terraform apply` "
                "will attempt to recreate the resource.\n\n"
                "### Remediation\n"
                "1. Run `terraform apply` to recreate the resource\n"
                "2. Or `terraform state rm <address>` to remove from state\n"
                "3. Investigate why resource was deleted manually\n"
            ),
            default_level=SARIFLevel.ERROR,
            security_severity=6.0,
            tags=["infrastructure", "drift", "terraform"],
            cwe_ids=[],
        ),
        "DRIFT003": SARIFRule(
            id="DRIFT003",
            name="ConfigurationDrift",
            short_description="Resource configuration has drifted",
            full_description=(
                "A resource's configuration in AWS differs from what Terraform expects. "
                "This could be due to manual changes via Console/CLI. Configuration drift "
                "can cause unexpected behavior and security issues."
            ),
            help_uri="https://replimap.dev/docs/rules/DRIFT003",
            help_text=(
                "## Configuration Drift\n\n"
                "### Impact\n"
                "Actual configuration differs from desired state, potentially causing "
                "security vulnerabilities or operational issues.\n\n"
                "### Remediation\n"
                "1. Run `terraform plan` to see full diff\n"
                "2. Run `terraform apply` to restore expected state\n"
                "3. Or update .tf files to match current reality\n"
            ),
            default_level=SARIFLevel.WARNING,
            security_severity=5.0,
            tags=["infrastructure", "drift", "terraform"],
            cwe_ids=[],
        ),
        "DRIFT004": SARIFRule(
            id="DRIFT004",
            name="SecurityDrift",
            short_description="Security-critical configuration has drifted",
            full_description=(
                "A security-critical attribute (IAM policy, security group rule, encryption "
                "setting) has been modified outside of Terraform. This requires immediate "
                "investigation as it may indicate a security incident."
            ),
            help_uri="https://replimap.dev/docs/rules/DRIFT004",
            help_text=(
                "## Security Configuration Drift\n\n"
                "### Impact\n"
                "Security controls may have been weakened or bypassed. This could be "
                "an indicator of compromise or policy violation.\n\n"
                "### Remediation\n"
                "1. **IMMEDIATE**: Investigate the change in CloudTrail\n"
                "2. Determine if change was authorized\n"
                "3. Restore expected configuration if unauthorized\n"
                "4. Review access controls and audit logs\n"
            ),
            default_level=SARIFLevel.ERROR,
            security_severity=9.0,
            tags=["security", "drift", "terraform", "incident"],
            cwe_ids=["CWE-284"],
        ),
        # ============ ANALYSIS RULES ============
        "ANALYSIS001": SARIFRule(
            id="ANALYSIS001",
            name="AttackPathIdentified",
            short_description="Potential attack path identified",
            full_description=(
                "RepliMap's graph analysis has identified a potential attack path from "
                "a public entry point to a sensitive resource. This represents a chain "
                "of permissions and connections that could be exploited."
            ),
            help_uri="https://replimap.dev/docs/rules/ANALYSIS001",
            help_text=(
                "## Attack Path Identified\n\n"
                "### Impact\n"
                "An attacker could potentially traverse this path to reach sensitive "
                "resources.\n\n"
                "### Remediation\n"
                "1. Review each hop in the attack path\n"
                "2. Remove unnecessary connections\n"
                "3. Add security controls at chokepoints\n"
                "4. Consider network segmentation\n"
            ),
            default_level=SARIFLevel.ERROR,
            security_severity=8.0,
            tags=["security", "attack-path", "graph-analysis"],
            cwe_ids=["CWE-284"],
        ),
        "ANALYSIS002": SARIFRule(
            id="ANALYSIS002",
            name="BlastRadiusHigh",
            short_description="Resource has high blast radius",
            full_description=(
                "A resource has connections to many other resources, meaning its compromise "
                "could affect a large portion of the infrastructure. Consider implementing "
                "additional controls or segmentation."
            ),
            help_uri="https://replimap.dev/docs/rules/ANALYSIS002",
            help_text=(
                "## High Blast Radius\n\n"
                "### Impact\n"
                "Compromise of this resource could have widespread impact across the "
                "infrastructure.\n\n"
                "### Remediation\n"
                "1. Implement additional security controls\n"
                "2. Consider breaking into smaller components\n"
                "3. Add monitoring and alerting\n"
                "4. Document incident response procedures\n"
            ),
            default_level=SARIFLevel.WARNING,
            security_severity=6.0,
            tags=["security", "blast-radius", "graph-analysis"],
            cwe_ids=[],
        ),
        "ANALYSIS003": SARIFRule(
            id="ANALYSIS003",
            name="OrphanedResource",
            short_description="Resource has no connections",
            full_description=(
                "A resource exists with no connections to other resources in the graph. "
                "This could indicate an abandoned resource that should be cleaned up, or "
                "a misconfiguration preventing proper functionality."
            ),
            help_uri="https://replimap.dev/docs/rules/ANALYSIS003",
            help_text=(
                "## Orphaned Resource\n\n"
                "### Impact\n"
                "Orphaned resources may incur costs without providing value, or may "
                "indicate integration issues.\n\n"
                "### Remediation\n"
                "1. Verify if resource is still needed\n"
                "2. Delete if no longer required\n"
                "3. Fix connections if misconfigured\n"
            ),
            default_level=SARIFLevel.NOTE,
            security_severity=2.0,
            tags=["governance", "cleanup", "graph-analysis"],
            cwe_ids=[],
        ),
        "ANALYSIS004": SARIFRule(
            id="ANALYSIS004",
            name="CircularDependency",
            short_description="Circular dependency detected",
            full_description=(
                "Resources form a circular dependency chain, which can cause issues with "
                "deployment, updates, and teardown operations."
            ),
            help_uri="https://replimap.dev/docs/rules/ANALYSIS004",
            help_text=(
                "## Circular Dependency\n\n"
                "### Impact\n"
                "Circular dependencies can cause deployment failures, race conditions, "
                "and difficulty with updates.\n\n"
                "### Remediation\n"
                "1. Identify the cycle in the dependency chain\n"
                "2. Break the cycle by refactoring\n"
                "3. Use depends_on to control ordering\n"
            ),
            default_level=SARIFLevel.WARNING,
            security_severity=3.0,
            tags=["infrastructure", "dependencies", "graph-analysis"],
            cwe_ids=["CWE-1047"],
        ),
    }

    def __init__(self):
        self._rules: dict[str, SARIFRule] = dict(self.PREDEFINED_RULES)
        self._used_rules: set[str] = set()

    def get_rule(self, rule_id: str) -> SARIFRule:
        """Get a rule by ID, creating fallback if not found."""
        self._used_rules.add(rule_id)

        if rule_id in self._rules:
            return self._rules[rule_id]

        # Generate fallback rule
        fallback = self._create_fallback_rule(rule_id)
        self._rules[rule_id] = fallback
        return fallback

    def register_rule(self, rule: SARIFRule) -> None:
        """Register a custom rule."""
        self._rules[rule.id] = rule

    def get_used_rules(self) -> list[SARIFRule]:
        """Get list of rules that have been used."""
        return [
            self._rules[rid] for rid in sorted(self._used_rules) if rid in self._rules
        ]

    def _create_fallback_rule(self, rule_id: str) -> SARIFRule:
        """Create a fallback rule for unknown rule IDs."""
        # Parse rule ID for hints
        parts = rule_id.lower().replace("/", "_").replace("-", "_").split("_")

        # Determine category and level
        level = SARIFLevel.WARNING
        severity = 5.0
        tags = ["cloud", "infrastructure"]

        if "security" in parts or "iam" in parts or "policy" in parts:
            level = SARIFLevel.ERROR
            severity = 7.0
            tags.append("security")
        elif "drift" in parts:
            tags.append("drift")
        elif "audit" in parts:
            tags.append("audit")

        # Create human-readable name
        name = "".join(word.title() for word in parts if word.isalpha())

        return SARIFRule(
            id=rule_id,
            name=name or "UnknownFinding",
            short_description=f"Finding: {rule_id}",
            full_description=(
                f"A finding of type '{rule_id}' was detected. "
                "Please review the finding details and take appropriate action."
            ),
            help_uri="https://replimap.dev/docs",
            default_level=level,
            security_severity=severity,
            tags=tags,
        )


# ============================================================
# SARIF GENERATOR
# ============================================================


class SARIFGenerator:
    """
    Production-grade SARIF generator for GitHub Security integration.

    Features:
    - Dynamic rule registry with predefined and fallback rules
    - Stable fingerprinting for GitHub deduplication
    - Hybrid locations (file + cloud resources)
    - Rich Markdown support for GitHub display
    - Full GitHub Advanced Security compatibility
    """

    SARIF_VERSION = "2.1.0"
    SARIF_SCHEMA = (
        "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/"
        "master/Schemata/sarif-schema-2.1.0.json"
    )
    TOOL_NAME = "replimap"
    TOOL_VERSION = "0.2.5"
    TOOL_INFO_URI = "https://github.com/RepliMap/replimap"

    # Map DriftSeverity to SARIF level
    SEVERITY_TO_LEVEL: dict[str, SARIFLevel] = {
        "critical": SARIFLevel.ERROR,
        "high": SARIFLevel.ERROR,
        "medium": SARIFLevel.WARNING,
        "low": SARIFLevel.NOTE,
        "info": SARIFLevel.NONE,
    }

    # Map DriftSeverity to security-severity score
    SEVERITY_TO_SCORE: dict[str, float] = {
        "critical": 9.0,
        "high": 7.0,
        "medium": 5.0,
        "low": 3.0,
        "info": 1.0,
    }

    def __init__(self):
        self.registry = RuleRegistry()
        self.md = MarkdownBuilder()

    def from_drift_report(self, report: DriftReport) -> dict[str, Any]:
        """
        Convert a DriftReport to SARIF format.

        Args:
            report: DriftReport from drift detection

        Returns:
            SARIF 2.1.0 compliant dictionary
        """
        results: list[SARIFResult] = []

        for finding in report.findings:
            result = self._drift_finding_to_result(finding, report)
            results.append(result)

        return self._build_sarif(results, report.scan_timestamp)

    def from_audit_findings(
        self,
        findings: list[dict[str, Any]],
        scan_timestamp: str | None = None,
    ) -> dict[str, Any]:
        """
        Convert audit findings to SARIF format.

        Args:
            findings: List of audit finding dictionaries
            scan_timestamp: ISO timestamp of scan

        Returns:
            SARIF 2.1.0 compliant dictionary
        """
        results: list[SARIFResult] = []

        for finding in findings:
            result = self._audit_finding_to_result(finding)
            results.append(result)

        timestamp = scan_timestamp or datetime.now(UTC).isoformat()
        return self._build_sarif(results, timestamp)

    def from_analysis_results(
        self,
        analysis: dict[str, Any],
        scan_timestamp: str | None = None,
    ) -> dict[str, Any]:
        """
        Convert graph analysis results to SARIF format.

        Args:
            analysis: Analysis results dictionary
            scan_timestamp: ISO timestamp of analysis

        Returns:
            SARIF 2.1.0 compliant dictionary
        """
        results: list[SARIFResult] = []

        # Process attack paths
        for path in analysis.get("attack_paths", []):
            result = self._attack_path_to_result(path)
            results.append(result)

        # Process high blast radius resources
        for resource in analysis.get("high_blast_radius", []):
            result = self._blast_radius_to_result(resource)
            results.append(result)

        # Process orphaned resources
        for resource in analysis.get("orphaned_resources", []):
            result = self._orphan_to_result(resource)
            results.append(result)

        # Process circular dependencies
        for cycle in analysis.get("circular_dependencies", []):
            result = self._circular_dep_to_result(cycle)
            results.append(result)

        timestamp = scan_timestamp or datetime.now(UTC).isoformat()
        return self._build_sarif(results, timestamp)

    def _build_sarif(
        self,
        results: list[SARIFResult],
        scan_timestamp: str,
    ) -> dict[str, Any]:
        """Build complete SARIF document."""
        return {
            "$schema": self.SARIF_SCHEMA,
            "version": self.SARIF_VERSION,
            "runs": [
                {
                    "tool": {
                        "driver": {
                            "name": self.TOOL_NAME,
                            "version": self.TOOL_VERSION,
                            "informationUri": self.TOOL_INFO_URI,
                            "rules": [
                                r.to_dict() for r in self.registry.get_used_rules()
                            ],
                        }
                    },
                    "results": [r.to_dict() for r in results],
                    "invocations": [
                        {
                            "executionSuccessful": True,
                            "endTimeUtc": scan_timestamp,
                        }
                    ],
                    "columnKind": "utf16CodeUnits",
                }
            ],
        }

    def _drift_finding_to_result(
        self,
        finding: Any,
        report: DriftReport,
    ) -> SARIFResult:
        """Convert a DriftFinding to SARIFResult."""
        from replimap.core.drift.detector import DriftSeverity, DriftType

        # Determine rule ID based on drift type and severity
        if finding.drift_type == DriftType.UNMANAGED:
            rule_id = "DRIFT001"
        elif finding.drift_type == DriftType.MISSING:
            rule_id = "DRIFT002"
        elif finding.max_change_severity == DriftSeverity.CRITICAL:
            rule_id = "DRIFT004"  # Security drift
        else:
            rule_id = "DRIFT003"  # Configuration drift

        # Get rule from registry (registers the rule as used)
        self.registry.get_rule(rule_id)

        # Determine level
        severity = finding.max_change_severity.value
        level = self.SEVERITY_TO_LEVEL.get(severity, SARIFLevel.WARNING)

        # Build message
        message_text = self._build_drift_message_text(finding)
        message_markdown = self._build_drift_message_markdown(finding)

        # Build location
        location = SARIFLocation(
            artifact_uri=report.state_file_path or "terraform.tfstate",
            logical_name=finding.resource_id,
            logical_kind="resource",
            fully_qualified_name=(
                finding.terraform_address
                or f"{finding.resource_type}.{finding.resource_name}"
            ),
            resource_id=finding.resource_id,
        )

        # Build fingerprint components
        fingerprint_components = [
            finding.resource_id,
            finding.drift_type.value,
        ]

        # Build fix suggestion
        fixes = [
            {
                "description": {
                    "text": finding.remediation_hint,
                    "markdown": f"**Remediation**: {finding.remediation_hint}",
                }
            }
        ]

        return SARIFResult(
            rule_id=rule_id,
            level=level,
            message_text=message_text,
            message_markdown=message_markdown,
            locations=[location],
            fingerprint_components=fingerprint_components,
            properties={
                "resource_type": finding.resource_type,
                "resource_id": finding.resource_id,
                "drift_type": finding.drift_type.value,
                "remediation": finding.remediation.value,
                "severity": severity,
            },
            fixes=fixes,
        )

    def _build_drift_message_text(self, finding: Any) -> str:
        """Build plain text message for drift finding."""
        from replimap.core.drift.detector import DriftType

        if finding.drift_type == DriftType.UNMANAGED:
            return (
                f"Unmanaged resource detected: {finding.resource_type} "
                f"'{finding.resource_name}' ({finding.resource_id}) exists in AWS "
                "but is not managed by Terraform."
            )
        elif finding.drift_type == DriftType.MISSING:
            return (
                f"Missing resource: {finding.resource_type} "
                f"'{finding.resource_name}' ({finding.resource_id}) exists in "
                "Terraform state but was deleted from AWS."
            )
        else:  # DRIFTED
            changes_text = ", ".join(
                f"{c.field}: {c.expected!r} -> {c.actual!r}"
                for c in finding.changes[:3]
            )
            more = (
                f" (+{len(finding.changes) - 3} more)"
                if len(finding.changes) > 3
                else ""
            )
            return (
                f"Configuration drift detected in {finding.resource_type} "
                f"'{finding.resource_name}': {changes_text}{more}"
            )

    def _build_drift_message_markdown(self, finding: Any) -> str:
        """Build rich Markdown message for drift finding."""
        from replimap.core.drift.detector import DriftType

        md = self.md
        parts = []

        # Header with severity badge
        severity = finding.max_change_severity.value
        parts.append(md.severity_badge(severity))
        parts.append(" ")

        if finding.drift_type == DriftType.UNMANAGED:
            parts.append(md.bold("Unmanaged Resource Detected"))
            parts.append("\n\n")
            parts.append(
                f"Resource `{finding.resource_type}` "
                f"**{finding.resource_name}** ({md.inline_code(finding.resource_id)}) "
                "exists in AWS but is not managed by Terraform.\n\n"
            )
        elif finding.drift_type == DriftType.MISSING:
            parts.append(md.bold("Missing Resource"))
            parts.append("\n\n")
            parts.append(
                f"Resource `{finding.resource_type}` "
                f"**{finding.resource_name}** ({md.inline_code(finding.resource_id)}) "
                "exists in Terraform state but was deleted from AWS.\n\n"
            )
        else:  # DRIFTED
            parts.append(md.bold("Configuration Drift"))
            parts.append("\n\n")
            parts.append(
                f"Resource `{finding.resource_type}` "
                f"**{finding.resource_name}** has configuration differences:\n\n"
            )

            # Build changes table
            if finding.changes:
                headers = ["Field", "Expected", "Actual", "Severity"]
                rows = []
                for change in finding.changes[:10]:  # Limit to 10 changes
                    expected = self._format_value(change.expected)
                    actual = self._format_value(change.actual)
                    rows.append(
                        [
                            md.inline_code(change.field),
                            expected,
                            actual,
                            change.severity.value,
                        ]
                    )
                parts.append(md.table(headers, rows))

                if len(finding.changes) > 10:
                    parts.append(
                        f"*...and {len(finding.changes) - 10} more changes*\n\n"
                    )

        # Add remediation
        parts.append(md.bold("Remediation"))
        parts.append(f": {finding.remediation_hint}\n")

        return "".join(parts)

    def _format_value(self, value: Any) -> str:
        """Format a value for display in markdown."""
        if value is None:
            return "*null*"
        if isinstance(value, bool):
            return str(value).lower()
        if isinstance(value, str):
            if len(value) > 30:
                return f"`{value[:27]}...`"
            return f"`{value}`"
        if isinstance(value, (list, dict)):
            s = json.dumps(value, default=str)
            if len(s) > 30:
                return f"`{s[:27]}...`"
            return f"`{s}`"
        return str(value)

    def _audit_finding_to_result(self, finding: dict[str, Any]) -> SARIFResult:
        """Convert an audit finding to SARIFResult."""
        rule_id = finding.get("rule_id", "AUDIT001")
        rule = self.registry.get_rule(rule_id)

        level = SARIFLevel.WARNING
        if finding.get("severity") in ("critical", "high"):
            level = SARIFLevel.ERROR
        elif finding.get("severity") == "low":
            level = SARIFLevel.NOTE

        location = SARIFLocation(
            resource_id=finding.get("resource_id"),
            resource_arn=finding.get("resource_arn"),
            logical_name=finding.get("resource_name"),
            region=finding.get("region"),
        )

        return SARIFResult(
            rule_id=rule_id,
            level=level,
            message_text=finding.get("message", rule.short_description),
            message_markdown=finding.get("message_markdown"),
            locations=[location],
            fingerprint_components=[
                finding.get("resource_id", ""),
                finding.get("finding_type", ""),
            ],
            properties=finding.get("properties", {}),
        )

    def _attack_path_to_result(self, path: dict[str, Any]) -> SARIFResult:
        """Convert an attack path to SARIFResult."""
        self.registry.get_rule("ANALYSIS001")  # Register rule as used

        # Build code flow for path visualization
        hops = path.get("hops", [])
        thread_flow_locations = []

        for i, hop in enumerate(hops):
            thread_flow_locations.append(
                {
                    "location": {
                        "logicalLocations": [
                            {
                                "name": hop.get("resource_id"),
                                "kind": "resource",
                                "fullyQualifiedName": hop.get("resource_arn", ""),
                            }
                        ],
                        "message": {"text": hop.get("description", f"Step {i + 1}")},
                    }
                }
            )

        code_flows = [
            {
                "threadFlows": [
                    {
                        "locations": thread_flow_locations,
                    }
                ]
            }
        ]

        # Build related locations
        related = [
            SARIFLocation(
                resource_id=hop.get("resource_id"),
                resource_arn=hop.get("resource_arn"),
                logical_name=hop.get("resource_name"),
            )
            for hop in hops
        ]

        # Build message
        entry = hops[0] if hops else {}
        target = hops[-1] if hops else {}
        message_text = (
            f"Attack path from {entry.get('resource_type', 'entry')} "
            f"to {target.get('resource_type', 'target')} ({len(hops)} hops)"
        )

        return SARIFResult(
            rule_id="ANALYSIS001",
            level=SARIFLevel.ERROR,
            message_text=message_text,
            locations=[related[0]] if related else [],
            fingerprint_components=[
                path.get("path_id", ""),
                entry.get("resource_id", ""),
                target.get("resource_id", ""),
            ],
            code_flows=code_flows,
            related_locations=related[1:],
            properties={
                "hop_count": len(hops),
                "risk_score": path.get("risk_score", 0),
            },
        )

    def _blast_radius_to_result(self, resource: dict[str, Any]) -> SARIFResult:
        """Convert high blast radius finding to SARIFResult."""
        self.registry.get_rule("ANALYSIS002")  # Register rule as used

        location = SARIFLocation(
            resource_id=resource.get("resource_id"),
            resource_arn=resource.get("resource_arn"),
            logical_name=resource.get("resource_name"),
        )

        connection_count = resource.get("connection_count", 0)
        message_text = (
            f"Resource {resource.get('resource_type')} '{resource.get('resource_name')}' "
            f"has {connection_count} connections (high blast radius)"
        )

        return SARIFResult(
            rule_id="ANALYSIS002",
            level=SARIFLevel.WARNING,
            message_text=message_text,
            locations=[location],
            fingerprint_components=[
                resource.get("resource_id", ""),
                "blast_radius",
            ],
            properties={
                "connection_count": connection_count,
                "affected_resources": resource.get("affected_resources", []),
            },
        )

    def _orphan_to_result(self, resource: dict[str, Any]) -> SARIFResult:
        """Convert orphaned resource to SARIFResult."""
        self.registry.get_rule("ANALYSIS003")  # Register rule as used

        location = SARIFLocation(
            resource_id=resource.get("resource_id"),
            resource_arn=resource.get("resource_arn"),
            logical_name=resource.get("resource_name"),
        )

        message_text = (
            f"Orphaned resource: {resource.get('resource_type')} "
            f"'{resource.get('resource_name')}' has no connections"
        )

        return SARIFResult(
            rule_id="ANALYSIS003",
            level=SARIFLevel.NOTE,
            message_text=message_text,
            locations=[location],
            fingerprint_components=[
                resource.get("resource_id", ""),
                "orphan",
            ],
            properties={
                "resource_type": resource.get("resource_type"),
                "created_at": resource.get("created_at"),
            },
        )

    def _circular_dep_to_result(self, cycle: dict[str, Any]) -> SARIFResult:
        """Convert circular dependency to SARIFResult."""
        self.registry.get_rule("ANALYSIS004")  # Register rule as used

        resources = cycle.get("resources", [])
        locations = [
            SARIFLocation(
                resource_id=r.get("resource_id"),
                logical_name=r.get("resource_name"),
            )
            for r in resources
        ]

        cycle_str = " -> ".join(r.get("resource_name", "?") for r in resources)
        message_text = f"Circular dependency detected: {cycle_str}"

        return SARIFResult(
            rule_id="ANALYSIS004",
            level=SARIFLevel.WARNING,
            message_text=message_text,
            locations=locations[:1] if locations else [],
            fingerprint_components=[
                cycle.get("cycle_id", ""),
            ],
            related_locations=locations[1:],
            properties={
                "cycle_length": len(resources),
                "cycle": [r.get("resource_id") for r in resources],
            },
        )

    # ================================================================
    # LEGACY COMPATIBILITY
    # ================================================================

    @classmethod
    def from_drift_report_legacy(cls, report: DriftReport) -> dict[str, Any]:
        """
        Legacy class method for backwards compatibility.

        New code should use instance method: SARIFGenerator().from_drift_report()
        """
        generator = cls()
        return generator.from_drift_report(report)
