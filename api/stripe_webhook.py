"""Stripe webhook handler with signature verification and idempotent event processing."""

import logging
from datetime import UTC, datetime
from typing import Any

import stripe
from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from database import get_db
from database.models import (
    Customer,
    License,
    LicenseStatus,
    PLAN_LIMITS,
    PlanType,
    ProcessedEvent,
    SubscriptionStatus,
)
from services.license_service import generate_license_key

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()

def get_stripe_price_to_plan_mapping() -> dict[str | None, str]:
    """Build price ID to plan mapping, filtering out None values."""
    mapping = {}
    if settings.stripe_price_id_solo:
        mapping[settings.stripe_price_id_solo] = PlanType.SOLO.value
    if settings.stripe_price_id_pro:
        mapping[settings.stripe_price_id_pro] = PlanType.PRO.value
    if settings.stripe_price_id_team:
        mapping[settings.stripe_price_id_team] = PlanType.TEAM.value
    # Legacy mappings
    if settings.stripe_price_id_starter:
        mapping[settings.stripe_price_id_starter] = PlanType.STARTER.value
    if settings.stripe_price_id_enterprise:
        mapping[settings.stripe_price_id_enterprise] = PlanType.ENTERPRISE.value
    return mapping


async def is_event_processed(db: AsyncSession, event_id: str) -> bool:
    """Check if a webhook event has already been processed."""
    result = await db.execute(
        select(ProcessedEvent).where(ProcessedEvent.event_id == event_id)
    )
    return result.scalar_one_or_none() is not None


async def mark_event_processed(
    db: AsyncSession,
    event_id: str,
    event_type: str,
    success: bool = True,
    error_message: str | None = None,
    result_data: dict | None = None,
    license_id: Any = None,
    customer_id: Any = None,
) -> None:
    """Record that an event has been processed for idempotency."""
    processed_event = ProcessedEvent(
        event_id=event_id,
        event_type=event_type,
        source="stripe",
        success=success,
        error_message=error_message,
        result_data=result_data or {},
        license_id=license_id,
        customer_id=customer_id,
    )
    db.add(processed_event)
    await db.commit()


async def get_or_create_customer(
    db: AsyncSession,
    stripe_customer_id: str,
    email: str,
    name: str | None = None,
) -> Customer:
    """Get existing customer or create new one from Stripe data."""
    # Try to find by Stripe customer ID
    result = await db.execute(
        select(Customer).where(Customer.stripe_customer_id == stripe_customer_id)
    )
    customer = result.scalar_one_or_none()

    if customer:
        return customer

    # Try to find by email
    result = await db.execute(
        select(Customer).where(Customer.email == email)
    )
    customer = result.scalar_one_or_none()

    if customer:
        # Link existing customer to Stripe
        customer.stripe_customer_id = stripe_customer_id
        if name and not customer.name:
            customer.name = name
        await db.commit()
        return customer

    # Create new customer
    customer = Customer(
        email=email,
        name=name,
        stripe_customer_id=stripe_customer_id,
    )
    db.add(customer)
    await db.commit()
    await db.refresh(customer)
    return customer


async def get_license_by_subscription(
    db: AsyncSession,
    subscription_id: str,
) -> License | None:
    """Get license by Stripe subscription ID."""
    result = await db.execute(
        select(License).where(License.stripe_subscription_id == subscription_id)
    )
    return result.scalar_one_or_none()


def get_plan_from_subscription(subscription: dict) -> str:
    """Extract plan type from Stripe subscription object."""
    price_to_plan = get_stripe_price_to_plan_mapping()
    items = subscription.get("items", {}).get("data", [])
    if items:
        price_id = items[0].get("price", {}).get("id")
        return price_to_plan.get(price_id, PlanType.SOLO.value)
    return PlanType.SOLO.value


async def handle_checkout_completed(
    db: AsyncSession,
    event: dict,
) -> dict[str, Any]:
    """
    Handle checkout.session.completed event.

    Creates license record when user completes checkout.
    """
    session = event["data"]["object"]

    customer_id = session.get("customer")
    subscription_id = session.get("subscription")
    customer_email = session.get("customer_email") or session.get("customer_details", {}).get("email")
    customer_name = session.get("customer_details", {}).get("name")

    if not customer_id or not subscription_id or not customer_email:
        raise ValueError("Missing required fields in checkout session")

    # Get or create customer
    customer = await get_or_create_customer(db, customer_id, customer_email, customer_name)

    # Check if license already exists for this subscription
    existing = await get_license_by_subscription(db, subscription_id)
    if existing:
        logger.info(f"License already exists for subscription {subscription_id}")
        return {"action": "skipped", "reason": "license_exists", "license_id": str(existing.id)}

    # Retrieve subscription details from Stripe
    stripe.api_key = settings.stripe_secret_key
    subscription = stripe.Subscription.retrieve(subscription_id)

    plan = get_plan_from_subscription(subscription)
    plan_limits = PLAN_LIMITS.get(plan, PLAN_LIMITS[PlanType.FREE.value])

    # Create license
    license_record = License(
        license_key=generate_license_key(),
        customer_id=customer.id,
        plan=plan,
        status=LicenseStatus.ACTIVE.value,
        stripe_subscription_id=subscription_id,
        subscription_status=subscription.get("status"),
        current_period_start=datetime.fromtimestamp(subscription["current_period_start"], UTC),
        current_period_end=datetime.fromtimestamp(subscription["current_period_end"], UTC),
        max_activations=plan_limits["max_activations"],
        max_scans_per_month=plan_limits["max_scans_per_month"],
        max_resources_per_scan=plan_limits["max_resources_per_scan"],
        max_aws_accounts=plan_limits["max_aws_accounts"],
        features=plan_limits["features"],
    )
    db.add(license_record)
    await db.commit()
    await db.refresh(license_record)

    logger.info(f"Created license {license_record.license_key[:8]}... for subscription {subscription_id}")

    return {
        "action": "created",
        "license_id": str(license_record.id),
        "license_key": license_record.license_key,
        "plan": plan,
    }


async def handle_subscription_updated(
    db: AsyncSession,
    event: dict,
) -> dict[str, Any]:
    """
    Handle customer.subscription.updated event.

    Updates license when subscription changes (upgrade/downgrade/status change).
    """
    subscription = event["data"]["object"]
    subscription_id = subscription["id"]

    license_record = await get_license_by_subscription(db, subscription_id)
    if not license_record:
        logger.warning(f"No license found for subscription {subscription_id}")
        return {"action": "skipped", "reason": "license_not_found"}

    # Update subscription status
    previous_status = license_record.subscription_status
    license_record.subscription_status = subscription.get("status")
    license_record.current_period_start = datetime.fromtimestamp(
        subscription["current_period_start"], UTC
    )
    license_record.current_period_end = datetime.fromtimestamp(
        subscription["current_period_end"], UTC
    )
    license_record.cancel_at_period_end = subscription.get("cancel_at_period_end", False)

    if subscription.get("canceled_at"):
        license_record.canceled_at = datetime.fromtimestamp(subscription["canceled_at"], UTC)

    if subscription.get("trial_end"):
        license_record.trial_end = datetime.fromtimestamp(subscription["trial_end"], UTC)

    # Check for plan change
    new_plan = get_plan_from_subscription(subscription)
    if new_plan != license_record.plan:
        old_plan = license_record.plan
        license_record.plan = new_plan
        plan_limits = PLAN_LIMITS.get(new_plan, PLAN_LIMITS[PlanType.FREE.value])
        license_record.max_activations = plan_limits["max_activations"]
        license_record.max_scans_per_month = plan_limits["max_scans_per_month"]
        license_record.max_resources_per_scan = plan_limits["max_resources_per_scan"]
        license_record.max_aws_accounts = plan_limits["max_aws_accounts"]
        license_record.features = plan_limits["features"]
        logger.info(f"Plan changed from {old_plan} to {new_plan} for license {license_record.id}")

    await db.commit()

    return {
        "action": "updated",
        "license_id": str(license_record.id),
        "previous_status": previous_status,
        "new_status": license_record.subscription_status,
        "plan": license_record.plan,
    }


async def handle_subscription_deleted(
    db: AsyncSession,
    event: dict,
) -> dict[str, Any]:
    """
    Handle customer.subscription.deleted event.

    Marks license as canceled when subscription ends.
    """
    subscription = event["data"]["object"]
    subscription_id = subscription["id"]

    license_record = await get_license_by_subscription(db, subscription_id)
    if not license_record:
        logger.warning(f"No license found for subscription {subscription_id}")
        return {"action": "skipped", "reason": "license_not_found"}

    license_record.subscription_status = SubscriptionStatus.CANCELED.value
    license_record.canceled_at = datetime.now(UTC)

    # If not cancel_at_period_end, expire immediately
    if not subscription.get("cancel_at_period_end"):
        license_record.status = LicenseStatus.EXPIRED.value
        logger.info(f"License {license_record.id} expired immediately")
    else:
        # Keep active until period end
        license_record.expires_at = license_record.current_period_end
        logger.info(f"License {license_record.id} will expire at period end")

    await db.commit()

    return {
        "action": "canceled",
        "license_id": str(license_record.id),
        "expires_at": license_record.expires_at.isoformat() if license_record.expires_at else None,
    }


async def handle_invoice_paid(
    db: AsyncSession,
    event: dict,
) -> dict[str, Any]:
    """
    Handle invoice.paid event.

    Confirms renewal and updates period end.
    """
    invoice = event["data"]["object"]
    subscription_id = invoice.get("subscription")

    if not subscription_id:
        return {"action": "skipped", "reason": "no_subscription"}

    license_record = await get_license_by_subscription(db, subscription_id)
    if not license_record:
        logger.warning(f"No license found for subscription {subscription_id}")
        return {"action": "skipped", "reason": "license_not_found"}

    # Retrieve updated subscription
    stripe.api_key = settings.stripe_secret_key
    subscription = stripe.Subscription.retrieve(subscription_id)

    license_record.subscription_status = SubscriptionStatus.ACTIVE.value
    license_record.current_period_start = datetime.fromtimestamp(
        subscription["current_period_start"], UTC
    )
    license_record.current_period_end = datetime.fromtimestamp(
        subscription["current_period_end"], UTC
    )
    license_record.status = LicenseStatus.ACTIVE.value

    await db.commit()

    logger.info(f"Renewal confirmed for license {license_record.id}")

    return {
        "action": "renewed",
        "license_id": str(license_record.id),
        "period_end": license_record.current_period_end.isoformat(),
    }


async def handle_invoice_payment_failed(
    db: AsyncSession,
    event: dict,
) -> dict[str, Any]:
    """
    Handle invoice.payment_failed event.

    Marks license as past_due.
    """
    invoice = event["data"]["object"]
    subscription_id = invoice.get("subscription")

    if not subscription_id:
        return {"action": "skipped", "reason": "no_subscription"}

    license_record = await get_license_by_subscription(db, subscription_id)
    if not license_record:
        return {"action": "skipped", "reason": "license_not_found"}

    license_record.subscription_status = SubscriptionStatus.PAST_DUE.value

    await db.commit()

    logger.warning(f"Payment failed for license {license_record.id}")

    return {
        "action": "marked_past_due",
        "license_id": str(license_record.id),
    }


async def handle_customer_deleted(
    db: AsyncSession,
    event: dict,
) -> dict[str, Any]:
    """
    Handle customer.deleted event.

    Expires all licenses for the customer.
    """
    customer_data = event["data"]["object"]
    stripe_customer_id = customer_data["id"]

    result = await db.execute(
        select(Customer).where(Customer.stripe_customer_id == stripe_customer_id)
    )
    customer = result.scalar_one_or_none()

    if not customer:
        return {"action": "skipped", "reason": "customer_not_found"}

    # Expire all licenses
    expired_count = 0
    for license_record in customer.licenses:
        if license_record.status == LicenseStatus.ACTIVE.value:
            license_record.status = LicenseStatus.EXPIRED.value
            license_record.subscription_status = SubscriptionStatus.CANCELED.value
            expired_count += 1

    await db.commit()

    logger.info(f"Expired {expired_count} licenses for customer {customer.id}")

    return {
        "action": "customer_deleted",
        "customer_id": str(customer.id),
        "expired_licenses": expired_count,
    }


# Event handler registry
EVENT_HANDLERS = {
    "checkout.session.completed": handle_checkout_completed,
    "customer.subscription.created": handle_subscription_updated,  # Same as update
    "customer.subscription.updated": handle_subscription_updated,
    "customer.subscription.deleted": handle_subscription_deleted,
    "invoice.paid": handle_invoice_paid,
    "invoice.payment_failed": handle_invoice_payment_failed,
    "customer.deleted": handle_customer_deleted,
}


@router.post("/webhook")
async def stripe_webhook(request: Request) -> dict[str, Any]:
    """
    Handle Stripe webhook events with signature verification and idempotency.

    All events are:
    1. Verified using Stripe signature
    2. Checked for duplicate processing (idempotency)
    3. Processed by appropriate handler
    4. Recorded for audit trail
    """
    # Get webhook secret
    webhook_secret = settings.stripe_webhook_secret
    if not webhook_secret:
        logger.error("STRIPE_WEBHOOK_SECRET not configured")
        raise HTTPException(status_code=503, detail="Webhook not configured")

    # Get request body and signature
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not sig_header:
        logger.warning("Missing stripe-signature header")
        raise HTTPException(status_code=400, detail="Missing signature header")

    # Verify webhook signature
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError as e:
        logger.warning(f"Invalid payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        logger.warning(f"Invalid signature: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")

    event_id = event["id"]
    event_type = event["type"]

    logger.info(f"Received Stripe event: {event_type} ({event_id})")

    # Get database session
    async for db in get_db():
        try:
            # Check idempotency
            if await is_event_processed(db, event_id):
                logger.info(f"Event {event_id} already processed, skipping")
                return {"status": "already_processed", "event_id": event_id}

            # Find handler
            handler = EVENT_HANDLERS.get(event_type)
            if not handler:
                logger.info(f"No handler for event type: {event_type}")
                await mark_event_processed(
                    db, event_id, event_type,
                    result_data={"action": "ignored", "reason": "no_handler"}
                )
                return {"status": "ignored", "event_type": event_type}

            # Process event
            try:
                result = await handler(db, event)
                await mark_event_processed(
                    db, event_id, event_type,
                    success=True,
                    result_data=result,
                )
                logger.info(f"Successfully processed {event_type}: {result}")
                return {"status": "processed", "event_id": event_id, **result}

            except Exception as e:
                logger.exception(f"Error processing {event_type}: {e}")
                await mark_event_processed(
                    db, event_id, event_type,
                    success=False,
                    error_message=str(e),
                )
                # Don't raise - acknowledge receipt to prevent retries for processing errors
                return {"status": "error", "event_id": event_id, "error": str(e)}

        except Exception as e:
            logger.exception(f"Webhook handler error: {e}")
            raise HTTPException(status_code=500, detail="Internal error")

    raise HTTPException(status_code=500, detail="Database unavailable")
