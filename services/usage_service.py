"""Usage tracking and quota management service."""

import re
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from database.models import AuditLog, License, UsageRecord

from .license_service import PLAN_FEATURES

# Maximum number of usage detail entries to keep per record (prevent unbounded growth)
MAX_USAGE_DETAILS_ENTRIES = 1000

# Valid period format pattern
PERIOD_PATTERN = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


class UsageService:
    """Service for usage tracking and quota management."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def sync_usage(
        self,
        license_key: str,
        machine_id: str,
        usage_data: dict[str, int],
        period: str | None = None,
    ) -> dict[str, Any]:
        """
        Sync usage data from a client.

        Args:
            license_key: The license key
            machine_id: The machine identifier
            usage_data: Usage counters to sync
            period: Period string (YYYY-MM), defaults to current month

        Returns:
            Sync result with updated quotas
        """
        # Get license
        result = await self.db.execute(
            select(License).where(License.license_key == license_key)
        )
        license_record = result.scalar_one_or_none()

        if not license_record:
            return {
                "synced": False,
                "error": "invalid_license",
            }

        # Default to current month
        if period is None:
            period = datetime.now(UTC).strftime("%Y-%m")
        elif not PERIOD_PATTERN.match(period):
            return {
                "synced": False,
                "error": "invalid_period",
                "message": "Period must be in YYYY-MM format",
            }

        # Validate usage data values are non-negative
        scans_delta = usage_data.get("scans_count", 0)
        resources_delta = usage_data.get("resources_scanned", 0)
        terraform_delta = usage_data.get("terraform_generations", 0)

        if any(v < 0 for v in [scans_delta, resources_delta, terraform_delta]):
            return {
                "synced": False,
                "error": "invalid_usage_data",
                "message": "Usage values cannot be negative",
            }

        # Find or create usage record for this period
        result = await self.db.execute(
            select(UsageRecord)
            .where(
                UsageRecord.license_id == license_record.id,
                UsageRecord.period == period,
            )
            .with_for_update()  # Lock row to prevent race conditions
        )
        usage_record = result.scalar_one_or_none()

        now = datetime.now(UTC)

        if not usage_record:
            usage_record = UsageRecord(
                license_id=license_record.id,
                period=period,
                first_usage_at=now,
                scans_count=scans_delta,
                resources_scanned=resources_delta,
                terraform_generations=terraform_delta,
                last_usage_at=now,
                usage_details=[{
                    "timestamp": now.isoformat(),
                    "machine_id": machine_id,
                    "data": usage_data,
                }],
            )
            self.db.add(usage_record)
        else:
            # Use atomic database-level increment to prevent race conditions
            await self.db.execute(
                update(UsageRecord)
                .where(UsageRecord.id == usage_record.id)
                .values(
                    scans_count=UsageRecord.scans_count + scans_delta,
                    resources_scanned=UsageRecord.resources_scanned + resources_delta,
                    terraform_generations=UsageRecord.terraform_generations + terraform_delta,
                    last_usage_at=now,
                )
            )

            # Refresh to get updated values
            await self.db.refresh(usage_record)

            # Update usage details with retention policy
            details = usage_record.usage_details or []
            details.append({
                "timestamp": now.isoformat(),
                "machine_id": machine_id,
                "data": usage_data,
            })

            # Apply retention policy - keep only most recent entries
            if len(details) > MAX_USAGE_DETAILS_ENTRIES:
                details = details[-MAX_USAGE_DETAILS_ENTRIES:]

            usage_record.usage_details = details
            flag_modified(usage_record, "usage_details")

        await self.db.commit()

        # Refresh to get final values after commit
        await self.db.refresh(usage_record)

        # Calculate remaining quotas
        quotas = await self._calculate_quotas(license_record, usage_record)

        await self._log_event(
            "usage_synced",
            {
                "period": period,
                "machine_id": machine_id,
                "usage": usage_data,
            },
            license_id=license_record.id,
        )

        return {
            "synced": True,
            "period": period,
            "current_usage": {
                "scans_count": usage_record.scans_count,
                "resources_scanned": usage_record.resources_scanned,
                "terraform_generations": usage_record.terraform_generations,
            },
            "quotas": quotas,
        }

    async def get_usage(
        self,
        license_key: str,
        period: str | None = None,
    ) -> dict[str, Any]:
        """Get usage data for a license."""
        # Get license
        result = await self.db.execute(
            select(License).where(License.license_key == license_key)
        )
        license_record = result.scalar_one_or_none()

        if not license_record:
            return {"error": "invalid_license"}

        # Default to current month
        if period is None:
            period = datetime.now(UTC).strftime("%Y-%m")
        elif not PERIOD_PATTERN.match(period):
            return {"error": "invalid_period", "message": "Period must be in YYYY-MM format"}

        # Get usage record
        result = await self.db.execute(
            select(UsageRecord).where(
                UsageRecord.license_id == license_record.id,
                UsageRecord.period == period,
            )
        )
        usage_record = result.scalar_one_or_none()

        # Return zero usage if no record exists (don't create transient object)
        usage = {
            "scans_count": 0,
            "resources_scanned": 0,
            "terraform_generations": 0,
        }
        if usage_record:
            usage = {
                "scans_count": usage_record.scans_count,
                "resources_scanned": usage_record.resources_scanned,
                "terraform_generations": usage_record.terraform_generations,
            }

        # Calculate quotas based on actual or zero usage
        quotas = await self._calculate_quotas_from_values(license_record, usage)

        return {
            "period": period,
            "usage": usage,
            "quotas": quotas,
            "limits": {
                "max_scans_per_month": license_record.max_scans_per_month,
                "max_resources_per_scan": license_record.max_resources_per_scan,
            },
        }

    async def get_usage_history(
        self,
        license_key: str,
        months: int = 6,
    ) -> dict[str, Any]:
        """Get usage history for a license."""
        # Validate months parameter (prevent resource exhaustion)
        if months < 1:
            months = 1
        elif months > 24:
            months = 24  # Cap at 2 years of history

        result = await self.db.execute(
            select(License).where(License.license_key == license_key)
        )
        license_record = result.scalar_one_or_none()

        if not license_record:
            return {"error": "invalid_license"}

        # Get all usage records for this license, ordered by period
        result = await self.db.execute(
            select(UsageRecord)
            .where(UsageRecord.license_id == license_record.id)
            .order_by(UsageRecord.period.desc())
            .limit(months)
        )
        records = result.scalars().all()

        history = []
        for record in records:
            history.append({
                "period": record.period,
                "scans_count": record.scans_count,
                "resources_scanned": record.resources_scanned,
                "terraform_generations": record.terraform_generations,
                "first_usage_at": record.first_usage_at.isoformat() if record.first_usage_at else None,
                "last_usage_at": record.last_usage_at.isoformat() if record.last_usage_at else None,
            })

        return {
            "license_key": license_key[:8] + "...",
            "plan": license_record.plan,
            "history": history,
        }

    async def check_quota(
        self,
        license_key: str,
        operation: str,
        amount: int = 1,
    ) -> dict[str, Any]:
        """
        Check if an operation is allowed within quota.

        Args:
            license_key: The license key
            operation: Operation type (scans, resources)
            amount: Amount to check

        Returns:
            Whether operation is allowed and quota info
        """
        # Validate operation type
        valid_operations = {"scans", "resources"}
        if operation not in valid_operations:
            return {
                "allowed": False,
                "error": "invalid_operation",
                "message": f"Operation must be one of: {', '.join(valid_operations)}",
            }

        # Validate amount
        if amount < 1:
            return {
                "allowed": False,
                "error": "invalid_amount",
                "message": "Amount must be at least 1",
            }

        result = await self.db.execute(
            select(License).where(License.license_key == license_key)
        )
        license_record = result.scalar_one_or_none()

        if not license_record:
            return {"allowed": False, "error": "invalid_license"}

        if operation == "scans":
            # Scans quota is cumulative per month
            period = datetime.now(UTC).strftime("%Y-%m")
            result = await self.db.execute(
                select(UsageRecord).where(
                    UsageRecord.license_id == license_record.id,
                    UsageRecord.period == period,
                )
            )
            usage_record = result.scalar_one_or_none()
            current_usage = usage_record.scans_count if usage_record else 0
            limit = license_record.max_scans_per_month

            if limit is None:
                return {"allowed": True, "unlimited": True}

            remaining = limit - current_usage
            allowed = remaining >= amount

            return {
                "allowed": allowed,
                "unlimited": False,
                "current": current_usage,
                "limit": limit,
                "remaining": max(0, remaining),
                "requested": amount,
            }

        elif operation == "resources":
            # Resources limit is per-scan (not cumulative)
            # Check if the requested amount exceeds the per-scan limit
            limit = license_record.max_resources_per_scan

            if limit is None:
                return {"allowed": True, "unlimited": True}

            allowed = amount <= limit

            return {
                "allowed": allowed,
                "unlimited": False,
                "current": 0,  # Not tracked cumulatively
                "limit": limit,
                "remaining": limit,  # Full limit available per scan
                "requested": amount,
            }

        # Should not reach here due to validation above
        return {"allowed": False, "error": "unknown_operation"}

    async def _calculate_quotas(
        self,
        license_record: License,
        usage_record: UsageRecord,
    ) -> dict[str, Any]:
        """Calculate remaining quotas for a license from a UsageRecord."""
        usage = {
            "scans_count": usage_record.scans_count,
            "resources_scanned": usage_record.resources_scanned,
            "terraform_generations": usage_record.terraform_generations,
        }
        return await self._calculate_quotas_from_values(license_record, usage)

    async def _calculate_quotas_from_values(
        self,
        license_record: License,
        usage: dict[str, int],
    ) -> dict[str, Any]:
        """Calculate remaining quotas for a license from usage values."""
        plan_config = PLAN_FEATURES.get(license_record.plan, PLAN_FEATURES["free"])

        max_scans = license_record.max_scans_per_month or plan_config.get("max_scans_per_month")
        max_resources = license_record.max_resources_per_scan or plan_config.get(
            "max_resources_per_scan"
        )

        scans_used = usage.get("scans_count", 0)
        scans_remaining = None
        if max_scans is not None:
            scans_remaining = max(0, max_scans - scans_used)

        return {
            "scans_remaining": scans_remaining,
            "resources_per_scan": max_resources,
        }

    async def _log_event(
        self,
        event_type: str,
        event_data: dict[str, Any],
        license_id: Any = None,
    ) -> None:
        """Log an audit event."""
        log = AuditLog(
            event_type=event_type,
            event_data=event_data,
            license_id=license_id,
            actor_type="api",
        )
        self.db.add(log)
        # Commit the log immediately to ensure it's persisted
        await self.db.commit()
