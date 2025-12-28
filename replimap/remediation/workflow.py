"""
Remediation Workflow Engine.

Provides multi-step remediation workflows with approval gates,
progress tracking, and rollback capabilities.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable

from .actions import RemediationAction, RemediationResult, RemediationStatus

logger = logging.getLogger(__name__)


class StepStatus(str, Enum):
    """Status of a workflow step."""

    PENDING = "pending"
    WAITING_APPROVAL = "waiting_approval"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ROLLED_BACK = "rolled_back"

    def __str__(self) -> str:
        return self.value


class WorkflowStatus(str, Enum):
    """Status of an overall workflow."""

    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ROLLED_BACK = "rolled_back"

    def __str__(self) -> str:
        return self.value


@dataclass
class ApprovalGate:
    """
    Approval gate for workflow steps.
    """

    id: str
    name: str
    description: str

    # Approval requirements
    required_approvers: int = 1
    approvers: list[str] = field(default_factory=list)

    # Current state
    approvals: list[dict[str, Any]] = field(default_factory=list)
    rejections: list[dict[str, Any]] = field(default_factory=list)

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: datetime | None = None

    @property
    def is_approved(self) -> bool:
        """Check if gate has sufficient approvals."""
        return len(self.approvals) >= self.required_approvers

    @property
    def is_rejected(self) -> bool:
        """Check if gate has been rejected."""
        return len(self.rejections) > 0

    def approve(self, approver: str, comment: str = "") -> bool:
        """
        Add an approval.

        Args:
            approver: ID of the approver
            comment: Optional approval comment

        Returns:
            True if approval was accepted
        """
        if approver in self.approvers or not self.approvers:
            self.approvals.append({
                "approver": approver,
                "timestamp": datetime.now().isoformat(),
                "comment": comment,
            })
            return True
        return False

    def reject(self, rejector: str, reason: str = "") -> None:
        """
        Reject the gate.

        Args:
            rejector: ID of the rejector
            reason: Reason for rejection
        """
        self.rejections.append({
            "rejector": rejector,
            "timestamp": datetime.now().isoformat(),
            "reason": reason,
        })

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "required_approvers": self.required_approvers,
            "allowed_approvers": self.approvers,
            "approvals": self.approvals,
            "rejections": self.rejections,
            "is_approved": self.is_approved,
            "is_rejected": self.is_rejected,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }


@dataclass
class RemediationStep:
    """
    A single step in a remediation workflow.
    """

    id: str
    name: str
    description: str
    order: int

    # Action to execute
    action: RemediationAction

    # Dependencies
    depends_on: list[str] = field(default_factory=list)

    # Approval gate (optional)
    approval_gate: ApprovalGate | None = None

    # Execution
    status: StepStatus = StepStatus.PENDING
    result: RemediationResult | None = None

    # Timing
    started_at: datetime | None = None
    completed_at: datetime | None = None

    # Rollback
    can_rollback: bool = True
    rollback_step_id: str | None = None  # Reference to rollback step if created

    # Retry configuration
    max_retries: int = 3
    retry_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "order": self.order,
            "action": self.action.to_dict(),
            "depends_on": self.depends_on,
            "approval_gate": self.approval_gate.to_dict() if self.approval_gate else None,
            "status": str(self.status),
            "result": self.result.to_dict() if self.result else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "can_rollback": self.can_rollback,
            "rollback_step_id": self.rollback_step_id,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
        }


@dataclass
class RemediationPlan:
    """
    A plan containing multiple remediation steps.
    """

    id: str
    name: str
    description: str

    # Steps
    steps: list[RemediationStep] = field(default_factory=list)

    # Overall approval
    requires_approval: bool = True
    approval_gate: ApprovalGate | None = None

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""

    # Execution settings
    stop_on_failure: bool = True
    parallel_execution: bool = False

    def add_step(self, step: RemediationStep) -> None:
        """Add a step to the plan."""
        self.steps.append(step)
        # Re-sort by order
        self.steps.sort(key=lambda s: s.order)

    def get_step(self, step_id: str) -> RemediationStep | None:
        """Get a step by ID."""
        for step in self.steps:
            if step.id == step_id:
                return step
        return None

    def get_next_step(self) -> RemediationStep | None:
        """Get the next step to execute."""
        for step in self.steps:
            if step.status == StepStatus.PENDING:
                # Check dependencies
                deps_satisfied = all(
                    (dep_step := self.get_step(dep_id)) is not None
                    and dep_step.status == StepStatus.COMPLETED
                    for dep_id in step.depends_on
                )
                if deps_satisfied:
                    return step
        return None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "steps": [s.to_dict() for s in self.steps],
            "requires_approval": self.requires_approval,
            "approval_gate": self.approval_gate.to_dict() if self.approval_gate else None,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
            "stop_on_failure": self.stop_on_failure,
            "parallel_execution": self.parallel_execution,
        }


@dataclass
class RemediationWorkflow:
    """
    A complete remediation workflow with execution state.
    """

    id: str
    name: str
    description: str

    # Plan
    plan: RemediationPlan

    # Status
    status: WorkflowStatus = WorkflowStatus.DRAFT
    current_step_id: str | None = None

    # Timing
    created_at: datetime = field(default_factory=datetime.now)
    started_at: datetime | None = None
    completed_at: datetime | None = None

    # Execution
    executed_by: str = ""
    execution_log: list[dict[str, Any]] = field(default_factory=list)

    # Rollback state
    rollback_in_progress: bool = False
    rollback_steps: list[RemediationStep] = field(default_factory=list)

    def log_event(self, event_type: str, message: str, details: dict[str, Any] | None = None) -> None:
        """Log a workflow event."""
        self.execution_log.append({
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "message": message,
            "details": details or {},
        })

    def get_progress(self) -> dict[str, int]:
        """Get workflow progress."""
        total = len(self.plan.steps)
        completed = len([s for s in self.plan.steps if s.status == StepStatus.COMPLETED])
        failed = len([s for s in self.plan.steps if s.status == StepStatus.FAILED])
        in_progress = len([s for s in self.plan.steps if s.status == StepStatus.IN_PROGRESS])
        pending = len([s for s in self.plan.steps if s.status == StepStatus.PENDING])

        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "in_progress": in_progress,
            "pending": pending,
            "percentage": int(completed / total * 100) if total > 0 else 0,
        }

    def can_start(self) -> bool:
        """Check if workflow can be started."""
        if self.status != WorkflowStatus.APPROVED:
            return False
        if self.plan.requires_approval and self.plan.approval_gate:
            return self.plan.approval_gate.is_approved
        return True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "plan": self.plan.to_dict(),
            "status": str(self.status),
            "current_step_id": self.current_step_id,
            "progress": self.get_progress(),
            "timing": {
                "created": self.created_at.isoformat(),
                "started": self.started_at.isoformat() if self.started_at else None,
                "completed": self.completed_at.isoformat() if self.completed_at else None,
            },
            "executed_by": self.executed_by,
            "execution_log": self.execution_log,
            "rollback_in_progress": self.rollback_in_progress,
        }


class WorkflowBuilder:
    """
    Builder for creating remediation workflows.
    """

    def __init__(self, name: str, description: str = "") -> None:
        """
        Initialize builder.

        Args:
            name: Workflow name
            description: Workflow description
        """
        self.workflow_id = f"wf-{uuid.uuid4().hex[:8]}"
        self.plan_id = f"plan-{uuid.uuid4().hex[:8]}"
        self.name = name
        self.description = description
        self.steps: list[RemediationStep] = []
        self.requires_approval = True
        self.stop_on_failure = True
        self._step_order = 0

    def add_action(
        self,
        action: RemediationAction,
        name: str | None = None,
        description: str | None = None,
        depends_on: list[str] | None = None,
        requires_approval: bool = False,
    ) -> str:
        """
        Add an action as a step.

        Args:
            action: The remediation action
            name: Step name (defaults to action name)
            description: Step description
            depends_on: List of step IDs this step depends on
            requires_approval: Whether step requires approval

        Returns:
            Step ID
        """
        self._step_order += 1
        step_id = f"step-{uuid.uuid4().hex[:8]}"

        approval_gate = None
        if requires_approval:
            approval_gate = ApprovalGate(
                id=f"gate-{step_id}",
                name=f"Approval for {name or action.name}",
                description=f"Approval required before executing: {description or action.description}",
            )

        step = RemediationStep(
            id=step_id,
            name=name or action.name,
            description=description or action.description,
            order=self._step_order,
            action=action,
            depends_on=depends_on or [],
            approval_gate=approval_gate,
        )

        self.steps.append(step)
        return step_id

    def add_parallel_actions(
        self,
        actions: list[RemediationAction],
        group_name: str,
    ) -> list[str]:
        """
        Add multiple actions to execute in parallel.

        Args:
            actions: List of actions to execute in parallel
            group_name: Name for the parallel group

        Returns:
            List of step IDs
        """
        step_ids = []
        self._step_order += 1
        base_order = self._step_order

        for i, action in enumerate(actions):
            step_id = f"step-{uuid.uuid4().hex[:8]}"
            step = RemediationStep(
                id=step_id,
                name=f"{group_name} - {action.name}",
                description=action.description,
                order=base_order,  # Same order = parallel
                action=action,
            )
            self.steps.append(step)
            step_ids.append(step_id)

        return step_ids

    def set_requires_approval(self, requires: bool) -> "WorkflowBuilder":
        """Set whether workflow requires initial approval."""
        self.requires_approval = requires
        return self

    def set_stop_on_failure(self, stop: bool) -> "WorkflowBuilder":
        """Set whether to stop on first failure."""
        self.stop_on_failure = stop
        return self

    def build(self) -> RemediationWorkflow:
        """
        Build the workflow.

        Returns:
            Complete RemediationWorkflow
        """
        approval_gate = None
        if self.requires_approval:
            approval_gate = ApprovalGate(
                id=f"gate-{self.plan_id}",
                name=f"Workflow Approval: {self.name}",
                description=f"Approval required to start workflow: {self.description}",
            )

        plan = RemediationPlan(
            id=self.plan_id,
            name=self.name,
            description=self.description,
            steps=self.steps,
            requires_approval=self.requires_approval,
            approval_gate=approval_gate,
            stop_on_failure=self.stop_on_failure,
        )

        return RemediationWorkflow(
            id=self.workflow_id,
            name=self.name,
            description=self.description,
            plan=plan,
        )


def create_workflow_from_findings(
    findings: list[dict[str, Any]],
    name: str = "Compliance Remediation",
) -> RemediationWorkflow:
    """
    Create a workflow from compliance findings.

    Args:
        findings: List of compliance finding dictionaries
        name: Workflow name

    Returns:
        RemediationWorkflow ready for approval and execution
    """
    from .actions import create_action_from_finding

    builder = WorkflowBuilder(
        name=name,
        description=f"Remediate {len(findings)} compliance findings",
    )

    for finding in findings:
        rule_id = finding.get("rule_id", "")
        action = create_action_from_finding(finding, rule_id)

        if action:
            # High severity findings require individual approval
            requires_approval = finding.get("severity", "").lower() in ["critical", "high"]

            builder.add_action(
                action=action,
                requires_approval=requires_approval,
            )

    return builder.build()
