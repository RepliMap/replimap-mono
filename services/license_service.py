"""License validation and management service."""

import hashlib
import hmac
import re
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from config import get_settings
from database.models import (
    Activation,
    AuditLog,
    AwsAccount,
    Customer,
    License,
    LicenseStatus,
    MachineChangeLog,
    PLAN_LIMITS,
    PlanType,
    SubscriptionStatus,
    generate_support_id,
)

settings = get_settings()

# License key format pattern
LICENSE_KEY_PATTERN = re.compile(r"^RP-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{4}$")


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
        # Find license with eager loading of activations for efficient count
        result = await self.db.execute(
            select(License)
            .where(License.license_key == license_key)
            .options(selectinload(License.activations))
        )
        license_record = result.scalar_one_or_none()

        if not license_record:
            await self._log_event(
                "license_validation_failed",
                {"reason": "not_found", "license_key": license_key[:8] + "..."},
                ip_address=client_ip,
            )
            return self._error_response(
                "invalid_license",
                "License key not found. Please check your license key or purchase a license.",
                action="purchase",
            )

        # Check status
        if license_record.status != LicenseStatus.ACTIVE.value:
            await self._log_event(
                "license_validation_failed",
                {"reason": "inactive", "status": license_record.status},
                license_id=license_record.id,
                ip_address=client_ip,
            )
            action = "renew" if license_record.status == LicenseStatus.EXPIRED.value else "contact_support"
            return self._error_response(
                "license_inactive",
                f"License is {license_record.status}. Please renew or contact support.",
                action=action,
                status=license_record.status,
            )

        # Check expiration (use timezone-aware comparison)
        now = datetime.now(UTC)
        if license_record.expires_at:
            # Handle both naive and aware datetimes
            expires_at = license_record.expires_at
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=UTC)
            if expires_at < now:
                # Auto-update status to expired
                license_record.status = LicenseStatus.EXPIRED.value
                await self.db.commit()

                await self._log_event(
                    "license_expired",
                    {"expires_at": license_record.expires_at.isoformat()},
                    license_id=license_record.id,
                    ip_address=client_ip,
                )
                return self._error_response(
                    "license_expired",
                    "License has expired. Please renew your subscription to continue using RepliMap.",
                    action="renew",
                    expired_at=license_record.expires_at.isoformat(),
                )

        # Check subscription status for Stripe-managed licenses
        if license_record.subscription_status:
            sub_status = license_record.subscription_status
            now = datetime.now(UTC)

            # Check for canceled subscription
            if sub_status == SubscriptionStatus.CANCELED.value:
                # Check if within grace period (7 days after period end)
                if license_record.current_period_end:
                    period_end = license_record.current_period_end
                    if period_end.tzinfo is None:
                        period_end = period_end.replace(tzinfo=UTC)
                    grace_period_end = period_end + timedelta(days=7)

                    if now < period_end:
                        # Still within paid period, allow access
                        pass
                    elif now < grace_period_end:
                        # In grace period, allow access but warn
                        pass  # Will be handled in response
                    else:
                        # Past grace period
                        license_record.status = LicenseStatus.EXPIRED.value
                        await self.db.commit()
                        return self._error_response(
                            "subscription_canceled",
                            "Your subscription has been canceled and the grace period has ended. "
                            "Please renew to continue using RepliMap.",
                            action="renew",
                            canceled_at=license_record.canceled_at.isoformat()
                            if license_record.canceled_at else None,
                        )
                else:
                    # No period end recorded, treat as expired
                    license_record.status = LicenseStatus.EXPIRED.value
                    await self.db.commit()
                    return self._error_response(
                        "subscription_canceled",
                        "Your subscription has been canceled. Please renew to continue.",
                        action="renew",
                    )

            # Check for unpaid/incomplete subscriptions
            elif sub_status in (
                SubscriptionStatus.UNPAID.value,
                SubscriptionStatus.INCOMPLETE_EXPIRED.value,
            ):
                return self._error_response(
                    "subscription_unpaid",
                    "Your subscription payment failed. Please update your payment method.",
                    action="update_payment",
                    subscription_status=sub_status,
                )

            # Check for paused subscriptions
            elif sub_status == SubscriptionStatus.PAUSED.value:
                return self._error_response(
                    "subscription_paused",
                    "Your subscription is paused. Please resume your subscription to continue.",
                    action="resume_subscription",
                )

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
                # Get accurate count via database query
                active_count = await self._get_active_activation_count(license_record.id)
                error_code = activation_result.get("error", "activation_limit")
                return self._error_response(
                    error_code,
                    activation_result["message"],
                    action=activation_result.get("action", "upgrade"),
                    max_activations=license_record.max_activations,
                    current_activations=active_count,
                )
            activation_info = activation_result

        # Get plan features
        plan_config = PLAN_FEATURES.get(license_record.plan, PLAN_FEATURES[PlanType.FREE.value])

        # Build response with cache_until for client-side caching
        cache_until = self._calculate_cache_until(license_record)

        response = {
            "valid": True,
            "license_id": str(license_record.id),
            "plan": license_record.plan,
            "features": license_record.features or plan_config["features"],
            "expires_at": license_record.expires_at.isoformat() if license_record.expires_at else None,
            "cache_until": cache_until,
            "limits": {
                "max_resources_per_scan": license_record.max_resources_per_scan
                or plan_config["max_resources_per_scan"],
                "max_scans_per_month": license_record.max_scans_per_month
                or plan_config["max_scans_per_month"],
                "max_aws_accounts": license_record.max_aws_accounts
                or plan_config.get("max_aws_accounts", 1),
            },
            "activation": activation_info,
            "subscription": {
                "status": license_record.subscription_status,
                "current_period_end": license_record.current_period_end.isoformat()
                if license_record.current_period_end else None,
                "cancel_at_period_end": license_record.cancel_at_period_end,
            } if license_record.subscription_status else None,
        }

        await self._log_event(
            "license_validated",
            {"plan": license_record.plan, "machine_id": machine_id},
            license_id=license_record.id,
            ip_address=client_ip,
        )

        return response

    async def _get_active_activation_count(self, license_id: Any) -> int:
        """Get count of active activations via database query (not in-memory)."""
        result = await self.db.execute(
            select(func.count())
            .select_from(Activation)
            .where(
                Activation.license_id == license_id,
                Activation.is_active.is_(True),
            )
        )
        return result.scalar_one()

    async def _get_machine_changes_this_month(self, license_id: Any) -> int:
        """Get count of machine changes for the current month."""
        current_period = datetime.now(UTC).strftime("%Y-%m")
        result = await self.db.execute(
            select(func.count())
            .select_from(MachineChangeLog)
            .where(
                MachineChangeLog.license_id == license_id,
                MachineChangeLog.period == current_period,
            )
        )
        return result.scalar_one()

    async def _record_machine_change(
        self,
        license_id: Any,
        machine_id: str,
        change_type: str,
        previous_machine_id: str | None = None,
        client_ip: str | None = None,
    ) -> None:
        """Record a machine activation change for rate limiting."""
        current_period = datetime.now(UTC).strftime("%Y-%m")
        change_log = MachineChangeLog(
            license_id=license_id,
            machine_id=machine_id,
            change_type=change_type,
            previous_machine_id=previous_machine_id,
            period=current_period,
            client_ip=client_ip,
        )
        self.db.add(change_log)
        # Don't commit here - let the caller handle transaction

    async def track_aws_account(
        self,
        license_key: str,
        aws_account_id: str,
        account_alias: str | None = None,
    ) -> dict[str, Any]:
        """
        Track an AWS account usage for a license.

        Returns tracking result with limit info.
        """
        # Validate AWS account ID format (12 digits)
        if not aws_account_id or len(aws_account_id) != 12 or not aws_account_id.isdigit():
            return self._error_response(
                "invalid_aws_account_id",
                "AWS account ID must be a 12-digit number.",
            )

        # Get license
        result = await self.db.execute(
            select(License)
            .where(License.license_key == license_key)
            .options(selectinload(License.aws_accounts))
        )
        license_record = result.scalar_one_or_none()

        if not license_record:
            return self._error_response(
                "invalid_license",
                "License key not found.",
                action="purchase",
            )

        if not license_record.is_valid:
            return self._error_response(
                "license_invalid",
                "License is not valid for use.",
                action="renew",
            )

        # Check if account already tracked
        result = await self.db.execute(
            select(AwsAccount).where(
                AwsAccount.license_id == license_record.id,
                AwsAccount.aws_account_id == aws_account_id,
            )
        )
        existing = result.scalar_one_or_none()

        now = datetime.now(UTC)

        if existing:
            # Update last seen
            existing.last_seen_at = now
            if account_alias and not existing.account_alias:
                existing.account_alias = account_alias
            if not existing.is_active:
                existing.is_active = True
            await self.db.commit()
            return {
                "tracked": True,
                "is_new": False,
                "aws_account_id": aws_account_id,
            }

        # Check AWS account limit
        max_accounts = license_record.max_aws_accounts
        if max_accounts is None:
            # Get from plan limits
            plan_limits = PLAN_LIMITS.get(license_record.plan, PLAN_LIMITS[PlanType.FREE.value])
            max_accounts = plan_limits.get("max_aws_accounts", 1)

        # Count active accounts
        active_count = await self._get_active_aws_account_count(license_record.id)

        if max_accounts is not None and active_count >= max_accounts:
            return self._error_response(
                "aws_account_limit",
                f"AWS account limit reached ({active_count}/{max_accounts}). "
                "Upgrade your plan for more AWS accounts.",
                action="upgrade",
                current_accounts=active_count,
                max_accounts=max_accounts,
            )

        # Create new tracking record
        aws_account = AwsAccount(
            license_id=license_record.id,
            aws_account_id=aws_account_id,
            account_alias=account_alias,
            first_seen_at=now,
            last_seen_at=now,
        )
        self.db.add(aws_account)
        await self.db.commit()

        await self._log_event(
            "aws_account_tracked",
            {
                "aws_account_id": aws_account_id,
                "account_alias": account_alias,
            },
            license_id=license_record.id,
        )

        return {
            "tracked": True,
            "is_new": True,
            "aws_account_id": aws_account_id,
            "current_accounts": active_count + 1,
            "max_accounts": max_accounts,
        }

    async def _get_active_aws_account_count(self, license_id: Any) -> int:
        """Get count of active AWS accounts for a license."""
        result = await self.db.execute(
            select(func.count())
            .select_from(AwsAccount)
            .where(
                AwsAccount.license_id == license_id,
                AwsAccount.is_active.is_(True),
            )
        )
        return result.scalar_one()

    async def get_aws_accounts(self, license_key: str) -> dict[str, Any]:
        """Get all AWS accounts tracked for a license."""
        result = await self.db.execute(
            select(License).where(License.license_key == license_key)
        )
        license_record = result.scalar_one_or_none()

        if not license_record:
            return {"error": "invalid_license"}

        result = await self.db.execute(
            select(AwsAccount)
            .where(AwsAccount.license_id == license_record.id)
            .order_by(AwsAccount.first_seen_at)
        )
        accounts = result.scalars().all()

        max_accounts = license_record.max_aws_accounts
        if max_accounts is None:
            plan_limits = PLAN_LIMITS.get(license_record.plan, PLAN_LIMITS[PlanType.FREE.value])
            max_accounts = plan_limits.get("max_aws_accounts", 1)

        return {
            "accounts": [
                {
                    "aws_account_id": acc.aws_account_id,
                    "account_alias": acc.account_alias,
                    "is_active": acc.is_active,
                    "first_seen_at": acc.first_seen_at.isoformat(),
                    "last_seen_at": acc.last_seen_at.isoformat(),
                }
                for acc in accounts
            ],
            "active_count": sum(1 for acc in accounts if acc.is_active),
            "max_accounts": max_accounts,
        }

    def _calculate_cache_until(self, license_record: License) -> str:
        """Calculate cache_until timestamp based on license state."""
        now = datetime.now(UTC)

        # Default: 24 hours cache for valid licenses
        cache_duration = timedelta(hours=24)

        # If subscription has a period end, don't cache past it
        if license_record.current_period_end:
            period_end = license_record.current_period_end
            if period_end.tzinfo is None:
                period_end = period_end.replace(tzinfo=UTC)
            # Cache until period end or 24h, whichever is sooner
            cache_until = min(now + cache_duration, period_end)
        else:
            cache_until = now + cache_duration

        # If license expires sooner, use that
        if license_record.expires_at:
            expires_at = license_record.expires_at
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=UTC)
            cache_until = min(cache_until, expires_at)

        # For past_due subscriptions, use shorter cache (4 hours)
        if license_record.subscription_status == SubscriptionStatus.PAST_DUE.value:
            cache_until = min(cache_until, now + timedelta(hours=4))

        return cache_until.isoformat()

    def _error_response(
        self,
        error_code: str,
        message: str,
        action: str | None = None,
        **extra: Any,
    ) -> dict[str, Any]:
        """Create a standardized error response with support ID."""
        support_id = generate_support_id()
        response = {
            "valid": False,
            "error": error_code,
            "message": message,
            "support_id": support_id,
        }
        if action:
            response["action"] = action
        response.update(extra)
        return response

    async def _handle_activation(
        self,
        license_record: License,
        machine_id: str,
        client_version: str | None,
        client_os: str | None,
        client_ip: str | None,
    ) -> dict[str, Any]:
        """Handle machine activation for a license with machine change limits."""
        now = datetime.now(UTC)

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
            existing.last_seen_at = now
            existing.client_version = client_version
            existing.client_ip = client_ip
            if not existing.is_active:
                # Reactivating a previously deactivated machine counts as a change
                max_changes = license_record.max_machine_changes_per_month
                if max_changes is not None:
                    changes_count = await self._get_machine_changes_this_month(license_record.id)
                    if changes_count >= max_changes:
                        return {
                            "success": False,
                            "error": "machine_change_limit",
                            "message": f"Machine change limit reached ({changes_count}/{max_changes} this month). "
                                       "Changes reset on the 1st of each month.",
                            "action": "wait",
                            "changes_used": changes_count,
                            "max_changes": max_changes,
                        }

                existing.is_active = True
                existing.deactivated_at = None
                # Record the reactivation
                await self._record_machine_change(
                    license_record.id,
                    machine_id,
                    "reactivated",
                    client_ip=client_ip,
                )
            await self.db.commit()
            return {
                "success": True,
                "activation_id": str(existing.id),
                "is_new": False,
            }

        # Check activation limit using database count (not in-memory property)
        if license_record.max_activations is not None:
            current_count = await self._get_active_activation_count(license_record.id)
            if current_count >= license_record.max_activations:
                return {
                    "success": False,
                    "error": "activation_limit",
                    "message": f"Activation limit reached ({current_count}/{license_record.max_activations}). "
                               "Upgrade your plan for more activations.",
                    "action": "upgrade",
                }

        # Check machine change limit for new activations
        max_changes = license_record.max_machine_changes_per_month
        if max_changes is not None:
            changes_count = await self._get_machine_changes_this_month(license_record.id)
            if changes_count >= max_changes:
                return {
                    "success": False,
                    "error": "machine_change_limit",
                    "message": f"Machine change limit reached ({changes_count}/{max_changes} this month). "
                               "Changes reset on the 1st of each month.",
                    "action": "wait",
                    "changes_used": changes_count,
                    "max_changes": max_changes,
                }

        # Create new activation
        activation = Activation(
            license_id=license_record.id,
            machine_id=machine_id,
            client_version=client_version,
            client_os=client_os,
            client_ip=client_ip,
            activated_at=now,
            last_seen_at=now,
        )
        self.db.add(activation)

        # Record the new activation
        await self._record_machine_change(
            license_record.id,
            machine_id,
            "activated",
            client_ip=client_ip,
        )

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
        # Validate plan type
        valid_plans = {p.value for p in PlanType}
        if plan not in valid_plans:
            raise ValueError(f"Invalid plan type: {plan}. Must be one of: {', '.join(valid_plans)}")

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
        now = datetime.now(UTC)
        expires_at = None
        if expires_in_days:
            expires_at = now + timedelta(days=expires_in_days)

        # Create license with retry for key collision
        max_retries = 3
        for attempt in range(max_retries):
            try:
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
                    issued_at=now,
                    created_at=now,
                )
                self.db.add(license_record)
                await self.db.commit()
                await self.db.refresh(license_record)
                break
            except IntegrityError:
                await self.db.rollback()
                if attempt == max_retries - 1:
                    raise RuntimeError("Failed to generate unique license key after multiple attempts")
                continue

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
            created_at=datetime.now(UTC),
        )
        self.db.add(log)
        # Commit the log to ensure it's persisted
        await self.db.commit()
