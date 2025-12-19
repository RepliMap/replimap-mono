/**
 * Stripe Webhook Handler
 * POST /v1/webhooks/stripe
 *
 * Handles Stripe subscription lifecycle events
 */

import type { Env } from '../types/env';
import { generateLicenseKey, timestampToISO } from '../lib/license';
import { getPlanFromPriceId } from '../lib/constants';
import {
  findOrCreateUser,
  getUserByStripeCustomerId,
  createLicense,
  getLicenseBySubscriptionId,
  updateLicensePlan,
  updateLicenseStatus,
  isEventProcessed,
  markEventProcessed,
} from '../lib/db';

// Stripe event types we handle
type StripeEventType =
  | 'checkout.session.completed'
  | 'customer.subscription.created'
  | 'customer.subscription.updated'
  | 'customer.subscription.deleted'
  | 'customer.deleted'
  | 'invoice.paid'
  | 'invoice.payment_failed';

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
    }>;
  };
  current_period_start: number;
  current_period_end: number;
  cancel_at_period_end: boolean;
}

interface StripeInvoice {
  id: string;
  customer: string;
  subscription: string;
  status: string;
  lines: {
    data: Array<{
      period: {
        start: number;
        end: number;
      };
    }>;
  };
}

interface StripeCheckoutSession {
  id: string;
  customer: string;
  customer_email: string;
  subscription: string;
  mode: string;
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
 * Creates user if needed, prepares for subscription creation
 */
async function handleCheckoutCompleted(
  db: D1Database,
  session: StripeCheckoutSession
): Promise<void> {
  if (session.mode !== 'subscription') {
    return; // Only handle subscription checkouts
  }

  // Find or create user
  await findOrCreateUser(db, session.customer_email, session.customer);
}

/**
 * Handle customer.subscription.created
 * Creates a new license for the subscription
 */
async function handleSubscriptionCreated(
  db: D1Database,
  subscription: StripeSubscription
): Promise<void> {
  // Check if license already exists for this subscription
  const existingLicense = await getLicenseBySubscriptionId(db, subscription.id);
  if (existingLicense) {
    return; // Already processed
  }

  // Get user by Stripe customer ID
  // Note: User should have been created by checkout.session.completed event
  // If user doesn't exist, checkout.session.completed may have failed - Stripe will retry
  const user = await getUserByStripeCustomerId(db, subscription.customer);
  if (!user) {
    // This could happen if checkout.session.completed wasn't processed yet
    // Throwing error will cause Stripe to retry the webhook
    throw new Error(`No user found for Stripe customer ${subscription.customer}. Checkout may not have been processed yet.`);
  }

  // Get plan from price ID
  const priceId = subscription.items.data[0]?.price.id ?? '';
  const plan = getPlanFromPriceId(priceId);

  // Create license
  await createLicense(db, {
    userId: user.id,
    licenseKey: generateLicenseKey(),
    plan,
    stripeSubscriptionId: subscription.id,
    stripePriceId: priceId,
    currentPeriodStart: timestampToISO(subscription.current_period_start),
    currentPeriodEnd: timestampToISO(subscription.current_period_end),
  });
}

/**
 * Handle customer.subscription.updated
 * Updates plan and/or status
 */
async function handleSubscriptionUpdated(
  db: D1Database,
  subscription: StripeSubscription
): Promise<void> {
  const license = await getLicenseBySubscriptionId(db, subscription.id);
  if (!license) {
    console.error(`No license found for subscription ${subscription.id}`);
    return;
  }

  // Get updated plan from price ID
  const priceId = subscription.items.data[0]?.price.id ?? '';
  const plan = getPlanFromPriceId(priceId);

  // Map Stripe status to our status
  let status: string;
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

  await updateLicensePlan(db, license.id, {
    plan,
    status,
    stripePriceId: priceId,
    currentPeriodStart: timestampToISO(subscription.current_period_start),
    currentPeriodEnd: timestampToISO(subscription.current_period_end),
  });
}

/**
 * Handle customer.subscription.deleted
 * Marks license as canceled
 */
async function handleSubscriptionDeleted(
  db: D1Database,
  subscription: StripeSubscription
): Promise<void> {
  const license = await getLicenseBySubscriptionId(db, subscription.id);
  if (!license) {
    console.error(`No license found for subscription ${subscription.id}`);
    return;
  }

  await updateLicenseStatus(db, license.id, 'canceled');
}

/**
 * Handle invoice.paid
 * Updates period dates and ensures active status
 */
async function handleInvoicePaid(
  db: D1Database,
  invoice: StripeInvoice
): Promise<void> {
  if (!invoice.subscription) {
    return; // Not a subscription invoice
  }

  const license = await getLicenseBySubscriptionId(db, invoice.subscription);
  if (!license) {
    console.error(`No license found for subscription ${invoice.subscription}`);
    return;
  }

  // Get period from invoice line items
  const lineItem = invoice.lines.data[0];
  if (lineItem) {
    await updateLicensePlan(db, license.id, {
      status: 'active',
      currentPeriodStart: timestampToISO(lineItem.period.start),
      currentPeriodEnd: timestampToISO(lineItem.period.end),
    });
  }
}

/**
 * Handle invoice.payment_failed
 * Sets status to past_due
 */
async function handlePaymentFailed(
  db: D1Database,
  invoice: StripeInvoice
): Promise<void> {
  if (!invoice.subscription) {
    return;
  }

  const license = await getLicenseBySubscriptionId(db, invoice.subscription);
  if (!license) {
    console.error(`No license found for subscription ${invoice.subscription}`);
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
  db: D1Database,
  customer: StripeCustomer
): Promise<void> {
  // Get user by Stripe customer ID
  const user = await getUserByStripeCustomerId(db, customer.id);
  if (!user) {
    console.log(`No user found for deleted Stripe customer ${customer.id}`);
    return;
  }

  // Get all licenses for this user and mark them as expired
  const licenses = await db.prepare(`
    SELECT id FROM licenses WHERE user_id = ? AND status = 'active'
  `).bind(user.id).all<{ id: string }>();

  for (const license of licenses.results) {
    await updateLicenseStatus(db, license.id, 'expired');
  }

  console.log(`Expired ${licenses.results.length} licenses for deleted customer ${customer.id}`);
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

    // Idempotency check
    const alreadyProcessed = await isEventProcessed(env.DB, event.id);
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
          env.DB,
          event.data.object as unknown as StripeCheckoutSession
        );
        break;

      case 'customer.subscription.created':
        await handleSubscriptionCreated(
          env.DB,
          event.data.object as unknown as StripeSubscription
        );
        break;

      case 'customer.subscription.updated':
        await handleSubscriptionUpdated(
          env.DB,
          event.data.object as unknown as StripeSubscription
        );
        break;

      case 'customer.subscription.deleted':
        await handleSubscriptionDeleted(
          env.DB,
          event.data.object as unknown as StripeSubscription
        );
        break;

      case 'invoice.paid':
        await handleInvoicePaid(
          env.DB,
          event.data.object as unknown as StripeInvoice
        );
        break;

      case 'invoice.payment_failed':
        await handlePaymentFailed(
          env.DB,
          event.data.object as unknown as StripeInvoice
        );
        break;

      case 'customer.deleted':
        await handleCustomerDeleted(
          env.DB,
          event.data.object as unknown as StripeCustomer
        );
        break;

      default:
        // Unhandled event type - log and acknowledge
        console.log(`Unhandled Stripe event type: ${event.type}`);
    }

    // Mark event as processed
    await markEventProcessed(env.DB, event.id, event.type);

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
