/**
 * Stripe Webhook Handler
 * POST /v1/webhooks/stripe
 *
 * Handles Stripe subscription lifecycle events AND one-time lifetime payments.
 *
 * Flow for Subscriptions:
 *   checkout.session.completed (mode=subscription) → Creates user
 *   customer.subscription.created → Creates license
 *
 * Flow for Lifetime Deals:
 *   checkout.session.completed (mode=payment) → Creates user + license immediately
 *   charge.refunded → Revokes lifetime license
 */

import type { Env } from '../types/env';
import { generateLicenseKey, timestampToISO, nowISO } from '../lib/license';
import { getPlanFromPriceId, isPlanDowngrade, getStripePriceMapping, LIFETIME_EXPIRY, PLAN_RANK } from '../lib/constants';
import {
  createDb,
  type DrizzleDb,
  findOrCreateUser,
  getUserByStripeCustomerId,
  createLicense,
  getLicenseBySubscriptionId,
  getLicenseBySessionId,
  getLifetimeLicenseByUserId,
  updateLicensePlan,
  updateLicenseStatus,
  revokeLicense,
  cancelLicense,
  isEventProcessed,
  markEventProcessed,
  deactivateAllDevices,
} from '../lib/db';
import { licenses } from '../db/schema';
import { eq, and } from 'drizzle-orm';
import { sendOpsAlert } from '../lib/alerts';

// Stripe event types we handle
type StripeEventType =
  | 'checkout.session.completed'
  | 'customer.subscription.created'
  | 'customer.subscription.updated'
  | 'customer.subscription.deleted'
  | 'customer.deleted'
  | 'invoice.paid'
  | 'invoice.payment_failed'
  | 'charge.refunded';

interface StripeEvent {
  id: string;
  type: string;
  data: {
    object: Record<string, unknown>;
  };
}

interface StripeSubscription {
  id: string;
  customer: string;
  status: string;
  items: {
    data: Array<{
      price: {
        id: string;
      };
      // API versions ≥2025-03-31 (basil/clover) moved the billing period
      // here from the subscription top level.
      current_period_start?: number;
      current_period_end?: number;
    }>;
  };
  // Present on API versions <2025-03-31 only — absent on real clover events.
  current_period_start?: number;
  current_period_end?: number;
  cancel_at_period_end: boolean;
}

/**
 * Resolve the billing period of a subscription across API versions.
 *
 * <2025-03-31: top-level `current_period_start/end`.
 * ≥2025-03-31 (basil/clover): moved to `items.data[].current_period_*`.
 * Verified against a real clover subscription (sub_1TpNk4AKLIiL9hdw5SKhWU18,
 * 2026-07-05) — this is why live licenses fell into the nowISO() fallback:
 * the top-level fields simply don't exist on current events.
 */
function getSubscriptionPeriod(subscription: StripeSubscription): {
  startISO: string | null;
  endISO: string | null;
} {
  const item = subscription.items?.data?.[0];
  const start =
    typeof subscription.current_period_start === 'number'
      ? subscription.current_period_start
      : typeof item?.current_period_start === 'number'
        ? item.current_period_start
        : null;
  const end =
    typeof subscription.current_period_end === 'number'
      ? subscription.current_period_end
      : typeof item?.current_period_end === 'number'
        ? item.current_period_end
        : null;
  return {
    startISO: start === null ? null : timestampToISO(start),
    endISO: end === null ? null : timestampToISO(end),
  };
}

interface StripeInvoice {
  id: string;
  customer: string;
  // Absent on API versions ≥2025-03-31 (basil/clover) — see `parent`.
  subscription?: string | null;
  status: string;
  // API versions ≥2025-03-31 moved the subscription id here.
  parent?: {
    type?: string;
    subscription_details?: {
      subscription?: string | null;
    } | null;
  } | null;
  lines: {
    data: Array<{
      period: {
        start: number;
        end: number;
      };
    }>;
  };
}

/**
 * Resolve the subscription id an invoice belongs to.
 *
 * API versions ≥2025-03-31 (basil, clover) removed the top-level
 * `invoice.subscription` field and moved it to
 * `parent.subscription_details.subscription`. Older-version events still
 * carry the top-level field, so keep it as a fallback. An invoice with
 * neither is genuinely not a subscription invoice.
 */
function getInvoiceSubscriptionId(invoice: StripeInvoice): string | null {
  return (
    invoice.parent?.subscription_details?.subscription ??
    invoice.subscription ??
    null
  );
}

interface StripeCheckoutSession {
  id: string;
  customer: string | null;
  // Stripe only populates the top-level customer_email when it was passed at
  // session creation. The email the customer actually entered always lands in
  // customer_details.email, so both must be consulted.
  customer_email: string | null;
  customer_details?: { email?: string | null } | null;
  subscription: string | null;
  mode: 'subscription' | 'payment' | 'setup';
  metadata?: Record<string, string>;
  line_items?: {
    data: Array<{
      price: {
        id: string;
      };
    }>;
  };
}

interface StripeCharge {
  id: string;
  customer: string | null;
  metadata?: Record<string, string>;
  payment_intent?: string;
}

/**
 * Verify Stripe webhook signature
 * Uses the Web Crypto API available in Cloudflare Workers
 */
async function verifyStripeSignature(
  payload: string,
  signature: string,
  secret: string
): Promise<boolean> {
  const parts = signature.split(',');
  const timestampPart = parts.find((p) => p.startsWith('t='));
  const signaturePart = parts.find((p) => p.startsWith('v1='));

  if (!timestampPart || !signaturePart) {
    return false;
  }

  const timestamp = timestampPart.slice(2);
  const expectedSignature = signaturePart.slice(3);

  // Check timestamp is within tolerance (5 minutes)
  const timestampNum = parseInt(timestamp, 10);
  const now = Math.floor(Date.now() / 1000);
  if (Math.abs(now - timestampNum) > 300) {
    return false;
  }

  // Compute expected signature
  const signedPayload = `${timestamp}.${payload}`;
  const encoder = new TextEncoder();

  const key = await crypto.subtle.importKey(
    'raw',
    encoder.encode(secret),
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign']
  );

  const signatureBuffer = await crypto.subtle.sign(
    'HMAC',
    key,
    encoder.encode(signedPayload)
  );

  // Convert to hex
  const computedSignature = Array.from(new Uint8Array(signatureBuffer))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('');

  // Constant-time comparison
  if (computedSignature.length !== expectedSignature.length) {
    return false;
  }

  let result = 0;
  for (let i = 0; i < computedSignature.length; i++) {
    result |= computedSignature.charCodeAt(i) ^ expectedSignature.charCodeAt(i);
  }

  return result === 0;
}

/**
 * Handle checkout.session.completed
 *
 * For subscription mode: Creates user, waits for subscription.created event
 * For payment mode (lifetime): Creates user + license immediately
 */
async function handleCheckoutCompleted(
  db: DrizzleDb,
  session: StripeCheckoutSession,
  env: Env
): Promise<void> {
  console.log(`[Stripe] Checkout completed: ${session.id}, mode: ${session.mode}`);

  // Resolve the customer email defensively: top-level customer_email is only
  // set when passed at session creation; the entered address always lands in
  // customer_details.email. (Mirrors checkout-license.ts.)
  const email = session.customer_email ?? session.customer_details?.email ?? null;
  if (!email) {
    // Nothing we can do without an email. Do NOT throw — a 5xx would make
    // Stripe retry this same emailless event for ~3 days to no effect.
    // Acknowledge and skip (the caller marks the event processed → 200).
    console.warn(
      `[Stripe] Checkout session ${session.id} has no resolvable email ` +
      `(customer_email and customer_details.email both empty). Acking and skipping.`
    );
    return;
  }

  // Find or create user first (needed for both modes)
  const user = await findOrCreateUser(db, email, session.customer ?? undefined);

  if (session.mode === 'subscription') {
    // For subscriptions, just ensure user exists. License created in subscription.created event.
    console.log(`[Stripe] Subscription checkout for user ${user.id}, waiting for subscription.created`);
    return;
  }

  if (session.mode === 'payment') {
    // For one-time payments (lifetime deals), create license immediately
    await createLifetimeLicense(db, session, user, env);
    return;
  }

  console.log(`[Stripe] Ignoring checkout mode: ${session.mode}`);
}

/**
 * Create a lifetime license from a one-time payment.
 * Uses session ID for idempotency.
 */
async function createLifetimeLicense(
  db: DrizzleDb,
  session: StripeCheckoutSession,
  user: { id: string; email: string },
  env: Env
): Promise<void> {
  // Idempotency check - ensure we don't process the same session twice
  const existingLicense = await getLicenseBySessionId(db, session.id);
  if (existingLicense) {
    console.log(`[Stripe] Session ${session.id} already processed, skipping`);
    return;
  }

  // Resolve the plan. CRITICAL: never default to a paid tier. If we cannot
  // determine the plan from the checkout metadata (our billing.ts always sets
  // metadata.plan) or from a mapped lifetime price, we must NOT guess — issuing
  // the wrong tier for a real payment is a revenue-integrity failure.
  const priceMapping = getStripePriceMapping(env);
  let plan: 'community' | 'pro' | 'team' | 'sovereign' | null = null;
  let priceId: string | null = null;

  // Try metadata first — only accept a recognized plan name.
  const metaPlan = session.metadata?.plan;
  if (metaPlan && metaPlan in PLAN_RANK) {
    plan = metaPlan as NonNullable<typeof plan>;
  }

  // Try line items — a mapped price is authoritative and overrides metadata.
  if (session.line_items?.data?.[0]?.price?.id) {
    priceId = session.line_items.data[0].price.id;
    const planInfo = priceMapping[priceId];
    if (planInfo) {
      plan = planInfo.plan;
    }
  }

  if (!plan) {
    // A payment was received but we cannot determine which tier to grant.
    // Do NOT issue a (wrong) license, do NOT 500 (retry yields no new info):
    // acknowledge, and flag loudly for manual intervention.
    const manualReviewDetail =
      `Lifetime payment with UNRESOLVABLE plan — NO license issued. ` +
      `session=${session.id}, user=${user.id}, email=${user.email}, ` +
      `priceId=${priceId ?? 'none'}, metadata.plan=${metaPlan ?? 'none'}. ` +
      `A payment was received but no plan could be determined; manual intervention required.`;
    console.error(`[Stripe][MANUAL_REVIEW] ${manualReviewDetail}`);
    // Push the same signal to a human (fail-open — never blocks the ack).
    await sendOpsAlert(env, 'Stripe MANUAL_REVIEW', manualReviewDetail);
    return;
  }

  console.log(`[Stripe] Creating Lifetime license: user=${user.id}, plan=${plan}`);

  // Create lifetime license
  try {
    await createLicense(db, {
      userId: user.id,
      licenseKey: generateLicenseKey(),
      plan,
      planType: 'lifetime',
      stripeSessionId: session.id,
      stripePriceId: priceId ?? undefined,
      currentPeriodStart: nowISO(),
      currentPeriodEnd: LIFETIME_EXPIRY,
    });

    console.log(`[Stripe] Lifetime license created for user ${user.id} (session ${session.id})`);
  } catch (error) {
    // Handle race condition: if UNIQUE constraint fails, check if license exists
    const existingAfterRace = await getLicenseBySessionId(db, session.id);
    if (existingAfterRace) {
      console.log(`[Stripe] License created by concurrent request for session ${session.id}`);
      return;
    }
    throw error;
  }
}

/**
 * Handle customer.subscription.created
 * Creates a new license for the subscription.
 *
 * EVENT ORDERING HANDLING:
 * Stripe often delivers `customer.subscription.created` BEFORE
 * `checkout.session.completed`, even though the latter logically precedes
 * the former. Rather than relying on Stripe's retry for the race, we
 * self-heal by fetching the customer's email directly from Stripe and
 * creating the user in-place. This works identically in production and
 * local `stripe listen` (which does not auto-retry 5xx responses).
 */
async function handleSubscriptionCreated(
  db: DrizzleDb,
  subscription: StripeSubscription,
  env: Env
): Promise<{ success: boolean; retry?: boolean }> {
  // Check if license already exists for this subscription (idempotency)
  const existingLicense = await getLicenseBySubscriptionId(db, subscription.id);
  if (existingLicense) {
    console.log(`[Stripe] License already exists for subscription ${subscription.id}`);
    return { success: true };
  }

  // Get user by Stripe customer ID — if not found, fetch email from Stripe
  // and create the user in place. This removes the "checkout.session.completed
  // hasn't fired yet" race entirely.
  let user = await getUserByStripeCustomerId(db, subscription.customer);
  if (!user) {
    const customerRes = await fetch(
      `https://api.stripe.com/v1/customers/${encodeURIComponent(subscription.customer)}`,
      { headers: { Authorization: `Bearer ${env.STRIPE_SECRET_KEY}` } }
    );
    if (!customerRes.ok) {
      console.warn(
        `[Stripe] Could not fetch customer ${subscription.customer} from Stripe ` +
        `(status ${customerRes.status}). Triggering retry.`
      );
      return { success: false, retry: true };
    }
    const customer = (await customerRes.json()) as {
      email?: string | null;
      deleted?: boolean;
    };
    if (!customer.email) {
      console.warn(
        `[Stripe] Customer ${subscription.customer} has no email. Triggering retry.`
      );
      return { success: false, retry: true };
    }
    user = await findOrCreateUser(db, customer.email, subscription.customer);
  }

  // Get plan from price ID
  const priceId = subscription.items.data[0]?.price.id ?? '';
  const plan = getPlanFromPriceId(priceId);

  // Billing period: top-level on old API versions, items.data[] on ≥2025-03-31
  // (clover). Reading items here is the §5 fix — it makes the first cycle's
  // period self-contained in this event instead of depending on invoice.paid,
  // whose delivery order Stripe explicitly does not guarantee. Falls back to
  // nowISO()/undefined only when neither location has the fields (in which
  // case a retried invoice.paid still backfills — see handleInvoicePaid).
  const period = getSubscriptionPeriod(subscription);
  const periodStart = period.startISO ?? nowISO();
  const periodEnd = period.endISO ?? undefined;

  // Create license. Schema has UNIQUE(stripe_subscription_id) as a safety net.
  try {
    await createLicense(db, {
      userId: user.id,
      licenseKey: generateLicenseKey(),
      plan,
      stripeSubscriptionId: subscription.id,
      stripePriceId: priceId,
      currentPeriodStart: periodStart,
      currentPeriodEnd: periodEnd,
    });

    console.log(`[Stripe] Created license for subscription ${subscription.id}`);
    return { success: true };
  } catch (error) {
    const existingAfterRace = await getLicenseBySubscriptionId(db, subscription.id);
    if (existingAfterRace) {
      console.log(`[Stripe] License created by concurrent request for ${subscription.id}`);
      return { success: true };
    }
    throw error;
  }
}

/**
 * Handle customer.subscription.updated
 * Updates plan and/or status
 *
 * IMPORTANT: On plan downgrade, we deactivate all devices to force re-activation
 * under the new (lower) device limits. This prevents users from keeping more
 * devices than their new plan allows.
 */
async function handleSubscriptionUpdated(
  db: DrizzleDb,
  subscription: StripeSubscription
): Promise<void> {
  const license = await getLicenseBySubscriptionId(db, subscription.id);
  if (!license) {
    console.error(`No license found for subscription ${subscription.id}`);
    return;
  }

  // Get updated plan from price ID
  const priceId = subscription.items.data[0]?.price.id ?? '';
  const newPlan = getPlanFromPriceId(priceId);
  const oldPlan = license.plan;

  // Map Stripe status to our status
  let status: 'active' | 'canceled' | 'expired' | 'past_due' | 'revoked';
  switch (subscription.status) {
    case 'active':
    case 'trialing':
      status = 'active';
      break;
    case 'past_due':
      status = 'past_due';
      break;
    case 'canceled':
    case 'unpaid':
      status = 'canceled';
      break;
    case 'incomplete':
    case 'incomplete_expired':
      status = 'expired';
      break;
    default:
      status = license.status; // Keep current status
  }

  // ─────────────────────────────────────────────────────────────────────────
  // PLAN DOWNGRADE HANDLING
  // ─────────────────────────────────────────────────────────────────────────
  // If user is downgrading (e.g., team → solo), deactivate all devices.
  // This forces re-activation under new limits and prevents users from
  // keeping more devices than their new plan allows.
  if (isPlanDowngrade(oldPlan, newPlan)) {
    console.log(
      `[Stripe] Plan downgrade detected: ${oldPlan} → ${newPlan} for license ${license.id}. ` +
      `Deactivating all devices to enforce new limits.`
    );

    const devicesDeactivated = await deactivateAllDevices(db, license.id);
    console.log(`[Stripe] Deactivated ${devicesDeactivated} devices for license ${license.id}`);
  }

  // Billing period across API versions (top-level, or items.data[] on
  // ≥2025-03-31) — see getSubscriptionPeriod. Fields stay undefined when
  // absent everywhere (P1-5: never corrupt existing values, never let an
  // unguarded timestampToISO(undefined) turn the plan change into a 500).
  const period = getSubscriptionPeriod(subscription);
  await updateLicensePlan(db, license.id, {
    plan: newPlan,
    status,
    stripePriceId: priceId,
    currentPeriodStart: period.startISO ?? undefined,
    currentPeriodEnd: period.endISO ?? undefined,
  });
}

/**
 * Handle customer.subscription.deleted
 * Marks license as canceled
 */
async function handleSubscriptionDeleted(
  db: DrizzleDb,
  subscription: StripeSubscription
): Promise<void> {
  const license = await getLicenseBySubscriptionId(db, subscription.id);
  if (!license) {
    console.error(`No license found for subscription ${subscription.id}`);
    return;
  }

  await cancelLicense(db, license.id);
  console.log(`[Stripe] License ${license.id} canceled`);
}

/**
 * Handle invoice.paid
 * Updates period dates and ensures active status
 */
async function handleInvoicePaid(
  db: DrizzleDb,
  invoice: StripeInvoice
): Promise<{ success: boolean; retry?: boolean }> {
  const subscriptionId = getInvoiceSubscriptionId(invoice);
  if (!subscriptionId) {
    return { success: true }; // Not a subscription invoice — acknowledge
  }

  const license = await getLicenseBySubscriptionId(db, subscriptionId);
  if (!license) {
    // §5 ordering race: Stripe doesn't guarantee event order, and invoice.paid
    // can land before customer.subscription.created has created the license
    // (observed twice on live, 2026-07-04). Do NOT mark the event processed —
    // return retry so the caller answers 500 and Stripe redelivers once the
    // license exists. Safety net only: the primary fix reads the period from
    // subscription.items in handleSubscriptionCreated.
    console.warn(
      `[Stripe] invoice.paid for subscription ${subscriptionId} arrived ` +
      `before its license exists. Triggering retry.`
    );
    return { success: false, retry: true };
  }

  // Get period from invoice line items. Setting absolute values keeps this
  // idempotent — redelivery writes the same period, never extends it.
  const lineItem = invoice.lines.data[0];
  if (lineItem) {
    await updateLicensePlan(db, license.id, {
      status: 'active',
      currentPeriodStart: timestampToISO(lineItem.period.start),
      currentPeriodEnd: timestampToISO(lineItem.period.end),
    });
  }
  return { success: true };
}

/**
 * Handle invoice.payment_failed
 * Sets status to past_due
 */
async function handlePaymentFailed(
  db: DrizzleDb,
  invoice: StripeInvoice
): Promise<void> {
  const subscriptionId = getInvoiceSubscriptionId(invoice);
  if (!subscriptionId) {
    return;
  }

  const license = await getLicenseBySubscriptionId(db, subscriptionId);
  if (!license) {
    console.error(`No license found for subscription ${subscriptionId}`);
    return;
  }

  await updateLicenseStatus(db, license.id, 'past_due');
}

interface StripeCustomer {
  id: string;
  email: string;
  deleted?: boolean;
}

/**
 * Handle customer.deleted
 * Expires all licenses for the customer
 */
async function handleCustomerDeleted(
  db: DrizzleDb,
  customer: StripeCustomer
): Promise<void> {
  // Get user by Stripe customer ID
  const user = await getUserByStripeCustomerId(db, customer.id);
  if (!user) {
    console.log(`No user found for deleted Stripe customer ${customer.id}`);
    return;
  }

  // Get all licenses for this user and mark them as expired
  const activeLicenses = await db.select({ id: licenses.id })
    .from(licenses)
    .where(and(eq(licenses.userId, user.id), eq(licenses.status, 'active')));

  for (const license of activeLicenses) {
    await updateLicenseStatus(db, license.id, 'expired');
  }

  console.log(`Expired ${activeLicenses.length} licenses for deleted customer ${customer.id}`);
}

/**
 * Handle charge.refunded
 * Revokes lifetime licenses when payment is refunded.
 *
 * NOTE: This only affects lifetime licenses. Subscription refunds are handled
 * through subscription.deleted event which is triggered by Stripe when a
 * subscription is canceled after refund.
 */
async function handleChargeRefunded(
  db: DrizzleDb,
  charge: StripeCharge,
  env: Env
): Promise<void> {
  console.log(`[Stripe] Charge refunded: ${charge.id}`);

  // Exact resolution first: map the charge to the checkout session it paid
  // for and revoke that specific license. Lifetime charges usually carry NO
  // customer (checkout payment mode defaults to customer_creation=
  // if_required), and the customer heuristic below picks the *most recent*
  // lifetime license — wrong when an account holds several.
  if (charge.payment_intent) {
    const resolved = await revokeLicenseByPaymentIntent(db, charge, env);
    if (resolved) return;
  }

  // Fallback: legacy events without payment_intent, or no session/license
  // matched — resolve via customer → most recent lifetime license.
  if (!charge.customer) {
    console.warn(`[Stripe] No customer on refunded charge ${charge.id}`);
    return;
  }

  // Get user by Stripe customer ID
  const user = await getUserByStripeCustomerId(db, charge.customer);
  if (!user) {
    console.warn(`[Stripe] No user found for refunded charge customer ${charge.customer}`);
    return;
  }

  // Find the most recent lifetime license for this user
  const license = await getLifetimeLicenseByUserId(db, user.id);

  if (!license) {
    console.log(`[Stripe] No lifetime license found for user ${user.id}, ignoring refund`);
    return;
  }

  // Only revoke if it's an active lifetime license
  if (license.planType !== 'lifetime') {
    console.log(`[Stripe] License ${license.id} is not lifetime (${license.planType}), ignoring refund`);
    return;
  }

  if (license.status !== 'active') {
    console.log(`[Stripe] License ${license.id} already ${license.status}, ignoring refund`);
    return;
  }

  // Revoke the license
  await revokeLicense(db, license.id, `Refunded: charge_${charge.id}`);
  console.log(`[Stripe] Lifetime license ${license.id} revoked due to refund`);
}

/**
 * Resolve the exact license a refunded charge paid for:
 * charge.payment_intent → checkout session → licenses.stripe_session_id.
 *
 * Returns true when the charge was definitively resolved to a license
 * (revoked, or deliberately skipped because it isn't an active lifetime
 * license). Returns false when no session/license matched, so the caller
 * may fall back to the customer heuristic.
 */
async function revokeLicenseByPaymentIntent(
  db: DrizzleDb,
  charge: StripeCharge,
  env: Env
): Promise<boolean> {
  let sessionId: string | undefined;
  try {
    const res = await fetch(
      `https://api.stripe.com/v1/checkout/sessions?payment_intent=${encodeURIComponent(
        charge.payment_intent ?? ''
      )}&limit=1`,
      { headers: { Authorization: `Bearer ${env.STRIPE_SECRET_KEY}` } }
    );
    if (!res.ok) {
      console.warn(
        `[Stripe] Session lookup for payment_intent ${charge.payment_intent} ` +
        `failed (status ${res.status}). Falling back to customer resolution.`
      );
      return false;
    }
    const body = (await res.json()) as { data?: Array<{ id?: string }> };
    sessionId = body.data?.[0]?.id;
  } catch (error) {
    console.warn(
      `[Stripe] Session lookup for payment_intent ${charge.payment_intent} ` +
      `threw: ${error instanceof Error ? error.message : String(error)}. ` +
      `Falling back to customer resolution.`
    );
    return false;
  }

  if (!sessionId) {
    return false; // Charge wasn't made through Checkout (or session expired).
  }

  const license = await getLicenseBySessionId(db, sessionId);
  if (!license) {
    return false; // e.g. subscription checkout — no session id on the license.
  }

  if (license.planType !== 'lifetime') {
    console.log(
      `[Stripe] License ${license.id} for session ${sessionId} is not ` +
      `lifetime (${license.planType}), ignoring refund`
    );
    return true;
  }

  if (license.status !== 'active') {
    console.log(
      `[Stripe] License ${license.id} already ${license.status}, ignoring refund`
    );
    return true;
  }

  await revokeLicense(db, license.id, `Refunded: charge_${charge.id}`);
  console.log(
    `[Stripe] Lifetime license ${license.id} revoked due to refund ` +
    `(resolved via payment_intent ${charge.payment_intent})`
  );
  return true;
}

/**
 * Main webhook handler
 */
export async function handleStripeWebhook(
  request: Request,
  env: Env
): Promise<Response> {
  try {
    // Validate webhook secret is configured
    if (!env.STRIPE_WEBHOOK_SECRET) {
      console.error('STRIPE_WEBHOOK_SECRET not configured');
      return new Response(JSON.stringify({ error: 'Webhook not configured' }), {
        status: 503,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    // Get signature header
    const signature = request.headers.get('stripe-signature');
    if (!signature) {
      return new Response(JSON.stringify({ error: 'Missing signature' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    // Get raw body
    const payload = await request.text();

    // Verify signature
    const isValid = await verifyStripeSignature(
      payload,
      signature,
      env.STRIPE_WEBHOOK_SECRET
    );

    if (!isValid) {
      console.error('Invalid Stripe webhook signature');
      return new Response(JSON.stringify({ error: 'Invalid signature' }), {
        status: 401,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    // Parse event
    const event: StripeEvent = JSON.parse(payload);

    // Create Drizzle DB instance
    const db = createDb(env.DB);

    // Idempotency check
    const alreadyProcessed = await isEventProcessed(db, event.id);
    if (alreadyProcessed) {
      return new Response(JSON.stringify({ received: true, duplicate: true }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    // Process event based on type
    switch (event.type as StripeEventType) {
      case 'checkout.session.completed':
        await handleCheckoutCompleted(
          db,
          event.data.object as unknown as StripeCheckoutSession,
          env
        );
        break;

      case 'customer.subscription.created': {
        const result = await handleSubscriptionCreated(
          db,
          event.data.object as unknown as StripeSubscription,
          env
        );
        if (!result.success && result.retry) {
          // Return 500 to trigger Stripe retry
          return new Response(JSON.stringify({
            error: 'User not found yet, retry needed',
            retry: true,
          }), {
            status: 500,
            headers: { 'Content-Type': 'application/json' },
          });
        }
        break;
      }

      case 'customer.subscription.updated':
        await handleSubscriptionUpdated(
          db,
          event.data.object as unknown as StripeSubscription
        );
        break;

      case 'customer.subscription.deleted':
        await handleSubscriptionDeleted(
          db,
          event.data.object as unknown as StripeSubscription
        );
        break;

      case 'invoice.paid': {
        const result = await handleInvoicePaid(
          db,
          event.data.object as unknown as StripeInvoice
        );
        if (!result.success && result.retry) {
          // Early return skips markEventProcessed — Stripe will redeliver
          // this event id and it will be processed for real next time.
          return new Response(JSON.stringify({
            error: 'License not found yet, retry needed',
            retry: true,
          }), {
            status: 500,
            headers: { 'Content-Type': 'application/json' },
          });
        }
        break;
      }

      case 'invoice.payment_failed':
        await handlePaymentFailed(
          db,
          event.data.object as unknown as StripeInvoice
        );
        break;

      case 'customer.deleted':
        await handleCustomerDeleted(
          db,
          event.data.object as unknown as StripeCustomer
        );
        break;

      case 'charge.refunded':
        await handleChargeRefunded(
          db,
          event.data.object as unknown as StripeCharge,
          env
        );
        break;

      default:
        // Unhandled event type - log and acknowledge
        console.log(`Unhandled Stripe event type: ${event.type}`);
    }

    // Mark event as processed
    await markEventProcessed(db, event.id, event.type);

    return new Response(JSON.stringify({ received: true }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
  } catch (error) {
    console.error('Stripe webhook error:', error);

    if (error instanceof SyntaxError) {
      return new Response(JSON.stringify({ error: 'Invalid JSON' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    return new Response(JSON.stringify({ error: 'Internal server error' }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' },
    });
  }
}
