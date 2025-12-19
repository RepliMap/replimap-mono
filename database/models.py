"""Database models for license and usage tracking."""

import secrets
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import uuid4


def utc_now() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(UTC)


def generate_support_id() -> str:
    """Generate a short support ID for error tracking."""
    return f"ERR-{secrets.token_hex(4).upper()}"


from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    """Base class for all models."""

    pass


class PlanType(str, Enum):
    """License plan types matching pricing tiers."""

    FREE = "free"
    SOLO = "solo"       # $49/mo
    PRO = "pro"         # $99/mo
    TEAM = "team"       # $199/mo
    # Legacy plans for backward compatibility
    STARTER = "starter"
    ENTERPRISE = "enterprise"


class LicenseStatus(str, Enum):
    """License status values."""

    ACTIVE = "active"
    EXPIRED = "expired"
    SUSPENDED = "suspended"
    REVOKED = "revoked"


class SubscriptionStatus(str, Enum):
    """Stripe subscription status values."""

    ACTIVE = "active"
    PAST_DUE = "past_due"
    UNPAID = "unpaid"
    CANCELED = "canceled"
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"
    TRIALING = "trialing"
    PAUSED = "paused"


class Customer(Base):
    """Customer/organization record."""

    __tablename__ = "customers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=True)
    company = Column(String(255), nullable=True)

    # Stripe integration
    stripe_customer_id = Column(String(255), unique=True, nullable=True, index=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    metadata = Column(JSON, default=dict)

    # Relationships
    licenses = relationship("License", back_populates="customer", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Customer {self.email}>"


class License(Base):
    """License record with full subscription lifecycle support."""

    __tablename__ = "licenses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    license_key = Column(String(64), unique=True, nullable=False, index=True)

    # Customer relationship
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    customer = relationship("Customer", back_populates="licenses")

    # Plan and features
    plan = Column(String(32), nullable=False, default=PlanType.FREE.value)
    features = Column(JSON, default=list)  # List of enabled feature names

    # License status
    status = Column(String(32), nullable=False, default=LicenseStatus.ACTIVE.value)
    issued_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)  # None = never expires

    # Subscription lifecycle (Stripe integration)
    stripe_subscription_id = Column(String(255), nullable=True, index=True)
    subscription_status = Column(String(32), nullable=True)  # SubscriptionStatus value
    current_period_start = Column(DateTime(timezone=True), nullable=True)
    current_period_end = Column(DateTime(timezone=True), nullable=True)
    cancel_at_period_end = Column(Boolean, default=False, nullable=False)
    canceled_at = Column(DateTime(timezone=True), nullable=True)
    trial_end = Column(DateTime(timezone=True), nullable=True)

    # Plan limits
    max_activations = Column(Integer, nullable=True)  # None = unlimited
    max_scans_per_month = Column(Integer, nullable=True)
    max_resources_per_scan = Column(Integer, nullable=True)
    max_aws_accounts = Column(Integer, nullable=True)
    max_machine_changes_per_month = Column(Integer, default=3, nullable=False)

    # Metadata
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # Relationships
    activations = relationship(
        "Activation", back_populates="license", cascade="all, delete-orphan"
    )
    usage_records = relationship(
        "UsageRecord", back_populates="license", cascade="all, delete-orphan"
    )
    machine_changes = relationship(
        "MachineChangeLog", back_populates="license", cascade="all, delete-orphan"
    )
    aws_accounts = relationship(
        "AwsAccount", back_populates="license", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_licenses_customer_plan", "customer_id", "plan"),
        Index("ix_licenses_status_expires", "status", "expires_at"),
        Index("ix_licenses_subscription_status", "subscription_status"),
    )

    def __repr__(self) -> str:
        return f"<License {self.license_key[:8]}... ({self.plan})>"

    @property
    def is_valid(self) -> bool:
        """Check if license is currently valid for use."""
        # Check license status
        if self.status not in (LicenseStatus.ACTIVE.value,):
            return False

        # Check subscription status if present
        if self.subscription_status:
            valid_sub_states = (
                SubscriptionStatus.ACTIVE.value,
                SubscriptionStatus.TRIALING.value,
                SubscriptionStatus.PAST_DUE.value,  # Allow grace period
            )
            if self.subscription_status not in valid_sub_states:
                return False

        # Check expiration
        if self.expires_at:
            now = datetime.now(UTC)
            expires_at = self.expires_at
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=UTC)
            if expires_at < now:
                return False

        # Check current_period_end for subscriptions
        if self.current_period_end:
            now = datetime.now(UTC)
            period_end = self.current_period_end
            if period_end.tzinfo is None:
                period_end = period_end.replace(tzinfo=UTC)
            if period_end < now and self.subscription_status != SubscriptionStatus.ACTIVE.value:
                return False

        return True

    @property
    def active_activation_count(self) -> int:
        """
        Get count of active activations.

        WARNING: This property loads all activations into memory.
        For performance-critical code, use the database count query in LicenseService.
        """
        return sum(1 for a in self.activations if a.is_active)


class Activation(Base):
    """Machine activation record."""

    __tablename__ = "activations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # License relationship
    license_id = Column(UUID(as_uuid=True), ForeignKey("licenses.id"), nullable=False)
    license = relationship("License", back_populates="activations")

    # Machine identification
    machine_id = Column(String(255), nullable=False)
    machine_name = Column(String(255), nullable=True)  # Friendly name

    # Activation details
    is_active = Column(Boolean, default=True, nullable=False)
    activated_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    deactivated_at = Column(DateTime(timezone=True), nullable=True)
    last_seen_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Client information
    client_version = Column(String(32), nullable=True)
    client_os = Column(String(64), nullable=True)
    client_ip = Column(String(45), nullable=True)  # IPv4 or IPv6

    __table_args__ = (
        UniqueConstraint("license_id", "machine_id", name="uq_activation_license_machine"),
        Index("ix_activations_machine", "machine_id"),
        Index("ix_activations_active", "license_id", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<Activation {self.machine_id[:8]}... ({self.license_id})>"


class MachineChangeLog(Base):
    """Tracks machine activation changes for rate limiting."""

    __tablename__ = "machine_change_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # License relationship
    license_id = Column(UUID(as_uuid=True), ForeignKey("licenses.id"), nullable=False)
    license = relationship("License", back_populates="machine_changes")

    # Change details
    machine_id = Column(String(255), nullable=False)
    change_type = Column(String(32), nullable=False)  # "activated", "deactivated", "replaced"
    previous_machine_id = Column(String(255), nullable=True)  # For replacements

    # Period tracking (YYYY-MM format)
    period = Column(String(7), nullable=False)

    # Metadata
    client_ip = Column(String(45), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    __table_args__ = (
        Index("ix_machine_changes_license_period", "license_id", "period"),
    )

    def __repr__(self) -> str:
        return f"<MachineChangeLog {self.change_type} {self.machine_id[:8]}...>"


class AwsAccount(Base):
    """Tracks AWS accounts linked to a license."""

    __tablename__ = "aws_accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # License relationship
    license_id = Column(UUID(as_uuid=True), ForeignKey("licenses.id"), nullable=False)
    license = relationship("License", back_populates="aws_accounts")

    # AWS account details
    aws_account_id = Column(String(12), nullable=False)  # AWS account IDs are 12 digits
    account_alias = Column(String(255), nullable=True)  # Friendly name

    # Metadata
    is_active = Column(Boolean, default=True, nullable=False)
    first_seen_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    last_seen_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    __table_args__ = (
        UniqueConstraint("license_id", "aws_account_id", name="uq_aws_account_license"),
        Index("ix_aws_accounts_account_id", "aws_account_id"),
    )

    def __repr__(self) -> str:
        return f"<AwsAccount {self.aws_account_id}>"


class ProcessedEvent(Base):
    """Tracks processed webhook events for idempotency."""

    __tablename__ = "processed_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Event identification
    event_id = Column(String(255), unique=True, nullable=False, index=True)
    event_type = Column(String(64), nullable=False)
    source = Column(String(32), nullable=False)  # "stripe", "api", etc.

    # Processing details
    processed_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    idempotency_key = Column(String(255), nullable=True, index=True)

    # Result tracking
    success = Column(Boolean, default=True, nullable=False)
    error_message = Column(Text, nullable=True)
    result_data = Column(JSON, default=dict)

    # Related entities
    license_id = Column(UUID(as_uuid=True), nullable=True)
    customer_id = Column(UUID(as_uuid=True), nullable=True)

    __table_args__ = (
        Index("ix_processed_events_type_created", "event_type", "processed_at"),
    )

    def __repr__(self) -> str:
        return f"<ProcessedEvent {self.event_id} ({self.event_type})>"


class UsageRecord(Base):
    """Usage tracking record (per license, per period)."""

    __tablename__ = "usage_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # License relationship
    license_id = Column(UUID(as_uuid=True), ForeignKey("licenses.id"), nullable=False)
    license = relationship("License", back_populates="usage_records")

    # Period (YYYY-MM format for monthly tracking)
    period = Column(String(7), nullable=False)  # e.g., "2025-01"

    # Usage counters
    scans_count = Column(Integer, default=0, nullable=False)
    resources_scanned = Column(Integer, default=0, nullable=False)
    terraform_generations = Column(Integer, default=0, nullable=False)

    # Timestamps
    first_usage_at = Column(DateTime(timezone=True), nullable=True)
    last_usage_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # Raw usage data (for detailed analytics)
    usage_details = Column(JSON, default=list)

    __table_args__ = (
        UniqueConstraint("license_id", "period", name="uq_usage_license_period"),
        Index("ix_usage_period", "period"),
        Index("ix_usage_license_period", "license_id", "period"),
    )

    def __repr__(self) -> str:
        return f"<UsageRecord {self.license_id} {self.period}>"


class AuditLog(Base):
    """Audit log for tracking important events."""

    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Event details
    event_type = Column(String(64), nullable=False, index=True)
    event_data = Column(JSON, default=dict)

    # Support ID for customer service
    support_id = Column(String(32), default=generate_support_id, nullable=False, index=True)

    # Actor (who triggered the event)
    actor_type = Column(String(32), nullable=True)  # "user", "system", "api", "stripe"
    actor_id = Column(String(255), nullable=True)

    # Related entities
    license_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    customer_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    # Metadata
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(512), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    __table_args__ = (Index("ix_audit_event_created", "event_type", "created_at"),)

    def __repr__(self) -> str:
        return f"<AuditLog {self.event_type} at {self.created_at}>"


# Plan configurations with limits matching pricing page
PLAN_LIMITS = {
    PlanType.FREE.value: {
        "max_resources_per_scan": 5,
        "max_scans_per_month": 3,
        "max_aws_accounts": 1,
        "max_activations": 1,
        "max_machine_changes_per_month": 3,
        "features": [],
        "export_formats": ["terraform"],
    },
    PlanType.SOLO.value: {
        "max_resources_per_scan": None,  # Unlimited
        "max_scans_per_month": None,  # Unlimited
        "max_aws_accounts": 1,
        "max_activations": 2,
        "max_machine_changes_per_month": 3,
        "features": ["unlimited_resources", "unlimited_scans"],
        "export_formats": ["terraform"],
    },
    PlanType.PRO.value: {
        "max_resources_per_scan": None,
        "max_scans_per_month": None,
        "max_aws_accounts": 3,
        "max_activations": 3,
        "max_machine_changes_per_month": 3,
        "features": ["unlimited_resources", "unlimited_scans", "multi_account"],
        "export_formats": ["terraform"],
    },
    PlanType.TEAM.value: {
        "max_resources_per_scan": None,
        "max_scans_per_month": None,
        "max_aws_accounts": 10,
        "max_activations": 10,
        "max_machine_changes_per_month": 3,
        "features": ["unlimited_resources", "unlimited_scans", "multi_account", "team"],
        "export_formats": ["terraform"],
    },
    # Legacy plan mappings
    PlanType.STARTER.value: {
        "max_resources_per_scan": 200,
        "max_scans_per_month": 100,
        "max_aws_accounts": 1,
        "max_activations": 2,
        "max_machine_changes_per_month": 3,
        "features": ["export_formats"],
        "export_formats": ["terraform"],
    },
    PlanType.ENTERPRISE.value: {
        "max_resources_per_scan": None,
        "max_scans_per_month": None,
        "max_aws_accounts": None,  # Unlimited
        "max_activations": None,  # Unlimited
        "max_machine_changes_per_month": None,  # Unlimited
        "features": ["unlimited_resources", "unlimited_scans", "multi_account", "team", "sso", "audit_logs", "api_access"],
        "export_formats": ["terraform"],
    },
}
