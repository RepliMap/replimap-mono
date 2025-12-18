"""License validation API endpoints."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from services import LicenseService

router = APIRouter()


class ValidateLicenseRequest(BaseModel):
    """Request to validate a license."""

    license_key: str = Field(..., description="The license key to validate")
    machine_id: str | None = Field(None, description="Machine identifier for activation")
    product_version: str | None = Field(None, description="Client product version")
    client_os: str | None = Field(None, description="Client operating system")


class ValidateLicenseResponse(BaseModel):
    """Response from license validation."""

    valid: bool
    error: str | None = None
    message: str | None = None
    license_id: str | None = None
    plan: str | None = None
    features: list[str] | None = None
    expires_at: str | None = None
    limits: dict[str, Any] | None = None
    activation: dict[str, Any] | None = None


class CreateLicenseRequest(BaseModel):
    """Request to create a license (admin only)."""

    customer_email: str
    plan: str = "free"
    expires_in_days: int | None = None
    features: list[str] | None = None
    notes: str | None = None


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

    # Get client IP
    client_ip = req.client.host if req.client else None

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


@router.post("/create", response_model=LicenseResponse)
async def create_license(
    request: CreateLicenseRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LicenseResponse:
    """
    Create a new license (admin endpoint).

    TODO: Add authentication/authorization for admin access.
    """
    service = LicenseService(db)

    license_record = await service.create_license(
        customer_email=request.customer_email,
        plan=request.plan,
        expires_in_days=request.expires_in_days,
        features=request.features,
        notes=request.notes,
    )

    return LicenseResponse(
        license_key=license_record.license_key,
        plan=license_record.plan,
        status=license_record.status,
        features=license_record.features or [],
        expires_at=license_record.expires_at.isoformat() if license_record.expires_at else None,
        max_activations=license_record.max_activations,
        created_at=license_record.created_at.isoformat(),
    )


@router.post("/{license_key}/revoke")
async def revoke_license(
    license_key: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    reason: str | None = None,
) -> dict[str, Any]:
    """
    Revoke a license (admin endpoint).

    TODO: Add authentication/authorization for admin access.
    """
    service = LicenseService(db)
    success = await service.revoke_license(license_key, reason)

    if not success:
        raise HTTPException(status_code=404, detail="License not found")

    return {"revoked": True, "license_key": license_key}
