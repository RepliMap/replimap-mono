"""
Remediation Actions.

Defines the types and data models for remediation actions
that can be executed against AWS resources.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class RemediationActionType(str, Enum):
    """Types of remediation actions."""

    # Encryption
    ENABLE_ENCRYPTION = "enable_encryption"
    ENABLE_KMS_ENCRYPTION = "enable_kms_encryption"
    ENABLE_KEY_ROTATION = "enable_key_rotation"

    # Access Control
    BLOCK_PUBLIC_ACCESS = "block_public_access"
    RESTRICT_SECURITY_GROUP = "restrict_security_group"
    ENABLE_SSL_ONLY = "enable_ssl_only"

    # Availability
    ENABLE_MULTI_AZ = "enable_multi_az"
    ENABLE_VERSIONING = "enable_versioning"
    ENABLE_BACKUP = "enable_backup"

    # Monitoring
    ENABLE_LOGGING = "enable_logging"
    ENABLE_MONITORING = "enable_monitoring"
    ENABLE_FLOW_LOGS = "enable_flow_logs"

    # Security
    ENABLE_IMDSV2 = "enable_imdsv2"
    ENABLE_DELETION_PROTECTION = "enable_deletion_protection"
    ENABLE_IAM_AUTH = "enable_iam_auth"

    # Terraform
    TERRAFORM_APPLY = "terraform_apply"
    TERRAFORM_IMPORT = "terraform_import"

    # Custom
    CUSTOM = "custom"

    def __str__(self) -> str:
        return self.value


class RemediationStatus(str, Enum):
    """Status of a remediation action."""

    PENDING = "pending"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    SKIPPED = "skipped"

    def __str__(self) -> str:
        return self.value


@dataclass
class RemediationAction:
    """
    A single remediation action to be executed.

    Represents an atomic remediation operation that can be
    applied to fix a compliance finding or security issue.
    """

    # Identification
    id: str
    name: str
    description: str
    action_type: RemediationActionType

    # Target
    resource_id: str
    resource_type: str
    region: str
    account_id: str = ""

    # Compliance link
    rule_id: str = ""
    finding_id: str = ""

    # Execution
    parameters: dict[str, Any] = field(default_factory=dict)
    terraform_code: str = ""  # Generated Terraform if applicable
    aws_api_call: str = ""  # AWS API operation to execute

    # Metadata
    severity: str = "medium"
    estimated_impact: str = ""
    requires_downtime: bool = False
    requires_approval: bool = True
    rollback_supported: bool = True

    # Risk assessment
    risk_level: str = "medium"  # low, medium, high
    risk_factors: list[str] = field(default_factory=list)

    # Status tracking
    status: RemediationStatus = RemediationStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    executed_at: datetime | None = None
    completed_at: datetime | None = None

    # Execution context
    executed_by: str = ""
    approved_by: str = ""
    approval_timestamp: datetime | None = None

    # Rollback
    rollback_data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "action_type": str(self.action_type),
            "resource": {
                "id": self.resource_id,
                "type": self.resource_type,
                "region": self.region,
                "account_id": self.account_id,
            },
            "compliance": {
                "rule_id": self.rule_id,
                "finding_id": self.finding_id,
            },
            "parameters": self.parameters,
            "terraform_code": self.terraform_code,
            "aws_api_call": self.aws_api_call,
            "severity": self.severity,
            "estimated_impact": self.estimated_impact,
            "requires_downtime": self.requires_downtime,
            "requires_approval": self.requires_approval,
            "rollback_supported": self.rollback_supported,
            "risk": {
                "level": self.risk_level,
                "factors": self.risk_factors,
            },
            "status": str(self.status),
            "timestamps": {
                "created": self.created_at.isoformat(),
                "executed": self.executed_at.isoformat() if self.executed_at else None,
                "completed": self.completed_at.isoformat() if self.completed_at else None,
                "approved": self.approval_timestamp.isoformat() if self.approval_timestamp else None,
            },
            "executed_by": self.executed_by,
            "approved_by": self.approved_by,
        }


@dataclass
class RemediationResult:
    """
    Result of executing a remediation action.
    """

    action_id: str
    success: bool
    status: RemediationStatus

    # Execution details
    started_at: datetime
    completed_at: datetime
    duration_seconds: float = 0.0

    # Outcome
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    # Errors
    error_code: str = ""
    error_message: str = ""

    # AWS response
    aws_request_id: str = ""
    aws_response: dict[str, Any] = field(default_factory=dict)

    # Rollback
    rollback_data: dict[str, Any] = field(default_factory=dict)
    rollback_available: bool = False

    # Changes made
    changes: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "action_id": self.action_id,
            "success": self.success,
            "status": str(self.status),
            "timing": {
                "started": self.started_at.isoformat(),
                "completed": self.completed_at.isoformat(),
                "duration_seconds": round(self.duration_seconds, 2),
            },
            "message": self.message,
            "details": self.details,
            "error": {
                "code": self.error_code,
                "message": self.error_message,
            } if self.error_code else None,
            "aws_request_id": self.aws_request_id,
            "rollback_available": self.rollback_available,
            "changes": self.changes,
        }


# Mapping from compliance rule IDs to remediation action types
COMPLIANCE_TO_ACTION_MAP: dict[str, RemediationActionType] = {
    # S3 rules
    "S3_001": RemediationActionType.ENABLE_ENCRYPTION,
    "S3_002": RemediationActionType.BLOCK_PUBLIC_ACCESS,

    # RDS rules
    "RDS_001": RemediationActionType.ENABLE_ENCRYPTION,
    "RDS_002": RemediationActionType.ENABLE_MULTI_AZ,

    # EC2 rules
    "EC2_001": RemediationActionType.ENABLE_IMDSV2,

    # VPC rules
    "VPC_001": RemediationActionType.ENABLE_FLOW_LOGS,

    # Security Group rules
    "SG_001": RemediationActionType.RESTRICT_SECURITY_GROUP,
    "SG_002": RemediationActionType.RESTRICT_SECURITY_GROUP,

    # EBS rules
    "EBS_001": RemediationActionType.ENABLE_ENCRYPTION,
    "EBS_002": RemediationActionType.ENABLE_ENCRYPTION,
}


def create_action_from_finding(
    finding: dict[str, Any],
    rule_id: str,
    action_id: str | None = None,
) -> RemediationAction | None:
    """
    Create a remediation action from a compliance finding.

    Args:
        finding: The compliance finding dictionary
        rule_id: The compliance rule ID
        action_id: Optional custom action ID

    Returns:
        RemediationAction or None if no mapping exists
    """
    action_type = COMPLIANCE_TO_ACTION_MAP.get(rule_id)
    if action_type is None:
        logger.debug(f"No remediation mapping for rule {rule_id}")
        return None

    resource_id = finding.get("resource_id", "")
    resource_type = finding.get("resource_type", "")
    region = finding.get("region", "")

    if not action_id:
        action_id = f"rem-{rule_id}-{resource_id[:8]}"

    return RemediationAction(
        id=action_id,
        name=f"Remediate {rule_id}",
        description=f"Fix {rule_id} compliance finding for {resource_id}",
        action_type=action_type,
        resource_id=resource_id,
        resource_type=resource_type,
        region=region,
        rule_id=rule_id,
        finding_id=finding.get("id", ""),
        severity=finding.get("severity", "medium"),
    )
