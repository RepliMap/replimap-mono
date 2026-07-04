/**
 * Real-database test harness.
 *
 * Boots a Miniflare-backed D1 database (the same engine `wrangler dev --local`
 * uses) and applies the real schema bootstrap chain (schema.sql → migrations
 * 003..011), so tests exercise genuine SQLite behavior: UNIQUE constraints,
 * ON CONFLICT clauses, and FK cascades — none of which regex-based DB mocks
 * can reproduce.
 *
 * Also provides a real Stripe webhook signature helper: it computes the same
 * HMAC-SHA256 over `${timestamp}.${payload}` that Stripe computes, so the
 * production `verifyStripeSignature` code path runs unmodified.
 */

import { Miniflare } from 'miniflare';
import { readFileSync, readdirSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import type { Env } from '../src/types/env';

const API_ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');

/** Test webhook secret — the "configured" secret for the fake Stripe account. */
export const TEST_WEBHOOK_SECRET = 'whsec_real_harness_secret_for_tests';

// ============================================================================
// SQL bootstrap
// ============================================================================

/**
 * Split a SQL file into individual statements.
 * Strips `--` line comments first; none of our schema files contain
 * semicolons inside a statement body, so a plain split is sound.
 */
function sqlStatements(sql: string): string[] {
  const withoutComments = sql
    .split('\n')
    .filter((line) => !line.trim().startsWith('--'))
    .join('\n');

  return withoutComments
    .split(';')
    .map((s) => s.trim())
    .filter((s) => s.length > 0);
}

/** schema.sql first, then migrations in numeric order (003..011). */
function bootstrapFiles(): string[] {
  const migrationsDir = join(API_ROOT, 'migrations');
  const migrations = readdirSync(migrationsDir)
    .filter((f) => f.endsWith('.sql'))
    .sort();
  return [
    join(API_ROOT, 'schema.sql'),
    ...migrations.map((f) => join(migrationsDir, f)),
  ];
}

// ============================================================================
// Miniflare D1
// ============================================================================

export interface RealD1 {
  DB: D1Database;
  /** Delete all rows from mutable tables — cheap per-test isolation. */
  reset: () => Promise<void>;
  dispose: () => Promise<void>;
}

const TABLES_TO_RESET = [
  'license_machines',
  'machine_changes',
  'license_aws_accounts',
  'usage_logs',
  'usage_events',
  'usage_daily',
  'usage_idempotency',
  'processed_events',
  'licenses',
  'session',
  'account',
  'verification',
  'user',
];

export async function createRealD1(): Promise<RealD1> {
  const mf = new Miniflare({
    modules: true,
    script: 'export default { fetch() { return new Response(null); } }',
    d1Databases: { DB: 'test-db' },
  });

  const DB = (await mf.getD1Database('DB')) as unknown as D1Database;

  for (const file of bootstrapFiles()) {
    for (const stmt of sqlStatements(readFileSync(file, 'utf8'))) {
      await DB.prepare(stmt).run();
    }
  }

  return {
    DB,
    reset: async () => {
      for (const table of TABLES_TO_RESET) {
        await DB.prepare(`DELETE FROM ${table}`).run();
      }
    },
    dispose: () => mf.dispose(),
  };
}

/** Env wired to the real D1 database. */
export function realEnv(DB: D1Database, overrides: Partial<Env> = {}): Env {
  return {
    DB,
    CACHE: undefined as unknown as Env['CACHE'],
    ENVIRONMENT: 'test',
    CORS_ORIGIN: '*',
    API_VERSION: 'v1',
    ADMIN_API_KEY: 'test-admin-key-1234567890',
    STRIPE_SECRET_KEY: 'sk_test_harness',
    STRIPE_WEBHOOK_SECRET: TEST_WEBHOOK_SECRET,
    RATE_LIMIT_DISABLED: 'true',
    ...overrides,
  } as Env;
}

// ============================================================================
// Real Stripe signature
// ============================================================================

/**
 * Compute a genuine Stripe-scheme signature header for a payload:
 * `t=<unix>,v1=hex(HMAC_SHA256(secret, "<unix>.<payload>"))`.
 * This is the exact algorithm Stripe documents; nothing is stubbed.
 */
export async function stripeSignatureHeader(
  payload: string,
  secret: string = TEST_WEBHOOK_SECRET,
  timestamp: number = Math.floor(Date.now() / 1000)
): Promise<string> {
  const encoder = new TextEncoder();
  const key = await crypto.subtle.importKey(
    'raw',
    encoder.encode(secret),
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign']
  );
  const sig = await crypto.subtle.sign(
    'HMAC',
    key,
    encoder.encode(`${timestamp}.${payload}`)
  );
  const hex = Array.from(new Uint8Array(sig))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('');
  return `t=${timestamp},v1=${hex}`;
}

/** Build a signed webhook Request exactly as Stripe would deliver it. */
export async function signedWebhookRequest(
  event: Record<string, unknown>,
  options: { secret?: string; timestamp?: number; tamper?: (payload: string) => string } = {}
): Promise<Request> {
  const payload = JSON.stringify(event);
  const signature = await stripeSignatureHeader(
    payload,
    options.secret,
    options.timestamp
  );
  const body = options.tamper ? options.tamper(payload) : payload;
  return new Request('https://api.test/v1/webhooks/stripe', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'stripe-signature': signature,
    },
    body,
  });
}
