/**
 * Generate golden test vectors for the License Blob Format Contract v1
 * (docs/security/license-blob-format.md in the replimap repo, §8).
 *
 * Produces three fixtures for the Python cross-language verifier test
 * suite (Phase 3):
 *   - valid.txt     — verifies cleanly end-to-end.
 *   - tampered.txt  — the valid blob's payload with one field changed
 *                     ("plan": "pro" -> "sovereign", per contract §8's own
 *                     example), WITHOUT re-signing -> must fail signature
 *                     verification (LicenseSignatureError on the Python
 *                     side).
 *   - expired.txt   — structurally identical to valid, but `exp` (and
 *                     `iat`/`nbf`) moved into the past, freshly signed
 *                     (this is a legitimately-signed-but-expired blob, not
 *                     a tamper case) -> must fail with LicenseExpiredError.
 * plus manifest.json recording the exact payload for each vector, the test
 * PUBLIC key PEM, the kid, and this generation command.
 *
 * Re-runnable: generates a FRESH Ed25519 test keypair every run. The test
 * PRIVATE key lives only in this process's memory — it is never written to
 * disk or logged. Test keys are never committed and never added to any
 * production PUBLIC_KEYS registry (contract §4 / §11 adjudication A).
 *
 * Usage:
 *   npx tsx apps/api/scripts/generate-golden-vectors.ts [output-dir]
 *
 * Default output-dir is ../../../replimap/tests/fixtures/golden_license_blobs
 * relative to this script (i.e. the sibling `replimap` Python repo).
 */

import { generateKeyPairSync } from 'node:crypto';
import { mkdirSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  signLicenseBlob,
  canonicalJSONStringify,
  type LicenseBlobPayload,
} from '../src/lib/license-blob-signer';

const SCRIPT_DIR = dirname(fileURLToPath(import.meta.url));
const DEFAULT_OUTPUT_DIR = resolve(
  SCRIPT_DIR,
  '../../../../replimap/tests/fixtures/golden_license_blobs'
);

const KID = 'key-test-2026';

/** Contract §8's deterministic golden payload, pinned field-for-field. */
const VALID_PAYLOAD: LicenseBlobPayload = {
  v: 1,
  email: 'golden-vector@replimap.test',
  exp: 4102444800, // 2100-01-01T00:00:00Z
  features: [],
  iat: 1750000000, // 2025-06-15T15:06:40Z
  kid: KID,
  lic: 'RM-TEST-GOLDEN-0001',
  machine_id: '00000000000000000000000000000000',
  nbf: 1750000000,
  nonce: '0123456789abcdef',
  org: 'RepliMap Test Fixtures',
  plan: 'pro',
};

function base64UrlEncodeString(str: string): string {
  const bytes = new TextEncoder().encode(str);
  let binary = '';
  for (const b of bytes) binary += String.fromCharCode(b);
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

async function main() {
  const outputDir = process.argv[2] ? resolve(process.argv[2]) : DEFAULT_OUTPUT_DIR;

  const { privateKey, publicKey } = generateKeyPairSync('ed25519');
  const privateKeyPem = privateKey.export({ type: 'pkcs8', format: 'pem' }).toString();
  const publicKeyPem = publicKey.export({ type: 'spki', format: 'pem' }).toString();

  // 1. valid.txt
  const validBlob = await signLicenseBlob(VALID_PAYLOAD, privateKeyPem);
  const [, validSigB64] = validBlob.split('.');

  // 2. tampered.txt — edit the decoded payload, re-encode, but reuse the
  // ORIGINAL signature (contract §8: "without re-signing").
  const tamperedPayload: LicenseBlobPayload = { ...VALID_PAYLOAD, plan: 'sovereign' };
  const tamperedPayloadB64 = base64UrlEncodeString(canonicalJSONStringify(tamperedPayload));
  const tamperedBlob = `${tamperedPayloadB64}.${validSigB64}`;

  // 3. expired.txt — structurally identical, exp/iat/nbf moved into the
  // past, freshly signed.
  const expiredPayload: LicenseBlobPayload = {
    ...VALID_PAYLOAD,
    iat: 1600000000, // 2020-09-13T12:26:40Z
    nbf: 1600000000,
    exp: 1600003600, // +1h, still long past
  };
  const expiredBlob = await signLicenseBlob(expiredPayload, privateKeyPem);

  mkdirSync(outputDir, { recursive: true });
  writeFileSync(join(outputDir, 'valid.txt'), `${validBlob}\n`);
  writeFileSync(join(outputDir, 'tampered.txt'), `${tamperedBlob}\n`);
  writeFileSync(join(outputDir, 'expired.txt'), `${expiredBlob}\n`);

  const manifest = {
    contract_version: 1,
    contract_doc: 'docs/security/license-blob-format.md (replimap repo)',
    generated_at: new Date().toISOString(),
    generation_command: 'npx tsx apps/api/scripts/generate-golden-vectors.ts (replimap-mono repo)',
    kid: KID,
    test_public_key_pem: publicKeyPem,
    note:
      'Test keypair generated fresh for this run and used only in-process ' +
      '— never written to disk, never committed, never added to any ' +
      'production PUBLIC_KEYS registry (contract §4 / §11 adjudication A). ' +
      'kid "key-test-2026" must only ever be registered in the Python test ' +
      "suite's monkeypatched KeyRegistry.PUBLIC_KEYS. Re-run this script " +
      'to rotate to a brand new test keypair; all three vectors from a ' +
      'single run share the same keypair.',
    vectors: {
      valid: {
        file: 'valid.txt',
        payload: VALID_PAYLOAD,
        expect: 'LicenseVerifier.verify() succeeds',
      },
      tampered: {
        file: 'tampered.txt',
        payload: tamperedPayload,
        tamper_note:
          'payload segment re-encoded with plan "pro" -> "sovereign" ' +
          "WITHOUT re-signing; signature segment is the valid vector's " +
          'unchanged signature.',
        expect: 'LicenseSignatureError',
      },
      expired: {
        file: 'expired.txt',
        payload: expiredPayload,
        expect: 'LicenseExpiredError',
      },
    },
  };
  writeFileSync(join(outputDir, 'manifest.json'), `${JSON.stringify(manifest, null, 2)}\n`);

  console.log(`Wrote golden vectors to ${outputDir}`);
  console.log(`  valid.txt, tampered.txt, expired.txt, manifest.json`);
  console.log(`  kid: ${KID}`);
  console.log('  test public key PEM (register only in a monkeypatched KeyRegistry.PUBLIC_KEYS):');
  console.log(publicKeyPem);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
