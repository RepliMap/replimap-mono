"""Database models for license and usage tracking."""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

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
    """License plan types."""

    FREE = "free"
    STARTER = "starter"
    TEAM = "team"
    ENTERPRISE = "enterprise"


class LicenseStatus(str, Enum):
    """License status values."""

    ACTIVE = "active"
    EXPIRED = "expired"
    SUSPENDED = "suspended"
    REVOKED = "revoked"


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
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    metadata = Column(JSON, default=dict)

    # Relationships
    licenses = relationship("License", back_populates="customer", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Customer {self.email}>"


class License(Base):
    """License record."""

    __tablename__ = "licenses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    license_key = Column(String(64), unique=True, nullable=False, index=True)

    # Customer relationship
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    customer = relationship("Customer", back_populates="licenses")

    # Plan and features
    plan = Column(String(32), nullable=False, default=PlanType.FREE.value)
    features = Column(JSON, default=list)  # List of enabled feature names

    # Status and validity
    status = Column(String(32), nullable=False, default=LicenseStatus.ACTIVE.value)
    issued_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)  # None = never expires

    # Activation limits
    max_activations = Column(Integer, nullable=True)  # None = unlimited

    # Usage limits (per period)
    max_scans_per_month = Column(Integer, nullable=True)
    max_resources_per_scan = Column(Integer, nullable=True)

    # Stripe integration
    stripe_subscription_id = Column(String(255), nullable=True, index=True)

    # Metadata
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    activations = relationship(
        "Activation", back_populates="license", cascade="all, delete-orphan"
    )
    usage_records = relationship(
        "UsageRecord", back_populates="license", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_licenses_customer_plan", "customer_id", "plan"),
        Index("ix_licenses_status_expires", "status", "expires_at"),
    )

    def __repr__(self) -> str:
        return f"<License {self.license_key[:8]}... ({self.plan})>"

    @property
    def is_valid(self) -> bool:
        """Check if license is currently valid."""
        if self.status != LicenseStatus.ACTIVE.value:
            return False
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        return True

    @property
    def active_activation_count(self) -> int:
        """Get count of active activations."""
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
    activated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    deactivated_at = Column(DateTime, nullable=True)
    last_seen_at = Column(DateTime, default=datetime.utcnow, nullable=False)

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
    first_usage_at = Column(DateTime, nullable=True)
    last_usage_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

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

    # Actor (who triggered the event)
    actor_type = Column(String(32), nullable=True)  # "user", "system", "api"
    actor_id = Column(String(255), nullable=True)

    # Related entities
    license_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    customer_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    # Metadata
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    __table_args__ = (Index("ix_audit_event_created", "event_type", "created_at"),)

    def __repr__(self) -> str:
        return f"<AuditLog {self.event_type} at {self.created_at}>"
