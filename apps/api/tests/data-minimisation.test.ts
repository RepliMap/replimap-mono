/**
 * Data minimisation: removed routes, frozen response contracts, error text and
 * log hygiene. Real D1 harness and the real Worker router.
 */

import { describe, it, expect, beforeAll, afterAll, beforeEach, afterEach, vi } from 'vitest';
import worker from '../src/index';
import { createDb, createLicense, findOrCreateUser } from '../src/lib/db';
import { createRealD1, realEnv, memoryKV, type RealD1 } from './real-d1';
import type { Env } from '../src/types/env';

const KEY = 'RM-MINI-TEST-0001-AAAA';
const MACHINE = 'a1b2c3d4e5f60718293a4b5c6d7e8f90';
const ADMIN_KEY = 'test-admin-key-1234567890';

let d1: RealD1;
let env: Env;
let licenseId: string;

beforeAll(async () => {
  d1 = await createRealD1();
}, 30_000);
afterAll(async () => {
  await d1.dispose();
});
beforeEach(async () => {
  await d1.reset();
  env = realEnv(d1.DB, { CACHE: memoryKV() });
});
afterEach(() => {
  vi.restoreAllMocks();
});

async function seed(plan: 'pro' | 'community' = 'pro'): Promise<string> {
  const db = createDb(env.DB);
  const user = await findOrCreateUser(db, 'mini@example.com', 'cus_mini_1');
  const lic = await createLicense(db, {
    userId: user.id,
    licenseKey: KEY,
    plan,
  } as Parameters<typeof createLicense>[1]);
  licenseId = lic.id;
  return lic.id;
}

function call(method: string, path: string, body?: unknown, headers: Record<string, string> = {}) {
  return worker.fetch(
    new Request(`https://api.test${path}`, {
      method,
      headers: { 'Content-Type': 'application/json', ...headers },
      body: body === undefined ? undefined : JSON.stringify(body),
    }),
    env
  );
}

const validateBody = (extra: Record<string, unknown> = {}) => ({
  license_key: KEY,
  machine_id: MACHINE,
  cli_version: '1.0.0',
  ...extra,
});

/** Sorted keys, ignoring optional underscore-prefixed advisory fields (_warning, ...). */
const sorted = (o: object) => Object.keys(o).filter((k) => !k.startsWith('_')).sort();

// ---------------------------------------------------------------------------
// Removed routes
// ---------------------------------------------------------------------------

const REMOVED_PATHS = [
  '/v1/aws-accounts/track',
  `/v1/licenses/${KEY}/aws-accounts`,
  '/v1/usage/sync',
  '/v1/usage/track',
  '/v1/usage/check-quota',
  `/v1/usage/${KEY}`,
  `/v1/usage/${KEY}/history`,
  '/v1/features',
  '/v1/features/check',
  '/v1/features/flags',
  '/v1/rightsizer/suggestions',
  '/v1/license/activate',
  '/v1/metrics/adoption',
  '/v1/metrics/conversion',
  '/v1/metrics/remediation-impact',
  '/v1/metrics/snapshot-usage',
  '/v1/metrics/deps-usage',
];
const METHODS = ['GET', 'POST', 'PUT', 'DELETE'];

describe('removed routes fall through to 404', () => {
  for (const path of REMOVED_PATHS) {
    for (const method of METHODS) {
      it(`${method} ${path} returns 404`, async () => {
        const withBody = method === 'POST' || method === 'PUT';
        const res = await call(
          method,
          path,
          withBody ? { license_key: KEY, machine_id: MACHINE } : undefined,
          { 'X-API-Key': ADMIN_KEY }
        );
        expect(res.status).toBe(404);
      });
    }
  }
});

describe('surviving routes still respond', () => {
  it('GET /health and GET / return 200', async () => {
    expect((await call('GET', '/health')).status).toBe(200);
    expect((await call('GET', '/')).status).toBe(200);
  });

  it('POST /v1/license/validate returns 200 for a seeded license', async () => {
    await seed();
    const res = await call('POST', '/v1/license/validate', validateBody());
    expect(res.status).toBe(200);
  });

  it('POST /v1/license/deactivate deactivates a registered machine', async () => {
    await seed();
    expect((await call('POST', '/v1/license/validate', validateBody())).status).toBe(200);
    const res = await call('POST', '/v1/license/deactivate', { license_key: KEY, machine_id: MACHINE });
    expect(res.status).toBe(200);
  });

  it('GET /v1/me/license and /v1/me/machines return 200', async () => {
    await seed();
    await call('POST', '/v1/license/validate', validateBody());
    expect((await call('GET', `/v1/me/license?license_key=${KEY}`)).status).toBe(200);
    expect((await call('GET', `/v1/me/machines?license_key=${KEY}`)).status).toBe(200);
  });

  it('GET /v1/admin/stats returns 200 with empty orphan tables', async () => {
    for (const t of ['usage_daily', 'usage_events', 'license_aws_accounts']) {
      await d1.DB.prepare(`DELETE FROM ${t}`).run();
    }
    const res = await call('GET', '/v1/admin/stats', undefined, { 'X-API-Key': ADMIN_KEY });
    expect(res.status).toBe(200);
    const stats = (await res.json()) as { events: { today: number; this_month: number } };
    expect(stats.events.today).toBe(0);
    expect(stats.events.this_month).toBe(0);
  });
});

// ---------------------------------------------------------------------------
// Frozen contracts
// ---------------------------------------------------------------------------

describe('response contract freeze', () => {
  it('validate response keeps every key, with zero-valued usage counters', async () => {
    await seed();
    const res = await call('POST', '/v1/license/validate', validateBody());
    const body = (await res.json()) as Record<string, Record<string, unknown>>;

    expect(sorted(body)).toEqual([
      'cache_until',
      'cli_version',
      'expires_at',
      'features',
      'limits',
      'new_features',
      'plan',
      'status',
      'usage',
      'valid',
    ]);
    expect(sorted(body.usage)).toEqual([
      'aws_accounts_active',
      'aws_accounts_limit',
      'machines_active',
      'machines_limit',
      'scans_this_month',
    ]);
    expect(body.usage.scans_this_month).toBe(0);
    expect(body.usage.aws_accounts_active).toBe(0);
    expect(sorted(body.features)).toEqual([
      'aws_accounts',
      'export_formats',
      'machines',
      'resources_per_scan',
      'scans_per_month',
    ]);
  });

  it('/v1/me/license response keeps every key, with zero-valued usage counters', async () => {
    await seed();
    const res = await call('GET', `/v1/me/license?license_key=${KEY}`);
    const body = (await res.json()) as Record<string, Record<string, unknown>>;

    expect(sorted(body)).toEqual([
      'created_at',
      'features',
      'license_key',
      'plan',
      'status',
      'subscription',
      'usage',
    ]);
    expect(sorted(body.usage)).toEqual([
      'aws_accounts_active',
      'aws_accounts_limit',
      'machines_active',
      'machines_limit',
      'scans_this_month',
    ]);
    expect(body.usage.scans_this_month).toBe(0);
    expect(body.usage.aws_accounts_active).toBe(0);
  });

  it('validate accepts machine_name and is_ci and stores no machine_name', async () => {
    await seed();
    const res = await call(
      'POST',
      '/v1/license/validate',
      validateBody({ machine_name: 'davids-laptop.local', is_ci: false })
    );
    expect(res.status).toBe(200);

    const rows = await d1.DB.prepare('SELECT machine_name FROM license_machines').all<{
      machine_name: string | null;
    }>();
    expect(rows.results).toHaveLength(1);
    expect(rows.results[0].machine_name).toBeNull();
  });

  it('request schema is unchanged: the strict schema still rejects an unknown machine_fingerprint key', async () => {
    await seed();
    const res = await call(
      'POST',
      '/v1/license/validate',
      validateBody({ machine_name: 'davids-laptop.local', is_ci: true, machine_fingerprint: MACHINE })
    );
    expect(res.status).toBe(400);
    expect(await d1.DB.prepare('SELECT COUNT(*) AS c FROM license_machines').first('c')).toBe(0);
  });
});
