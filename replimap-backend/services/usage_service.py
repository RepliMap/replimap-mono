"""Usage tracking and quota management service."""

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import AuditLog, License, UsageRecord

from .license_service import PLAN_FEATURES


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
            period = datetime.utcnow().strftime("%Y-%m")

        # Find or create usage record for this period
        result = await self.db.execute(
            select(UsageRecord).where(
                UsageRecord.license_id == license_record.id,
                UsageRecord.period == period,
            )
        )
        usage_record = result.scalar_one_or_none()

        if not usage_record:
            usage_record = UsageRecord(
                license_id=license_record.id,
                period=period,
                first_usage_at=datetime.utcnow(),
            )
            self.db.add(usage_record)

        # Update counters (additive)
        usage_record.scans_count += usage_data.get("scans_count", 0)
        usage_record.resources_scanned += usage_data.get("resources_scanned", 0)
        usage_record.terraform_generations += usage_data.get("terraform_generations", 0)
        usage_record.last_usage_at = datetime.utcnow()

        # Append to usage details for detailed tracking
        if usage_record.usage_details is None:
            usage_record.usage_details = []
        usage_record.usage_details.append({
            "timestamp": datetime.utcnow().isoformat(),
            "machine_id": machine_id,
            "data": usage_data,
        })

        await self.db.commit()

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
            period = datetime.utcnow().strftime("%Y-%m")

        # Get usage record
        result = await self.db.execute(
            select(UsageRecord).where(
                UsageRecord.license_id == license_record.id,
                UsageRecord.period == period,
            )
        )
        usage_record = result.scalar_one_or_none()

        if not usage_record:
            usage_record = UsageRecord(
                license_id=license_record.id,
                period=period,
            )

        quotas = await self._calculate_quotas(license_record, usage_record)

        return {
            "period": period,
            "usage": {
                "scans_count": usage_record.scans_count,
                "resources_scanned": usage_record.resources_scanned,
                "terraform_generations": usage_record.terraform_generations,
            },
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
            operation: Operation type (scans, resources, etc.)
            amount: Amount to check

        Returns:
            Whether operation is allowed and quota info
        """
        result = await self.db.execute(
            select(License).where(License.license_key == license_key)
        )
        license_record = result.scalar_one_or_none()

        if not license_record:
            return {"allowed": False, "error": "invalid_license"}

        period = datetime.utcnow().strftime("%Y-%m")

        result = await self.db.execute(
            select(UsageRecord).where(
                UsageRecord.license_id == license_record.id,
                UsageRecord.period == period,
            )
        )
        usage_record = result.scalar_one_or_none()

        current_usage = 0
        limit = None

        if operation == "scans":
            current_usage = usage_record.scans_count if usage_record else 0
            limit = license_record.max_scans_per_month
        elif operation == "resources":
            limit = license_record.max_resources_per_scan

        if limit is None:
            # Unlimited
            return {
                "allowed": True,
                "unlimited": True,
            }

        remaining = limit - current_usage
        allowed = remaining >= amount

        return {
            "allowed": allowed,
            "current": current_usage,
            "limit": limit,
            "remaining": max(0, remaining),
            "requested": amount,
        }

    async def _calculate_quotas(
        self,
        license_record: License,
        usage_record: UsageRecord,
    ) -> dict[str, Any]:
        """Calculate remaining quotas for a license."""
        plan_config = PLAN_FEATURES.get(license_record.plan, PLAN_FEATURES["free"])

        max_scans = license_record.max_scans_per_month or plan_config.get("max_scans_per_month")
        max_resources = license_record.max_resources_per_scan or plan_config.get(
            "max_resources_per_scan"
        )

        return {
            "scans_remaining": (max_scans - usage_record.scans_count) if max_scans else None,
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
