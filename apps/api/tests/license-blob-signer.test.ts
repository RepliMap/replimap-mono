/**
 * Tests for lib/license-blob-signer.ts — License Blob Format Contract v1
 * (docs/security/license-blob-format.md in the replimap repo).
 *
 * TEST KEY — throwaway Ed25519 keypair generated solely for this suite via:
 *   node -e "const c=require('crypto');
 *     const {privateKey,publicKey}=c.generateKeyPairSync('ed25519');
 *     console.log(privateKey.export({type:'pkcs8',format:'pem'}).toString());
 *     console.log(publicKey.export({type:'spki',format:'pem'}).toString());"
 * It signs nothing outside this file, is never added to any production
 * PUBLIC_KEYS registry, and has no production value (contract §4/§11.A).
 */

import { describe, it, expect } from 'vitest';
import {
  signLicenseBlob,
  canonicalJSONStringify,
  deriveLicenseExpiry,
  generateLicenseNonce,
  buildContractLicensePayload,
  type LicenseBlobPayload,
} from '../src/lib/license-blob-signer';

// TEST KEY — see file header. Never use outside this suite.
const TEST_PRIVATE_KEY_PEM = `-----BEGIN PRIVATE KEY-----
MC4CAQAwBQYDK2VwBCIEINnVIuuR8WTakYKsfFfJKLeOAYKj+PYXJj/ORCZG8jr2
-----END PRIVATE KEY-----`;

const TEST_PUBLIC_KEY_PEM = `-----BEGIN PUBLIC KEY-----
MCowBQYDK2VwAyEAWabq1kPwCc/veNKy9hsFL2OeXN66xz1hgMR5yQdLX5c=
-----END PUBLIC KEY-----`;

function base64UrlDecode(str: string): Uint8Array {
  const padded = str.replace(/-/g, '+').replace(/_/g, '/').padEnd(
    str.length + ((4 - (str.length % 4)) % 4),
    '='
  );
  const binary = atob(padded);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  return bytes;
}

async function importTestPublicKey(): Promise<CryptoKey> {
  const body = TEST_PUBLIC_KEY_PEM.replace(/-----[A-Z ]+-----/g, '').replace(/\s+/g, '');
  const binary = atob(body);
  const der = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) der[i] = binary.charCodeAt(i);
  return crypto.subtle.importKey('spki', der, { name: 'Ed25519' }, false, ['verify']);
}

/** The exact golden-vector payload from contract §8, key-sorted. */
function goldenPayload(): LicenseBlobPayload {
  return {
    v: 1,
    email: 'golden-vector@replimap.test',
    exp: 4102444800,
    features: [],
    iat: 1750000000,
    kid: 'key-test-2026',
    lic: 'RM-TEST-GOLDEN-0001',
    machine_id: '00000000000000000000000000000000',
    nbf: 1750000000,
    nonce: '0123456789abcdef',
    org: 'RepliMap Test Fixtures',
    plan: 'pro',
  };
}

describe('canonicalJSONStringify', () => {
  it('sorts object keys alphabetically and uses compact separators', () => {
    const json = canonicalJSONStringify(goldenPayload());
    expect(json).toBe(
      '{"email":"golden-vector@replimap.test","exp":4102444800,"features":[],' +
        '"iat":1750000000,"kid":"key-test-2026","lic":"RM-TEST-GOLDEN-0001",' +
        '"machine_id":"00000000000000000000000000000000","nbf":1750000000,' +
        '"nonce":"0123456789abcdef","org":"RepliMap Test Fixtures","plan":"pro","v":1}'
    );
  });

  it('sorts nested object keys too', () => {
    const json = canonicalJSONStringify({ b: { z: 1, a: 2 }, a: 1 });
    expect(json).toBe('{"a":1,"b":{"a":2,"z":1}}');
  });

  it('escapes non-ASCII as \\uXXXX (matches Python ensure_ascii=True)', () => {
    expect(canonicalJSONStringify({ name: 'café' })).toBe('{"name":"caf\\u00e9"}');
  });

  it('does not insert whitespace', () => {
    const json = canonicalJSONStringify({ a: [1, 2, 3], b: 'x' });
    expect(json).not.toMatch(/[\s]/);
  });
});

describe('signLicenseBlob', () => {
  it('produces exactly two unpadded base64url segments', async () => {
    const blob = await signLicenseBlob(goldenPayload(), TEST_PRIVATE_KEY_PEM);
    const parts = blob.split('.');
    expect(parts).toHaveLength(2);
    for (const part of parts) {
      expect(part).toMatch(/^[A-Za-z0-9_-]+$/); // base64url alphabet, no '+', '/', '='
      expect(part.endsWith('=')).toBe(false);
    }
  });

  it('signs the canonical payload bytes exactly (payload segment round-trips)', async () => {
    const payload = goldenPayload();
    const blob = await signLicenseBlob(payload, TEST_PRIVATE_KEY_PEM);
    const [payloadB64] = blob.split('.');
    const payloadBytes = base64UrlDecode(payloadB64);
    const decodedJson = new TextDecoder().decode(payloadBytes);
    expect(decodedJson).toBe(canonicalJSONStringify(payload));
    expect(JSON.parse(decodedJson)).toEqual(payload);
  });

  it('produces a 64-byte Ed25519 signature', async () => {
    const blob = await signLicenseBlob(goldenPayload(), TEST_PRIVATE_KEY_PEM);
    const [, sigB64] = blob.split('.');
    expect(base64UrlDecode(sigB64)).toHaveLength(64);
  });

  it('verifies cleanly against the matching public key', async () => {
    const blob = await signLicenseBlob(goldenPayload(), TEST_PRIVATE_KEY_PEM);
    const [payloadB64, sigB64] = blob.split('.');
    const publicKey = await importTestPublicKey();
    const isValid = await crypto.subtle.verify(
      'Ed25519',
      publicKey,
      base64UrlDecode(sigB64),
      base64UrlDecode(payloadB64)
    );
    expect(isValid).toBe(true);
  });

  it('rejects verification after a single byte is flipped in the payload segment (tamper detection)', async () => {
    const blob = await signLicenseBlob(goldenPayload(), TEST_PRIVATE_KEY_PEM);
    const [payloadB64, sigB64] = blob.split('.');

    // Flip "pro" -> "sovereign" the way contract §8's tampered.txt does:
    // edit the decoded JSON, re-encode, but do NOT re-sign.
    const decoded = JSON.parse(new TextDecoder().decode(base64UrlDecode(payloadB64)));
    decoded.plan = 'sovereign';
    const tamperedJson = canonicalJSONStringify(decoded);
    const tamperedBytes = new TextEncoder().encode(tamperedJson);
    let binary = '';
    for (const b of tamperedBytes) binary += String.fromCharCode(b);
    const tamperedB64 = btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');

    const publicKey = await importTestPublicKey();
    const isValid = await crypto.subtle.verify(
      'Ed25519',
      publicKey,
      base64UrlDecode(sigB64),
      base64UrlDecode(tamperedB64)
    );
    expect(isValid).toBe(false);
  });

  it('rejects verification against a different key pair', async () => {
    const otherKeyPair = (await crypto.subtle.generateKey(
      { name: 'Ed25519' },
      true,
      ['sign', 'verify']
    )) as CryptoKeyPair;

    const blob = await signLicenseBlob(goldenPayload(), TEST_PRIVATE_KEY_PEM);
    const [payloadB64, sigB64] = blob.split('.');

    const isValid = await crypto.subtle.verify(
      'Ed25519',
      otherKeyPair.publicKey,
      base64UrlDecode(sigB64),
      base64UrlDecode(payloadB64)
    );
    expect(isValid).toBe(false);
  });
});

describe('deriveLicenseExpiry (adjudication D)', () => {
  const now = 1750000000;

  it('uses DB period end + plan offline_grace_days when period end is known', () => {
    const periodEndSeconds = 1750500000;
    const exp = deriveLicenseExpiry(
      new Date(periodEndSeconds * 1000).toISOString(),
      7,
      now
    );
    expect(exp).toBe(periodEndSeconds + 7 * 86400);
  });

  it('falls back to now + 365 days when period end is null', () => {
    expect(deriveLicenseExpiry(null, 7, now)).toBe(now + 365 * 86400);
  });

  it('falls back to now + 365 days when period end is undefined', () => {
    expect(deriveLicenseExpiry(undefined, 30, now)).toBe(now + 365 * 86400);
  });

  it('falls back to now + 365 days when period end is unparsable', () => {
    expect(deriveLicenseExpiry('not-a-date', 7, now)).toBe(now + 365 * 86400);
  });
});

describe('generateLicenseNonce', () => {
  it('produces 16 lowercase hex characters', () => {
    expect(generateLicenseNonce()).toMatch(/^[0-9a-f]{16}$/);
  });

  it('is not deterministic across calls', () => {
    const a = generateLicenseNonce();
    const b = generateLicenseNonce();
    expect(a).not.toBe(b);
  });
});

describe('buildContractLicensePayload', () => {
  it('assembles a contract §2 payload with machine_id passed through unchanged', () => {
    const payload = buildContractLicensePayload({
      licenseKey: 'RM-PRO-1234-5678-ABCD',
      plan: 'pro',
      machineId: 'a'.repeat(32),
      kid: 'key-test-mono',
      currentPeriodEnd: null,
      offlineGraceDays: 7,
      now: 1750000000,
      nonce: 'fixed-for-test',
    });

    expect(payload).toEqual({
      v: 1,
      kid: 'key-test-mono',
      lic: 'RM-PRO-1234-5678-ABCD',
      plan: 'pro',
      email: '',
      org: '',
      iat: 1750000000,
      exp: 1750000000 + 365 * 86400,
      nbf: 1750000000,
      nonce: 'fixed-for-test',
      machine_id: 'a'.repeat(32),
    });
  });

  it('includes features/limits only when provided', () => {
    const withExtras = buildContractLicensePayload({
      licenseKey: 'RM-PRO-1234-5678-ABCD',
      plan: 'pro',
      machineId: 'a'.repeat(32),
      kid: 'key-test-mono',
      currentPeriodEnd: null,
      offlineGraceDays: 7,
      now: 1750000000,
      nonce: 'n',
      features: ['scan'],
      limits: {
        max_accounts: 3,
        max_regions: -1,
        max_resources_per_scan: -1,
        max_concurrent_scans: 1,
        max_scans_per_day: -1,
        offline_grace_days: 7,
      },
    });
    expect(withExtras.features).toEqual(['scan']);
    expect(withExtras.limits?.max_accounts).toBe(3);

    const withoutExtras = buildContractLicensePayload({
      licenseKey: 'RM-PRO-1234-5678-ABCD',
      plan: 'pro',
      machineId: 'a'.repeat(32),
      kid: 'key-test-mono',
      currentPeriodEnd: null,
      offlineGraceDays: 7,
      now: 1750000000,
      nonce: 'n',
    });
    expect(withoutExtras.features).toBeUndefined();
    expect(withoutExtras.limits).toBeUndefined();
  });

  it('round-trips through signLicenseBlob end to end', async () => {
    const payload = buildContractLicensePayload({
      licenseKey: 'RM-PRO-1234-5678-ABCD',
      plan: 'pro',
      machineId: 'b'.repeat(32),
      kid: 'key-test-mono',
      currentPeriodEnd: '2027-01-01T00:00:00.000Z',
      offlineGraceDays: 7,
    });
    const blob = await signLicenseBlob(payload, TEST_PRIVATE_KEY_PEM);
    const [payloadB64, sigB64] = blob.split('.');

    const publicKey = await importTestPublicKey();
    const isValid = await crypto.subtle.verify(
      'Ed25519',
      publicKey,
      base64UrlDecode(sigB64),
      base64UrlDecode(payloadB64)
    );
    expect(isValid).toBe(true);

    const decoded = JSON.parse(new TextDecoder().decode(base64UrlDecode(payloadB64)));
    expect(decoded.lic).toBe('RM-PRO-1234-5678-ABCD');
    expect(decoded.machine_id).toBe('b'.repeat(32));
    expect(decoded.exp).toBe(Math.floor(Date.parse('2027-01-01T00:00:00.000Z') / 1000) + 7 * 86400);
  });
});
