"""License validation and management service."""

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from database.models import Activation, AuditLog, Customer, License, LicenseStatus, PlanType

settings = get_settings()


# Plan feature definitions
PLAN_FEATURES: dict[str, dict[str, Any]] = {
    PlanType.FREE.value: {
        "features": [],
        "max_resources_per_scan": 50,
        "max_scans_per_month": 10,
        "max_activations": 1,
    },
    PlanType.STARTER.value: {
        "features": ["export_formats"],
        "max_resources_per_scan": 200,
        "max_scans_per_month": 100,
        "max_activations": 2,
    },
    PlanType.TEAM.value: {
        "features": ["export_formats", "async_scanning", "custom_templates"],
        "max_resources_per_scan": None,  # Unlimited
        "max_scans_per_month": None,
        "max_activations": 10,
    },
    PlanType.ENTERPRISE.value: {
        "features": [
            "export_formats",
            "async_scanning",
            "custom_templates",
            "api_access",
            "sso",
            "audit_logs",
        ],
        "max_resources_per_scan": None,
        "max_scans_per_month": None,
        "max_activations": None,  # Unlimited
    },
}


def generate_license_key() -> str:
    """Generate a unique license key."""
    # Format: RP-XXXX-XXXX-XXXX-XXXX
    segments = [secrets.token_hex(2).upper() for _ in range(4)]
    return f"RP-{'-'.join(segments)}"


def sign_license_data(data: str) -> str:
    """Sign license data for integrity verification."""
    signature = hmac.new(
        settings.license_signing_key.encode(),
        data.encode(),
        hashlib.sha256,
    ).hexdigest()[:16]
    return signature


class LicenseService:
    """Service for license operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def validate_license(
        self,
        license_key: str,
        machine_id: str | None = None,
        client_version: str | None = None,
        client_os: str | None = None,
        client_ip: str | None = None,
    ) -> dict[str, Any]:
        """
        Validate a license key and optionally activate for a machine.

        Returns validation result with plan details and features.
        """
        # Find license
        result = await self.db.execute(
            select(License).where(License.license_key == license_key)
        )
        license_record = result.scalar_one_or_none()

        if not license_record:
            await self._log_event(
                "license_validation_failed",
                {"reason": "not_found", "license_key": license_key[:8] + "..."},
                ip_address=client_ip,
            )
            return {
                "valid": False,
                "error": "invalid_license",
                "message": "License key not found",
            }

        # Check status
        if license_record.status != LicenseStatus.ACTIVE.value:
            await self._log_event(
                "license_validation_failed",
                {"reason": "inactive", "status": license_record.status},
                license_id=license_record.id,
                ip_address=client_ip,
            )
            return {
                "valid": False,
                "error": "license_inactive",
                "message": f"License is {license_record.status}",
            }

        # Check expiration
        if license_record.expires_at and license_record.expires_at < datetime.utcnow():
            # Auto-update status to expired
            license_record.status = LicenseStatus.EXPIRED.value
            await self.db.commit()

            await self._log_event(
                "license_expired",
                {"expires_at": license_record.expires_at.isoformat()},
                license_id=license_record.id,
                ip_address=client_ip,
            )
            return {
                "valid": False,
                "error": "license_expired",
                "message": "License has expired",
                "expired_at": license_record.expires_at.isoformat(),
            }

        # Handle machine activation if machine_id provided
        activation_info: dict[str, Any] = {}
        if machine_id and settings.enable_activation_limits:
            activation_result = await self._handle_activation(
                license_record,
                machine_id,
                client_version,
                client_os,
                client_ip,
            )
            if not activation_result["success"]:
                return {
                    "valid": False,
                    "error": "activation_limit",
                    "message": activation_result["message"],
                    "max_activations": license_record.max_activations,
                    "current_activations": license_record.active_activation_count,
                }
            activation_info = activation_result

        # Get plan features
        plan_config = PLAN_FEATURES.get(license_record.plan, PLAN_FEATURES[PlanType.FREE.value])

        # Build response
        response = {
            "valid": True,
            "license_id": str(license_record.id),
            "plan": license_record.plan,
            "features": license_record.features or plan_config["features"],
            "expires_at": license_record.expires_at.isoformat() if license_record.expires_at else None,
            "limits": {
                "max_resources_per_scan": license_record.max_resources_per_scan
                or plan_config["max_resources_per_scan"],
                "max_scans_per_month": license_record.max_scans_per_month
                or plan_config["max_scans_per_month"],
            },
            "activation": activation_info,
        }

        await self._log_event(
            "license_validated",
            {"plan": license_record.plan, "machine_id": machine_id},
            license_id=license_record.id,
            ip_address=client_ip,
        )

        return response

    async def _handle_activation(
        self,
        license_record: License,
        machine_id: str,
        client_version: str | None,
        client_os: str | None,
        client_ip: str | None,
    ) -> dict[str, Any]:
        """Handle machine activation for a license."""
        # Check if already activated for this machine
        result = await self.db.execute(
            select(Activation).where(
                Activation.license_id == license_record.id,
                Activation.machine_id == machine_id,
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            # Update last seen
            existing.last_seen_at = datetime.utcnow()
            existing.client_version = client_version
            existing.client_ip = client_ip
            if not existing.is_active:
                existing.is_active = True
                existing.deactivated_at = None
            await self.db.commit()
            return {
                "success": True,
                "activation_id": str(existing.id),
                "is_new": False,
            }

        # Check activation limit
        if license_record.max_activations is not None:
            current_count = license_record.active_activation_count
            if current_count >= license_record.max_activations:
                return {
                    "success": False,
                    "message": f"Activation limit reached ({current_count}/{license_record.max_activations})",
                }

        # Create new activation
        activation = Activation(
            license_id=license_record.id,
            machine_id=machine_id,
            client_version=client_version,
            client_os=client_os,
            client_ip=client_ip,
        )
        self.db.add(activation)
        await self.db.commit()

        return {
            "success": True,
            "activation_id": str(activation.id),
            "is_new": True,
        }

    async def create_license(
        self,
        customer_email: str,
        plan: str = PlanType.FREE.value,
        expires_in_days: int | None = None,
        features: list[str] | None = None,
        notes: str | None = None,
    ) -> License:
        """Create a new license for a customer."""
        # Find or create customer
        result = await self.db.execute(
            select(Customer).where(Customer.email == customer_email)
        )
        customer = result.scalar_one_or_none()

        if not customer:
            customer = Customer(email=customer_email)
            self.db.add(customer)
            await self.db.flush()

        # Get plan defaults
        plan_config = PLAN_FEATURES.get(plan, PLAN_FEATURES[PlanType.FREE.value])

        # Calculate expiration
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

        # Create license
        license_record = License(
            license_key=generate_license_key(),
            customer_id=customer.id,
            plan=plan,
            features=features or plan_config["features"],
            expires_at=expires_at,
            max_activations=plan_config["max_activations"],
            max_resources_per_scan=plan_config["max_resources_per_scan"],
            max_scans_per_month=plan_config["max_scans_per_month"],
            notes=notes,
        )
        self.db.add(license_record)
        await self.db.commit()
        await self.db.refresh(license_record)

        await self._log_event(
            "license_created",
            {
                "plan": plan,
                "customer_email": customer_email,
                "expires_at": expires_at.isoformat() if expires_at else None,
            },
            license_id=license_record.id,
            customer_id=customer.id,
        )

        return license_record

    async def revoke_license(self, license_key: str, reason: str | None = None) -> bool:
        """Revoke a license."""
        result = await self.db.execute(
            select(License).where(License.license_key == license_key)
        )
        license_record = result.scalar_one_or_none()

        if not license_record:
            return False

        license_record.status = LicenseStatus.REVOKED.value
        await self.db.commit()

        await self._log_event(
            "license_revoked",
            {"reason": reason},
            license_id=license_record.id,
        )

        return True

    async def get_license_by_key(self, license_key: str) -> License | None:
        """Get license by key."""
        result = await self.db.execute(
            select(License).where(License.license_key == license_key)
        )
        return result.scalar_one_or_none()

    async def _log_event(
        self,
        event_type: str,
        event_data: dict[str, Any],
        license_id: Any = None,
        customer_id: Any = None,
        ip_address: str | None = None,
    ) -> None:
        """Log an audit event."""
        log = AuditLog(
            event_type=event_type,
            event_data=event_data,
            license_id=license_id,
            customer_id=customer_id,
            ip_address=ip_address,
            actor_type="api",
        )
        self.db.add(log)
        # Don't commit here - let the caller handle transactions
