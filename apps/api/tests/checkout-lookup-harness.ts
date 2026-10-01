/**
 * Shared setup for the checkout license-lookup tests: real D1 + real Clerk
 * tokens (clerk-harness) + a Stripe session stub on global fetch.
 */

import { vi } from 'vitest';
import { handleGetCheckoutLicense } from '../src/handlers/checkout-license';
import type { Env } from '../src/types/env';
import type { RealD1 } from './real-d1';
import {
  createClerkHarness,
  TEST_CLERK_ISSUER,
  TEST_CLERK_SECRET_KEY,
  type ClerkHarness,
} from './clerk-harness';
import { createRealD1, realEnv } from './real-d1';

export const BUYER_ID = 'user_clerk_buyer';
export const BUYER_EMAIL = 'buyer@example.com';
export const OTHER_ID = 'user_clerk_other';
export const OTHER_EMAIL = 'other@example.com';

export interface StripeSessionStub {
  mode?: 'payment' | 'subscription';
  status?: string;
  payment_status?: string;
  customer_email?: string | null;
  customer_details?: { email?: string | null } | null;
  subscription?: string | null;
}

export interface LookupCtx {
  d1: RealD1;
  env: Env;
  clerk: ClerkHarness;
  /** Stripe URLs requested through the stub (session fetches). */
  stripeCalls: string[];
  /** Install fetch stub; `stripe` decides the Stripe response. */
  install: (
    stripe?: (url: string) => Response | Promise<Response>
  ) => ReturnType<typeof vi.fn>;
  call: (sessionId: string, opts?: { token?: string; env?: Env }) => Promise<Response>;
  token: (userId?: string, email?: string) => Promise<string>;
  seedUser: (id: string, email: string) => Promise<void>;
  seedLicense: (row: {
    id: string;
    userId: string;
    key: string;
    plan?: string;
    planType?: string;
    sessionId?: string | null;
    subscriptionId?: string | null;
    createdAt?: number;
  }) => Promise<void>;
}

export function stripeSession(s: StripeSessionStub = {}): Response {
  return new Response(
    JSON.stringify({
      id: 'cs_test_x',
      mode: 'subscription',
      status: 'complete',
      payment_status: 'paid',
      customer_email: BUYER_EMAIL,
      subscription: 'sub_new',
      ...s,
    }),
    { status: 200, headers: { 'Content-Type': 'application/json' } }
  );
}

export async function createLookupCtx(): Promise<LookupCtx> {
  const d1 = await createRealD1();
  const clerk = await createClerkHarness();
  const env = realEnv(d1.DB, {
    CLERK_ISSUER: TEST_CLERK_ISSUER,
    CLERK_SECRET_KEY: TEST_CLERK_SECRET_KEY,
  });
  const stripeCalls: string[] = [];

  const ctx: LookupCtx = {
    d1,
    env,
    clerk,
    stripeCalls,
    install: (stripe) =>
      clerk.installFetchStub({
        users: { [BUYER_ID]: BUYER_EMAIL, [OTHER_ID]: OTHER_EMAIL },
        stripe: (url) => {
          stripeCalls.push(url);
          return stripe ? stripe(url) : stripeSession();
        },
      }),
    token: (userId = BUYER_ID, email = BUYER_EMAIL) =>
      clerk.mintToken({ userId, email }),
    call: (sessionId, opts = {}) => {
      const headers: Record<string, string> = {};
      if (opts.token) headers['Authorization'] = `Bearer ${opts.token}`;
      return handleGetCheckoutLicense(
        new Request(`https://api.test/v1/checkout/session/${sessionId}/license`, {
          headers,
        }),
        opts.env ?? env,
        '127.0.0.1',
        sessionId
      );
    },
    seedUser: async (id, email) => {
      await env.DB.prepare(
        `INSERT INTO user (id, email, name) VALUES (?, ?, '')`
      )
        .bind(id, email)
        .run();
    },
    seedLicense: async (r) => {
      await env.DB.prepare(
        `INSERT INTO licenses (id, user_id, license_key, plan, plan_type, status,
           stripe_session_id, stripe_subscription_id, created_at)
         VALUES (?, ?, ?, ?, ?, 'active', ?, ?, ?)`
      )
        .bind(
          r.id,
          r.userId,
          r.key,
          r.plan ?? 'pro',
          r.planType ?? 'monthly',
          r.sessionId ?? null,
          r.subscriptionId ?? null,
          r.createdAt ?? Date.now()
        )
        .run();
    },
  };
  return ctx;
}
