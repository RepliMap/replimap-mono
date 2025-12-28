"""
AWS API operation classifier for categorizing read/write/delete operations.

Classifies AWS API operations by their effect on resources:
- READ: Operations that only retrieve information
- WRITE: Operations that create or modify resources
- DELETE: Operations that remove resources
- ADMIN: Privileged operations (IAM, Organizations)
"""

from __future__ import annotations

from .models import APICategory


class OperationClassifier:
    """
    Classifies AWS API operations by category (read/write/delete/admin).

    Uses prefix matching with special cases for operations that don't
    follow standard naming conventions.
    """

    # Standard prefixes for read operations
    READ_PREFIXES: set[str] = {
        "Describe",
        "Get",
        "List",
        "Head",
        "Lookup",
        "Search",
        "Scan",
        "Query",
        "Check",
        "Validate",
        "Test",
        "Preview",
        "Simulate",
        "Evaluate",
        "Estimate",
        "Download",
        "Export",
        "Batch",  # BatchGet*, etc.
        "Filter",
        "Find",
        "Select",
    }

    # Standard prefixes for write operations
    WRITE_PREFIXES: set[str] = {
        "Create",
        "Put",
        "Update",
        "Modify",
        "Set",
        "Attach",
        "Associate",
        "Enable",
        "Add",
        "Register",
        "Start",
        "Run",
        "Invoke",
        "Execute",
        "Apply",
        "Import",
        "Upload",
        "Copy",
        "Restore",
        "Reboot",
        "Reset",
        "Rotate",
        "Renew",
        "Accept",
        "Confirm",
        "Allocate",
        "Assign",
        "Tag",
        "Send",
        "Publish",
        "Subscribe",
        "Authorize",
    }

    # Standard prefixes for delete operations
    DELETE_PREFIXES: set[str] = {
        "Delete",
        "Remove",
        "Detach",
        "Disassociate",
        "Disable",
        "Stop",
        "Terminate",
        "Deregister",
        "Cancel",
        "Revoke",
        "Release",
        "Unassign",
        "Untag",
        "Purge",
        "Destroy",
        "Reject",
        "Deny",
        "Abort",
        "Unsubscribe",
    }

    # Admin operations (IAM, Organizations, etc.)
    ADMIN_OPERATIONS: set[str] = {
        # IAM User Management
        "CreateUser",
        "DeleteUser",
        "UpdateUser",
        "CreateLoginProfile",
        "DeleteLoginProfile",
        "UpdateLoginProfile",
        "CreateAccessKey",
        "DeleteAccessKey",
        "UpdateAccessKey",
        # IAM Role Management
        "CreateRole",
        "DeleteRole",
        "UpdateRole",
        "UpdateAssumeRolePolicy",
        # IAM Policy Management
        "CreatePolicy",
        "DeletePolicy",
        "CreatePolicyVersion",
        "DeletePolicyVersion",
        "SetDefaultPolicyVersion",
        "AttachUserPolicy",
        "DetachUserPolicy",
        "AttachRolePolicy",
        "DetachRolePolicy",
        "AttachGroupPolicy",
        "DetachGroupPolicy",
        "PutUserPolicy",
        "DeleteUserPolicy",
        "PutRolePolicy",
        "DeleteRolePolicy",
        "PutGroupPolicy",
        "DeleteGroupPolicy",
        # IAM Group Management
        "CreateGroup",
        "DeleteGroup",
        "UpdateGroup",
        "AddUserToGroup",
        "RemoveUserFromGroup",
        # Organizations
        "CreateAccount",
        "CloseAccount",
        "CreateOrganization",
        "DeleteOrganization",
        "CreateOrganizationalUnit",
        "DeleteOrganizationalUnit",
        "InviteAccountToOrganization",
        "RemoveAccountFromOrganization",
        # STS (privileged)
        "AssumeRole",
        "AssumeRoleWithSAML",
        "AssumeRoleWithWebIdentity",
        # Service Control Policies
        "CreatePolicy",
        "UpdatePolicy",
        "DeletePolicy",
        "AttachPolicy",
        "DetachPolicy",
    }

    # Special cases: Operations that don't follow standard prefixes
    SPECIAL_CASES: dict[str, APICategory] = {
        # S3
        "HeadObject": APICategory.READ,
        "HeadBucket": APICategory.READ,
        "GetBucketAcl": APICategory.READ,
        "GetBucketPolicy": APICategory.READ,
        "GetBucketCors": APICategory.READ,
        "GetBucketEncryption": APICategory.READ,
        "GetBucketVersioning": APICategory.READ,
        "GetBucketLocation": APICategory.READ,
        "GetObjectAcl": APICategory.READ,
        "GetObjectTagging": APICategory.READ,
        "PutBucketAcl": APICategory.WRITE,
        "PutBucketPolicy": APICategory.WRITE,
        "PutBucketCors": APICategory.WRITE,
        "PutBucketEncryption": APICategory.WRITE,
        "PutObjectAcl": APICategory.WRITE,
        "PutObjectTagging": APICategory.WRITE,
        "AbortMultipartUpload": APICategory.DELETE,
        "DeleteBucketPolicy": APICategory.DELETE,
        "DeleteBucketCors": APICategory.DELETE,
        "DeleteObjectTagging": APICategory.DELETE,
        # EC2
        "AuthorizeSecurityGroupIngress": APICategory.WRITE,
        "AuthorizeSecurityGroupEgress": APICategory.WRITE,
        "RevokeSecurityGroupIngress": APICategory.DELETE,
        "RevokeSecurityGroupEgress": APICategory.DELETE,
        "RunInstances": APICategory.WRITE,
        "TerminateInstances": APICategory.DELETE,
        "StopInstances": APICategory.WRITE,
        "StartInstances": APICategory.WRITE,
        "RebootInstances": APICategory.WRITE,
        "ModifyInstanceAttribute": APICategory.WRITE,
        "MonitorInstances": APICategory.WRITE,
        "UnmonitorInstances": APICategory.WRITE,
        # RDS
        "RebootDBInstance": APICategory.WRITE,
        "FailoverDBCluster": APICategory.WRITE,
        "PromoteReadReplica": APICategory.WRITE,
        "SwitchoverReadReplica": APICategory.WRITE,
        # Lambda
        "InvokeFunction": APICategory.WRITE,
        "InvokeAsync": APICategory.WRITE,
        # CloudWatch
        "PutMetricData": APICategory.WRITE,
        "PutMetricAlarm": APICategory.WRITE,
        "DeleteAlarms": APICategory.DELETE,
        "EnableAlarmActions": APICategory.WRITE,
        "DisableAlarmActions": APICategory.WRITE,
        # STS - Read-like operations
        "GetCallerIdentity": APICategory.READ,
        "GetSessionToken": APICategory.READ,
        "GetFederationToken": APICategory.READ,
        "GetAccessKeyInfo": APICategory.READ,
        "DecodeAuthorizationMessage": APICategory.READ,
        # SNS
        "ConfirmSubscription": APICategory.WRITE,
        # SQS
        "ReceiveMessage": APICategory.READ,
        "SendMessage": APICategory.WRITE,
        "SendMessageBatch": APICategory.WRITE,
        "PurgeQueue": APICategory.DELETE,
        # DynamoDB
        "TransactGetItems": APICategory.READ,
        "TransactWriteItems": APICategory.WRITE,
        "BatchGetItem": APICategory.READ,
        "BatchWriteItem": APICategory.WRITE,
    }

    def classify(self, operation: str) -> APICategory:
        """
        Classify an AWS API operation.

        Args:
            operation: Operation name (e.g., "DescribeInstances")

        Returns:
            APICategory enum value
        """
        # Check special cases first
        if operation in self.SPECIAL_CASES:
            return self.SPECIAL_CASES[operation]

        # Check admin operations
        if operation in self.ADMIN_OPERATIONS:
            return APICategory.ADMIN

        # Check prefixes (order matters for accuracy)
        for prefix in self.READ_PREFIXES:
            if operation.startswith(prefix):
                return APICategory.READ

        for prefix in self.DELETE_PREFIXES:
            if operation.startswith(prefix):
                return APICategory.DELETE

        for prefix in self.WRITE_PREFIXES:
            if operation.startswith(prefix):
                return APICategory.WRITE

        return APICategory.UNKNOWN

    def classify_with_confidence(
        self,
        operation: str,
    ) -> tuple[APICategory, str]:
        """
        Classify operation with confidence level.

        Returns:
            Tuple of (category, confidence) where confidence is
            "exact", "prefix", or "unknown"
        """
        if operation in self.SPECIAL_CASES:
            return self.SPECIAL_CASES[operation], "exact"

        if operation in self.ADMIN_OPERATIONS:
            return APICategory.ADMIN, "exact"

        for prefix in self.READ_PREFIXES:
            if operation.startswith(prefix):
                return APICategory.READ, "prefix"

        for prefix in self.DELETE_PREFIXES:
            if operation.startswith(prefix):
                return APICategory.DELETE, "prefix"

        for prefix in self.WRITE_PREFIXES:
            if operation.startswith(prefix):
                return APICategory.WRITE, "prefix"

        return APICategory.UNKNOWN, "unknown"

    def is_read_only(self, operation: str) -> bool:
        """Quick check if an operation is read-only."""
        return self.classify(operation) == APICategory.READ

    def is_destructive(self, operation: str) -> bool:
        """Check if an operation is destructive (write/delete/admin)."""
        return self.classify(operation) in (
            APICategory.WRITE,
            APICategory.DELETE,
            APICategory.ADMIN,
        )


# Global instance for convenience
classifier = OperationClassifier()
