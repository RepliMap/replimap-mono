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
    """Available features that can be gated by plan."""

    # Core scanning
    BASIC_SCAN = "basic_scan"
    UNLIMITED_RESOURCES = "unlimited_resources"
    ASYNC_SCANNING = "async_scanning"

    # Multi-account support
    SINGLE_ACCOUNT = "single_account"
    MULTI_ACCOUNT = "multi_account"
    UNLIMITED_ACCOUNTS = "unlimited_accounts"

    # Transformation features
    BASIC_TRANSFORM = "basic_transform"
    ADVANCED_TRANSFORM = "advanced_transform"
    CUSTOM_TEMPLATES = "custom_templates"

    # Output features
    TERRAFORM_OUTPUT = "terraform_output"
    PULUMI_OUTPUT = "pulumi_output"
    CDK_OUTPUT = "cdk_output"

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


@dataclass
class PlanFeatures:
    """Feature configuration for a plan tier."""

    plan: Plan
    price_monthly: int  # USD
    max_resources_per_scan: int | None  # None = unlimited
    max_scans_per_month: int | None  # None = unlimited
    max_aws_accounts: int | None  # None = unlimited
    features: set[Feature] = field(default_factory=set)

    def has_feature(self, feature: Feature) -> bool:
        """Check if this plan includes a feature."""
        return feature in self.features

    def can_scan_resources(self, count: int) -> bool:
        """Check if the plan allows scanning this many resources."""
        if self.max_resources_per_scan is None:
            return True
        return count <= self.max_resources_per_scan

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "plan": str(self.plan),
            "price_monthly": self.price_monthly,
            "max_resources_per_scan": self.max_resources_per_scan,
            "max_scans_per_month": self.max_scans_per_month,
            "max_aws_accounts": self.max_aws_accounts,
            "features": [str(f) for f in self.features],
        }


# Plan feature configurations
PLAN_FEATURES: dict[Plan, PlanFeatures] = {
    Plan.FREE: PlanFeatures(
        plan=Plan.FREE,
        price_monthly=0,
        max_resources_per_scan=5,
        max_scans_per_month=3,
        max_aws_accounts=1,
        features={
            Feature.BASIC_SCAN,
            Feature.SINGLE_ACCOUNT,
            Feature.BASIC_TRANSFORM,
            Feature.TERRAFORM_OUTPUT,
        },
    ),
    Plan.SOLO: PlanFeatures(
        plan=Plan.SOLO,
        price_monthly=49,
        max_resources_per_scan=None,  # Unlimited
        max_scans_per_month=None,  # Unlimited
        max_aws_accounts=1,
        features={
            Feature.BASIC_SCAN,
            Feature.UNLIMITED_RESOURCES,
            Feature.ASYNC_SCANNING,
            Feature.SINGLE_ACCOUNT,
            Feature.BASIC_TRANSFORM,
            Feature.ADVANCED_TRANSFORM,
            Feature.TERRAFORM_OUTPUT,
        },
    ),
    Plan.PRO: PlanFeatures(
        plan=Plan.PRO,
        price_monthly=99,
        max_resources_per_scan=None,
        max_scans_per_month=None,
        max_aws_accounts=3,
        features={
            Feature.BASIC_SCAN,
            Feature.UNLIMITED_RESOURCES,
            Feature.ASYNC_SCANNING,
            Feature.MULTI_ACCOUNT,
            Feature.BASIC_TRANSFORM,
            Feature.ADVANCED_TRANSFORM,
            Feature.CUSTOM_TEMPLATES,
            Feature.TERRAFORM_OUTPUT,
            Feature.PULUMI_OUTPUT,
            Feature.WEB_DASHBOARD,
        },
    ),
    Plan.TEAM: PlanFeatures(
        plan=Plan.TEAM,
        price_monthly=199,
        max_resources_per_scan=None,
        max_scans_per_month=None,
        max_aws_accounts=10,
        features={
            Feature.BASIC_SCAN,
            Feature.UNLIMITED_RESOURCES,
            Feature.ASYNC_SCANNING,
            Feature.MULTI_ACCOUNT,
            Feature.BASIC_TRANSFORM,
            Feature.ADVANCED_TRANSFORM,
            Feature.CUSTOM_TEMPLATES,
            Feature.TERRAFORM_OUTPUT,
            Feature.PULUMI_OUTPUT,
            Feature.CDK_OUTPUT,
            Feature.WEB_DASHBOARD,
            Feature.COLLABORATION,
            Feature.SHARED_GRAPHS,
        },
    ),
    Plan.ENTERPRISE: PlanFeatures(
        plan=Plan.ENTERPRISE,
        price_monthly=499,  # Starting price
        max_resources_per_scan=None,
        max_scans_per_month=None,
        max_aws_accounts=None,  # Unlimited
        features={
            Feature.BASIC_SCAN,
            Feature.UNLIMITED_RESOURCES,
            Feature.ASYNC_SCANNING,
            Feature.UNLIMITED_ACCOUNTS,
            Feature.BASIC_TRANSFORM,
            Feature.ADVANCED_TRANSFORM,
            Feature.CUSTOM_TEMPLATES,
            Feature.TERRAFORM_OUTPUT,
            Feature.PULUMI_OUTPUT,
            Feature.CDK_OUTPUT,
            Feature.WEB_DASHBOARD,
            Feature.COLLABORATION,
            Feature.SHARED_GRAPHS,
            Feature.SSO,
            Feature.AUDIT_LOGS,
            Feature.PRIORITY_SUPPORT,
            Feature.SLA_GUARANTEE,
            Feature.CUSTOM_INTEGRATIONS,
        },
    ),
}


def get_plan_features(plan: Plan) -> PlanFeatures:
    """Get the feature configuration for a plan."""
    return PLAN_FEATURES[plan]


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
        if mac != uuid.getnode():  # Check for random MAC
            components.append(str(mac))
    except OSError:
        # MAC address not available on this platform
        pass

    fingerprint_string = "|".join(components)
    return hashlib.sha256(fingerprint_string.encode()).hexdigest()[:32]
