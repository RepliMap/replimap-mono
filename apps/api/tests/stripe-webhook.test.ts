/**
 * Tests for the REAL Stripe webhook handler (handleStripeWebhook).
 *
 * Every test in this file:
 *   - invokes the actual exported handler with a Request object,
 *   - signs payloads with the genuine Stripe HMAC-SHA256 scheme
 *     (no crypto stubbing — the production verifyStripeSignature runs as-is),
 *   - asserts against a real D1 database (Miniflare/workerd SQLite) with the
 *     production schema applied, so UNIQUE constraints and ON CONFLICT
 *     behavior are the real thing.
 *
 * The only stub is `fetch` for api.stripe.com in the subscription.created
 * self-heal path — unavoidable, since tests must not call Stripe.
 */

import {
  describe,
  it,
  expect,
  beforeAll,
  afterAll,
  beforeEach,
  afterEach,
  vi,
} from 'vitest';
import { handleStripeWebhook } from '../src/handlers/stripe-webhook';
import { LIFETIME_EXPIRY } from '../src/lib/constants';
import type { Env } from '../src/types/env';
import { createDb, findOrCreateUser } from '../src/lib/db';
import { AppError } from '../src/lib/errors';
import {
  createRealD1,
  realEnv,
  signedWebhookRequest,
  stripeSignatureHeader,
  TEST_WEBHOOK_SECRET,
  type RealD1,
} from './real-d1';

// ============================================================================
// Harness
// ============================================================================

let d1: RealD1;
let env: Env;

beforeAll(async () => {
  d1 = await createRealD1();
  env = realEnv(d1.DB);
}, 30_000);

afterAll(async () => {
  await d1.dispose();
});

beforeEach(async () => {
  await d1.reset();
  // Keep test output clean — the handler logs operational messages.
  vi.spyOn(console, 'log').mockImplementation(() => {});
  vi.spyOn(console, 'warn').mockImplementation(() => {});
  vi.spyOn(console, 'error').mockImplementation(() => {});
});

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

// ============================================================================
// Event fixtures — realistic payload subsets (note: real webhook events do
// NOT include expanded line_items; plan resolution relies on metadata).
// ============================================================================

let eventSeq = 0;
function eventId(): string {
  return `evt_test_${String(++eventSeq).padStart(6, '0')}`;
}

const CUSTOMER = 'cus_TestCustomer01';
const EMAIL = 'buyer@example.com';
const SUBSCRIPTION = 'sub_TestSub01';
const PRO_MONTHLY_PRICE = 'price_1SiMYgAKLIiL9hdwZLjLUOPm'; // real mapping: pro
const TEAM_MONTHLY_PRICE = 'price_1SiMZvAKLIiL9hdw8LAIvjrS'; // real mapping: team

const PERIOD_START = 1_750_000_000;
const PERIOD_END = 1_752_600_000;

function checkoutCompletedEvent(
  overrides: Record<string, unknown> = {},
  id = eventId()
) {
  return {
    id,
    type: 'checkout.session.completed',
    data: {
      object: {
        id: 'cs_test_Session01',
        customer: CUSTOMER,
        customer_email: EMAIL,
        subscription: SUBSCRIPTION,
        mode: 'subscription',
        metadata: { plan: 'pro', billing_period: 'monthly' },
        ...overrides,
      },
    },
  };
}

function subscriptionEvent(
  type:
    | 'customer.subscription.created'
    | 'customer.subscription.updated'
    | 'customer.subscription.deleted',
  overrides: Record<string, unknown> = {},
  id = eventId()
) {
  return {
    id,
    type,
    data: {
      object: {
        id: SUBSCRIPTION,
        customer: CUSTOMER,
        status: 'active',
        items: { data: [{ price: { id: PRO_MONTHLY_PRICE } }] },
        current_period_start: PERIOD_START,
        current_period_end: PERIOD_END,
        cancel_at_period_end: false,
        ...overrides,
      },
    },
  };
}

function invoiceEvent(
  type: 'invoice.paid' | 'invoice.payment_failed',
  overrides: Record<string, unknown> = {},
  id = eventId()
) {
  return {
    id,
    type,
    data: {
      object: {
        id: 'in_test_Invoice01',
        customer: CUSTOMER,
        subscription: SUBSCRIPTION,
        status: type === 'invoice.paid' ? 'paid' : 'open',
        lines: {
          data: [
            { period: { start: PERIOD_START + 100, end: PERIOD_END + 100 } },
          ],
        },
        ...overrides,
      },
    },
  };
}

async function deliver(event: Record<string, unknown>): Promise<Response> {
  return handleStripeWebhook(await signedWebhookRequest(event), env);
}

/** Seed a subscription license via the real event flow. */
async function seedSubscriptionLicense(): Promise<void> {
  expect((await deliver(checkoutCompletedEvent())).status).toBe(200);
  expect(
    (await deliver(subscriptionEvent('customer.subscription.created'))).status
  ).toBe(200);
}

async function rows<T = Record<string, unknown>>(sql: string): Promise<T[]> {
  const result = await env.DB.prepare(sql).all();
  return result.results as T[];
}

async function licenseRows() {
  return rows<{
    id: string;
    plan: string;
    plan_type: string;
    status: string;
    license_key: string;
    stripe_subscription_id: string | null;
    stripe_session_id: string | null;
    current_period_start: string | null;
    current_period_end: string | null;
    revoked_reason: string | null;
  }>('SELECT * FROM licenses');
}

// ============================================================================
// Signature verification (real HMAC, real verifier)
// ============================================================================

describe('signature verification', () => {
  it('accepts a correctly signed payload', async () => {
    const res = await deliver(checkoutCompletedEvent());
    expect(res.status).toBe(200);
    expect(await res.json()).toEqual({ received: true });
  });

  it('rejects a payload signed with the wrong secret', async () => {
    const req = await signedWebhookRequest(checkoutCompletedEvent(), {
      secret: 'whsec_attacker_forged_secret',
    });
    const res = await handleStripeWebhook(req, env);
    expect(res.status).toBe(401);
    // No side effects: no user, no processed event.
    expect(await rows('SELECT * FROM user')).toHaveLength(0);
    expect(await rows('SELECT * FROM processed_events')).toHaveLength(0);
  });

  it('rejects a payload tampered with after signing', async () => {
    const req = await signedWebhookRequest(checkoutCompletedEvent(), {
      tamper: (payload) => payload.replace(EMAIL, 'attacker@evil.example'),
    });
    const res = await handleStripeWebhook(req, env);
    expect(res.status).toBe(401);
    expect(await rows('SELECT * FROM user')).toHaveLength(0);
  });

  it('rejects a missing stripe-signature header', async () => {
    const req = new Request('https://api.test/v1/webhooks/stripe', {
      method: 'POST',
      body: JSON.stringify(checkoutCompletedEvent()),
    });
    const res = await handleStripeWebhook(req, env);
    expect(res.status).toBe(400);
  });

  it('rejects a stale timestamp outside the 5-minute tolerance', async () => {
    const req = await signedWebhookRequest(checkoutCompletedEvent(), {
      timestamp: Math.floor(Date.now() / 1000) - 600,
    });
    const res = await handleStripeWebhook(req, env);
    expect(res.status).toBe(401);
  });

  it('returns 503 when STRIPE_WEBHOOK_SECRET is not configured', async () => {
    const req = await signedWebhookRequest(checkoutCompletedEvent());
    const res = await handleStripeWebhook(
      req,
      realEnv(d1.DB, { STRIPE_WEBHOOK_SECRET: '' as unknown as string })
    );
    expect(res.status).toBe(503);
  });
});

// ============================================================================
// Idempotency & duplicate delivery
// ============================================================================

describe('idempotency', () => {
  it('processes the same event id only once on sequential redelivery', async () => {
    const event = checkoutCompletedEvent(
      {
        mode: 'payment',
        subscription: null,
        metadata: { plan: 'pro', billing_period: 'lifetime' },
      },
      'evt_dup_sequential'
    );

    const first = await deliver(event);
    expect(first.status).toBe(200);
    expect(await first.json()).toEqual({ received: true });

    const second = await deliver(event);
    expect(second.status).toBe(200);
    expect(await second.json()).toEqual({ received: true, duplicate: true });

    expect(await licenseRows()).toHaveLength(1);
    expect(await rows('SELECT * FROM processed_events')).toHaveLength(1);
  });

  it('issues exactly one license under CONCURRENT duplicate delivery of the same event', async () => {
    const event = checkoutCompletedEvent(
      {
        mode: 'payment',
        subscription: null,
        metadata: { plan: 'team', billing_period: 'lifetime' },
      },
      'evt_dup_concurrent'
    );

    // Simulate Stripe redelivering the same event 5 times concurrently.
    // The check-then-act on processed_events can race; the UNIQUE constraint
    // on licenses.stripe_session_id plus the race fallback must hold the line.
    const responses = await Promise.all(
      Array.from({ length: 5 }, () => deliver(event))
    );

    for (const res of responses) {
      expect(res.status).toBe(200);
    }
    expect(await licenseRows()).toHaveLength(1);
    expect(await rows('SELECT * FROM processed_events')).toHaveLength(1);
  });

  it('issues exactly one license when subscription.created is redelivered with different event ids', async () => {
    await deliver(checkoutCompletedEvent());

    // Stripe retries reuse the same event id, but defensive coding should
    // also hold when the same subscription arrives under two distinct events.
    const first = subscriptionEvent(
      'customer.subscription.created',
      {},
      'evt_sub_a'
    );
    const second = subscriptionEvent(
      'customer.subscription.created',
      {},
      'evt_sub_b'
    );

    expect((await deliver(first)).status).toBe(200);
    expect((await deliver(second)).status).toBe(200);

    expect(await licenseRows()).toHaveLength(1);
  });

  it('issues exactly one license under concurrent lifetime redelivery with different event ids', async () => {
    const eventA = checkoutCompletedEvent(
      {
        mode: 'payment',
        subscription: null,
        metadata: { plan: 'pro', billing_period: 'lifetime' },
      },
      'evt_life_a'
    );
    const eventB = checkoutCompletedEvent(
      {
        mode: 'payment',
        subscription: null,
        metadata: { plan: 'pro', billing_period: 'lifetime' },
      },
      'evt_life_b'
    );

    const [resA, resB] = await Promise.all([deliver(eventA), deliver(eventB)]);
    expect(resA.status).toBe(200);
    expect(resB.status).toBe(200);

    // Same checkout session → UNIQUE(stripe_session_id) race fallback → one license.
    expect(await licenseRows()).toHaveLength(1);
  });
});

// ============================================================================
// checkout.session.completed
// ============================================================================

describe('checkout.session.completed', () => {
  it('subscription mode: creates the user, defers license to subscription.created', async () => {
    const res = await deliver(checkoutCompletedEvent());
    expect(res.status).toBe(200);

    const users = await rows<{ email: string; customer_id: string }>(
      'SELECT * FROM user'
    );
    expect(users).toHaveLength(1);
    expect(users[0].email).toBe(EMAIL);
    expect(users[0].customer_id).toBe(CUSTOMER);

    expect(await licenseRows()).toHaveLength(0);
  });

  it('payment mode (lifetime): creates user + license immediately, plan from metadata', async () => {
    // Real webhook payloads do NOT include expanded line_items — the plan
    // must resolve from checkout metadata (set by handleCreateCheckout).
    const res = await deliver(
      checkoutCompletedEvent({
        mode: 'payment',
        subscription: null,
        metadata: { plan: 'team', billing_period: 'lifetime' },
      })
    );
    expect(res.status).toBe(200);

    const licenses = await licenseRows();
    expect(licenses).toHaveLength(1);
    expect(licenses[0].plan).toBe('team');
    expect(licenses[0].plan_type).toBe('lifetime');
    expect(licenses[0].status).toBe('active');
    expect(licenses[0].stripe_session_id).toBe('cs_test_Session01');
    expect(licenses[0].current_period_end).toBe(LIFETIME_EXPIRY);
    expect(licenses[0].license_key).toMatch(
      /^RM-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$/
    );
  });

  it('setup mode: acknowledged without side effects', async () => {
    const res = await deliver(checkoutCompletedEvent({ mode: 'setup' }));
    expect(res.status).toBe(200);
    expect(await licenseRows()).toHaveLength(0);
  });
});

// ============================================================================
// customer.subscription.created
// ============================================================================

describe('customer.subscription.created', () => {
  it('creates an active license with the plan mapped from the real price id', async () => {
    await seedSubscriptionLicense();

    const licenses = await licenseRows();
    expect(licenses).toHaveLength(1);
    expect(licenses[0].plan).toBe('pro');
    expect(licenses[0].status).toBe('active');
    expect(licenses[0].stripe_subscription_id).toBe(SUBSCRIPTION);
    expect(licenses[0].current_period_start).toBe(
      new Date(PERIOD_START * 1000).toISOString()
    );
    expect(licenses[0].current_period_end).toBe(
      new Date(PERIOD_END * 1000).toISOString()
    );
  });

  it('self-heals a missing user by fetching the customer from Stripe', async () => {
    // subscription.created arrives BEFORE checkout.session.completed —
    // the documented Stripe event-ordering race.
    const fetchSpy = vi.fn(async (input: RequestInfo | URL) => {
      expect(String(input)).toBe(
        `https://api.stripe.com/v1/customers/${CUSTOMER}`
      );
      return new Response(JSON.stringify({ id: CUSTOMER, email: EMAIL }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      });
    });
    vi.stubGlobal('fetch', fetchSpy);

    const res = await deliver(
      subscriptionEvent('customer.subscription.created')
    );
    expect(res.status).toBe(200);
    expect(fetchSpy).toHaveBeenCalledTimes(1);

    const users = await rows<{ email: string }>('SELECT * FROM user');
    expect(users).toHaveLength(1);
    expect(users[0].email).toBe(EMAIL);
    expect(await licenseRows()).toHaveLength(1);
  });

  it('returns 500 (Stripe retry) and does NOT mark the event processed when the customer fetch fails', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => new Response('{}', { status: 500 }))
    );

    const event = subscriptionEvent(
      'customer.subscription.created',
      {},
      'evt_retry_me'
    );
    const res = await deliver(event);
    expect(res.status).toBe(500);

    // Crucial for retry semantics: the event must remain unprocessed so the
    // idempotency check does not swallow Stripe's retry.
    expect(await rows('SELECT * FROM processed_events')).toHaveLength(0);
    expect(await licenseRows()).toHaveLength(0);
  });

  it('tolerates missing period fields on newly created subscriptions', async () => {
    await deliver(checkoutCompletedEvent());
    const res = await deliver(
      subscriptionEvent('customer.subscription.created', {
        current_period_start: undefined,
        current_period_end: undefined,
      })
    );
    expect(res.status).toBe(200);

    const licenses = await licenseRows();
    expect(licenses).toHaveLength(1);
    expect(licenses[0].current_period_start).not.toBeNull(); // backfilled with now
  });
});

// ============================================================================
// customer.subscription.updated
// ============================================================================

describe('customer.subscription.updated', () => {
  it('upgrade pro→team updates the plan and keeps devices active', async () => {
    await seedSubscriptionLicense();
    const [{ id: licenseId }] = await licenseRows();
    await env.DB.prepare(
      `INSERT INTO license_machines (id, license_id, machine_id, is_active, first_seen_at, last_seen_at)
       VALUES ('m1', ?, 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa', 1, datetime('now'), datetime('now'))`
    )
      .bind(licenseId)
      .run();

    const res = await deliver(
      subscriptionEvent('customer.subscription.updated', {
        items: { data: [{ price: { id: TEAM_MONTHLY_PRICE } }] },
      })
    );
    expect(res.status).toBe(200);

    const licenses = await licenseRows();
    expect(licenses[0].plan).toBe('team');
    const machines = await rows<{ is_active: number }>(
      'SELECT is_active FROM license_machines'
    );
    expect(machines[0].is_active).toBe(1);
  });

  it('downgrade team→pro deactivates all devices to re-enforce limits', async () => {
    await deliver(checkoutCompletedEvent());
    await deliver(
      subscriptionEvent('customer.subscription.created', {
        items: { data: [{ price: { id: TEAM_MONTHLY_PRICE } }] },
      })
    );
    const [{ id: licenseId }] = await licenseRows();
    await env.DB.prepare(
      `INSERT INTO license_machines (id, license_id, machine_id, is_active, first_seen_at, last_seen_at)
       VALUES ('m1', ?, 'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb', 1, datetime('now'), datetime('now'))`
    )
      .bind(licenseId)
      .run();

    const res = await deliver(
      subscriptionEvent('customer.subscription.updated', {
        items: { data: [{ price: { id: PRO_MONTHLY_PRICE } }] },
      })
    );
    expect(res.status).toBe(200);

    const licenses = await licenseRows();
    expect(licenses[0].plan).toBe('pro');
    const machines = await rows<{ is_active: number }>(
      'SELECT is_active FROM license_machines'
    );
    expect(machines[0].is_active).toBe(0);
  });

  it('maps Stripe status past_due onto the license', async () => {
    await seedSubscriptionLicense();

    const res = await deliver(
      subscriptionEvent('customer.subscription.updated', {
        status: 'past_due',
      })
    );
    expect(res.status).toBe(200);

    const licenses = await licenseRows();
    expect(licenses[0].status).toBe('past_due');
  });

  it('P1-5 regression: survives an update event with missing period fields and still applies the plan change', async () => {
    await seedSubscriptionLicense();

    // Newer Stripe API versions can omit current_period_start/end on the
    // subscription object. The handler must not 500 (RangeError) — a 500
    // here blocks the tier change until Stripe gives up retrying.
    const res = await deliver(
      subscriptionEvent('customer.subscription.updated', {
        items: { data: [{ price: { id: TEAM_MONTHLY_PRICE } }] },
        current_period_start: undefined,
        current_period_end: undefined,
      })
    );
    expect(res.status).toBe(200);

    const licenses = await licenseRows();
    expect(licenses[0].plan).toBe('team');
    // Existing period values must be preserved, not corrupted.
    expect(licenses[0].current_period_start).toBe(
      new Date(PERIOD_START * 1000).toISOString()
    );
    expect(licenses[0].current_period_end).toBe(
      new Date(PERIOD_END * 1000).toISOString()
    );
  });

  it('acknowledges an update for an unknown subscription without crashing', async () => {
    const res = await deliver(
      subscriptionEvent('customer.subscription.updated', {
        id: 'sub_never_seen',
      })
    );
    expect(res.status).toBe(200);
    expect(await licenseRows()).toHaveLength(0);
  });
});

// ============================================================================
// customer.subscription.deleted
// ============================================================================

describe('customer.subscription.deleted', () => {
  it('marks the license canceled', async () => {
    await seedSubscriptionLicense();

    const res = await deliver(
      subscriptionEvent('customer.subscription.deleted')
    );
    expect(res.status).toBe(200);

    const licenses = await licenseRows();
    expect(licenses[0].status).toBe('canceled');
  });
});

// ============================================================================
// invoice.paid / invoice.payment_failed
// ============================================================================

describe('invoice.paid', () => {
  it('backfills the billing period and reactivates the license', async () => {
    await seedSubscriptionLicense();
    await deliver(
      subscriptionEvent('customer.subscription.updated', {
        status: 'past_due',
      })
    );

    const res = await deliver(invoiceEvent('invoice.paid'));
    expect(res.status).toBe(200);

    const licenses = await licenseRows();
    expect(licenses[0].status).toBe('active');
    expect(licenses[0].current_period_start).toBe(
      new Date((PERIOD_START + 100) * 1000).toISOString()
    );
    expect(licenses[0].current_period_end).toBe(
      new Date((PERIOD_END + 100) * 1000).toISOString()
    );
  });

  it('ignores non-subscription invoices', async () => {
    const res = await deliver(
      invoiceEvent('invoice.paid', { subscription: null })
    );
    expect(res.status).toBe(200);
    expect(await licenseRows()).toHaveLength(0);
  });

  // API version 2025-03-31+ (basil/clover) removed top-level
  // invoice.subscription — the id now lives at
  // parent.subscription_details.subscription. Verified against a live
  // clover event (evt_1TpLd7AKLIiL9hdw2NceIJUH, 2026-07-04).
  it('clover shape: resolves the subscription from parent.subscription_details and backfills the period', async () => {
    await seedSubscriptionLicense();
    await deliver(
      subscriptionEvent('customer.subscription.updated', {
        status: 'past_due',
      })
    );

    const res = await deliver(
      invoiceEvent('invoice.paid', {
        subscription: null,
        parent: {
          type: 'subscription_details',
          quote_details: null,
          subscription_details: { metadata: {}, subscription: SUBSCRIPTION },
        },
      })
    );
    expect(res.status).toBe(200);

    const licenses = await licenseRows();
    expect(licenses[0].status).toBe('active');
    expect(licenses[0].current_period_start).toBe(
      new Date((PERIOD_START + 100) * 1000).toISOString()
    );
    expect(licenses[0].current_period_end).toBe(
      new Date((PERIOD_END + 100) * 1000).toISOString()
    );
  });

  it('clover shape: still ignores invoices with no subscription in either location', async () => {
    await seedSubscriptionLicense();
    const before = await licenseRows();

    const res = await deliver(
      invoiceEvent('invoice.paid', {
        subscription: null,
        parent: { type: 'quote_details', subscription_details: null },
      })
    );
    expect(res.status).toBe(200);
    expect(await licenseRows()).toEqual(before);
  });
});

describe('invoice.payment_failed', () => {
  it('marks the license past_due', async () => {
    await seedSubscriptionLicense();

    const res = await deliver(invoiceEvent('invoice.payment_failed'));
    expect(res.status).toBe(200);

    const licenses = await licenseRows();
    expect(licenses[0].status).toBe('past_due');
  });

  it('clover shape: resolves the subscription from parent.subscription_details and marks past_due', async () => {
    await seedSubscriptionLicense();

    const res = await deliver(
      invoiceEvent('invoice.payment_failed', {
        subscription: null,
        parent: {
          type: 'subscription_details',
          quote_details: null,
          subscription_details: { metadata: {}, subscription: SUBSCRIPTION },
        },
      })
    );
    expect(res.status).toBe(200);

    const licenses = await licenseRows();
    expect(licenses[0].status).toBe('past_due');
  });
});

// ============================================================================
// charge.refunded
// ============================================================================

describe('charge.refunded', () => {
  const chargeEvent = (overrides: Record<string, unknown> = {}) => ({
    id: eventId(),
    type: 'charge.refunded',
    data: {
      object: {
        id: 'ch_test_Charge01',
        customer: CUSTOMER,
        ...overrides,
      },
    },
  });

  it('revokes an active lifetime license and records the reason', async () => {
    await deliver(
      checkoutCompletedEvent({
        mode: 'payment',
        subscription: null,
        metadata: { plan: 'pro', billing_period: 'lifetime' },
      })
    );

    const res = await deliver(chargeEvent());
    expect(res.status).toBe(200);

    const licenses = await licenseRows();
    expect(licenses[0].status).toBe('revoked');
    expect(licenses[0].revoked_reason).toContain('ch_test_Charge01');
  });

  // Real lifetime purchases have NO customer on the charge (checkout payment
  // mode defaults to customer_creation=if_required). The charge must be
  // mapped to its checkout session via payment_intent instead. Verified live
  // on dev 2026-07-04: refund re_3TpKfg… no-op'd with
  // "[Stripe] No customer on refunded charge".
  it('customer=null: resolves the license via payment_intent → checkout session and revokes it', async () => {
    await deliver(
      checkoutCompletedEvent({
        mode: 'payment',
        subscription: null,
        metadata: { plan: 'pro', billing_period: 'lifetime' },
      })
    );

    const fetchSpy = vi.fn(async (input: RequestInfo | URL) => {
      expect(String(input)).toBe(
        'https://api.stripe.com/v1/checkout/sessions?payment_intent=pi_test_PI01&limit=1'
      );
      return new Response(
        JSON.stringify({ data: [{ id: 'cs_test_Session01' }] }),
        { status: 200, headers: { 'Content-Type': 'application/json' } }
      );
    });
    vi.stubGlobal('fetch', fetchSpy);

    const res = await deliver(
      chargeEvent({ customer: null, payment_intent: 'pi_test_PI01' })
    );
    expect(res.status).toBe(200);

    const licenses = await licenseRows();
    expect(licenses[0].status).toBe('revoked');
    expect(licenses[0].revoked_reason).toContain('ch_test_Charge01');
  });

  it('with several lifetime licenses, payment_intent resolution revokes exactly the purchased one', async () => {
    // Two lifetime purchases on the same account, different sessions.
    await deliver(
      checkoutCompletedEvent({
        mode: 'payment',
        subscription: null,
        metadata: { plan: 'pro', billing_period: 'lifetime' },
      })
    );
    await deliver(
      checkoutCompletedEvent({
        id: 'cs_test_Session02',
        mode: 'payment',
        subscription: null,
        metadata: { plan: 'team', billing_period: 'lifetime' },
      })
    );

    vi.stubGlobal(
      'fetch',
      vi.fn(async () =>
        new Response(JSON.stringify({ data: [{ id: 'cs_test_Session01' }] }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
      )
    );

    // The refund is for the FIRST purchase. The customer heuristic
    // ("most recent lifetime") would pick Session02's license — wrong.
    const res = await deliver(
      chargeEvent({ customer: CUSTOMER, payment_intent: 'pi_test_PI01' })
    );
    expect(res.status).toBe(200);

    const bySession = Object.fromEntries(
      (await licenseRows()).map((l) => [l.stripe_session_id, l])
    );
    expect(bySession['cs_test_Session01'].status).toBe('revoked');
    expect(bySession['cs_test_Session02'].status).toBe('active');
  });

  it('leaves subscription licenses untouched (refund handled via subscription.deleted)', async () => {
    await seedSubscriptionLicense();

    const res = await deliver(chargeEvent());
    expect(res.status).toBe(200);

    const licenses = await licenseRows();
    expect(licenses[0].status).toBe('active');
  });

  it('acknowledges a charge without a customer', async () => {
    const res = await deliver(chargeEvent({ customer: null }));
    expect(res.status).toBe(200);
  });
});

// ============================================================================
// customer.deleted
// ============================================================================

describe('customer.deleted', () => {
  it('expires all active licenses of the deleted customer', async () => {
    await seedSubscriptionLicense();

    const res = await deliver({
      id: eventId(),
      type: 'customer.deleted',
      data: { object: { id: CUSTOMER, email: EMAIL, deleted: true } },
    });
    expect(res.status).toBe(200);

    const licenses = await licenseRows();
    expect(licenses[0].status).toBe('expired');
  });
});

// ============================================================================
// Unhandled events & malformed payloads
// ============================================================================

describe('dispatch edge cases', () => {
  it('acknowledges unhandled event types and marks them processed', async () => {
    const res = await deliver({
      id: eventId(),
      type: 'payment_intent.succeeded',
      data: { object: { id: 'pi_test' } },
    });
    expect(res.status).toBe(200);
    expect(await rows('SELECT * FROM processed_events')).toHaveLength(1);
  });

  it('rejects a correctly signed but non-JSON payload with 400', async () => {
    const payload = 'not-json';
    const signature = await stripeSignatureHeader(
      payload,
      TEST_WEBHOOK_SECRET
    );
    const req = new Request('https://api.test/v1/webhooks/stripe', {
      method: 'POST',
      headers: { 'stripe-signature': signature },
      body: payload,
    });
    const res = await handleStripeWebhook(req, env);
    expect(res.status).toBe(400);
  });
});

// ============================================================================
// Null / missing email handling (regression for the dev 500 crash)
// ============================================================================

describe('checkout.session.completed — email resolution', () => {
  it('falls back to customer_details.email when top-level customer_email is null (payment mode)', async () => {
    // Stripe delivers sessions with customer_email=null but the entered email
    // in customer_details.email. The old code crashed (null.toLowerCase → 500).
    const res = await deliver(
      checkoutCompletedEvent({
        mode: 'payment',
        customer: null,
        customer_email: null,
        customer_details: { email: 'fallback@example.com' },
        metadata: { plan: 'pro', billing_period: 'lifetime' },
      })
    );
    expect(res.status).toBe(200);

    const users = await rows<{ email: string }>('SELECT * FROM user');
    expect(users).toHaveLength(1);
    expect(users[0].email).toBe('fallback@example.com');

    const licenses = await licenseRows();
    expect(licenses).toHaveLength(1);
    expect(licenses[0].plan_type).toBe('lifetime');
  });

  it('falls back to customer_details.email in subscription mode', async () => {
    const res = await deliver(
      checkoutCompletedEvent({
        customer: null,
        customer_email: null,
        customer_details: { email: 'sub-fallback@example.com' },
      })
    );
    expect(res.status).toBe(200);

    const users = await rows<{ email: string }>('SELECT * FROM user');
    expect(users).toHaveLength(1);
    expect(users[0].email).toBe('sub-fallback@example.com');
  });

  it('acks (200) and skips when neither customer_email nor customer_details.email is present', async () => {
    // Nothing we can do without an email — do NOT 500 (Stripe would retry for
    // ~3 days to no effect). Acknowledge and skip.
    const res = await deliver(
      checkoutCompletedEvent({
        mode: 'payment',
        customer: null,
        customer_email: null,
        customer_details: null,
        metadata: {},
      })
    );
    expect(res.status).toBe(200);
    expect(await res.json()).toEqual({ received: true });

    // No user, no license created.
    expect(await rows('SELECT * FROM user')).toHaveLength(0);
    expect(await licenseRows()).toHaveLength(0);
    // Event still marked processed (we acknowledged it).
    expect(await rows('SELECT * FROM processed_events')).toHaveLength(1);
  });
});

// ============================================================================
// findOrCreateUser null-email guard (defense in depth)
// ============================================================================

describe('findOrCreateUser email guard', () => {
  it('throws a typed AppError (not a raw TypeError) for a null email', async () => {
    const db = createDb(env.DB);
    await expect(
      findOrCreateUser(db, null as unknown as string)
    ).rejects.toBeInstanceOf(AppError);
  });

  it('throws a typed AppError for an empty / whitespace email', async () => {
    const db = createDb(env.DB);
    await expect(findOrCreateUser(db, '')).rejects.toBeInstanceOf(AppError);
    await expect(findOrCreateUser(db, '   ')).rejects.toBeInstanceOf(AppError);
  });

  it('still creates a user for a valid email (regression)', async () => {
    const db = createDb(env.DB);
    const user = await findOrCreateUser(db, 'Valid@Example.com', 'cus_guard_1');
    expect(user.email).toBe('valid@example.com');
    expect(user.customerId).toBe('cus_guard_1');
  });
});

// ============================================================================
// Lifetime plan resolution — never default to a paid tier (revenue integrity)
// ============================================================================

function captureErrors(): string[] {
  const messages: string[] = [];
  vi.spyOn(console, 'error').mockImplementation((...args: unknown[]) => {
    messages.push(args.map(String).join(' '));
  });
  return messages;
}

describe('lifetime plan resolution', () => {
  it('does NOT issue a license when the plan is unresolvable (empty metadata, no line_items) — acks 200 + logs for manual review', async () => {
    const errors = captureErrors();
    const res = await deliver(
      checkoutCompletedEvent({
        mode: 'payment',
        subscription: null,
        customer: null,
        customer_email: 'paid-noplan@example.com',
        metadata: {},
      })
    );

    // Ack so Stripe stops retrying (retry yields no new info), but issue NOTHING.
    expect(res.status).toBe(200);
    expect(await res.json()).toEqual({ received: true });
    expect(await licenseRows()).toHaveLength(0);

    // A payment was received — it must be loudly flagged, not silently dropped.
    expect(errors.some((m) => m.includes('MANUAL_REVIEW'))).toBe(true);
    expect(
      errors.some(
        (m) =>
          m.includes('paid-noplan@example.com') && m.includes('cs_test_Session01')
      )
    ).toBe(true);
  });

  it('does NOT issue a license when metadata.plan is an unknown value (garbage), and flags it', async () => {
    const errors = captureErrors();
    const res = await deliver(
      checkoutCompletedEvent({
        mode: 'payment',
        subscription: null,
        customer_email: 'paid-garbage@example.com',
        metadata: { plan: 'gold', billing_period: 'lifetime' },
      })
    );

    expect(res.status).toBe(200);
    expect(await licenseRows()).toHaveLength(0);
    expect(errors.some((m) => m.includes('MANUAL_REVIEW'))).toBe(true);
  });

  it('regression: still issues the correct license when metadata.plan is valid (team)', async () => {
    const res = await deliver(
      checkoutCompletedEvent({
        mode: 'payment',
        subscription: null,
        customer_email: 'paid-team@example.com',
        metadata: { plan: 'team', billing_period: 'lifetime' },
      })
    );
    expect(res.status).toBe(200);

    const licenses = await licenseRows();
    expect(licenses).toHaveLength(1);
    expect(licenses[0].plan).toBe('team');
    expect(licenses[0].plan_type).toBe('lifetime');
  });

  it('regression: still issues the correct license when a mapped lifetime price is in line_items (no metadata.plan)', async () => {
    const res = await deliver(
      checkoutCompletedEvent({
        mode: 'payment',
        subscription: null,
        customer_email: 'paid-price@example.com',
        metadata: {},
        line_items: { data: [{ price: { id: 'price_test_team_lifetime' } }] },
      })
    );
    expect(res.status).toBe(200);

    const licenses = await licenseRows();
    expect(licenses).toHaveLength(1);
    expect(licenses[0].plan).toBe('team');
  });
});
