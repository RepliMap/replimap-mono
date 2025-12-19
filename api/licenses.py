"""License validation API endpoints."""

import secrets
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from database import get_db
from database.models import PlanType
from services import LicenseService

router = APIRouter()
settings = get_settings()


async def verify_admin_api_key(
    x_api_key: Annotated[str | None, Header()] = None,
) -> None:
    """
    Verify admin API key for protected endpoints.

    The API key should be set via the ADMIN_API_KEY environment variable.
    """
    admin_key = getattr(settings, "admin_api_key", None)

    if not admin_key:
        raise HTTPException(
            status_code=503,
            detail="Admin API is not configured. Set ADMIN_API_KEY environment variable.",
        )

    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing X-API-Key header",
        )

    # Use constant-time comparison to prevent timing attacks
    if not secrets.compare_digest(x_api_key, admin_key):
        raise HTTPException(
            status_code=403,
            detail="Invalid API key",
        )


class ValidateLicenseRequest(BaseModel):
    """Request to validate a license."""

    license_key: str = Field(..., description="The license key to validate", min_length=1)
    machine_id: str | None = Field(None, description="Machine identifier for activation")
    product_version: str | None = Field(None, description="Client product version")
    client_os: str | None = Field(None, description="Client operating system")


class SubscriptionInfo(BaseModel):
    """Subscription details in validation response."""

    status: str | None = None
    current_period_end: str | None = None
    cancel_at_period_end: bool = False


class ValidateLicenseResponse(BaseModel):
    """Response from license validation."""

    valid: bool
    error: str | None = None
    message: str | None = None
    support_id: str | None = None  # For error tracking
    action: str | None = None  # Suggested action: "purchase", "renew", "upgrade", "wait", "contact_support"
    license_id: str | None = None
    plan: str | None = None
    features: list[str] | None = None
    expires_at: str | None = None
    cache_until: str | None = None  # Client should cache validation until this time
    limits: dict[str, Any] | None = None
    activation: dict[str, Any] | None = None
    subscription: SubscriptionInfo | None = None


class CreateLicenseRequest(BaseModel):
    """Request to create a license (admin only)."""

    customer_email: EmailStr
    plan: str = Field(default="free", description="License plan type")
    expires_in_days: int | None = Field(None, ge=1, le=3650, description="Days until expiration")
    features: list[str] | None = None
    notes: str | None = Field(None, max_length=1000)

    @field_validator("plan")
    @classmethod
    def validate_plan(cls, v: str) -> str:
        """Validate that plan is a valid PlanType."""
        valid_plans = {p.value for p in PlanType}
        if v not in valid_plans:
            raise ValueError(f"Invalid plan. Must be one of: {', '.join(sorted(valid_plans))}")
        return v


class LicenseResponse(BaseModel):
    """License details response."""

    license_key: str
    plan: str
    status: str
    features: list[str]
    expires_at: str | None
    max_activations: int | None
    created_at: str


@router.post("/validate", response_model=ValidateLicenseResponse)
async def validate_license(
    request: ValidateLicenseRequest,
    req: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ValidateLicenseResponse:
    """
    Validate a license key.

    Optionally activates the license for a specific machine.
    """
    service = LicenseService(db)

    # Get client IP (handle proxies)
    client_ip = None
    if req.client:
        client_ip = req.client.host
    # Check for forwarded header (behind reverse proxy)
    forwarded_for = req.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP in the chain (original client)
        client_ip = forwarded_for.split(",")[0].strip()

    result = await service.validate_license(
        license_key=request.license_key,
        machine_id=request.machine_id,
        client_version=request.product_version,
        client_os=request.client_os,
        client_ip=client_ip,
    )

    return ValidateLicenseResponse(**result)


@router.get("/{license_key}", response_model=LicenseResponse)
async def get_license(
    license_key: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LicenseResponse:
    """Get license details by key."""
    if not license_key or len(license_key) < 1:
        raise HTTPException(status_code=400, detail="License key is required")

    service = LicenseService(db)
    license_record = await service.get_license_by_key(license_key)

    if not license_record:
        raise HTTPException(status_code=404, detail="License not found")

    return LicenseResponse(
        license_key=license_record.license_key,
        plan=license_record.plan,
        status=license_record.status,
        features=license_record.features or [],
        expires_at=license_record.expires_at.isoformat() if license_record.expires_at else None,
        max_activations=license_record.max_activations,
        created_at=license_record.created_at.isoformat(),
    )


@router.post("/create", response_model=LicenseResponse, dependencies=[Depends(verify_admin_api_key)])
async def create_license(
    request: CreateLicenseRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LicenseResponse:
    """
    Create a new license (admin endpoint).

    Requires X-API-Key header with valid admin API key.
    """
    service = LicenseService(db)

    try:
        license_record = await service.create_license(
            customer_email=request.customer_email,
            plan=request.plan,
            expires_in_days=request.expires_in_days,
            features=request.features,
            notes=request.notes,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return LicenseResponse(
        license_key=license_record.license_key,
        plan=license_record.plan,
        status=license_record.status,
        features=license_record.features or [],
        expires_at=license_record.expires_at.isoformat() if license_record.expires_at else None,
        max_activations=license_record.max_activations,
        created_at=license_record.created_at.isoformat(),
    )


@router.post(
    "/{license_key}/revoke",
    dependencies=[Depends(verify_admin_api_key)],
)
async def revoke_license(
    license_key: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    reason: str | None = None,
) -> dict[str, Any]:
    """
    Revoke a license (admin endpoint).

    Requires X-API-Key header with valid admin API key.
    """
    if not license_key or len(license_key) < 1:
        raise HTTPException(status_code=400, detail="License key is required")

    service = LicenseService(db)
    success = await service.revoke_license(license_key, reason)

    if not success:
        raise HTTPException(status_code=404, detail="License not found")

    return {"revoked": True, "license_key": license_key}


class TrackAwsAccountRequest(BaseModel):
    """Request to track an AWS account."""

    license_key: str = Field(..., description="The license key")
    aws_account_id: str = Field(
        ...,
        description="AWS account ID (12 digits)",
        min_length=12,
        max_length=12,
    )
    account_alias: str | None = Field(None, description="Friendly name for the account")


class TrackAwsAccountResponse(BaseModel):
    """Response from AWS account tracking."""

    tracked: bool
    valid: bool | None = None
    error: str | None = None
    message: str | None = None
    support_id: str | None = None
    action: str | None = None
    is_new: bool | None = None
    aws_account_id: str | None = None
    current_accounts: int | None = None
    max_accounts: int | None = None


@router.post("/aws-accounts/track", response_model=TrackAwsAccountResponse)
async def track_aws_account(
    request: TrackAwsAccountRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TrackAwsAccountResponse:
    """
    Track an AWS account for a license.

    This endpoint is called by the CLI when scanning an AWS account.
    It tracks which accounts are used and enforces the per-plan limit.
    """
    service = LicenseService(db)

    result = await service.track_aws_account(
        license_key=request.license_key,
        aws_account_id=request.aws_account_id,
        account_alias=request.account_alias,
    )

    return TrackAwsAccountResponse(**result)


@router.get("/{license_key}/aws-accounts")
async def get_aws_accounts(
    license_key: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """Get all AWS accounts tracked for a license."""
    service = LicenseService(db)
    return await service.get_aws_accounts(license_key)
