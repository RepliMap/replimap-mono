/**
 * Tests for the admin-issued offline license blob:
 *   POST /v1/admin/licenses/{key}/offline-blob
 *   GET  /v1/admin/licenses/{key}/offline-blobs
 *
 * Real D1 harness + the real Worker router (auth guard, admin rate-limit
 * bucket, handler) + real Ed25519 signing. Nothing is stubbed.
 */

import { describe, it, expect, beforeAll, afterAll, beforeEach } from 'vitest';
import { mkdirSync, writeFileSync } from 'node:fs';
import { dirname } from 'node:path';
import worker from '../src/index';
import { createDb, createLicense, findOrCreateUser, updateLicenseStatus } from '../src/lib/db';
import { createRealD1, realEnv, memoryKV, type RealD1 } from './real-d1';
import {
  signLicenseBlob,
  buildContractLicensePayload,
  canonicalJSONStringify,
} from '../src/lib/license-blob-signer';
import { buildSecureLicenseLimits, getEnabledFeatures, Plan } from '../src/features';
import { TEST_LICENSE_SIGNING_PUBLIC_KEY_PEM } from './helpers';
import type { Env } from '../src/types/env';

// Test-only Ed25519 key (same pair as tests/helpers.ts / license-blob-signer.test.ts).
const TEST_PRIVATE_KEY_PEM = `-----BEGIN PRIVATE KEY-----
MC4CAQAwBQYDK2VwBCIEINnVIuuR8WTakYKsfFfJKLeOAYKj+PYXJj/ORCZG8jr2
-----END PRIVATE KEY-----`;
const TEST_KID = 'key-test-mono';
const ADMIN_KEY = 'test-admin-key-1234567890';
const KEY = 'RM-OFFL-TEST-0001-AAAA';
const MACHINE = 'a1b2c3d4e5f60718293a4b5c6d7e8f90';
const DAY = 86400;

let d1: RealD1;
let env: Env;

const makeEnv = (): Env =>
  realEnv(d1.DB, {
    CACHE: memoryKV(), // fresh KV per test: the admin rate-limit bucket is real
    LICENSE_SIGNING_KEY: TEST_PRIVATE_KEY_PEM,
    LICENSE_SIGNING_KID: TEST_KID,
  });

beforeAll(async () => {
  d1 = await createRealD1();
}, 30_000);
afterAll(async () => {
  await d1.dispose();
});
beforeEach(async () => {
  await d1.reset();
  env = makeEnv();
});

// ---------------------------------------------------------------- helpers

function b64uToBytes(str: string): Uint8Array {
  const padded = str.replace(/-/g, '+').replace(/_/g, '/').padEnd(str.length + ((4 - (str.length % 4)) % 4), '=');
  const bin = atob(padded);
  return Uint8Array.from(bin, (c) => c.charCodeAt(0));
}

async function verifyBlob(blob: string): Promise<Record<string, unknown>> {
  const [p, s] = blob.split('.');
  const body = TEST_LICENSE_SIGNING_PUBLIC_KEY_PEM.replace(/-----[A-Z ]+-----/g, '').replace(/\s+/g, '');
  const pub = await crypto.subtle.importKey(
    'spki',
    Uint8Array.from(atob(body), (c) => c.charCodeAt(0)),
    { name: 'Ed25519' },
    false,
    ['verify']
  );
  const ok = await crypto.subtle.verify('Ed25519', pub, b64uToBytes(s), b64uToBytes(p));
  expect(ok).toBe(true);
  return JSON.parse(new TextDecoder().decode(b64uToBytes(p)));
}

async function seed(plan: 'sovereign' | 'pro' = 'sovereign', status?: string) {
  const db = createDb(env.DB);
  const user = await findOrCreateUser(db, 'sov@example.com', 'cus_off_1');
  const lic = await createLicense(db, {
    userId: user.id,
    licenseKey: KEY,
    plan,
  } as Parameters<typeof createLicense>[1]);
  if (status) await updateLicenseStatus(db, lic.id, status as 'revoked');
  return lic;
}

function isoIn(days: number): string {
  return new Date(Math.floor(Date.now() / 1000) * 1000 + days * DAY * 1000).toISOString();
}

function call(
  body: unknown,
  opts: { key?: string | null; licenseKey?: string; e?: Env } = {}
): Promise<Response> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  const key = opts.key === undefined ? ADMIN_KEY : opts.key;
  if (key !== null) headers['X-API-Key'] = key;
  return worker.fetch(
    new Request(`https://api.test/v1/admin/licenses/${opts.licenseKey ?? KEY}/offline-blob`, {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
    }),
    opts.e ?? env
  );
}

async function ledgerCount(): Promise<number> {
  const r = await env.DB.prepare(
    `SELECT COUNT(*) AS c FROM usage_logs WHERE json_extract(metadata, '$.kind') = 'offline_issue'`
  ).first<{ c: number }>();
  return r?.c ?? 0;
}

const valid = () => ({ machine_id: MACHINE, expires_at: isoIn(30) });

// ------------------------------------------------------------------ tests

describe('POST /v1/admin/licenses/{key}/offline-blob', () => {
  describe('admin auth', () => {
    it('401 without X-API-Key', async () => {
      await seed();
      expect((await call(valid(), { key: null })).status).toBe(401);
      expect(await ledgerCount()).toBe(0);
    });
    it('403 with a wrong X-API-Key', async () => {
      await seed();
      expect((await call(valid(), { key: 'wrong-key-wrong-key-wrong' })).status).toBe(403);
      expect(await ledgerCount()).toBe(0);
    });
  });

  describe('machine_id validation (400)', () => {
    it.each([
      ['missing', undefined],
      ['non-hex', 'z'.repeat(32)],
      ['uppercase', 'A1B2C3D4E5F60718293A4B5C6D7E8F90'],
      ['31 chars', 'a'.repeat(31)],
      ['33 chars', 'a'.repeat(33)],
      ['not a string', 12345],
    ])('rejects %s machine_id', async (_name, machine_id) => {
      await seed();
      const res = await call({ expires_at: isoIn(30), ...(machine_id === undefined ? {} : { machine_id }) });
      expect(res.status).toBe(400);
      expect(await ledgerCount()).toBe(0);
    });
  });

  describe('expires_at validation (400)', () => {
    it.each([
      ['missing', undefined],
      ['not a timestamp', 'next tuesday'],
      ['no timezone', '2030-01-01T00:00:00'],
      ['in the past', '2020-01-01T00:00:00Z'],
      ['beyond the 400-day cap', isoIn(401)],
    ])('rejects %s expires_at', async (_name, expires_at) => {
      await seed();
      const res = await call({ machine_id: MACHINE, ...(expires_at === undefined ? {} : { expires_at }) });
      expect(res.status).toBe(400);
      expect(await ledgerCount()).toBe(0);
    });

    it('accepts expires_at just inside the cap', async () => {
      await seed();
      expect((await call({ machine_id: MACHINE, expires_at: isoIn(399) })).status).toBe(200);
    });
  });

  describe('license checks (nothing signed, no ledger row)', () => {
    it('404 for an unknown license', async () => {
      const res = await call(valid());
      expect(res.status).toBe(404);
      expect(await ledgerCount()).toBe(0);
    });
    it.each(['pro'] as const)('403 for a non-Sovereign license (%s)', async (plan) => {
      await seed(plan);
      const res = await call(valid());
      expect(res.status).toBe(403);
      expect(await ledgerCount()).toBe(0);
    });
    it('403 LICENSE_REVOKED for a revoked license', async () => {
      await seed('sovereign', 'revoked');
      const res = await call(valid());
      expect(res.status).toBe(403);
      expect(((await res.json()) as { error_code: string }).error_code).toBe('LICENSE_REVOKED');
      expect(await ledgerCount()).toBe(0);
    });
    it('403 LICENSE_EXPIRED for an expired license', async () => {
      await seed('sovereign', 'expired');
      const res = await call(valid());
      expect(res.status).toBe(403);
      expect(((await res.json()) as { error_code: string }).error_code).toBe('LICENSE_EXPIRED');
      expect(await ledgerCount()).toBe(0);
    });
    it('403 LICENSE_PAST_DUE for a past-due license', async () => {
      await seed('sovereign', 'past_due');
      const res = await call(valid());
      expect(res.status).toBe(403);
      expect(((await res.json()) as { error_code: string }).error_code).toBe('LICENSE_PAST_DUE');
      expect(await ledgerCount()).toBe(0);
    });
    it('403 for a canceled license whose period has ended', async () => {
      await seed('sovereign', 'canceled');
      const res = await call(valid());
      expect(res.status).toBe(403);
      expect(await ledgerCount()).toBe(0);
    });
  });

  it('503 and no blob when the signing key is not configured', async () => {
    await seed();
    const noKeyEnv = realEnv(d1.DB, { CACHE: memoryKV(), LICENSE_SIGNING_KEY: undefined });
    const res = await call(valid(), { e: noKeyEnv });
    expect(res.status).toBe(503);
    const text = await res.text();
    expect(text).not.toContain('license_blob');
    expect(await ledgerCount()).toBe(0);
  });

  describe('happy path', () => {
    it('signs a verifiable, machine-bound blob with the exact requested exp and a backdated nbf', async () => {
      const lic = await seed();
      const expiresAt = isoIn(30);
      const before = Math.floor(Date.now() / 1000);
      const res = await call({ machine_id: MACHINE, expires_at: expiresAt, note: 'ticket-42' });
      const after = Math.floor(Date.now() / 1000);

      expect(res.status).toBe(200);
      const data = (await res.json()) as {
        license_blob: string;
        machine_id: string;
        expires_at: string;
        kid: string;
      };
      expect(data.machine_id).toBe(MACHINE);
      expect(data.kid).toBe(TEST_KID);
      expect(data.expires_at).toBe(expiresAt);

      const payload = await verifyBlob(data.license_blob);
      const wantExp = Math.floor(Date.parse(expiresAt) / 1000);
      expect(payload.machine_id).toBe(MACHINE);
      expect(payload.exp).toBe(wantExp);
      // never the now+365d online fallback
      expect(Math.abs((payload.exp as number) - (before + 365 * DAY))).toBeGreaterThan(30 * DAY);
      expect(payload.iat as number).toBeGreaterThanOrEqual(before);
      expect(payload.iat as number).toBeLessThanOrEqual(after);
      expect(payload.nbf).toBe((payload.iat as number) - 48 * 3600);
      expect(payload.lic).toBe(KEY);
      expect(payload.plan).toBe('sovereign');
      expect(payload.kid).toBe(TEST_KID);
      expect(payload.v).toBe(1);
      expect(payload.limits).toEqual(buildSecureLicenseLimits(Plan.SOVEREIGN));
      expect(payload.features).toEqual(getEnabledFeatures(Plan.SOVEREIGN));

      const row = await env.DB.prepare(
        `SELECT license_id, machine_id, created_at, metadata FROM usage_logs
         WHERE json_extract(metadata, '$.kind') = 'offline_issue'`
      ).first<{ license_id: string; machine_id: string; created_at: string; metadata: string }>();
      expect(row?.license_id).toBe(lic.id);
      expect(row?.machine_id).toBe(MACHINE);
      const meta = JSON.parse(row!.metadata);
      expect(meta.exp).toBe(wantExp);
      expect(meta.nonce).toBe(payload.nonce);
      expect(meta.note).toBe('ticket-42');
      expect(row?.created_at).toBeTruthy();
      // the blob itself is never stored
      expect(row!.metadata).not.toContain(data.license_blob);
    });

    it('GET /offline-blobs lists ledger entries without blobs', async () => {
      await seed();
      await call({ ...valid(), note: 'first' });
      const res = await worker.fetch(
        new Request(`https://api.test/v1/admin/licenses/${KEY}/offline-blobs`, {
          headers: { 'X-API-Key': ADMIN_KEY },
        }),
        env
      );
      expect(res.status).toBe(200);
      const text = await res.text();
      expect(text).not.toContain('license_blob');
      const data = JSON.parse(text) as { entries: Array<Record<string, unknown>> };
      expect(data.entries).toHaveLength(1);
      expect(data.entries[0].machine_id).toBe(MACHINE);
      expect(data.entries[0].note).toBe('first');
      expect(typeof data.entries[0].nonce).toBe('string');
    });

    it('GET /offline-blobs requires the admin key', async () => {
      await seed();
      const res = await worker.fetch(
        new Request(`https://api.test/v1/admin/licenses/${KEY}/offline-blobs`),
        env
      );
      expect(res.status).toBe(401);
    });
  });

  describe('abuse / machine-change counters', () => {
    it('six offline blobs in one day do not touch machine counters; online validate still works', async () => {
      const lic = await seed();
      const monthlyChanges = async () =>
        (
          await env.DB.prepare(
            `SELECT COUNT(*) AS c FROM machine_changes
             WHERE license_id = ? AND changed_at >= datetime('now', 'start of month')`
          )
            .bind(lic.id)
            .first<{ c: number }>()
        )?.c;

      expect(await monthlyChanges()).toBe(0);
      for (let i = 0; i < 6; i++) {
        const id = String(i + 1).padStart(32, 'c');
        expect((await call({ machine_id: id, expires_at: isoIn(30) })).status).toBe(200);
      }
      expect(await ledgerCount()).toBe(6);
      expect(await monthlyChanges()).toBe(0);
      const machines = await env.DB.prepare('SELECT COUNT(*) AS c FROM license_machines WHERE license_id = ?')
        .bind(lic.id)
        .first<{ c: number }>();
      expect(machines?.c).toBe(0);

      const validate = await worker.fetch(
        new Request('https://api.test/v1/license/validate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ license_key: KEY, machine_id: 'd'.repeat(32), cli_version: '1.0.0' }),
        }),
        env
      );
      expect(validate.status).toBe(200);
      // exactly the one online registration, none from the six offline issuances
      expect(await monthlyChanges()).toBe(1);
    });
  });
});

describe('explicit-exp signer path + cross-language golden vector', () => {
  const FIXED = {
    now: 1790000000,
    nonce: '0123456789abcdef',
    exp: 4102444800,
    machineId: '00000000000000000000000000000000',
  };

  async function goldenBlob() {
    const limits = buildSecureLicenseLimits(Plan.SOVEREIGN);
    const payload = buildContractLicensePayload({
      licenseKey: 'RM-TEST-GOLDEN-0001',
      plan: 'sovereign',
      machineId: FIXED.machineId,
      kid: TEST_KID,
      currentPeriodEnd: '2030-01-01T00:00:00Z', // must be ignored when explicitExp is set
      offlineGraceDays: 30,
      limits,
      features: getEnabledFeatures(Plan.SOVEREIGN),
      now: FIXED.now,
      nonce: FIXED.nonce,
      explicitExp: FIXED.exp,
      nbfLeewaySeconds: 48 * 3600,
    });
    return { payload, blob: await signLicenseBlob(payload, TEST_PRIVATE_KEY_PEM) };
  }

  it('explicitExp is used verbatim; nbf/iat follow the inputs; blob verifies', async () => {
    const { payload, blob } = await goldenBlob();
    expect(payload.exp).toBe(FIXED.exp);
    expect(payload.iat).toBe(FIXED.now);
    expect(payload.nbf).toBe(FIXED.now - 172800);
    const decoded = await verifyBlob(blob);
    expect(decoded).toEqual(JSON.parse(canonicalJSONStringify(payload)));
  });

  it('without explicitExp the online derivation is unchanged', () => {
    const p = buildContractLicensePayload({
      licenseKey: 'RM-TEST-GOLDEN-0001',
      plan: 'sovereign',
      machineId: FIXED.machineId,
      kid: TEST_KID,
      currentPeriodEnd: null,
      offlineGraceDays: 30,
      now: FIXED.now,
    });
    expect(p.exp).toBe(FIXED.now + 365 * DAY);
    expect(p.nbf).toBe(FIXED.now - 300);
  });

  it('writes the golden vector when OFFLINE_GOLDEN_OUT is set', async () => {
    const out = process.env.OFFLINE_GOLDEN_OUT;
    if (!out) return;
    const { payload, blob } = await goldenBlob();
    mkdirSync(dirname(out), { recursive: true });
    writeFileSync(
      out,
      JSON.stringify(
        {
          description:
            'Offline (admin-issued) license blob signed by the mono Worker signer with the mono TEST key. Test-only key; never ships.',
          kid: TEST_KID,
          test_public_key_pem: TEST_LICENSE_SIGNING_PUBLIC_KEY_PEM,
          inputs: {
            now_iat: FIXED.now,
            nonce: FIXED.nonce,
            exp: FIXED.exp,
            nbf_backdate_seconds: 172800,
            machine_id: FIXED.machineId,
            license_key: 'RM-TEST-GOLDEN-0001',
            plan: 'sovereign',
          },
          payload,
          license_blob: blob,
          expect:
            'LicenseVerifier.verify(blob, machine_id=<machine_id>) succeeds with kid registered to test_public_key_pem, evaluated at a time between nbf and exp',
        },
        null,
        2
      ) + '\n'
    );
  });
});
