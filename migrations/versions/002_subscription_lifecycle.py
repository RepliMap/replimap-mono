"""Add subscription lifecycle tables and columns.

Revision ID: 002
Revises: 001
Create Date: 2025-12-19

Adds:
- Subscription lifecycle columns to licenses table
- machine_change_logs table for tracking machine changes (3/month limit)
- aws_accounts table for tracking AWS accounts per license
- processed_events table for webhook idempotency
- support_id column to audit_logs table
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add subscription lifecycle columns to licenses table
    op.add_column(
        "licenses",
        sa.Column("subscription_status", sa.String(32), nullable=True),
    )
    op.add_column(
        "licenses",
        sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "licenses",
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "licenses",
        sa.Column("cancel_at_period_end", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "licenses",
        sa.Column("canceled_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "licenses",
        sa.Column("trial_end", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "licenses",
        sa.Column("max_aws_accounts", sa.Integer(), nullable=True),
    )
    op.add_column(
        "licenses",
        sa.Column("max_machine_changes_per_month", sa.Integer(), nullable=False, server_default="3"),
    )
    op.create_index(
        "ix_licenses_subscription_status",
        "licenses",
        ["subscription_status"],
    )

    # Create machine_change_logs table
    op.create_table(
        "machine_change_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("license_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("machine_id", sa.String(255), nullable=False),
        sa.Column("change_type", sa.String(32), nullable=False),
        sa.Column("previous_machine_id", sa.String(255), nullable=True),
        sa.Column("period", sa.String(7), nullable=False),
        sa.Column("client_ip", sa.String(45), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["license_id"], ["licenses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_machine_changes_license_period",
        "machine_change_logs",
        ["license_id", "period"],
    )

    # Create aws_accounts table
    op.create_table(
        "aws_accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("license_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("aws_account_id", sa.String(12), nullable=False),
        sa.Column("account_alias", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["license_id"], ["licenses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("license_id", "aws_account_id", name="uq_aws_account_license"),
    )
    op.create_index(
        "ix_aws_accounts_account_id",
        "aws_accounts",
        ["aws_account_id"],
    )

    # Create processed_events table for webhook idempotency
    op.create_table(
        "processed_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_id", sa.String(255), nullable=False),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("source", sa.String(32), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("idempotency_key", sa.String(255), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=False, default=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("result_data", postgresql.JSON(), nullable=True),
        sa.Column("license_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id"),
    )
    op.create_index(
        "ix_processed_events_event_id",
        "processed_events",
        ["event_id"],
    )
    op.create_index(
        "ix_processed_events_idempotency_key",
        "processed_events",
        ["idempotency_key"],
    )
    op.create_index(
        "ix_processed_events_type_created",
        "processed_events",
        ["event_type", "processed_at"],
    )

    # Add support_id column to audit_logs
    op.add_column(
        "audit_logs",
        sa.Column("support_id", sa.String(32), nullable=True),
    )
    op.create_index(
        "ix_audit_logs_support_id",
        "audit_logs",
        ["support_id"],
    )


def downgrade() -> None:
    # Remove support_id from audit_logs
    op.drop_index("ix_audit_logs_support_id", table_name="audit_logs")
    op.drop_column("audit_logs", "support_id")

    # Drop processed_events table
    op.drop_table("processed_events")

    # Drop aws_accounts table
    op.drop_table("aws_accounts")

    # Drop machine_change_logs table
    op.drop_table("machine_change_logs")

    # Remove subscription lifecycle columns from licenses
    op.drop_index("ix_licenses_subscription_status", table_name="licenses")
    op.drop_column("licenses", "max_machine_changes_per_month")
    op.drop_column("licenses", "max_aws_accounts")
    op.drop_column("licenses", "trial_end")
    op.drop_column("licenses", "canceled_at")
    op.drop_column("licenses", "cancel_at_period_end")
    op.drop_column("licenses", "current_period_end")
    op.drop_column("licenses", "current_period_start")
    op.drop_column("licenses", "subscription_status")
