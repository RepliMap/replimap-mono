/**
 * Regression: a plan limit of -1 means UNLIMITED (Sovereign machines). `count >= -1` is always true, which used to reject every new
 * Sovereign machine. Runs against the real D1 harness.
 */

import { describe, it, expect, beforeAll, afterAll, beforeEach } from 'vitest';
import { handleValidateLicense } from '../src/handlers/validate-license';
import { createDb, createLicense, findOrCreateUser } from '../src/lib/db';
import { createRealD1, realEnv, memoryKV, type RealD1 } from './real-d1';
import type { Env } from '../src/types/env';
import type { ErrorResponse } from '../src/types/api';

const TEST_ED25519_PRIVATE_KEY =
  'MC4CAQAwBQYDK2VwBCIEIGC5v0PBhH8RkoiqTt9rEt2mS9SXA2WvCz08lilmjSIO';

let d1: RealD1;
let env: Env;

beforeAll(async () => {
  d1 = await createRealD1();
  env = realEnv(d1.DB, { CACHE: memoryKV(), ED25519_PRIVATE_KEY: TEST_ED25519_PRIVATE_KEY });
}, 30_000);
afterAll(async () => {
  await d1.dispose();
});
beforeEach(async () => {
  await d1.reset();
});

const KEY = 'RM-UNLM-TEST-0001-AAAA';

async function seed(plan: 'pro' | 'sovereign') {
  const db = createDb(env.DB);
  const user = await findOrCreateUser(db, 'unlimited@example.com', 'cus_unl_1');
  return createLicense(db, {
    userId: user.id,
    licenseKey: KEY,
    plan,
  } as Parameters<typeof createLicense>[1]);
}

/** Insert N already-registered machines, seen long ago so abuse heuristics stay quiet. */
async function seedMachines(licenseId: string, n: number): Promise<void> {
  const old = new Date(Date.now() - 10 * 86400_000).toISOString();
  const recent = new Date(Date.now() - 3600_000).toISOString();
  for (let i = 0; i < n; i++) {
    await env.DB.prepare(
      `INSERT INTO license_machines (id, license_id, machine_id, is_active, first_seen_at, last_seen_at)
       VALUES (?, ?, ?, 1, ?, ?)`
    )
      .bind(`m${i}`, licenseId, String(i).padStart(32, '0'), old, recent)
      .run();
  }
}

const NEW_MACHINE = 'f'.repeat(32);

function post(path: string, body: Record<string, unknown>): Request {
  return new Request(`https://api.test${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

describe('machines = -1 (unlimited)', () => {
  it('validate: Sovereign with 4 active machines registers a new machine (200)', async () => {
    const lic = await seed('sovereign');
    await seedMachines(lic.id, 4);
    const res = await handleValidateLicense(
      post('/v1/license/validate', { license_key: KEY, machine_id: NEW_MACHINE, cli_version: '1.0.0' }),
      env,
      '127.0.0.1'
    );
    expect(res.status).toBe(200);
    const row = await env.DB.prepare('SELECT COUNT(*) AS c FROM license_machines WHERE license_id = ?')
      .bind(lic.id)
      .first<{ c: number }>();
    expect(row?.c).toBe(5);
  });

  it('validate: Pro at its machine limit (10) still rejects a new machine', async () => {
    const lic = await seed('pro');
    await seedMachines(lic.id, 10);
    const res = await handleValidateLicense(
      post('/v1/license/validate', { license_key: KEY, machine_id: NEW_MACHINE, cli_version: '1.0.0' }),
      env,
      '127.0.0.1'
    );
    expect(res.status).toBe(403);
    expect(((await res.json()) as ErrorResponse).error_code).toBe('MACHINE_LIMIT_EXCEEDED');
  });

  it('error text does not mention the nonexistent REPLIMAP_MACHINE_ID variable', async () => {
    const lic = await seed('pro');
    await seedMachines(lic.id, 10);
    const res = await handleValidateLicense(
      post('/v1/license/validate', { license_key: KEY, machine_id: NEW_MACHINE, cli_version: '1.0.0' }),
      env,
      '127.0.0.1'
    );
    expect(JSON.stringify(await res.json())).not.toContain('REPLIMAP_MACHINE_ID');
  });
});
