/**
 * Device-limit error text and licence-key log hygiene. Real D1 harness and the real Worker router.
 */

import { describe, it, expect, beforeAll, afterAll, beforeEach, afterEach, vi } from 'vitest';
import worker from '../src/index';
import { createDb, createLicense, findOrCreateUser } from '../src/lib/db';
import { createRealD1, realEnv, memoryKV, type RealD1 } from './real-d1';
import type { Env } from '../src/types/env';

const KEY = 'RM-MINI-TEST-0001-AAAA';
const MACHINE = 'a1b2c3d4e5f60718293a4b5c6d7e8f90';

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


// ---------------------------------------------------------------------------
// Error payload and logs
// ---------------------------------------------------------------------------

describe('MACHINE_LIMIT_EXCEEDED payload', () => {
  it('does not promise expiry or recommend the local-only CLI deactivate', async () => {
    await seed('community');
    // Fill the Community device allowance with machines last seen a while ago.
    const seen = new Date(Date.now() - 10 * 86_400_000).toISOString();
    for (let i = 0; i < 5; i++) {
      await d1.DB.prepare(
        `INSERT INTO license_machines (id, license_id, machine_id, is_active, first_seen_at, last_seen_at)
         VALUES (?, ?, ?, 1, ?, ?)`
      )
        .bind(`m${i}`, licenseId, String(i).padStart(32, '0'), seen, seen)
        .run();
    }

    const res = await call('POST', '/v1/license/validate', validateBody());
    expect(res.status).toBe(403);
    const text = JSON.stringify(await res.json());
    expect(text).toContain('MACHINE_LIMIT_EXCEEDED');
    expect(text).not.toContain('30 days');
    expect(text).not.toContain('replimap license deactivate');
    expect(text).toContain('dashboard');
    expect(text).toContain('replimap license activate');
  });
});

describe('license key in logs', () => {
  it('the abuse log line carries at most RM- plus 4 key characters', async () => {
    await seed();
    const recent = new Date().toISOString();
    for (let i = 0; i < 5; i++) {
      await d1.DB.prepare(
        `INSERT INTO license_machines (id, license_id, machine_id, is_active, first_seen_at, last_seen_at)
         VALUES (?, ?, ?, 1, ?, ?)`
      )
        .bind(`n${i}`, licenseId, String(i).padStart(32, '0'), recent, recent)
        .run();
    }
    const warn = vi.spyOn(console, 'warn').mockImplementation(() => {});

    const res = await call('POST', '/v1/license/validate', validateBody());
    expect(res.status).toBe(403);

    const line = warn.mock.calls.map((c) => String(c[0])).find((l) => l.includes('[ABUSE]'));
    expect(line).toBeDefined();
    expect(line).toContain('RM-MINI');
    expect(line).not.toContain('RM-MINI-');
    expect(line).not.toContain('TEST');
    expect(line).not.toContain(KEY);
  });
});
