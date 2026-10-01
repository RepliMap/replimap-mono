/**
 * Ed25519 license-blob signing: key generation, sign/verify roundtrip.
 *
 * P2-11 regression: generateEd25519KeyPair used exportKey('raw') for the
 * private key, but signLicenseBlob imports 'pkcs8' and verifyLicenseBlob
 * imports 'spki'. A key pair produced by the generator could never be
 * consumed by the signer/verifier — the roundtrip below locks the formats
 * together.
 */

import { describe, it, expect } from 'vitest';
import {
  generateEd25519KeyPair,
  signLicenseBlob,
  verifyLicenseBlob,
  type LicensePayload,
} from '../src/lib/ed25519';

function payload(overrides: Partial<LicensePayload> = {}): LicensePayload {
  const now = Math.floor(Date.now() / 1000);
  return {
    license_key: 'RM-TEST-AAAA-BBBB-CCCC',
    plan: 'pro',
    status: 'active',
    machine_fingerprint: 'a'.repeat(32),
    fingerprint_type: 'machine',
    limits: {
      max_accounts: 3,
      max_regions: 10,
      max_resources_per_scan: -1,
      max_concurrent_scans: 2,
      max_scans_per_day: 100,
      offline_grace_days: 7,
    },
    features: ['scan', 'clone'],
    iat: now,
    exp: now + 86400,
    nbf: now - 300,
    ...overrides,
  };
}

describe('generateEd25519KeyPair → signLicenseBlob → verifyLicenseBlob', () => {
  it('produces a key pair the signer and verifier can actually consume (pkcs8/spki roundtrip)', async () => {
    const { privateKey, publicKey } = await generateEd25519KeyPair();

    const original = payload();
    const blob = await signLicenseBlob(original, privateKey);
    expect(blob.split('.')).toHaveLength(2);

    const verified = await verifyLicenseBlob(blob, publicKey);
    expect(verified).not.toBeNull();
    expect(verified).toEqual(original);
  });

  it('exposes a 32-byte raw public key as hex for CLI embedding', async () => {
    const { publicKeyHex } = await generateEd25519KeyPair();
    expect(publicKeyHex).toMatch(/^[0-9a-f]{64}$/);
  });

  it('rejects a blob whose payload was tampered with after signing', async () => {
    const { privateKey, publicKey } = await generateEd25519KeyPair();
    const blob = await signLicenseBlob(payload(), privateKey);

    const [payloadB64, sigB64] = blob.split('.');
    const decoded = JSON.parse(
      Buffer.from(payloadB64, 'base64url').toString('utf8')
    ) as LicensePayload;
    decoded.plan = 'sovereign'; // privilege escalation attempt
    const tamperedB64 = Buffer.from(JSON.stringify(decoded), 'utf8').toString(
      'base64url'
    );

    const verified = await verifyLicenseBlob(
      `${tamperedB64}.${sigB64}`,
      publicKey
    );
    expect(verified).toBeNull();
  });

  it('rejects a blob signed by a different key pair', async () => {
    const keysA = await generateEd25519KeyPair();
    const keysB = await generateEd25519KeyPair();

    const blob = await signLicenseBlob(payload(), keysA.privateKey);
    expect(await verifyLicenseBlob(blob, keysB.publicKey)).toBeNull();
  });

  it('rejects an expired payload', async () => {
    const { privateKey, publicKey } = await generateEd25519KeyPair();
    const now = Math.floor(Date.now() / 1000);
    const blob = await signLicenseBlob(
      payload({ iat: now - 7200, exp: now - 3600 }),
      privateKey
    );
    expect(await verifyLicenseBlob(blob, publicKey)).toBeNull();
  });
});
