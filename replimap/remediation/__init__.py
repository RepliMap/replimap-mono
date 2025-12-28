"""
Advanced Remediation Automation for RepliMap.

Provides a workflow-based remediation system that integrates with
the compliance engine, supports both Terraform and AWS API remediation,
and includes impact analysis, approval workflows, and rollback capabilities.

Features:
- Compliance finding to remediation action mapping
- Multi-step remediation workflows
- Pre-remediation impact analysis
- Approval gate support
- Remediation history tracking
- Rollback capabilities
- Both Terraform and direct AWS API remediation

This is a Pro+ feature ($79/mo).
"""

from .actions import (
    RemediationAction,
    RemediationActionType,
    RemediationResult,
    RemediationStatus,
)
from .analyzer import (
    ImpactAnalysis,
    ImpactAnalyzer,
    ImpactLevel,
    ResourceImpact,
)
from .engine import (
    RemediationEngine,
    RemediationExecutor,
)
from .workflow import (
    ApprovalGate,
    RemediationPlan,
    RemediationStep,
    RemediationWorkflow,
    StepStatus,
    WorkflowBuilder,
    WorkflowStatus,
)

__all__ = [
    # Actions
    "RemediationAction",
    "RemediationActionType",
    "RemediationResult",
    "RemediationStatus",
    # Analyzer
    "ImpactAnalyzer",
    "ImpactAnalysis",
    "ImpactLevel",
    "ResourceImpact",
    # Engine
    "RemediationEngine",
    "RemediationExecutor",
    # Workflow
    "RemediationWorkflow",
    "RemediationStep",
    "RemediationPlan",
    "ApprovalGate",
    "StepStatus",
    "WorkflowStatus",
    "WorkflowBuilder",
]
