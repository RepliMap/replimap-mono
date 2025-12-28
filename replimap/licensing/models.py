"""
Licensing Models for RepliMap.

Defines the Plan tiers, License structure, and feature configurations.
"""

from __future__ import annotations

import hashlib
import platform
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class LicenseValidationError(Exception):
    """Raised when license validation fails."""

    pass


class Plan(str, Enum):
    """Subscription plan tiers."""

    FREE = "free"
    SOLO = "solo"
    PRO = "pro"
    TEAM = "team"
    ENTERPRISE = "enterprise"

    def __str__(self) -> str:
        return self.value


class LicenseStatus(str, Enum):
    """License validation status."""

    VALID = "valid"
    EXPIRED = "expired"
    INVALID = "invalid"
    SUSPENDED = "suspended"
    MACHINE_MISMATCH = "machine_mismatch"


class Feature(str, Enum):
    """
    Available features that can be gated by plan.

    Gate Philosophy: Gate at OUTPUT, not at SCAN.
    - Scanning is always free (user experiences full value)
    - Gating happens when users try to export/download

    Core Principles:
    - SCAN: Unlimited resources, frequency limited only
    - GRAPH: Full viewing free, watermark on export
    - CLONE: Full generation, download is paid
    - AUDIT: Full scan, detailed findings are paid
    - DRIFT: Fully paid feature
    """

    # Core scanning (always available, frequency limited for FREE)
    SCAN = "scan"
    SCAN_UNLIMITED_FREQUENCY = "scan_unlimited_frequency"
    ASYNC_SCANNING = "async_scanning"

    # Multi-account support
    SINGLE_ACCOUNT = "single_account"
    MULTI_ACCOUNT = "multi_account"
    UNLIMITED_ACCOUNTS = "unlimited_accounts"

    # Clone features (gate at DOWNLOAD, not generation)
    CLONE_GENERATE = "clone_generate"  # Always available
    CLONE_FULL_PREVIEW = "clone_full_preview"  # See all lines
    CLONE_DOWNLOAD = "clone_download"  # Download to disk

    # Graph features (gate at EXPORT, not viewing)
    GRAPH_VIEW = "graph_view"  # Always available
    GRAPH_EXPORT_NO_WATERMARK = "graph_export_no_watermark"

    # Audit features (gate at DETAILS, not scan)
    AUDIT_SCAN = "audit_scan"  # Always available
    AUDIT_FULL_FINDINGS = "audit_full_findings"  # See all findings
    AUDIT_REPORT_EXPORT = "audit_report_export"  # Export HTML/PDF
    AUDIT_EXPORT_HTML = "audit_export_html"  # HTML format
    AUDIT_EXPORT_PDF = "audit_export_pdf"  # PDF format (Pro+)
    AUDIT_EXPORT_JSON = "audit_export_json"  # JSON format (Team+)
    AUDIT_EXPORT_CSV = "audit_export_csv"  # CSV format (Enterprise)
    AUDIT_CI_MODE = "audit_ci_mode"  # --fail-on-high

    # Drift features (Pro+ only)
    DRIFT_DETECT = "drift_detect"
    DRIFT_WATCH = "drift_watch"
    DRIFT_ALERTS = "drift_alerts"

    # Advanced features
    COST_ESTIMATE = "cost_estimate"
    COST_ESTIMATE_BASIC = "cost_estimate_basic"  # Basic cost (FREE)
    COST_DIFF = "cost_diff"  # Cost diff comparison (Solo+)
    RIGHT_SIZER = "right_sizer"  # Auto-downsize for dev/staging
    DEPENDENCY_EXPLORER = "dependency_explorer"
    BLAST_RADIUS = "dependency_explorer"  # Backward compatibility alias

    # Transformation features
    BASIC_TRANSFORM = "basic_transform"
    ADVANCED_TRANSFORM = "advanced_transform"
    CUSTOM_TEMPLATES = "custom_templates"

    # Output format features
    TERRAFORM_OUTPUT = "terraform_output"
    CLOUDFORMATION_OUTPUT = "cloudformation_output"
    PULUMI_OUTPUT = "pulumi_output"
    CDK_OUTPUT = "cdk_output"

    # Storage layer features (Solo+)
    LOCAL_CACHE = "local_cache"  # SQLite + Zstd caching
    SNAPSHOT_CREATE = "snapshot_create"  # Create snapshots
    SNAPSHOT_DIFF = "snapshot_diff"  # Diff snapshots

    # Trust Center features (Team+)
    TRUST_CENTER = "trust_center"  # replimap trust status
    TRUST_EXPORT = "trust_export"  # replimap trust export
    TRUST_VERIFY = "trust_verify"  # replimap trust verify (Enterprise)
    TRUST_COMPLIANCE = "trust_compliance"  # replimap trust compliance (Enterprise)
    DIGITAL_SIGNATURES = "digital_signatures"  # SHA256 signed reports

    # Regional Compliance features (Enterprise only)
    COMPLIANCE_APRA_CPS234 = "compliance_apra_cps234"  # APRA CPS 234 mapping
    COMPLIANCE_ESSENTIAL_EIGHT = "compliance_essential_eight"  # Essential Eight
    COMPLIANCE_RBNZ_BS11 = "compliance_rbnz_bs11"  # RBNZ BS11 mapping
    COMPLIANCE_NZISM = "compliance_nzism"  # NZISM alignment

    # Remediate features
    REMEDIATE_BETA = "remediate_beta"  # Remediate beta access

    # Team features
    WEB_DASHBOARD = "web_dashboard"
    COLLABORATION = "collaboration"
    SHARED_GRAPHS = "shared_graphs"

    # Enterprise features
    SSO = "sso"
    AUDIT_LOGS = "audit_logs"
    PRIORITY_SUPPORT = "priority_support"
    SLA_GUARANTEE = "sla_guarantee"
    CUSTOM_INTEGRATIONS = "custom_integrations"

    # Legacy compatibility (mapped to new features)
    BASIC_SCAN = "basic_scan"
    UNLIMITED_RESOURCES = "unlimited_resources"


@dataclass
class PlanFeatures:
    """
    Feature configuration for a plan tier.

    Gate Philosophy: Gate at OUTPUT, not at SCAN.
    - max_resources_per_scan: DEPRECATED - always None (unlimited)
    - Limits are on OUTPUT actions (download, export, view findings)

    Pricing Philosophy: Simple USD pricing, subscriptions only (no lifetime in v1).
    """

    plan: Plan
    price_monthly: int  # USD
    price_annual: int  # USD, annual price (2 months free)

    # Scan limits (frequency only - NO resource count limit!)
    max_scans_per_month: int | None  # None = unlimited
    max_aws_accounts: int | None  # None = unlimited

    # Clone output limits
    clone_preview_lines: int | None  # Lines shown in preview, None = full
    clone_download_enabled: bool  # Can download generated code

    # Audit output limits
    audit_titles_visible: bool  # Show all issue titles (always True)
    audit_first_critical_preview_lines: (
        int | None
    )  # Lines for 1st critical, None = full
    audit_details_visible: bool  # See full remediation details
    audit_report_export: bool  # Can export reports
    audit_export_formats: set[str]  # Available formats: html, pdf, json, csv
    audit_ci_mode: bool  # Can use --fail-on-high

    # Graph export limits
    graph_export_watermark: bool  # Export has watermark

    # Advanced features
    drift_enabled: bool
    drift_watch_enabled: bool
    drift_alerts_enabled: bool
    cost_enabled: bool  # Full cost estimation
    cost_basic_enabled: bool  # Basic cost (FREE tier)
    cost_diff_enabled: bool  # Cost diff comparison
    rightsizer_enabled: bool  # Right-Sizer for dev/staging optimization
    deps_enabled: bool  # Dependency explorer (formerly blast_enabled)

    # Storage layer (SQLite + Zstd)
    local_cache_enabled: bool
    max_snapshots: int  # 0 = disabled, -1 = unlimited
    snapshot_retention_days: int  # 0 = disabled

    # Trust Center (Audit Logging)
    trust_center_enabled: bool
    max_recorded_calls: int | None  # None = unlimited
    max_sessions: int | None  # None = unlimited
    audit_log_retention_days: int  # 0 = disabled
    trust_export_formats: set[str]  # Available: json, csv, pdf
    digital_signatures: bool  # SHA256 signed reports
    compliance_reports: bool  # Tamper-evident reports

    # Regional Compliance (Enterprise only)
    apra_cps234_mapping: bool
    essential_eight_assessment: bool
    rbnz_bs11_mapping: bool
    nzism_alignment: bool

    # Remediate Integration
    remediate_beta_access: bool
    remediate_priority: str  # "none", "priority", "first"

    # Support
    email_support: bool
    email_sla_hours: int | None  # None = no SLA

    # Team features
    max_team_members: int | None  # None = unlimited

    # Feature set
    features: set[Feature] = field(default_factory=set)

    # Legacy: kept for backwards compatibility, always None
    max_resources_per_scan: int | None = None  # DEPRECATED: always unlimited

    # Legacy: for backward compatibility
    @property
    def price_annual_monthly(self) -> int:
        """Monthly equivalent of annual price (deprecated, use price_annual)."""
        return self.price_annual // 12 if self.price_annual > 0 else 0

    @property
    def audit_visible_findings(self) -> int | None:
        """Deprecated: Use audit_details_visible instead."""
        return None if self.audit_details_visible else 3

    def has_feature(self, feature: Feature) -> bool:
        """Check if this plan includes a feature."""
        return feature in self.features

    def can_scan_resources(self, count: int) -> bool:
        """
        Check if the plan allows scanning this many resources.

        DEPRECATED: Always returns True. Resources are unlimited.
        Gating happens at output time, not scan time.
        """
        return True  # Always allow scanning

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "plan": str(self.plan),
            "price_monthly": self.price_monthly,
            "price_annual": self.price_annual,
            "price_annual_monthly": self.price_annual_monthly,  # Backward compat
            "max_scans_per_month": self.max_scans_per_month,
            "max_aws_accounts": self.max_aws_accounts,
            "clone_preview_lines": self.clone_preview_lines,
            "clone_download_enabled": self.clone_download_enabled,
            "audit_titles_visible": self.audit_titles_visible,
            "audit_first_critical_preview_lines": self.audit_first_critical_preview_lines,
            "audit_details_visible": self.audit_details_visible,
            "audit_visible_findings": self.audit_visible_findings,  # Backward compat
            "audit_report_export": self.audit_report_export,
            "audit_export_formats": list(self.audit_export_formats),
            "audit_ci_mode": self.audit_ci_mode,
            "graph_export_watermark": self.graph_export_watermark,
            "drift_enabled": self.drift_enabled,
            "drift_watch_enabled": self.drift_watch_enabled,
            "drift_alerts_enabled": self.drift_alerts_enabled,
            "cost_enabled": self.cost_enabled,
            "cost_basic_enabled": self.cost_basic_enabled,
            "cost_diff_enabled": self.cost_diff_enabled,
            "rightsizer_enabled": self.rightsizer_enabled,
            "deps_enabled": self.deps_enabled,
            "blast_enabled": self.deps_enabled,  # Backward compatibility alias
            "local_cache_enabled": self.local_cache_enabled,
            "max_snapshots": self.max_snapshots,
            "snapshot_retention_days": self.snapshot_retention_days,
            "trust_center_enabled": self.trust_center_enabled,
            "max_recorded_calls": self.max_recorded_calls,
            "max_sessions": self.max_sessions,
            "audit_log_retention_days": self.audit_log_retention_days,
            "trust_export_formats": list(self.trust_export_formats),
            "digital_signatures": self.digital_signatures,
            "compliance_reports": self.compliance_reports,
            "apra_cps234_mapping": self.apra_cps234_mapping,
            "essential_eight_assessment": self.essential_eight_assessment,
            "rbnz_bs11_mapping": self.rbnz_bs11_mapping,
            "nzism_alignment": self.nzism_alignment,
            "remediate_beta_access": self.remediate_beta_access,
            "remediate_priority": self.remediate_priority,
            "email_support": self.email_support,
            "email_sla_hours": self.email_sla_hours,
            "max_team_members": self.max_team_members,
            "features": [str(f) for f in self.features],
            # Legacy field
            "max_resources_per_scan": None,
        }


# =============================================================================
# PLAN FEATURE CONFIGURATIONS (v3.2 Pricing Matrix)
#
# Gate Strategy (核心原则):
# - SCAN: Unlimited resources, limit frequency (3/month for FREE)
# - GRAPH: Full visualization, watermark on export for FREE
# - CLONE: Full generation, block download for FREE
# - AUDIT: Full scan, show all titles + first CRITICAL preview for FREE
# - DRIFT: Disabled for FREE and SOLO
#
# Pricing Philosophy: Simple USD pricing, subscriptions only.
# Annual billing: 2 months free (10 months price for 12 months)
# =============================================================================

PLAN_FEATURES: dict[Plan, PlanFeatures] = {
    # =========================================================================
    # FREE TIER ($0) - Experience everything, pay to export
    # =========================================================================
    Plan.FREE: PlanFeatures(
        plan=Plan.FREE,
        price_monthly=0,
        price_annual=0,
        # Scan: UNLIMITED resources, limited frequency
        max_scans_per_month=3,
        max_aws_accounts=1,
        # Clone: Generate but NO download
        clone_preview_lines=100,  # Show first 100 lines
        clone_download_enabled=False,
        # Audit: See ALL titles + first CRITICAL with 2-line remediation preview
        audit_titles_visible=True,
        audit_first_critical_preview_lines=2,  # 2-line preview
        audit_details_visible=False,  # No full details
        audit_report_export=False,
        audit_export_formats=set(),  # No exports
        audit_ci_mode=False,
        # Graph: View all, watermark on export
        graph_export_watermark=True,
        # Advanced: Basic cost only
        drift_enabled=False,
        drift_watch_enabled=False,
        drift_alerts_enabled=False,
        cost_enabled=False,
        cost_basic_enabled=True,  # Basic cost estimates
        cost_diff_enabled=False,
        rightsizer_enabled=False,  # Right-Sizer is Solo+
        deps_enabled=False,
        # Storage: None
        local_cache_enabled=False,
        max_snapshots=0,
        snapshot_retention_days=0,
        # Trust Center: None
        trust_center_enabled=False,
        max_recorded_calls=0,
        max_sessions=0,
        audit_log_retention_days=0,
        trust_export_formats=set(),
        digital_signatures=False,
        compliance_reports=False,
        # Regional Compliance: None
        apra_cps234_mapping=False,
        essential_eight_assessment=False,
        rbnz_bs11_mapping=False,
        nzism_alignment=False,
        # Remediate: None
        remediate_beta_access=False,
        remediate_priority="none",
        # Support: None
        email_support=False,
        email_sla_hours=None,
        # Team: Solo only
        max_team_members=1,
        features={
            Feature.SCAN,
            Feature.GRAPH_VIEW,
            Feature.CLONE_GENERATE,
            Feature.AUDIT_SCAN,
            Feature.COST_ESTIMATE_BASIC,
            Feature.SINGLE_ACCOUNT,
            Feature.BASIC_TRANSFORM,
            Feature.TERRAFORM_OUTPUT,
            # Legacy compatibility
            Feature.BASIC_SCAN,
        },
    ),
    # =========================================================================
    # SOLO TIER ($49/mo) - For individual DevOps/SRE
    # =========================================================================
    Plan.SOLO: PlanFeatures(
        plan=Plan.SOLO,
        price_monthly=49,
        price_annual=490,  # 2 months free
        max_scans_per_month=None,  # Unlimited
        max_aws_accounts=1,
        clone_preview_lines=None,  # Full preview
        clone_download_enabled=True,  # Can download!
        # Audit: Full access
        audit_titles_visible=True,
        audit_first_critical_preview_lines=None,  # Full remediation
        audit_details_visible=True,
        audit_report_export=True,
        audit_export_formats={"html"},  # HTML only
        audit_ci_mode=False,  # CI mode is Pro
        graph_export_watermark=False,  # No watermark
        # Advanced
        drift_enabled=False,  # Drift is Pro
        drift_watch_enabled=False,
        drift_alerts_enabled=False,
        cost_enabled=True,  # Full cost!
        cost_basic_enabled=True,
        cost_diff_enabled=True,  # Cost diff!
        rightsizer_enabled=True,  # Right-Sizer enabled!
        deps_enabled=False,
        # Storage layer
        local_cache_enabled=True,
        max_snapshots=5,
        snapshot_retention_days=7,
        # Trust Center: None
        trust_center_enabled=False,
        max_recorded_calls=0,
        max_sessions=0,
        audit_log_retention_days=0,
        trust_export_formats=set(),
        digital_signatures=False,
        compliance_reports=False,
        # Regional Compliance: None
        apra_cps234_mapping=False,
        essential_eight_assessment=False,
        rbnz_bs11_mapping=False,
        nzism_alignment=False,
        # Remediate: None
        remediate_beta_access=False,
        remediate_priority="none",
        # Support: 48h SLA
        email_support=True,
        email_sla_hours=48,
        max_team_members=1,
        features={
            Feature.SCAN,
            Feature.SCAN_UNLIMITED_FREQUENCY,
            Feature.GRAPH_VIEW,
            Feature.GRAPH_EXPORT_NO_WATERMARK,
            Feature.CLONE_GENERATE,
            Feature.CLONE_DOWNLOAD,
            Feature.CLONE_FULL_PREVIEW,
            Feature.AUDIT_SCAN,
            Feature.AUDIT_FULL_FINDINGS,
            Feature.AUDIT_REPORT_EXPORT,
            Feature.AUDIT_EXPORT_HTML,
            Feature.COST_ESTIMATE,
            Feature.COST_ESTIMATE_BASIC,
            Feature.COST_DIFF,
            Feature.RIGHT_SIZER,
            Feature.LOCAL_CACHE,
            Feature.SNAPSHOT_CREATE,
            Feature.SNAPSHOT_DIFF,
            Feature.SINGLE_ACCOUNT,
            Feature.BASIC_TRANSFORM,
            Feature.ADVANCED_TRANSFORM,
            Feature.TERRAFORM_OUTPUT,
            Feature.ASYNC_SCANNING,
            # Legacy compatibility
            Feature.BASIC_SCAN,
            Feature.UNLIMITED_RESOURCES,
        },
    ),
    # =========================================================================
    # PRO TIER ($99/mo) - Senior engineers, multi-account
    # =========================================================================
    Plan.PRO: PlanFeatures(
        plan=Plan.PRO,
        price_monthly=99,
        price_annual=990,  # 2 months free
        max_scans_per_month=None,
        max_aws_accounts=3,  # dev/staging/prod
        clone_preview_lines=None,
        clone_download_enabled=True,
        # Audit: Full + PDF
        audit_titles_visible=True,
        audit_first_critical_preview_lines=None,
        audit_details_visible=True,
        audit_report_export=True,
        audit_export_formats={"html", "pdf"},  # HTML/PDF
        audit_ci_mode=True,  # CI mode enabled!
        graph_export_watermark=False,
        # Advanced
        drift_enabled=True,  # Drift enabled!
        drift_watch_enabled=False,  # Watch is Team
        drift_alerts_enabled=False,
        cost_enabled=True,
        cost_basic_enabled=True,
        cost_diff_enabled=True,
        rightsizer_enabled=True,
        deps_enabled=False,
        # Storage layer
        local_cache_enabled=True,
        max_snapshots=15,
        snapshot_retention_days=30,
        # Trust Center: None
        trust_center_enabled=False,
        max_recorded_calls=0,
        max_sessions=0,
        audit_log_retention_days=0,
        trust_export_formats=set(),
        digital_signatures=False,
        compliance_reports=False,
        # Regional Compliance: None
        apra_cps234_mapping=False,
        essential_eight_assessment=False,
        rbnz_bs11_mapping=False,
        nzism_alignment=False,
        # Remediate: Priority access
        remediate_beta_access=True,
        remediate_priority="priority",
        # Support: 24h SLA
        email_support=True,
        email_sla_hours=24,
        max_team_members=1,
        features={
            Feature.SCAN,
            Feature.SCAN_UNLIMITED_FREQUENCY,
            Feature.GRAPH_VIEW,
            Feature.GRAPH_EXPORT_NO_WATERMARK,
            Feature.CLONE_GENERATE,
            Feature.CLONE_DOWNLOAD,
            Feature.CLONE_FULL_PREVIEW,
            Feature.AUDIT_SCAN,
            Feature.AUDIT_FULL_FINDINGS,
            Feature.AUDIT_REPORT_EXPORT,
            Feature.AUDIT_EXPORT_HTML,
            Feature.AUDIT_EXPORT_PDF,
            Feature.AUDIT_CI_MODE,
            Feature.DRIFT_DETECT,
            Feature.COST_ESTIMATE,
            Feature.COST_ESTIMATE_BASIC,
            Feature.COST_DIFF,
            Feature.RIGHT_SIZER,
            Feature.LOCAL_CACHE,
            Feature.SNAPSHOT_CREATE,
            Feature.SNAPSHOT_DIFF,
            Feature.REMEDIATE_BETA,
            Feature.MULTI_ACCOUNT,
            Feature.BASIC_TRANSFORM,
            Feature.ADVANCED_TRANSFORM,
            Feature.CUSTOM_TEMPLATES,
            Feature.TERRAFORM_OUTPUT,
            Feature.CLOUDFORMATION_OUTPUT,
            Feature.PULUMI_OUTPUT,
            Feature.WEB_DASHBOARD,
            Feature.ASYNC_SCANNING,
            # Legacy compatibility
            Feature.BASIC_SCAN,
            Feature.UNLIMITED_RESOURCES,
        },
    ),
    # =========================================================================
    # TEAM TIER ($199/mo) - Small teams, basic compliance
    # =========================================================================
    Plan.TEAM: PlanFeatures(
        plan=Plan.TEAM,
        price_monthly=199,
        price_annual=1990,  # 2 months free
        max_scans_per_month=None,
        max_aws_accounts=10,
        clone_preview_lines=None,
        clone_download_enabled=True,
        # Audit: Full + all formats except CSV
        audit_titles_visible=True,
        audit_first_critical_preview_lines=None,
        audit_details_visible=True,
        audit_report_export=True,
        audit_export_formats={"html", "pdf", "json"},  # All except CSV
        audit_ci_mode=True,
        graph_export_watermark=False,
        # Advanced
        drift_enabled=True,
        drift_watch_enabled=True,  # Watch mode!
        drift_alerts_enabled=True,  # Alerts!
        cost_enabled=True,
        cost_basic_enabled=True,
        cost_diff_enabled=True,
        rightsizer_enabled=True,
        deps_enabled=True,  # Dependency explorer!
        # Storage layer
        local_cache_enabled=True,
        max_snapshots=30,
        snapshot_retention_days=90,
        # Trust Center: Basic
        trust_center_enabled=True,
        max_recorded_calls=100,  # Last 100 calls
        max_sessions=10,
        audit_log_retention_days=7,
        trust_export_formats={"json"},  # JSON only
        digital_signatures=False,
        compliance_reports=False,
        # Regional Compliance: None
        apra_cps234_mapping=False,
        essential_eight_assessment=False,
        rbnz_bs11_mapping=False,
        nzism_alignment=False,
        # Remediate: Priority access
        remediate_beta_access=True,
        remediate_priority="priority",
        # Support: 12h SLA
        email_support=True,
        email_sla_hours=12,
        max_team_members=5,  # 5 members included
        features={
            Feature.SCAN,
            Feature.SCAN_UNLIMITED_FREQUENCY,
            Feature.GRAPH_VIEW,
            Feature.GRAPH_EXPORT_NO_WATERMARK,
            Feature.CLONE_GENERATE,
            Feature.CLONE_DOWNLOAD,
            Feature.CLONE_FULL_PREVIEW,
            Feature.AUDIT_SCAN,
            Feature.AUDIT_FULL_FINDINGS,
            Feature.AUDIT_REPORT_EXPORT,
            Feature.AUDIT_EXPORT_HTML,
            Feature.AUDIT_EXPORT_PDF,
            Feature.AUDIT_EXPORT_JSON,
            Feature.AUDIT_CI_MODE,
            Feature.DRIFT_DETECT,
            Feature.DRIFT_WATCH,
            Feature.DRIFT_ALERTS,
            Feature.COST_ESTIMATE,
            Feature.COST_ESTIMATE_BASIC,
            Feature.COST_DIFF,
            Feature.RIGHT_SIZER,
            Feature.DEPENDENCY_EXPLORER,
            Feature.LOCAL_CACHE,
            Feature.SNAPSHOT_CREATE,
            Feature.SNAPSHOT_DIFF,
            Feature.TRUST_CENTER,
            Feature.TRUST_EXPORT,
            Feature.REMEDIATE_BETA,
            Feature.MULTI_ACCOUNT,
            Feature.BASIC_TRANSFORM,
            Feature.ADVANCED_TRANSFORM,
            Feature.CUSTOM_TEMPLATES,
            Feature.TERRAFORM_OUTPUT,
            Feature.CLOUDFORMATION_OUTPUT,
            Feature.PULUMI_OUTPUT,
            Feature.CDK_OUTPUT,
            Feature.WEB_DASHBOARD,
            Feature.COLLABORATION,
            Feature.SHARED_GRAPHS,
            Feature.ASYNC_SCANNING,
            # Legacy compatibility
            Feature.BASIC_SCAN,
            Feature.UNLIMITED_RESOURCES,
        },
    ),
    # =========================================================================
    # ENTERPRISE TIER (From $500/mo) - Banks, regulated industries
    # =========================================================================
    Plan.ENTERPRISE: PlanFeatures(
        plan=Plan.ENTERPRISE,
        price_monthly=500,  # Starting price
        price_annual=5000,  # Custom pricing typically
        max_scans_per_month=None,
        max_aws_accounts=None,  # Unlimited
        clone_preview_lines=None,
        clone_download_enabled=True,
        # Audit: Full + all formats
        audit_titles_visible=True,
        audit_first_critical_preview_lines=None,
        audit_details_visible=True,
        audit_report_export=True,
        audit_export_formats={"html", "pdf", "json", "csv"},  # All formats
        audit_ci_mode=True,
        graph_export_watermark=False,
        # Advanced
        drift_enabled=True,
        drift_watch_enabled=True,
        drift_alerts_enabled=True,
        cost_enabled=True,
        cost_basic_enabled=True,
        cost_diff_enabled=True,
        rightsizer_enabled=True,
        deps_enabled=True,
        # Storage layer: Unlimited
        local_cache_enabled=True,
        max_snapshots=-1,  # Unlimited
        snapshot_retention_days=365,  # 1 year
        # Trust Center: Full
        trust_center_enabled=True,
        max_recorded_calls=None,  # Unlimited
        max_sessions=None,  # Unlimited
        audit_log_retention_days=365,  # 1 year
        trust_export_formats={"json", "csv", "pdf"},  # All formats
        digital_signatures=True,  # SHA256
        compliance_reports=True,  # Tamper-evident
        # Regional Compliance: All
        apra_cps234_mapping=True,
        essential_eight_assessment=True,
        rbnz_bs11_mapping=True,
        nzism_alignment=True,
        # Remediate: First access
        remediate_beta_access=True,
        remediate_priority="first",
        # Support: 4h SLA
        email_support=True,
        email_sla_hours=4,
        max_team_members=None,  # Unlimited
        features=set(Feature),  # All features
    ),
}


def get_plan_features(plan: Plan) -> PlanFeatures:
    """Get the feature configuration for a plan."""
    return PLAN_FEATURES[plan]


def has_feature(plan: Plan, feature: Feature) -> bool:
    """Check if a plan has a specific feature."""
    return feature in PLAN_FEATURES[plan].features


def get_upgrade_target(current_plan: Plan, required_feature: Feature) -> Plan | None:
    """
    Find the cheapest plan that has the required feature.

    Args:
        current_plan: User's current plan
        required_feature: Feature they need

    Returns:
        The cheapest plan with the feature, or None if no upgrade available
    """
    plan_order = [Plan.FREE, Plan.SOLO, Plan.PRO, Plan.TEAM, Plan.ENTERPRISE]
    current_idx = plan_order.index(current_plan)

    for plan in plan_order[current_idx + 1 :]:
        if has_feature(plan, required_feature):
            return plan
    return None


def get_plan_for_limit(limit_type: str, required_value: int) -> Plan | None:
    """
    Find the cheapest plan that meets a limit requirement.

    Args:
        limit_type: Type of limit (e.g., "max_aws_accounts")
        required_value: Minimum value needed

    Returns:
        The cheapest plan meeting the requirement
    """
    plan_order = [Plan.FREE, Plan.SOLO, Plan.PRO, Plan.TEAM, Plan.ENTERPRISE]

    for plan in plan_order:
        features = PLAN_FEATURES[plan]
        limit_value = getattr(features, limit_type, None)

        if limit_value is None:  # Unlimited
            return plan
        if limit_value >= required_value:
            return plan

    return Plan.ENTERPRISE


@dataclass
class License:
    """License information for a user/organization."""

    license_key: str
    plan: Plan
    email: str
    organization: str | None = None
    issued_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime | None = None
    machine_fingerprint: str | None = None
    max_machines: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        """Check if the license has expired."""
        if self.expires_at is None:
            return False
        return datetime.now(UTC) > self.expires_at

    @property
    def features(self) -> PlanFeatures:
        """Get the features for this license's plan."""
        return get_plan_features(self.plan)

    def has_feature(self, feature: Feature) -> bool:
        """Check if this license includes a feature."""
        return self.features.has_feature(feature)

    def validate_machine(self, fingerprint: str) -> bool:
        """Validate the machine fingerprint."""
        if self.machine_fingerprint is None:
            return True  # Not bound to machine
        return self.machine_fingerprint == fingerprint

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "license_key": self.license_key,
            "plan": str(self.plan),
            "email": self.email,
            "organization": self.organization,
            "issued_at": self.issued_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "machine_fingerprint": self.machine_fingerprint,
            "max_machines": self.max_machines,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> License:
        """Create License from dictionary."""
        return cls(
            license_key=data["license_key"],
            plan=Plan(data["plan"]),
            email=data["email"],
            organization=data.get("organization"),
            issued_at=datetime.fromisoformat(data["issued_at"]),
            expires_at=(
                datetime.fromisoformat(data["expires_at"])
                if data.get("expires_at")
                else None
            ),
            machine_fingerprint=data.get("machine_fingerprint"),
            max_machines=data.get("max_machines", 1),
            metadata=data.get("metadata", {}),
        )


def get_machine_fingerprint() -> str:
    """
    Generate a unique fingerprint for the current machine.

    Combines multiple system identifiers for a stable fingerprint.
    """
    components = [
        platform.node(),  # Hostname
        platform.machine(),  # Architecture
        platform.system(),  # OS
    ]

    # Try to get MAC address
    try:
        mac = uuid.getnode()
        # Check if MAC is stable (not random) by calling twice
        # uuid.getnode() returns a random value if no real MAC is available
        if mac == uuid.getnode():  # MAC is stable, use it
            components.append(str(mac))
    except OSError:
        # MAC address not available on this platform
        pass

    fingerprint_string = "|".join(components)
    return hashlib.sha256(fingerprint_string.encode()).hexdigest()[:32]
