"""
Tests for P1-3 Advanced Remediation Automation.

These tests verify:
1. Remediation action types and models
2. Impact analysis functionality
3. Workflow construction and management
4. Remediation engine execution
"""

from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from replimap.remediation import (
    ApprovalGate,
    ImpactAnalysis,
    ImpactAnalyzer,
    ImpactLevel,
    RemediationAction,
    RemediationActionType,
    RemediationEngine,
    RemediationExecutor,
    RemediationPlan,
    RemediationResult,
    RemediationStatus,
    RemediationStep,
    RemediationWorkflow,
    ResourceImpact,
    StepStatus,
    WorkflowBuilder,
    WorkflowStatus,
)
from replimap.remediation.actions import (
    COMPLIANCE_TO_ACTION_MAP,
    create_action_from_finding,
)
from replimap.remediation.workflow import create_workflow_from_findings


# =============================================================================
# ACTION TESTS
# =============================================================================


class TestRemediationActionType:
    """Test RemediationActionType enum."""

    def test_all_action_types_exist(self) -> None:
        """Test that all expected action types exist."""
        expected_types = [
            "ENABLE_ENCRYPTION",
            "ENABLE_KMS_ENCRYPTION",
            "ENABLE_KEY_ROTATION",
            "BLOCK_PUBLIC_ACCESS",
            "RESTRICT_SECURITY_GROUP",
            "ENABLE_SSL_ONLY",
            "ENABLE_MULTI_AZ",
            "ENABLE_VERSIONING",
            "ENABLE_BACKUP",
            "ENABLE_LOGGING",
            "ENABLE_MONITORING",
            "ENABLE_FLOW_LOGS",
            "ENABLE_IMDSV2",
            "ENABLE_DELETION_PROTECTION",
            "TERRAFORM_APPLY",
            "CUSTOM",
        ]
        for type_name in expected_types:
            assert hasattr(RemediationActionType, type_name)

    def test_action_type_values(self) -> None:
        """Test action type values are strings."""
        for action_type in RemediationActionType:
            assert isinstance(action_type.value, str)

    def test_action_type_str(self) -> None:
        """Test string representation."""
        assert str(RemediationActionType.ENABLE_ENCRYPTION) == "enable_encryption"


class TestRemediationStatus:
    """Test RemediationStatus enum."""

    def test_all_status_values(self) -> None:
        """Test all status values exist."""
        expected = ["PENDING", "APPROVED", "IN_PROGRESS", "COMPLETED", "FAILED", "ROLLED_BACK", "SKIPPED"]
        for status_name in expected:
            assert hasattr(RemediationStatus, status_name)


class TestRemediationAction:
    """Test RemediationAction dataclass."""

    def test_create_basic_action(self) -> None:
        """Test creating a basic remediation action."""
        action = RemediationAction(
            id="rem-001",
            name="Enable S3 Encryption",
            description="Enable encryption on S3 bucket",
            action_type=RemediationActionType.ENABLE_ENCRYPTION,
            resource_id="my-bucket",
            resource_type="aws_s3_bucket",
            region="us-east-1",
        )

        assert action.id == "rem-001"
        assert action.action_type == RemediationActionType.ENABLE_ENCRYPTION
        assert action.resource_id == "my-bucket"
        assert action.resource_type == "aws_s3_bucket"
        assert action.status == RemediationStatus.PENDING
        assert action.parameters == {}

    def test_action_with_parameters(self) -> None:
        """Test creating an action with parameters."""
        action = RemediationAction(
            id="rem-002",
            name="Enable KMS Encryption",
            description="Enable KMS encryption on S3 bucket",
            action_type=RemediationActionType.ENABLE_KMS_ENCRYPTION,
            resource_id="my-bucket",
            resource_type="aws_s3_bucket",
            region="us-east-1",
            parameters={"kms_key_id": "alias/my-key", "bucket_key": True},
        )

        assert action.parameters["kms_key_id"] == "alias/my-key"
        assert action.parameters["bucket_key"] is True

    def test_action_with_rule_id(self) -> None:
        """Test action with compliance rule mapping."""
        action = RemediationAction(
            id="rem-003",
            name="Enable Encryption",
            description="Enable encryption",
            action_type=RemediationActionType.ENABLE_ENCRYPTION,
            resource_id="my-bucket",
            resource_type="aws_s3_bucket",
            region="us-east-1",
            rule_id="S3_001",
        )

        assert action.rule_id == "S3_001"

    def test_action_to_dict(self) -> None:
        """Test action serialization."""
        action = RemediationAction(
            id="rem-004",
            name="Test Action",
            description="Test",
            action_type=RemediationActionType.ENABLE_ENCRYPTION,
            resource_id="resource-1",
            resource_type="aws_s3_bucket",
            region="us-east-1",
        )

        data = action.to_dict()

        assert data["id"] == "rem-004"
        assert data["name"] == "Test Action"
        assert data["action_type"] == "enable_encryption"
        assert data["resource"]["id"] == "resource-1"


class TestRemediationResult:
    """Test RemediationResult dataclass."""

    def test_successful_result(self) -> None:
        """Test creating a successful result."""
        now = datetime.now()
        result = RemediationResult(
            action_id="rem-001",
            success=True,
            status=RemediationStatus.COMPLETED,
            started_at=now,
            completed_at=now,
            message="Encryption enabled successfully",
        )

        assert result.success is True
        assert result.status == RemediationStatus.COMPLETED
        assert result.message == "Encryption enabled successfully"
        assert result.error_code == ""

    def test_failed_result(self) -> None:
        """Test creating a failed result."""
        now = datetime.now()
        result = RemediationResult(
            action_id="rem-001",
            success=False,
            status=RemediationStatus.FAILED,
            started_at=now,
            completed_at=now,
            message="Failed to enable encryption",
            error_code="AccessDenied",
            error_message="Insufficient permissions",
        )

        assert result.success is False
        assert result.error_code == "AccessDenied"

    def test_result_to_dict(self) -> None:
        """Test result serialization."""
        now = datetime.now()
        result = RemediationResult(
            action_id="rem-001",
            success=True,
            status=RemediationStatus.COMPLETED,
            started_at=now,
            completed_at=now,
            message="Success",
            changes=[{"field": "encryption", "old": "none", "new": "AES256"}],
        )

        data = result.to_dict()

        assert data["action_id"] == "rem-001"
        assert data["success"] is True
        assert len(data["changes"]) == 1


class TestComplianceToActionMap:
    """Test COMPLIANCE_TO_ACTION_MAP."""

    def test_s3_mappings(self) -> None:
        """Test S3 compliance rule mappings."""
        assert COMPLIANCE_TO_ACTION_MAP["S3_001"] == RemediationActionType.ENABLE_ENCRYPTION
        assert COMPLIANCE_TO_ACTION_MAP["S3_002"] == RemediationActionType.BLOCK_PUBLIC_ACCESS

    def test_rds_mappings(self) -> None:
        """Test RDS compliance rule mappings."""
        assert COMPLIANCE_TO_ACTION_MAP["RDS_001"] == RemediationActionType.ENABLE_ENCRYPTION
        assert COMPLIANCE_TO_ACTION_MAP["RDS_002"] == RemediationActionType.ENABLE_MULTI_AZ

    def test_security_group_mapping(self) -> None:
        """Test security group mappings."""
        assert COMPLIANCE_TO_ACTION_MAP["SG_001"] == RemediationActionType.RESTRICT_SECURITY_GROUP
        assert COMPLIANCE_TO_ACTION_MAP["SG_002"] == RemediationActionType.RESTRICT_SECURITY_GROUP


class TestCreateActionFromFinding:
    """Test create_action_from_finding helper."""

    def test_create_action_from_s3_finding(self) -> None:
        """Test creating action from S3 finding."""
        finding = {
            "resource_id": "my-bucket",
            "resource_type": "aws_s3_bucket",
            "region": "us-east-1",
        }

        action = create_action_from_finding(finding, "S3_001")

        assert action is not None
        assert action.action_type == RemediationActionType.ENABLE_ENCRYPTION
        assert action.rule_id == "S3_001"

    def test_create_action_unknown_rule(self) -> None:
        """Test creating action from unknown rule returns None."""
        finding = {
            "resource_id": "some_resource",
            "resource_type": "unknown",
            "region": "us-east-1",
        }

        action = create_action_from_finding(finding, "UNKNOWN_999")

        assert action is None


# =============================================================================
# ANALYZER TESTS
# =============================================================================


class TestImpactLevel:
    """Test ImpactLevel enum."""

    def test_impact_levels_exist(self) -> None:
        """Test all impact levels exist."""
        expected = ["NONE", "MINIMAL", "MODERATE", "SIGNIFICANT", "CRITICAL"]
        for level_name in expected:
            assert hasattr(ImpactLevel, level_name)

    def test_requires_maintenance_window(self) -> None:
        """Test requires_maintenance_window property."""
        assert ImpactLevel.NONE.requires_maintenance_window is False
        assert ImpactLevel.MINIMAL.requires_maintenance_window is False
        assert ImpactLevel.MODERATE.requires_maintenance_window is False
        assert ImpactLevel.SIGNIFICANT.requires_maintenance_window is True
        assert ImpactLevel.CRITICAL.requires_maintenance_window is True


class TestResourceImpact:
    """Test ResourceImpact dataclass."""

    def test_create_resource_impact(self) -> None:
        """Test creating a resource impact."""
        impact = ResourceImpact(
            resource_id="my-bucket",
            resource_type="aws_s3_bucket",
            resource_name="my-bucket",
            region="us-east-1",
            impact_level=ImpactLevel.MINIMAL,
            impact_description="Enabling encryption requires no downtime",
        )

        assert impact.resource_id == "my-bucket"
        assert impact.impact_level == ImpactLevel.MINIMAL

    def test_resource_impact_with_affected_resources(self) -> None:
        """Test resource impact with affected downstream resources."""
        impact = ResourceImpact(
            resource_id="sg-123",
            resource_type="aws_security_group",
            resource_name="web-sg",
            region="us-east-1",
            impact_level=ImpactLevel.MODERATE,
            impact_description="Restricting ingress may affect connected instances",
            dependent_resources=["i-instance1", "i-instance2"],
        )

        assert len(impact.dependent_resources) == 2

    def test_resource_impact_to_dict(self) -> None:
        """Test resource impact serialization."""
        impact = ResourceImpact(
            resource_id="bucket-1",
            resource_type="aws_s3_bucket",
            resource_name="bucket-1",
            region="us-east-1",
            impact_level=ImpactLevel.MINIMAL,
            impact_description="Test",
        )

        data = impact.to_dict()

        assert data["resource_id"] == "bucket-1"
        assert data["impact_level"] == "minimal"


class TestImpactAnalysis:
    """Test ImpactAnalysis dataclass."""

    def test_create_impact_analysis(self) -> None:
        """Test creating an impact analysis."""
        analysis = ImpactAnalysis(
            analysis_id="analysis-001",
            overall_impact=ImpactLevel.MODERATE,
            resource_impacts=[
                ResourceImpact(
                    resource_id="bucket1",
                    resource_type="aws_s3_bucket",
                    resource_name="bucket1",
                    region="us-east-1",
                    impact_level=ImpactLevel.MINIMAL,
                    impact_description="Low impact",
                ),
            ],
            estimated_total_downtime_seconds=60,
        )

        assert analysis.overall_impact == ImpactLevel.MODERATE
        assert len(analysis.resource_impacts) == 1
        assert analysis.estimated_total_downtime_seconds == 60

    def test_is_safe_to_proceed(self) -> None:
        """Test safe to proceed check."""
        analysis = ImpactAnalysis(
            analysis_id="analysis-001",
            overall_impact=ImpactLevel.MODERATE,
            risk_score=50.0,
        )

        assert analysis.is_safe_to_proceed() is True

    def test_not_safe_to_proceed_critical(self) -> None:
        """Test not safe when critical impact."""
        analysis = ImpactAnalysis(
            analysis_id="analysis-001",
            overall_impact=ImpactLevel.CRITICAL,
            risk_score=50.0,
        )

        assert analysis.is_safe_to_proceed() is False


class TestImpactAnalyzer:
    """Test ImpactAnalyzer class."""

    def test_analyze_encryption_action(self) -> None:
        """Test analyzing encryption action impact."""
        action = RemediationAction(
            id="rem-001",
            name="Enable Encryption",
            description="Enable encryption",
            action_type=RemediationActionType.ENABLE_ENCRYPTION,
            resource_id="my-bucket",
            resource_type="aws_s3_bucket",
            region="us-east-1",
        )

        analyzer = ImpactAnalyzer()
        analysis = analyzer.analyze([action])

        assert analysis.overall_impact == ImpactLevel.MINIMAL
        assert len(analysis.resource_impacts) == 1

    def test_analyze_security_group_restriction(self) -> None:
        """Test analyzing security group restriction impact."""
        action = RemediationAction(
            id="rem-002",
            name="Restrict SG",
            description="Restrict security group",
            action_type=RemediationActionType.RESTRICT_SECURITY_GROUP,
            resource_id="sg-123",
            resource_type="aws_security_group",
            region="us-east-1",
        )

        analyzer = ImpactAnalyzer()
        analysis = analyzer.analyze([action])

        # Security group changes should be SIGNIFICANT impact
        assert analysis.overall_impact == ImpactLevel.SIGNIFICANT

    def test_analyze_multiple_actions(self) -> None:
        """Test analyzing multiple actions."""
        actions = [
            RemediationAction(
                id="rem-001",
                name="Enable Encryption",
                description="Enable encryption",
                action_type=RemediationActionType.ENABLE_ENCRYPTION,
                resource_id="bucket1",
                resource_type="aws_s3_bucket",
                region="us-east-1",
            ),
            RemediationAction(
                id="rem-002",
                name="Enable Multi-AZ",
                description="Enable Multi-AZ",
                action_type=RemediationActionType.ENABLE_MULTI_AZ,
                resource_id="db-instance",
                resource_type="aws_db_instance",
                region="us-east-1",
            ),
        ]

        analyzer = ImpactAnalyzer()
        analysis = analyzer.analyze(actions)

        assert len(analysis.resource_impacts) == 2

    def test_analyze_empty_actions(self) -> None:
        """Test analyzing empty action list."""
        analyzer = ImpactAnalyzer()
        analysis = analyzer.analyze([])

        assert analysis.overall_impact == ImpactLevel.NONE
        assert len(analysis.resource_impacts) == 0


# =============================================================================
# WORKFLOW TESTS
# =============================================================================


class TestApprovalGate:
    """Test ApprovalGate class."""

    def test_create_approval_gate(self) -> None:
        """Test creating an approval gate."""
        gate = ApprovalGate(
            id="gate-001",
            name="Security Review",
            description="Security team must approve",
            required_approvers=1,
            approvers=["security-team"],
        )

        assert gate.name == "Security Review"
        assert gate.is_approved is False
        assert len(gate.approvals) == 0

    def test_approve_gate(self) -> None:
        """Test approving a gate."""
        gate = ApprovalGate(
            id="gate-001",
            name="Security Review",
            description="Security review",
            required_approvers=1,
            approvers=["security-team"],
        )

        result = gate.approve("security-team", "Approved after review")

        assert result is True
        assert gate.is_approved is True
        assert len(gate.approvals) == 1
        assert gate.approvals[0]["approver"] == "security-team"

    def test_reject_gate(self) -> None:
        """Test rejecting a gate."""
        gate = ApprovalGate(
            id="gate-001",
            name="Security Review",
            description="Security review",
            required_approvers=1,
        )

        gate.reject("security-team", "Needs more review")

        assert gate.is_rejected is True
        assert len(gate.rejections) == 1
        assert gate.rejections[0]["reason"] == "Needs more review"


class TestRemediationStep:
    """Test RemediationStep class."""

    def test_create_step(self) -> None:
        """Test creating a remediation step."""
        action = RemediationAction(
            id="rem-001",
            name="Enable Encryption",
            description="Enable encryption",
            action_type=RemediationActionType.ENABLE_ENCRYPTION,
            resource_id="my-bucket",
            resource_type="aws_s3_bucket",
            region="us-east-1",
        )

        step = RemediationStep(
            id="step-001",
            name="Enable S3 Encryption",
            description="Enable encryption on bucket",
            order=1,
            action=action,
        )

        assert step.id == "step-001"
        assert step.status == StepStatus.PENDING
        assert step.depends_on == []

    def test_step_with_dependencies(self) -> None:
        """Test step with dependencies."""
        action = RemediationAction(
            id="rem-002",
            name="Enable Versioning",
            description="Enable versioning",
            action_type=RemediationActionType.ENABLE_VERSIONING,
            resource_id="my-bucket",
            resource_type="aws_s3_bucket",
            region="us-east-1",
        )

        step = RemediationStep(
            id="step-002",
            name="Enable Versioning",
            description="Enable versioning",
            order=2,
            action=action,
            depends_on=["step-001"],
        )

        assert step.depends_on == ["step-001"]

    def test_step_with_approval_gate(self) -> None:
        """Test step with approval gate."""
        action = RemediationAction(
            id="rem-003",
            name="Restrict SG",
            description="Restrict security group",
            action_type=RemediationActionType.RESTRICT_SECURITY_GROUP,
            resource_id="sg-123",
            resource_type="aws_security_group",
            region="us-east-1",
        )

        gate = ApprovalGate(
            id="gate-001",
            name="Network Review",
            description="Network team review",
            required_approvers=1,
            approvers=["network-team"],
        )

        step = RemediationStep(
            id="step-003",
            name="Restrict Security Group",
            description="Restrict SG",
            order=1,
            action=action,
            approval_gate=gate,
        )

        assert step.approval_gate is not None


class TestRemediationPlanAdvanced:
    """Test RemediationPlan from advanced module."""

    def test_create_plan(self) -> None:
        """Test creating a remediation plan."""
        action = RemediationAction(
            id="rem-001",
            name="Enable Encryption",
            description="Enable encryption",
            action_type=RemediationActionType.ENABLE_ENCRYPTION,
            resource_id="bucket1",
            resource_type="aws_s3_bucket",
            region="us-east-1",
        )

        step = RemediationStep(
            id="step-001",
            name="Step 1",
            description="First step",
            order=1,
            action=action,
        )

        plan = RemediationPlan(
            id="plan-001",
            name="S3 Security Remediation",
            description="Remediate S3 security issues",
            steps=[step],
        )

        assert plan.id == "plan-001"
        assert len(plan.steps) == 1

    def test_plan_get_next_step(self) -> None:
        """Test getting next step to execute."""
        action1 = RemediationAction(
            id="rem-001",
            name="First",
            description="First",
            action_type=RemediationActionType.ENABLE_ENCRYPTION,
            resource_id="bucket1",
            resource_type="aws_s3_bucket",
            region="us-east-1",
        )
        action2 = RemediationAction(
            id="rem-002",
            name="Second",
            description="Second",
            action_type=RemediationActionType.ENABLE_VERSIONING,
            resource_id="bucket1",
            resource_type="aws_s3_bucket",
            region="us-east-1",
        )

        step1 = RemediationStep(id="step-1", name="First", description="First", order=1, action=action1)
        step2 = RemediationStep(id="step-2", name="Second", description="Second", order=2, action=action2, depends_on=["step-1"])

        plan = RemediationPlan(
            id="plan-001",
            name="Test Plan",
            description="Test",
            steps=[step1, step2],
        )

        # First step should be next
        next_step = plan.get_next_step()
        assert next_step is not None
        assert next_step.id == "step-1"

        # After completing step1, step2 should be next
        step1.status = StepStatus.COMPLETED
        next_step = plan.get_next_step()
        assert next_step is not None
        assert next_step.id == "step-2"


class TestRemediationWorkflow:
    """Test RemediationWorkflow class."""

    def test_create_workflow(self) -> None:
        """Test creating a workflow."""
        plan = RemediationPlan(
            id="plan-001",
            name="Test Plan",
            description="Test",
            steps=[],
        )

        workflow = RemediationWorkflow(
            id="wf-001",
            name="Test Workflow",
            description="Test workflow",
            plan=plan,
        )

        assert workflow.id == "wf-001"
        assert workflow.status == WorkflowStatus.DRAFT

    def test_workflow_status_transitions(self) -> None:
        """Test workflow status transitions."""
        plan = RemediationPlan(id="plan-001", name="Test", description="Test", steps=[])
        workflow = RemediationWorkflow(
            id="wf-001",
            name="Test",
            description="Test",
            plan=plan,
        )

        assert workflow.status == WorkflowStatus.DRAFT

        workflow.status = WorkflowStatus.PENDING_APPROVAL
        assert workflow.status == WorkflowStatus.PENDING_APPROVAL

        workflow.status = WorkflowStatus.IN_PROGRESS
        assert workflow.status == WorkflowStatus.IN_PROGRESS

    def test_workflow_progress(self) -> None:
        """Test workflow progress tracking."""
        action = RemediationAction(
            id="rem-001",
            name="Test",
            description="Test",
            action_type=RemediationActionType.ENABLE_ENCRYPTION,
            resource_id="bucket",
            resource_type="aws_s3_bucket",
            region="us-east-1",
        )
        step1 = RemediationStep(id="step-1", name="Step 1", description="Step 1", order=1, action=action)
        step2 = RemediationStep(id="step-2", name="Step 2", description="Step 2", order=2, action=action)

        plan = RemediationPlan(id="plan-001", name="Test", description="Test", steps=[step1, step2])
        workflow = RemediationWorkflow(id="wf-001", name="Test", description="Test", plan=plan)

        progress = workflow.get_progress()

        assert progress["total"] == 2
        assert progress["pending"] == 2
        assert progress["completed"] == 0


class TestWorkflowBuilder:
    """Test WorkflowBuilder class."""

    def test_build_simple_workflow(self) -> None:
        """Test building a simple workflow."""
        action1 = RemediationAction(
            id="rem-001",
            name="Enable Encryption",
            description="Enable encryption",
            action_type=RemediationActionType.ENABLE_ENCRYPTION,
            resource_id="bucket1",
            resource_type="aws_s3_bucket",
            region="us-east-1",
        )
        action2 = RemediationAction(
            id="rem-002",
            name="Enable Versioning",
            description="Enable versioning",
            action_type=RemediationActionType.ENABLE_VERSIONING,
            resource_id="bucket1",
            resource_type="aws_s3_bucket",
            region="us-east-1",
        )

        builder = WorkflowBuilder("My Workflow", "Test workflow")
        builder.add_action(action1)
        builder.add_action(action2)
        workflow = builder.build()

        assert workflow.name == "My Workflow"
        assert len(workflow.plan.steps) == 2

    def test_build_workflow_with_approval(self) -> None:
        """Test building workflow with approval gate."""
        action = RemediationAction(
            id="rem-001",
            name="Restrict SG",
            description="Restrict security group",
            action_type=RemediationActionType.RESTRICT_SECURITY_GROUP,
            resource_id="sg-123",
            resource_type="aws_security_group",
            region="us-east-1",
        )

        builder = WorkflowBuilder("Secure Workflow", "Workflow with approval")
        builder.add_action(action, requires_approval=True)
        workflow = builder.build()

        # The step should have an approval gate
        step = workflow.plan.steps[0]
        assert step.approval_gate is not None

    def test_build_workflow_with_dependencies(self) -> None:
        """Test building workflow with step dependencies."""
        action1 = RemediationAction(
            id="rem-001",
            name="First",
            description="First",
            action_type=RemediationActionType.ENABLE_ENCRYPTION,
            resource_id="bucket1",
            resource_type="aws_s3_bucket",
            region="us-east-1",
        )
        action2 = RemediationAction(
            id="rem-002",
            name="Second",
            description="Second",
            action_type=RemediationActionType.ENABLE_VERSIONING,
            resource_id="bucket1",
            resource_type="aws_s3_bucket",
            region="us-east-1",
        )

        builder = WorkflowBuilder("Sequential Workflow")
        step1_id = builder.add_action(action1, name="encrypt")
        builder.add_action(action2, name="version", depends_on=[step1_id])
        workflow = builder.build()

        version_step = workflow.plan.steps[1]
        assert step1_id in version_step.depends_on


class TestCreateWorkflowFromFindings:
    """Test create_workflow_from_findings helper."""

    def test_create_from_single_finding(self) -> None:
        """Test creating workflow from single finding."""
        findings = [
            {
                "rule_id": "S3_001",
                "resource_id": "my-bucket",
                "resource_type": "aws_s3_bucket",
                "region": "us-east-1",
            }
        ]

        workflow = create_workflow_from_findings(findings, "S3 Remediation")

        assert workflow is not None
        assert len(workflow.plan.steps) == 1

    def test_create_from_multiple_findings(self) -> None:
        """Test creating workflow from multiple findings."""
        findings = [
            {
                "rule_id": "S3_001",
                "resource_id": "bucket1",
                "resource_type": "aws_s3_bucket",
                "region": "us-east-1",
            },
            {
                "rule_id": "S3_002",
                "resource_id": "bucket2",
                "resource_type": "aws_s3_bucket",
                "region": "us-east-1",
            },
            {
                "rule_id": "RDS_001",
                "resource_id": "my-db",
                "resource_type": "aws_db_instance",
                "region": "us-east-1",
            },
        ]

        workflow = create_workflow_from_findings(findings, "Multi-Resource Remediation")

        assert len(workflow.plan.steps) == 3

    def test_skip_unknown_findings(self) -> None:
        """Test that unknown findings are skipped."""
        findings = [
            {
                "rule_id": "UNKNOWN_999",
                "resource_id": "unknown",
                "resource_type": "unknown",
                "region": "us-east-1",
            },
            {
                "rule_id": "S3_001",
                "resource_id": "bucket1",
                "resource_type": "aws_s3_bucket",
                "region": "us-east-1",
            },
        ]

        workflow = create_workflow_from_findings(findings, "Mixed Findings")

        # Only the known finding should be included
        assert len(workflow.plan.steps) == 1


# =============================================================================
# ENGINE TESTS
# =============================================================================


class TestRemediationExecutor:
    """Test RemediationExecutor class."""

    @pytest.mark.asyncio
    async def test_execute_dry_run(self) -> None:
        """Test executing action in dry run mode."""
        executor = RemediationExecutor(region="us-east-1")
        action = RemediationAction(
            id="rem-001",
            name="Enable Encryption",
            description="Enable encryption",
            action_type=RemediationActionType.ENABLE_ENCRYPTION,
            resource_id="my-bucket",
            resource_type="aws_s3_bucket",
            region="us-east-1",
        )

        # Dry run should not make actual AWS calls
        result = await executor.execute(action, dry_run=True)

        assert result.success is True
        assert "[DRY RUN]" in result.message

    @pytest.mark.asyncio
    async def test_execute_unsupported_action(self) -> None:
        """Test executing unsupported action type."""
        executor = RemediationExecutor(region="us-east-1")
        action = RemediationAction(
            id="rem-001",
            name="Custom Action",
            description="Custom",
            action_type=RemediationActionType.CUSTOM,
            resource_id="resource",
            resource_type="unknown",
            region="us-east-1",
        )

        result = await executor.execute(action)

        # Custom actions should indicate they're not supported
        assert result.success is False
        assert "Unsupported" in result.error_message

    @pytest.mark.asyncio
    async def test_execute_with_mocked_client(self) -> None:
        """Test executing with mocked AWS client."""
        executor = RemediationExecutor(region="us-east-1")
        action = RemediationAction(
            id="rem-001",
            name="Enable Encryption",
            description="Enable encryption",
            action_type=RemediationActionType.ENABLE_ENCRYPTION,
            resource_id="my-bucket",
            resource_type="aws_s3_bucket",
            region="us-east-1",
        )

        # Mock the _get_client method to return a mock client
        mock_client = MagicMock()
        mock_client.call = AsyncMock(return_value={})

        with patch.object(executor, '_get_client', return_value=mock_client):
            result = await executor.execute(action)

        assert result.success is True
        mock_client.call.assert_called()

    @pytest.mark.asyncio
    async def test_execute_failure_handling_mocked(self) -> None:
        """Test handling execution failure with mocked client."""
        executor = RemediationExecutor(region="us-east-1")
        action = RemediationAction(
            id="rem-001",
            name="Enable Encryption",
            description="Enable encryption",
            action_type=RemediationActionType.ENABLE_ENCRYPTION,
            resource_id="my-bucket",
            resource_type="aws_s3_bucket",
            region="us-east-1",
        )

        # Mock the _get_client method to return a failing client
        mock_client = MagicMock()
        mock_client.call = AsyncMock(side_effect=Exception("Access Denied"))

        with patch.object(executor, '_get_client', return_value=mock_client):
            result = await executor.execute(action)

        assert result.success is False
        assert "Access Denied" in result.error_message


class TestRemediationEngine:
    """Test RemediationEngine class."""

    @pytest.fixture
    def sample_workflow(self) -> RemediationWorkflow:
        """Create a sample workflow for testing."""
        action = RemediationAction(
            id="rem-001",
            name="Enable Encryption",
            description="Enable encryption",
            action_type=RemediationActionType.ENABLE_ENCRYPTION,
            resource_id="bucket1",
            resource_type="aws_s3_bucket",
            region="us-east-1",
        )
        step = RemediationStep(
            id="step-001",
            name="Enable Encryption",
            description="Enable encryption",
            order=1,
            action=action,
        )
        plan = RemediationPlan(
            id="plan-001",
            name="Test Plan",
            description="Test",
            steps=[step],
            requires_approval=False,
        )
        workflow = RemediationWorkflow(
            id="wf-001",
            name="Test Workflow",
            description="Test",
            plan=plan,
        )
        workflow.status = WorkflowStatus.APPROVED
        return workflow

    @pytest.mark.asyncio
    async def test_analyze_workflow(self, sample_workflow: RemediationWorkflow) -> None:
        """Test analyzing workflow impact."""
        engine = RemediationEngine()
        analysis = await engine.analyze_workflow(sample_workflow)

        assert analysis is not None
        assert isinstance(analysis, ImpactAnalysis)

    @pytest.mark.asyncio
    async def test_execute_workflow_dry_run(
        self, sample_workflow: RemediationWorkflow
    ) -> None:
        """Test executing a workflow in dry run mode."""
        from replimap.remediation.engine import ExecutionContext

        engine = RemediationEngine()
        context = ExecutionContext(dry_run=True, skip_approval=True)

        result_workflow = await engine.execute_workflow(sample_workflow, context)

        assert result_workflow.status == WorkflowStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_execute_workflow_with_mocked_executor(
        self, sample_workflow: RemediationWorkflow
    ) -> None:
        """Test executing a workflow with mocked executor."""
        from replimap.remediation.engine import ExecutionContext

        engine = RemediationEngine()
        now = datetime.now()

        # Mock the executor's execute method
        mock_result = RemediationResult(
            action_id="rem-001",
            success=True,
            status=RemediationStatus.COMPLETED,
            started_at=now,
            completed_at=now,
            message="Success",
        )

        with patch.object(engine.executor, 'execute', new_callable=AsyncMock, return_value=mock_result):
            context = ExecutionContext(skip_approval=True)
            result_workflow = await engine.execute_workflow(sample_workflow, context)

        assert result_workflow.status == WorkflowStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_execute_workflow_with_failure(
        self, sample_workflow: RemediationWorkflow
    ) -> None:
        """Test workflow execution with step failure."""
        from replimap.remediation.engine import ExecutionContext

        engine = RemediationEngine()
        now = datetime.now()

        # Mock the executor's execute method to return failure
        mock_result = RemediationResult(
            action_id="rem-001",
            success=False,
            status=RemediationStatus.FAILED,
            started_at=now,
            completed_at=now,
            message="Failed",
            error_code="AccessDenied",
            error_message="Access Denied",
        )

        # Also mock rollback to prevent issues
        mock_rollback = RemediationResult(
            action_id="rem-001",
            success=True,
            status=RemediationStatus.ROLLED_BACK,
            started_at=now,
            completed_at=now,
            message="Rolled back",
        )

        with patch.object(engine.executor, 'execute', new_callable=AsyncMock, return_value=mock_result):
            with patch.object(engine.executor, 'rollback', new_callable=AsyncMock, return_value=mock_rollback):
                context = ExecutionContext(skip_approval=True, auto_rollback=False)
                result_workflow = await engine.execute_workflow(sample_workflow, context)

        assert result_workflow.status == WorkflowStatus.FAILED

    def test_approve_workflow(self, sample_workflow: RemediationWorkflow) -> None:
        """Test approving a workflow."""
        # Add approval gate to workflow
        sample_workflow.plan.requires_approval = True
        sample_workflow.plan.approval_gate = ApprovalGate(
            id="gate-001",
            name="Test Gate",
            description="Test",
            required_approvers=1,
        )
        sample_workflow.status = WorkflowStatus.PENDING_APPROVAL

        engine = RemediationEngine()
        result = engine.approve_workflow(sample_workflow, "admin", "Approved")

        assert result is True
        assert sample_workflow.status == WorkflowStatus.APPROVED


# =============================================================================
# MODULE IMPORT TESTS
# =============================================================================


class TestModuleImports:
    """Test module imports."""

    def test_import_all_from_remediation(self) -> None:
        """Test all expected exports are available."""
        from replimap.remediation import (
            ApprovalGate,
            ImpactAnalysis,
            ImpactAnalyzer,
            ImpactLevel,
            RemediationAction,
            RemediationActionType,
            RemediationEngine,
            RemediationExecutor,
            RemediationPlan,
            RemediationResult,
            RemediationStatus,
            RemediationStep,
            RemediationWorkflow,
            ResourceImpact,
            StepStatus,
            WorkflowBuilder,
            WorkflowStatus,
        )

        # Just verify imports work (no assertions needed)
        assert RemediationActionType is not None
        assert RemediationEngine is not None

    def test_import_actions_module(self) -> None:
        """Test actions module imports."""
        from replimap.remediation.actions import (
            COMPLIANCE_TO_ACTION_MAP,
            RemediationAction,
            RemediationActionType,
            RemediationResult,
            RemediationStatus,
            create_action_from_finding,
        )

        assert COMPLIANCE_TO_ACTION_MAP is not None
        assert create_action_from_finding is not None

    def test_import_analyzer_module(self) -> None:
        """Test analyzer module imports."""
        from replimap.remediation.analyzer import (
            ACTION_IMPACT_PROFILES,
            ImpactAnalysis,
            ImpactAnalyzer,
            ImpactLevel,
            ResourceImpact,
        )

        assert ACTION_IMPACT_PROFILES is not None
        assert ImpactAnalyzer is not None

    def test_import_workflow_module(self) -> None:
        """Test workflow module imports."""
        from replimap.remediation.workflow import (
            ApprovalGate,
            RemediationPlan,
            RemediationStep,
            RemediationWorkflow,
            StepStatus,
            WorkflowBuilder,
            WorkflowStatus,
            create_workflow_from_findings,
        )

        assert WorkflowBuilder is not None
        assert create_workflow_from_findings is not None

    def test_import_engine_module(self) -> None:
        """Test engine module imports."""
        from replimap.remediation.engine import RemediationEngine, RemediationExecutor

        assert RemediationEngine is not None
        assert RemediationExecutor is not None
