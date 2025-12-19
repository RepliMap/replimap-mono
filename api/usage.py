"""Usage tracking API endpoints."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from services import UsageService

router = APIRouter()


class SyncUsageRequest(BaseModel):
    """Request to sync usage data."""

    license_key: str = Field(..., description="The license key")
    machine_id: str = Field(..., description="Machine identifier")
    usage: dict[str, int] = Field(
        ...,
        description="Usage counters (scans_count, resources_scanned, terraform_generations)",
    )
    period: str | None = Field(None, description="Period (YYYY-MM), defaults to current month")
    idempotency_key: str | None = Field(
        None,
        description="Optional idempotency key to prevent duplicate processing",
        max_length=255,
    )


class SyncUsageResponse(BaseModel):
    """Response from usage sync."""

    synced: bool
    error: str | None = None
    period: str | None = None
    current_usage: dict[str, int] | None = None
    quotas: dict[str, Any] | None = None


class UsageResponse(BaseModel):
    """Usage data response."""

    period: str
    usage: dict[str, int]
    quotas: dict[str, Any]
    limits: dict[str, Any]


class QuotaCheckRequest(BaseModel):
    """Request to check quota availability."""

    license_key: str
    operation: str = Field(..., description="Operation type (scans, resources)")
    amount: int = Field(1, description="Amount to check")


class QuotaCheckResponse(BaseModel):
    """Response from quota check."""

    allowed: bool
    error: str | None = None
    unlimited: bool | None = None
    current: int | None = None
    limit: int | None = None
    remaining: int | None = None
    requested: int | None = None


@router.post("/sync", response_model=SyncUsageResponse)
async def sync_usage(
    request: SyncUsageRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SyncUsageResponse:
    """
    Sync usage data from a client.

    This endpoint is called periodically by the CLI to report usage metrics.
    Supports idempotency via optional idempotency_key to prevent duplicate processing.
    """
    service = UsageService(db)

    result = await service.sync_usage(
        license_key=request.license_key,
        machine_id=request.machine_id,
        usage_data=request.usage,
        period=request.period,
        idempotency_key=request.idempotency_key,
    )

    return SyncUsageResponse(**result)


@router.get("/{license_key}", response_model=UsageResponse)
async def get_usage(
    license_key: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    period: str | None = None,
) -> UsageResponse:
    """Get usage data for a license."""
    service = UsageService(db)
    result = await service.get_usage(license_key, period)

    if "error" in result:
        return UsageResponse(
            period=period or "",
            usage={},
            quotas={},
            limits={},
        )

    return UsageResponse(**result)


@router.get("/{license_key}/history")
async def get_usage_history(
    license_key: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    months: int = 6,
) -> dict[str, Any]:
    """Get usage history for a license."""
    service = UsageService(db)
    return await service.get_usage_history(license_key, months)


@router.post("/check-quota", response_model=QuotaCheckResponse)
async def check_quota(
    request: QuotaCheckRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> QuotaCheckResponse:
    """
    Check if an operation is allowed within quota.

    Used by the CLI before starting operations to verify quotas.
    """
    service = UsageService(db)

    result = await service.check_quota(
        license_key=request.license_key,
        operation=request.operation,
        amount=request.amount,
    )

    return QuotaCheckResponse(**result)
