"""Initial schema with all tables.

Revision ID: 001
Revises:
Create Date: 2025-12-19

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create customers table
    op.create_table(
        "customers",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("company", sa.String(255), nullable=True),
        sa.Column("stripe_customer_id", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", postgresql.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("stripe_customer_id"),
    )
    op.create_index("ix_customers_email", "customers", ["email"])
    op.create_index("ix_customers_stripe_customer_id", "customers", ["stripe_customer_id"])

    # Create licenses table
    op.create_table(
        "licenses",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("license_key", sa.String(64), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("plan", sa.String(32), nullable=False),
        sa.Column("features", postgresql.JSON(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("max_activations", sa.Integer(), nullable=True),
        sa.Column("max_scans_per_month", sa.Integer(), nullable=True),
        sa.Column("max_resources_per_scan", sa.Integer(), nullable=True),
        sa.Column("stripe_subscription_id", sa.String(255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("license_key"),
    )
    op.create_index("ix_licenses_license_key", "licenses", ["license_key"])
    op.create_index("ix_licenses_customer_plan", "licenses", ["customer_id", "plan"])
    op.create_index("ix_licenses_status_expires", "licenses", ["status", "expires_at"])
    op.create_index("ix_licenses_stripe_subscription_id", "licenses", ["stripe_subscription_id"])

    # Create activations table
    op.create_table(
        "activations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("license_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("machine_id", sa.String(255), nullable=False),
        sa.Column("machine_name", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deactivated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("client_version", sa.String(32), nullable=True),
        sa.Column("client_os", sa.String(64), nullable=True),
        sa.Column("client_ip", sa.String(45), nullable=True),
        sa.ForeignKeyConstraint(["license_id"], ["licenses.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("license_id", "machine_id", name="uq_activation_license_machine"),
    )
    op.create_index("ix_activations_machine", "activations", ["machine_id"])
    op.create_index("ix_activations_active", "activations", ["license_id", "is_active"])

    # Create usage_records table
    op.create_table(
        "usage_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("license_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("period", sa.String(7), nullable=False),
        sa.Column("scans_count", sa.Integer(), nullable=False, default=0),
        sa.Column("resources_scanned", sa.Integer(), nullable=False, default=0),
        sa.Column("terraform_generations", sa.Integer(), nullable=False, default=0),
        sa.Column("first_usage_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_usage_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("usage_details", postgresql.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["license_id"], ["licenses.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("license_id", "period", name="uq_usage_license_period"),
    )
    op.create_index("ix_usage_period", "usage_records", ["period"])
    op.create_index("ix_usage_license_period", "usage_records", ["license_id", "period"])

    # Create audit_logs table
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("event_data", postgresql.JSON(), nullable=True),
        sa.Column("actor_type", sa.String(32), nullable=True),
        sa.Column("actor_id", sa.String(255), nullable=True),
        sa.Column("license_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_logs_event_type", "audit_logs", ["event_type"])
    op.create_index("ix_audit_logs_license_id", "audit_logs", ["license_id"])
    op.create_index("ix_audit_logs_customer_id", "audit_logs", ["customer_id"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])
    op.create_index("ix_audit_event_created", "audit_logs", ["event_type", "created_at"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("usage_records")
    op.drop_table("activations")
    op.drop_table("licenses")
    op.drop_table("customers")
