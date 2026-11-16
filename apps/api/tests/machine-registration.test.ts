/**
 * Atomic device activation (real D1): the device-limit check and the insert
 * are one statement, so parallel validations cannot overshoot the limit, and
 * the same machine validated twice in parallel succeeds instead of hitting
 * the UNIQUE(license_id, machine_id) constraint as a 500.
 */

import { describe, it, expect, beforeAll, afterAll, beforeEach } from 'vitest';
import { handleValidateLicense } from '../src/handlers/validate-license';
import { createDb, createLicense, findOrCreateUser, registerMachine } from '../src/lib/db';
import { PLAN_FEATURES } from '../src/lib/constants';
import { createRealD1, realEnv, memoryKV, type RealD1 } from './real-d1';
import type { Env } from '../src/types/env';

const TEST_ED25519_PRIVATE_KEY =
  'MC4CAQAwBQYDK2VwBCIEIGC5v0PBhH8RkoiqTt9rEt2mS9SXA2WvCz08lilmjSIO';
const KEY = 'RM-ATOM-TEST-0001-AAAA';

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

async function seed(plan: 'pro' | 'sovereign') {
  const db = createDb(env.DB);
  const user = await findOrCreateUser(db, 'atomic@example.com', 'cus_atomic_1');
  return createLicense(db, {
    userId: user.id,
    licenseKey: KEY,
    plan,
  } as Parameters<typeof createLicense>[1]);
}

/** N active machines seen long ago, so abuse heuristics stay quiet. */
async function seedMachines(licenseId: string, n: number): Promise<void> {
  const old = new Date(Date.now() - 10 * 86400_000).toISOString();
  for (let i = 0; i < n; i++) {
    await env.DB.prepare(
      `INSERT INTO license_machines (id, license_id, machine_id, is_active, first_seen_at, last_seen_at)
       VALUES (?, ?, ?, 1, ?, ?)`
    )
      .bind(`m${i}`, licenseId, String(i).padStart(32, '0'), old, old)
      .run();
  }
}

async function activeCount(licenseId: string): Promise<number> {
  const row = await env.DB.prepare(
    'SELECT COUNT(*) AS c FROM license_machines WHERE license_id = ? AND is_active = 1'
  )
    .bind(licenseId)
    .first<{ c: number }>();
  return row?.c ?? 0;
}

function validate(machineId: string): Promise<Response> {
  return handleValidateLicense(
    new Request('https://api.test/v1/license/validate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ license_key: KEY, machine_id: machineId, cli_version: '1.0.0' }),
    }),
    env,
    '127.0.0.1'
  );
}

describe('atomic device activation', () => {
  it('parallel validations with different new machines cannot exceed the device limit', async () => {
    const limit = PLAN_FEATURES.pro.machines;
    const lic = await seed('pro');
    await seedMachines(lic.id, limit - 1); // one slot left

    const results = await Promise.all(
      ['a', 'b', 'c'].map((c) => validate(c.repeat(32)))
    );

    const statuses = results.map((r) => r.status).sort();
    expect(statuses).toEqual([200, 403, 403]);
    expect(await activeCount(lic.id)).toBe(limit);
  });

  it('the same new machine validated twice in parallel succeeds both times (no 500)', async () => {
    const lic = await seed('pro');
    const results = await Promise.all([validate('d'.repeat(32)), validate('d'.repeat(32))]);

    expect(results.map((r) => r.status)).toEqual([200, 200]);
    expect(await activeCount(lic.id)).toBe(1);
    const changes = await env.DB.prepare('SELECT COUNT(*) AS c FROM machine_changes WHERE license_id = ?')
      .bind(lic.id)
      .first<{ c: number }>();
    expect(changes?.c).toBe(1);
  });

  it('unlimited (-1) still registers past any count', async () => {
    const lic = await seed('sovereign');
    await seedMachines(lic.id, 4);
    const res = await validate('e'.repeat(32));
    expect(res.status).toBe(200);
    expect(await activeCount(lic.id)).toBe(5);
  });

  it('registerMachine reports limit_reached / already_registered and writes migration-010 columns', async () => {
    const lic = await seed('pro');
    const db = createDb(env.DB);

    expect(
      await registerMachine(db, lic.id, '1'.repeat(32), 1, 'ci-box', 'ci', {
        ci_provider: 'github',
        ci_repo: 'org/repo',
      })
    ).toBe('registered');
    expect(await registerMachine(db, lic.id, '2'.repeat(32), 1)).toBe('limit_reached');
    expect(await registerMachine(db, lic.id, '1'.repeat(32), 5)).toBe('already_registered');
    expect(await registerMachine(db, lic.id, '3'.repeat(32), -1)).toBe('registered');

    const row = await env.DB.prepare(
      'SELECT machine_name, fingerprint_type, ci_provider, ci_repo FROM license_machines WHERE machine_id = ?'
    )
      .bind('1'.repeat(32))
      .first();
    expect(row).toEqual({
      machine_name: 'ci-box',
      fingerprint_type: 'ci',
      ci_provider: 'github',
      ci_repo: 'org/repo',
    });
  });
});
