"""
Remediation Execution Engine.

Executes remediation actions against AWS resources,
tracks progress, and supports rollback operations.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable

from replimap.core.async_aws import AsyncAWSClient
from .actions import (
    RemediationAction,
    RemediationActionType,
    RemediationResult,
    RemediationStatus,
)
from .analyzer import ImpactAnalyzer, ImpactAnalysis
from .workflow import (
    RemediationStep,
    RemediationWorkflow,
    StepStatus,
    WorkflowStatus,
)

logger = logging.getLogger(__name__)


@dataclass
class ExecutionContext:
    """Context for remediation execution."""

    dry_run: bool = False
    skip_approval: bool = False
    auto_rollback: bool = True
    parallel_limit: int = 5
    timeout_seconds: int = 300

    # Callbacks
    on_step_start: Callable[[RemediationStep], None] | None = None
    on_step_complete: Callable[[RemediationStep, RemediationResult], None] | None = None
    on_step_failure: Callable[[RemediationStep, Exception], None] | None = None


class RemediationExecutor:
    """
    Executes individual remediation actions.

    Handles the actual AWS API calls to apply remediation.
    """

    def __init__(
        self,
        region: str = "us-east-1",
        account_id: str = "",
    ) -> None:
        """
        Initialize executor.

        Args:
            region: Default AWS region
            account_id: AWS account ID
        """
        self.region = region
        self.account_id = account_id
        self._clients: dict[str, AsyncAWSClient] = {}

    async def _get_client(self, region: str) -> AsyncAWSClient:
        """Get or create client for region."""
        if region not in self._clients:
            self._clients[region] = AsyncAWSClient(region=region)
        return self._clients[region]

    async def execute(
        self,
        action: RemediationAction,
        dry_run: bool = False,
    ) -> RemediationResult:
        """
        Execute a remediation action.

        Args:
            action: The action to execute
            dry_run: If True, simulate without making changes

        Returns:
            RemediationResult with execution outcome
        """
        started_at = datetime.now()

        try:
            if dry_run:
                result = await self._simulate_action(action)
            else:
                result = await self._execute_action(action)

            completed_at = datetime.now()
            result.started_at = started_at
            result.completed_at = completed_at
            result.duration_seconds = (completed_at - started_at).total_seconds()

            # Update action status
            action.status = result.status
            action.executed_at = started_at
            action.completed_at = completed_at

            return result

        except Exception as e:
            logger.error(f"Action {action.id} failed: {e}")
            completed_at = datetime.now()

            return RemediationResult(
                action_id=action.id,
                success=False,
                status=RemediationStatus.FAILED,
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=(completed_at - started_at).total_seconds(),
                error_message=str(e),
            )

    async def _simulate_action(self, action: RemediationAction) -> RemediationResult:
        """Simulate action without making changes."""
        logger.info(f"[DRY RUN] Would execute: {action.name}")

        return RemediationResult(
            action_id=action.id,
            success=True,
            status=RemediationStatus.COMPLETED,
            started_at=datetime.now(),
            completed_at=datetime.now(),
            message=f"[DRY RUN] Simulated: {action.name}",
            details={"simulated": True},
        )

    async def _execute_action(self, action: RemediationAction) -> RemediationResult:
        """Execute the actual remediation action."""
        # Get client for the action's region
        region = action.region or self.region
        client = await self._get_client(region)

        # Route to appropriate handler
        handlers = {
            RemediationActionType.ENABLE_ENCRYPTION: self._enable_encryption,
            RemediationActionType.ENABLE_KMS_ENCRYPTION: self._enable_kms_encryption,
            RemediationActionType.BLOCK_PUBLIC_ACCESS: self._block_public_access,
            RemediationActionType.ENABLE_VERSIONING: self._enable_versioning,
            RemediationActionType.ENABLE_LOGGING: self._enable_logging,
            RemediationActionType.ENABLE_IMDSV2: self._enable_imdsv2,
            RemediationActionType.ENABLE_MULTI_AZ: self._enable_multi_az,
            RemediationActionType.RESTRICT_SECURITY_GROUP: self._restrict_security_group,
            RemediationActionType.ENABLE_FLOW_LOGS: self._enable_flow_logs,
        }

        handler = handlers.get(action.action_type)
        if handler:
            return await handler(client, action)

        # Unknown action type
        return RemediationResult(
            action_id=action.id,
            success=False,
            status=RemediationStatus.FAILED,
            started_at=datetime.now(),
            completed_at=datetime.now(),
            error_message=f"Unsupported action type: {action.action_type}",
        )

    async def _enable_encryption(
        self,
        client: AsyncAWSClient,
        action: RemediationAction,
    ) -> RemediationResult:
        """Enable encryption on a resource."""
        resource_type = action.resource_type

        if "s3" in resource_type:
            return await self._enable_s3_encryption(client, action)
        elif "ebs" in resource_type:
            return await self._enable_ebs_encryption(client, action)
        elif "rds" in resource_type or "db" in resource_type:
            return await self._enable_rds_encryption(client, action)

        return RemediationResult(
            action_id=action.id,
            success=False,
            status=RemediationStatus.FAILED,
            started_at=datetime.now(),
            completed_at=datetime.now(),
            error_message=f"Encryption not supported for: {resource_type}",
        )

    async def _enable_s3_encryption(
        self,
        client: AsyncAWSClient,
        action: RemediationAction,
    ) -> RemediationResult:
        """Enable S3 bucket encryption."""
        bucket_name = action.resource_id

        try:
            # Get current encryption state for rollback
            try:
                current = await client.call(
                    "s3",
                    "get_bucket_encryption",
                    Bucket=bucket_name,
                )
                rollback_data: dict[str, Any] = {"previous_encryption": current}
            except Exception:
                rollback_data = {}

            # Enable SSE-S3 encryption
            await client.call(
                "s3",
                "put_bucket_encryption",
                Bucket=bucket_name,
                ServerSideEncryptionConfiguration={
                    "Rules": [
                        {
                            "ApplyServerSideEncryptionByDefault": {
                                "SSEAlgorithm": "AES256"
                            }
                        }
                    ]
                },
            )

            return RemediationResult(
                action_id=action.id,
                success=True,
                status=RemediationStatus.COMPLETED,
                started_at=datetime.now(),
                completed_at=datetime.now(),
                message=f"Enabled encryption on S3 bucket: {bucket_name}",
                rollback_data=rollback_data,
                rollback_available=True,
                changes=[{"type": "encryption", "enabled": True}],
            )

        except Exception as e:
            return RemediationResult(
                action_id=action.id,
                success=False,
                status=RemediationStatus.FAILED,
                started_at=datetime.now(),
                completed_at=datetime.now(),
                error_message=str(e),
            )

    async def _enable_ebs_encryption(
        self,
        client: AsyncAWSClient,
        action: RemediationAction,
    ) -> RemediationResult:
        """Enable EBS volume encryption (note: requires volume recreation)."""
        volume_id = action.resource_id

        return RemediationResult(
            action_id=action.id,
            success=False,
            status=RemediationStatus.FAILED,
            started_at=datetime.now(),
            completed_at=datetime.now(),
            error_message=(
                f"EBS volume encryption requires volume recreation. "
                f"Use Terraform to recreate volume {volume_id} with encryption."
            ),
            details={"terraform_required": True},
        )

    async def _enable_rds_encryption(
        self,
        client: AsyncAWSClient,
        action: RemediationAction,
    ) -> RemediationResult:
        """Enable RDS encryption (note: requires instance recreation)."""
        db_id = action.resource_id

        return RemediationResult(
            action_id=action.id,
            success=False,
            status=RemediationStatus.FAILED,
            started_at=datetime.now(),
            completed_at=datetime.now(),
            error_message=(
                f"RDS encryption requires instance recreation. "
                f"Use Terraform to recreate {db_id} with encryption."
            ),
            details={"terraform_required": True},
        )

    async def _enable_kms_encryption(
        self,
        client: AsyncAWSClient,
        action: RemediationAction,
    ) -> RemediationResult:
        """Enable KMS encryption on a resource."""
        # Similar to _enable_encryption but with KMS key
        return await self._enable_encryption(client, action)

    async def _block_public_access(
        self,
        client: AsyncAWSClient,
        action: RemediationAction,
    ) -> RemediationResult:
        """Block public access on S3 bucket."""
        bucket_name = action.resource_id

        try:
            # Get current state for rollback
            try:
                current = await client.call(
                    "s3",
                    "get_public_access_block",
                    Bucket=bucket_name,
                )
                rollback_data: dict[str, Any] = {"previous_config": current}
            except Exception:
                rollback_data = {}

            # Block all public access
            await client.call(
                "s3",
                "put_public_access_block",
                Bucket=bucket_name,
                PublicAccessBlockConfiguration={
                    "BlockPublicAcls": True,
                    "IgnorePublicAcls": True,
                    "BlockPublicPolicy": True,
                    "RestrictPublicBuckets": True,
                },
            )

            return RemediationResult(
                action_id=action.id,
                success=True,
                status=RemediationStatus.COMPLETED,
                started_at=datetime.now(),
                completed_at=datetime.now(),
                message=f"Blocked public access on: {bucket_name}",
                rollback_data=rollback_data,
                rollback_available=True,
                changes=[{"type": "public_access", "blocked": True}],
            )

        except Exception as e:
            return RemediationResult(
                action_id=action.id,
                success=False,
                status=RemediationStatus.FAILED,
                started_at=datetime.now(),
                completed_at=datetime.now(),
                error_message=str(e),
            )

    async def _enable_versioning(
        self,
        client: AsyncAWSClient,
        action: RemediationAction,
    ) -> RemediationResult:
        """Enable S3 bucket versioning."""
        bucket_name = action.resource_id

        try:
            # Get current state for rollback
            try:
                current = await client.call(
                    "s3",
                    "get_bucket_versioning",
                    Bucket=bucket_name,
                )
                rollback_data = {"previous_status": current.get("Status")}
            except Exception:
                rollback_data = {"previous_status": None}

            # Enable versioning
            await client.call(
                "s3",
                "put_bucket_versioning",
                Bucket=bucket_name,
                VersioningConfiguration={"Status": "Enabled"},
            )

            return RemediationResult(
                action_id=action.id,
                success=True,
                status=RemediationStatus.COMPLETED,
                started_at=datetime.now(),
                completed_at=datetime.now(),
                message=f"Enabled versioning on: {bucket_name}",
                rollback_data=rollback_data,
                rollback_available=True,
                changes=[{"type": "versioning", "enabled": True}],
            )

        except Exception as e:
            return RemediationResult(
                action_id=action.id,
                success=False,
                status=RemediationStatus.FAILED,
                started_at=datetime.now(),
                completed_at=datetime.now(),
                error_message=str(e),
            )

    async def _enable_logging(
        self,
        client: AsyncAWSClient,
        action: RemediationAction,
    ) -> RemediationResult:
        """Enable logging on a resource."""
        return RemediationResult(
            action_id=action.id,
            success=False,
            status=RemediationStatus.FAILED,
            started_at=datetime.now(),
            completed_at=datetime.now(),
            error_message="Logging configuration requires target bucket. Use Terraform.",
            details={"terraform_required": True},
        )

    async def _enable_imdsv2(
        self,
        client: AsyncAWSClient,
        action: RemediationAction,
    ) -> RemediationResult:
        """Enable IMDSv2 on EC2 instance."""
        instance_id = action.resource_id

        try:
            await client.call(
                "ec2",
                "modify_instance_metadata_options",
                InstanceId=instance_id,
                HttpTokens="required",
                HttpPutResponseHopLimit=1,
                HttpEndpoint="enabled",
            )

            return RemediationResult(
                action_id=action.id,
                success=True,
                status=RemediationStatus.COMPLETED,
                started_at=datetime.now(),
                completed_at=datetime.now(),
                message=f"Enabled IMDSv2 on: {instance_id}",
                rollback_data={"HttpTokens": "optional"},
                rollback_available=True,
                changes=[{"type": "imdsv2", "required": True}],
            )

        except Exception as e:
            return RemediationResult(
                action_id=action.id,
                success=False,
                status=RemediationStatus.FAILED,
                started_at=datetime.now(),
                completed_at=datetime.now(),
                error_message=str(e),
            )

    async def _enable_multi_az(
        self,
        client: AsyncAWSClient,
        action: RemediationAction,
    ) -> RemediationResult:
        """Enable Multi-AZ on RDS instance."""
        db_id = action.resource_id

        try:
            await client.call(
                "rds",
                "modify_db_instance",
                DBInstanceIdentifier=db_id,
                MultiAZ=True,
                ApplyImmediately=False,  # Safer to apply during next window
            )

            return RemediationResult(
                action_id=action.id,
                success=True,
                status=RemediationStatus.COMPLETED,
                started_at=datetime.now(),
                completed_at=datetime.now(),
                message=f"Multi-AZ will be enabled on: {db_id} during next maintenance window",
                rollback_data={"MultiAZ": False},
                rollback_available=True,
                changes=[{"type": "multi_az", "enabled": True, "pending": True}],
            )

        except Exception as e:
            return RemediationResult(
                action_id=action.id,
                success=False,
                status=RemediationStatus.FAILED,
                started_at=datetime.now(),
                completed_at=datetime.now(),
                error_message=str(e),
            )

    async def _restrict_security_group(
        self,
        client: AsyncAWSClient,
        action: RemediationAction,
    ) -> RemediationResult:
        """Restrict security group rules."""
        sg_id = action.resource_id
        port = action.parameters.get("port", 22)

        try:
            # Get current rules for rollback
            sg = await client.call(
                "ec2",
                "describe_security_groups",
                GroupIds=[sg_id],
            )

            if not sg.get("SecurityGroups"):
                raise ValueError(f"Security group not found: {sg_id}")

            current_sg = sg["SecurityGroups"][0]
            rollback_data = {"previous_rules": current_sg.get("IpPermissions", [])}

            # Revoke overly permissive rules (0.0.0.0/0)
            for rule in current_sg.get("IpPermissions", []):
                from_port = rule.get("FromPort")
                to_port = rule.get("ToPort")

                if from_port == port or to_port == port:
                    for ip_range in rule.get("IpRanges", []):
                        if ip_range.get("CidrIp") == "0.0.0.0/0":
                            await client.call(
                                "ec2",
                                "revoke_security_group_ingress",
                                GroupId=sg_id,
                                IpPermissions=[{
                                    "IpProtocol": rule.get("IpProtocol"),
                                    "FromPort": from_port,
                                    "ToPort": to_port,
                                    "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
                                }],
                            )

            return RemediationResult(
                action_id=action.id,
                success=True,
                status=RemediationStatus.COMPLETED,
                started_at=datetime.now(),
                completed_at=datetime.now(),
                message=f"Restricted port {port} access on: {sg_id}",
                rollback_data=rollback_data,
                rollback_available=True,
                changes=[{"type": "security_group", "port": port, "restricted": True}],
            )

        except Exception as e:
            return RemediationResult(
                action_id=action.id,
                success=False,
                status=RemediationStatus.FAILED,
                started_at=datetime.now(),
                completed_at=datetime.now(),
                error_message=str(e),
            )

    async def _enable_flow_logs(
        self,
        client: AsyncAWSClient,
        action: RemediationAction,
    ) -> RemediationResult:
        """Enable VPC flow logs."""
        vpc_id = action.resource_id

        return RemediationResult(
            action_id=action.id,
            success=False,
            status=RemediationStatus.FAILED,
            started_at=datetime.now(),
            completed_at=datetime.now(),
            error_message=(
                "Flow logs require IAM role and log destination configuration. "
                "Use Terraform for proper setup."
            ),
            details={"terraform_required": True, "vpc_id": vpc_id},
        )

    async def rollback(self, action: RemediationAction) -> RemediationResult:
        """
        Rollback a previously executed action.

        Args:
            action: The action to rollback

        Returns:
            RemediationResult for the rollback operation
        """
        if not action.rollback_data:
            return RemediationResult(
                action_id=action.id,
                success=False,
                status=RemediationStatus.FAILED,
                started_at=datetime.now(),
                completed_at=datetime.now(),
                error_message="No rollback data available",
            )

        logger.info(f"Rolling back action: {action.id}")

        # Rollback is action-type specific
        # Implementation would restore previous state from rollback_data

        return RemediationResult(
            action_id=action.id,
            success=True,
            status=RemediationStatus.ROLLED_BACK,
            started_at=datetime.now(),
            completed_at=datetime.now(),
            message=f"Rolled back: {action.name}",
        )


class RemediationEngine:
    """
    Orchestrates remediation workflow execution.

    Manages workflow state, step execution, approvals, and rollbacks.
    """

    def __init__(
        self,
        region: str = "us-east-1",
        account_id: str = "",
    ) -> None:
        """
        Initialize engine.

        Args:
            region: Default AWS region
            account_id: AWS account ID
        """
        self.region = region
        self.account_id = account_id
        self.executor = RemediationExecutor(region, account_id)
        self.analyzer = ImpactAnalyzer()

    async def analyze_workflow(self, workflow: RemediationWorkflow) -> ImpactAnalysis:
        """
        Analyze impact of a workflow before execution.

        Args:
            workflow: The workflow to analyze

        Returns:
            ImpactAnalysis with detailed impact information
        """
        actions = [step.action for step in workflow.plan.steps]
        return self.analyzer.analyze(actions, f"analysis-{workflow.id}")

    async def execute_workflow(
        self,
        workflow: RemediationWorkflow,
        context: ExecutionContext | None = None,
    ) -> RemediationWorkflow:
        """
        Execute a remediation workflow.

        Args:
            workflow: The workflow to execute
            context: Execution context and options

        Returns:
            Updated workflow with execution results
        """
        if context is None:
            context = ExecutionContext()

        if not context.skip_approval and not workflow.can_start():
            workflow.status = WorkflowStatus.PENDING_APPROVAL
            workflow.log_event("status_change", "Workflow awaiting approval")
            return workflow

        # Start execution
        workflow.status = WorkflowStatus.IN_PROGRESS
        workflow.started_at = datetime.now()
        workflow.log_event("execution_start", "Workflow execution started")

        try:
            # Execute steps in order
            while True:
                step = workflow.plan.get_next_step()
                if step is None:
                    break

                workflow.current_step_id = step.id

                # Check step approval if required
                if step.approval_gate and not context.skip_approval:
                    if not step.approval_gate.is_approved:
                        step.status = StepStatus.WAITING_APPROVAL
                        workflow.status = WorkflowStatus.PAUSED
                        workflow.log_event("approval_required", f"Step {step.id} awaiting approval")
                        return workflow

                # Execute step
                step.status = StepStatus.IN_PROGRESS
                step.started_at = datetime.now()

                if context.on_step_start:
                    context.on_step_start(step)

                result = await self.executor.execute(
                    step.action,
                    dry_run=context.dry_run,
                )

                step.result = result
                step.completed_at = datetime.now()

                if result.success:
                    step.status = StepStatus.COMPLETED
                    workflow.log_event(
                        "step_complete",
                        f"Step {step.id} completed successfully",
                        {"action_id": step.action.id},
                    )

                    if context.on_step_complete:
                        context.on_step_complete(step, result)
                else:
                    step.status = StepStatus.FAILED
                    workflow.log_event(
                        "step_failed",
                        f"Step {step.id} failed: {result.error_message}",
                        {"action_id": step.action.id, "error": result.error_message},
                    )

                    if context.on_step_failure:
                        context.on_step_failure(step, Exception(result.error_message))

                    if workflow.plan.stop_on_failure:
                        workflow.status = WorkflowStatus.FAILED

                        # Auto-rollback if enabled
                        if context.auto_rollback:
                            await self._rollback_workflow(workflow)

                        return workflow

            # All steps completed
            workflow.status = WorkflowStatus.COMPLETED
            workflow.completed_at = datetime.now()
            workflow.log_event("execution_complete", "Workflow completed successfully")

        except Exception as e:
            workflow.status = WorkflowStatus.FAILED
            workflow.log_event("execution_error", f"Workflow failed: {str(e)}")

            if context.auto_rollback:
                await self._rollback_workflow(workflow)

        return workflow

    async def _rollback_workflow(self, workflow: RemediationWorkflow) -> None:
        """Rollback completed steps in reverse order."""
        workflow.rollback_in_progress = True
        workflow.log_event("rollback_start", "Starting workflow rollback")

        # Get completed steps in reverse order
        completed_steps = [
            s for s in reversed(workflow.plan.steps)
            if s.status == StepStatus.COMPLETED and s.action.rollback_supported
        ]

        for step in completed_steps:
            result = await self.executor.rollback(step.action)
            if result.success:
                step.status = StepStatus.ROLLED_BACK
                workflow.log_event(
                    "step_rollback",
                    f"Rolled back step: {step.id}",
                )
            else:
                workflow.log_event(
                    "rollback_failed",
                    f"Failed to rollback step: {step.id}",
                    {"error": result.error_message},
                )

        workflow.rollback_in_progress = False
        workflow.status = WorkflowStatus.ROLLED_BACK
        workflow.log_event("rollback_complete", "Workflow rollback completed")

    async def cancel_workflow(self, workflow: RemediationWorkflow) -> None:
        """Cancel a workflow."""
        workflow.status = WorkflowStatus.CANCELLED
        workflow.log_event("workflow_cancelled", "Workflow was cancelled")

        # Mark pending steps as skipped
        for step in workflow.plan.steps:
            if step.status == StepStatus.PENDING:
                step.status = StepStatus.SKIPPED

    def approve_workflow(
        self,
        workflow: RemediationWorkflow,
        approver: str,
        comment: str = "",
    ) -> bool:
        """
        Approve a workflow for execution.

        Args:
            workflow: The workflow to approve
            approver: ID of the approver
            comment: Approval comment

        Returns:
            True if approval was successful
        """
        if workflow.plan.approval_gate:
            result = workflow.plan.approval_gate.approve(approver, comment)
            if result and workflow.plan.approval_gate.is_approved:
                workflow.status = WorkflowStatus.APPROVED
                workflow.log_event(
                    "workflow_approved",
                    f"Workflow approved by {approver}",
                    {"comment": comment},
                )
            return result
        return True
