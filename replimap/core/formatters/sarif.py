"""
SARIF (Static Analysis Results Interchange Format) generator.

Converts RepliMap findings to SARIF format for GitHub Security integration.
SARIF 2.1.0 specification: https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from replimap.core.drift.detector import DriftReport


class SARIFGenerator:
    """
    Generate SARIF format output for GitHub Security integration.

    SARIF (Static Analysis Results Interchange Format) is the standard
    format for uploading security findings to GitHub's Security tab.
    """

    SARIF_VERSION = "2.1.0"
    SARIF_SCHEMA = "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json"
    TOOL_NAME = "replimap"
    TOOL_VERSION = "0.2.5"

    # Map DriftSeverity to SARIF level
    SEVERITY_TO_LEVEL: dict[str, str] = {
        "critical": "error",
        "high": "error",
        "medium": "warning",
        "low": "note",
        "info": "none",
    }

    # Map DriftSeverity to SARIF security-severity score
    SEVERITY_TO_SCORE: dict[str, float] = {
        "critical": 9.0,
        "high": 7.0,
        "medium": 5.0,
        "low": 3.0,
        "info": 1.0,
    }

    @classmethod
    def from_drift_report(cls, report: DriftReport) -> dict[str, Any]:
        """
        Convert a DriftReport to SARIF format.

        Args:
            report: DriftReport from drift detection

        Returns:
            SARIF 2.1.0 compliant dictionary
        """
        # Build rules from unique finding types
        rules = cls._build_rules(report)

        # Build results from findings
        results = cls._build_results(report)

        return {
            "$schema": cls.SARIF_SCHEMA,
            "version": cls.SARIF_VERSION,
            "runs": [
                {
                    "tool": {
                        "driver": {
                            "name": cls.TOOL_NAME,
                            "version": cls.TOOL_VERSION,
                            "informationUri": "https://github.com/RepliMap/replimap",
                            "rules": list(rules.values()),
                        }
                    },
                    "results": results,
                    "invocations": [
                        {
                            "executionSuccessful": True,
                            "endTimeUtc": report.scan_timestamp,
                        }
                    ],
                }
            ],
        }

    @classmethod
    def _build_rules(cls, report: DriftReport) -> dict[str, dict[str, Any]]:
        """Build SARIF rules from unique finding types."""
        rules: dict[str, dict[str, Any]] = {}

        for finding in report.findings:
            rule_id = f"drift/{finding.drift_type.value}/{finding.resource_type}"

            if rule_id in rules:
                continue

            severity = finding.max_change_severity.value
            level = cls.SEVERITY_TO_LEVEL.get(severity, "warning")
            score = cls.SEVERITY_TO_SCORE.get(severity, 5.0)

            rules[rule_id] = {
                "id": rule_id,
                "name": f"{finding.drift_type.value.title()}Resource",
                "shortDescription": {
                    "text": f"Infrastructure drift detected: {finding.drift_type.value}"
                },
                "fullDescription": {
                    "text": cls._get_rule_description(finding.drift_type.value)
                },
                "helpUri": "https://replimap.dev/docs/drift-detection",
                "defaultConfiguration": {"level": level},
                "properties": {
                    "security-severity": str(score),
                    "tags": ["infrastructure", "drift", "terraform"],
                },
            }

        return rules

    @classmethod
    def _build_results(cls, report: DriftReport) -> list[dict[str, Any]]:
        """Build SARIF results from findings."""
        results = []

        for finding in report.findings:
            rule_id = f"drift/{finding.drift_type.value}/{finding.resource_type}"
            severity = finding.max_change_severity.value
            level = cls.SEVERITY_TO_LEVEL.get(severity, "warning")

            # Build message with changes
            message = cls._build_message(finding)

            result = {
                "ruleId": rule_id,
                "level": level,
                "message": {"text": message},
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {
                                "uri": report.state_file_path or "terraform.tfstate",
                                "uriBaseId": "%SRCROOT%",
                            }
                        },
                        "logicalLocations": [
                            {
                                "name": finding.resource_id,
                                "kind": "resource",
                                "fullyQualifiedName": finding.terraform_address
                                or f"{finding.resource_type}.{finding.resource_name}",
                            }
                        ],
                    }
                ],
                "properties": {
                    "resource_type": finding.resource_type,
                    "resource_id": finding.resource_id,
                    "drift_type": finding.drift_type.value,
                    "remediation": finding.remediation.value,
                },
                "fixes": [
                    {
                        "description": {"text": finding.remediation_hint},
                    }
                ],
            }

            results.append(result)

        return results

    @classmethod
    def _build_message(cls, finding: Any) -> str:
        """Build human-readable message for a finding."""
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

    @staticmethod
    def _get_rule_description(drift_type: str) -> str:
        """Get full description for a drift type rule."""
        descriptions = {
            "unmanaged": (
                "An AWS resource exists that is not managed by Terraform. "
                "This could be a resource created manually via the AWS Console, "
                "CLI, or another tool. Consider importing it into Terraform or "
                "deleting it if unneeded."
            ),
            "missing": (
                "A resource defined in Terraform state no longer exists in AWS. "
                "This indicates the resource was deleted outside of Terraform "
                "(e.g., via Console or CLI). Run 'terraform apply' to recreate "
                "it or 'terraform state rm' to remove it from state."
            ),
            "drifted": (
                "A resource's configuration in AWS differs from what Terraform "
                "expects. This could be due to manual changes via Console/CLI. "
                "Run 'terraform apply' to restore expected state or update your "
                ".tf files to match reality."
            ),
        }
        return descriptions.get(drift_type, "Infrastructure drift detected.")
