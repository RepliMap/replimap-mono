"""
Secure license data models with plan limits and features.

Changes from original models.py:
- SecureLicenseData created ONLY from verified signatures
- Added SecureLicenseLimits for per-plan resource limits
- No mutable fields that could be tampered
- Type-safe plan and feature access

IMPORTANT: This module contains the SECURE license data.
For legacy compatibility, see models.py
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

# Import from existing models for compatibility
from replimap.licensing.models import Feature, Plan, get_plan_features

UTC = timezone.utc


@dataclass
class SecureLicenseLimits:
    """
    Resource limits for a secure license.

    -1 means unlimited.
    """

    max_accounts: int = 1
    max_regions: int = 1
    max_resources_per_scan: int = 100
    max_concurrent_scans: int = 1
    max_scans_per_day: int = 10
    offline_grace_days: int = 0

    def to_dict(self) -> dict[str, int]:
        """Convert to dictionary."""
        return {
            "max_accounts": self.max_accounts,
            "max_regions": self.max_regions,
            "max_resources_per_scan": self.max_resources_per_scan,
            "max_concurrent_scans": self.max_concurrent_scans,
            "max_scans_per_day": self.max_scans_per_day,
            "offline_grace_days": self.offline_grace_days,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SecureLicenseLimits:
        """Create from dictionary."""
        return cls(
            max_accounts=data.get("max_accounts", 1),
            max_regions=data.get("max_regions", 1),
            max_resources_per_scan=data.get("max_resources_per_scan", 100),
            max_concurrent_scans=data.get("max_concurrent_scans", 1),
            max_scans_per_day=data.get("max_scans_per_day", 10),
            offline_grace_days=data.get("offline_grace_days", 0),
        )

    def check_limit(self, limit_name: str, current_value: int) -> bool:
        """Check if a value is within limits."""
        limit = getattr(self, limit_name, None)
        if limit is None:
            return True
        if limit == -1:  # Unlimited
            return True
        return current_value <= limit


# ═══════════════════════════════════════════════════════════════════════════
# PLAN CONFIGURATIONS FOR SECURE LICENSES
# ═══════════════════════════════════════════════════════════════════════════

SECURE_PLAN_FEATURES: dict[Plan, set[Feature]] = {
    Plan.FREE: {
        Feature.SCAN,
        Feature.GRAPH_VIEW,
        Feature.CLONE_GENERATE,
        Feature.AUDIT_SCAN,
        Feature.COST_ESTIMATE_BASIC,
        Feature.SINGLE_ACCOUNT,
        Feature.BASIC_TRANSFORM,
        Feature.TERRAFORM_OUTPUT,
    },
    Plan.SOLO: {
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
    },
    Plan.PRO: {
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
    },
    Plan.TEAM: {
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
    },
    Plan.ENTERPRISE: set(Feature),  # All features
}

SECURE_PLAN_LIMITS: dict[Plan, SecureLicenseLimits] = {
    Plan.FREE: SecureLicenseLimits(
        max_accounts=1,
        max_regions=1,
        max_resources_per_scan=100,
        max_concurrent_scans=1,
        max_scans_per_day=5,
        offline_grace_days=0,
    ),
    Plan.SOLO: SecureLicenseLimits(
        max_accounts=3,
        max_regions=5,
        max_resources_per_scan=1000,
        max_concurrent_scans=2,
        max_scans_per_day=50,
        offline_grace_days=7,
    ),
    Plan.PRO: SecureLicenseLimits(
        max_accounts=5,
        max_regions=10,
        max_resources_per_scan=5000,
        max_concurrent_scans=3,
        max_scans_per_day=100,
        offline_grace_days=14,
    ),
    Plan.TEAM: SecureLicenseLimits(
        max_accounts=10,
        max_regions=-1,  # Unlimited
        max_resources_per_scan=-1,
        max_concurrent_scans=5,
        max_scans_per_day=-1,
        offline_grace_days=14,
    ),
    Plan.ENTERPRISE: SecureLicenseLimits(
        max_accounts=-1,
        max_regions=-1,
        max_resources_per_scan=-1,
        max_concurrent_scans=-1,
        max_scans_per_day=-1,
        offline_grace_days=30,
    ),
}


@dataclass
class SecureLicenseData:
    """
    Verified license data.

    This object is ONLY created after successful signature verification.
    All fields come from the signed payload, not user input.
    """

    license_key: str
    plan: Plan
    email: str
    organization: str
    issued_at: datetime
    expires_at: Optional[datetime]
    features: set[Feature]
    limits: SecureLicenseLimits
    nonce: Optional[str] = None
    kid: Optional[str] = None  # Key ID used for signing

    def has_feature(self, feature: Feature) -> bool:
        """Check if license grants a feature."""
        # First check explicit features
        if feature in self.features:
            return True
        # Fall back to plan features
        return feature in SECURE_PLAN_FEATURES.get(self.plan, set())

    def is_expired(self) -> bool:
        """Check if license has expired."""
        if self.expires_at is None:
            return False  # No expiry = never expires
        return datetime.now(UTC) > self.expires_at

    def days_until_expiry(self) -> Optional[int]:
        """Days until license expires, or None if no expiry."""
        if self.expires_at is None:
            return None
        delta = self.expires_at - datetime.now(UTC)
        return max(0, delta.days)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "license_key": self.license_key,
            "plan": self.plan.value,
            "email": self.email,
            "organization": self.organization,
            "issued_at": self.issued_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "features": [f.value for f in self.features],
            "limits": self.limits.to_dict(),
            "nonce": self.nonce,
            "kid": self.kid,
        }

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> SecureLicenseData:
        """
        Create from verified payload.

        ONLY call this after signature verification!
        """
        # Parse plan
        plan_value = payload.get("plan", "free").lower()
        try:
            plan = Plan(plan_value)
        except ValueError:
            plan = Plan.FREE

        # Parse features (explicit + plan default)
        explicit_features: set[Feature] = set()
        for f in payload.get("features", []):
            try:
                explicit_features.add(Feature(f))
            except ValueError:
                pass  # Skip unknown features

        plan_features = SECURE_PLAN_FEATURES.get(plan, set())
        all_features = explicit_features | plan_features

        # Parse limits (explicit or plan default)
        if "limits" in payload:
            limits = SecureLicenseLimits.from_dict(payload["limits"])
        else:
            limits = SECURE_PLAN_LIMITS.get(plan, SecureLicenseLimits())

        # Parse timestamps
        iat = payload.get("iat")
        issued_at = datetime.fromtimestamp(iat, UTC) if iat else datetime.now(UTC)

        exp = payload.get("exp")
        expires_at = datetime.fromtimestamp(exp, UTC) if exp else None

        return cls(
            license_key=payload.get("lic", ""),
            plan=plan,
            email=payload.get("email", ""),
            organization=payload.get("org", ""),
            issued_at=issued_at,
            expires_at=expires_at,
            features=all_features,
            limits=limits,
            nonce=payload.get("nonce"),
            kid=payload.get("kid"),
        )

    def to_legacy_license(self) -> "License":
        """
        Convert to legacy License object for backward compatibility.

        Returns:
            Legacy License object
        """
        from replimap.licensing.models import License

        return License(
            license_key=self.license_key,
            plan=self.plan,
            email=self.email,
            organization=self.organization,
            issued_at=self.issued_at,
            expires_at=self.expires_at,
            machine_fingerprint=None,
            max_machines=1,
            metadata={
                "secure_license": True,
                "kid": self.kid,
                "nonce": self.nonce,
            },
        )


# Type alias for imports
from replimap.licensing.models import License  # noqa: E402
