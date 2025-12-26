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
 *
 * RACE CONDITION HANDLING:
 * If user doesn't exist yet (checkout.session.completed hasn't fired),
 * we return a 500 error to trigger Stripe's exponential backoff retry.
 * This is the expected behavior - Stripe will retry until user exists.
 */
async function handleSubscriptionCreated(
  db: D1Database,
  subscription: StripeSubscription
): Promise<{ success: boolean; retry?: boolean }> {
  // Check if license already exists for this subscription (idempotency)
  const existingLicense = await getLicenseBySubscriptionId(db, subscription.id);
  if (existingLicense) {
    console.log(`[Stripe] License already exists for subscription ${subscription.id}`);
    return { success: true }; // Already processed
  }

  // Get user by Stripe customer ID
  // Note: User should have been created by checkout.session.completed event
  const user = await getUserByStripeCustomerId(db, subscription.customer);
  if (!user) {
    // Race condition: checkout.session.completed hasn't fired yet
    // Return 500 to trigger Stripe retry with exponential backoff
    console.warn(
      `[Stripe] User not found for customer ${subscription.customer}. ` +
      `This is expected if checkout.session.completed hasn't fired yet. ` +
      `Triggering retry...`
    );
    return { success: false, retry: true };
  }

  // Get plan from price ID
  const priceId = subscription.items.data[0]?.price.id ?? '';
  const plan = getPlanFromPriceId(priceId);

  // Create license
  // Note: Schema has UNIQUE constraint on stripe_subscription_id for extra safety.
  // If a race condition causes duplicate INSERT, SQLite will reject it and
  // Stripe's retry will find the existing license via the check above.
  try {
    await createLicense(db, {
      userId: user.id,
      licenseKey: generateLicenseKey(),
      plan,
      stripeSubscriptionId: subscription.id,
      stripePriceId: priceId,
      currentPeriodStart: timestampToISO(subscription.current_period_start),
      currentPeriodEnd: timestampToISO(subscription.current_period_end),
    });

    console.log(`[Stripe] Created license for subscription ${subscription.id}`);
    return { success: true };
  } catch (error) {
    // Handle race condition: if UNIQUE constraint fails, check if license exists
    const existingAfterRace = await getLicenseBySubscriptionId(db, subscription.id);
    if (existingAfterRace) {
      console.log(`[Stripe] License created by concurrent request for ${subscription.id}`);
      return { success: true };
    }
    throw error; // Re-throw if it's a different error
  }
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

      case 'customer.subscription.created': {
        const result = await handleSubscriptionCreated(
          env.DB,
          event.data.object as unknown as StripeSubscription
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
