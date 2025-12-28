"""
RepliMap Audit Module.

Two main components:

1. Security Compliance Scanning (Checkov):
   - Generates forensic Terraform snapshots
   - Runs Checkov security analysis
   - Maps to SOC2 controls

2. Trust Center API Auditing (P1-9):
   - Records all AWS API calls
   - Classifies operations (read/write/delete/admin)
   - Proves Read-Only operation for enterprise procurement
   - Generates compliance reports
"""

# Security compliance scanning (existing)
from replimap.audit.checkov_runner import (
    CheckovExecutionError,
    CheckovFinding,
    CheckovNotInstalledError,
    CheckovResults,
    CheckovRunner,
)
from replimap.audit.engine import AuditEngine
from replimap.audit.remediation import (
    RemediationFile,
    RemediationGenerator,
    RemediationPlan,
    RemediationSeverity,
    RemediationType,
)
from replimap.audit.renderer import AuditRenderer
from replimap.audit.reporter import AuditReporter, ReportMetadata
from replimap.audit.soc2_mapping import get_soc2_mapping, get_soc2_summary

# Trust Center API auditing (P1-9)
from replimap.audit.classifier import OperationClassifier, classifier
from replimap.audit.exporters import (
    export_csv,
    export_json,
    export_summary_csv,
    generate_compliance_text,
    save_compliance_text,
)
from replimap.audit.hooks import AuditHooks
from replimap.audit.models import (
    APICallRecord,
    APICategory,
    AuditEventType,
    AuditSession,
    TrustCenterReport,
)
from replimap.audit.trust_center import TrustCenter

__all__ = [
    # Security Compliance Scanning
    "AuditEngine",
    "AuditRenderer",
    "AuditReporter",
    "CheckovExecutionError",
    "CheckovFinding",
    "CheckovNotInstalledError",
    "CheckovResults",
    "CheckovRunner",
    "RemediationFile",
    "RemediationGenerator",
    "RemediationPlan",
    "RemediationSeverity",
    "RemediationType",
    "ReportMetadata",
    "get_soc2_mapping",
    "get_soc2_summary",
    # Trust Center (P1-9)
    "TrustCenter",
    "APICategory",
    "AuditEventType",
    "APICallRecord",
    "AuditSession",
    "TrustCenterReport",
    "OperationClassifier",
    "classifier",
    "AuditHooks",
    "export_json",
    "export_csv",
    "export_summary_csv",
    "generate_compliance_text",
    "save_compliance_text",
]
