/**
 * Ed25519 License Blob Signing
 *
 * Blob Format: Base64URL(payload_json).Base64URL(signature)
 *
 * CLI verification workflow:
 *   1. Split blob by '.'
 *   2. Decode payload and signature from Base64URL
 *   3. Verify: Ed25519.verify(payload_bytes, signature, public_key)
 *   4. Parse payload JSON
 *
 * Security model:
 *   - Private key is stored in Cloudflare Workers secret (ED25519_PRIVATE_KEY)
 *   - Public key is embedded in CLI source code
 *   - Even if public key leaks, signatures cannot be forged
 */

// ============================================================================
// Types
// ============================================================================

export type FingerprintType = 'machine' | 'ci' | 'container';

/**
 * License payload - signed and sent to CLI.
 * Must match CLI's SecureLicenseData structure.
 */
export interface LicensePayload {
  /** License key (full key for binding verification) */
  license_key: string;

  /** Plan: community, pro, team, sovereign */
  plan: string;

  /** Status: active, canceled, expired, past_due, revoked */
  status: string;

  /** Bound machine fingerprint */
  machine_fingerprint: string;

  /** Fingerprint type: machine, ci, container */
  fingerprint_type: FingerprintType;

  /** Plan limits */
  limits: SecureLicenseLimits;

  /** Enabled feature list */
  features: string[];

  /** Issued at (Unix timestamp seconds) */
  iat: number;

  /** Expiration (Unix timestamp seconds) */
  exp: number;

  /** Not before (Unix timestamp seconds) - clock skew tolerance */
  nbf: number;
}

/**
 * Limits structure matching CLI SecureLicenseLimits
 */
export interface SecureLicenseLimits {
  max_accounts: number;
  max_regions: number;
  max_resources_per_scan: number;
  max_concurrent_scans: number;
  max_scans_per_day: number;
  offline_grace_days: number;
}

// ============================================================================
// Ed25519 Signing
// ============================================================================

/**
 * Sign a license payload using Ed25519.
 *
 * @param payload - License payload to sign
 * @param privateKeyBase64 - Base64 encoded Ed25519 private key (32 bytes seed or 64 bytes full)
 * @returns Base64URL encoded blob: "payload.signature"
 */
export async function signLicenseBlob(
  payload: LicensePayload,
  privateKeyBase64: string
): Promise<string> {
  // 1. Serialize payload to JSON bytes
  const payloadJson = JSON.stringify(payload);
  const payloadBytes = new TextEncoder().encode(payloadJson);
  const payloadBase64 = base64UrlEncode(payloadBytes);

  // 2. Import private key
  const privateKeyBytes = base64Decode(privateKeyBase64);

  // Ed25519 keys can be 32-byte seed or 64-byte full key (seed + public)
  // Web Crypto API expects the 32-byte seed
  const keyData =
    privateKeyBytes.length === 64
      ? privateKeyBytes.slice(0, 32)
      : privateKeyBytes;

  if (keyData.length !== 32) {
    throw new Error(
      `Invalid Ed25519 key length: ${keyData.length} (expected 32 or 64 bytes)`
    );
  }

  const privateKey = await crypto.subtle.importKey(
    'raw',
    keyData,
    { name: 'Ed25519' },
    false,
    ['sign']
  );

  // 3. Sign the payload bytes (not the base64 encoded version)
  const signature = await crypto.subtle.sign('Ed25519', privateKey, payloadBytes);

  // 4. Encode signature and combine
  const signatureBase64 = base64UrlEncode(new Uint8Array(signature));

  return `${payloadBase64}.${signatureBase64}`;
}

/**
 * Verify a license blob (for testing and debug purposes).
 *
 * @param blob - The signed blob: "payload_base64.signature_base64"
 * @param publicKeyBase64 - Base64 encoded Ed25519 public key (32 bytes)
 * @returns Parsed payload if valid, null if invalid
 */
export async function verifyLicenseBlob(
  blob: string,
  publicKeyBase64: string
): Promise<LicensePayload | null> {
  try {
    const parts = blob.split('.');
    if (parts.length !== 2) {
      return null;
    }

    const [payloadBase64, signatureBase64] = parts;
    if (!payloadBase64 || !signatureBase64) {
      return null;
    }

    const payloadBytes = base64UrlDecode(payloadBase64);
    const signatureBytes = base64UrlDecode(signatureBase64);
    const publicKeyBytes = base64Decode(publicKeyBase64);

    if (publicKeyBytes.length !== 32) {
      return null;
    }

    const publicKey = await crypto.subtle.importKey(
      'raw',
      publicKeyBytes,
      { name: 'Ed25519' },
      false,
      ['verify']
    );

    const isValid = await crypto.subtle.verify(
      'Ed25519',
      publicKey,
      signatureBytes,
      payloadBytes
    );

    if (!isValid) {
      return null;
    }

    const payload: LicensePayload = JSON.parse(
      new TextDecoder().decode(payloadBytes)
    );

    // Validate time bounds
    const now = Math.floor(Date.now() / 1000);
    if (payload.exp < now) {
      return null; // Expired
    }
    if (payload.nbf > now) {
      return null; // Not yet valid
    }

    return payload;
  } catch {
    return null;
  }
}

// ============================================================================
// Key Generation (run once to generate key pair)
// ============================================================================

/**
 * Generate an Ed25519 key pair.
 *
 * Usage:
 *   1. Run this function once (e.g., in wrangler dev or a script)
 *   2. Store privateKey in Cloudflare Secret: ED25519_PRIVATE_KEY
 *   3. Embed publicKey in CLI: replimap/licensing/crypto/keys.py
 *
 * @returns Object with privateKey, publicKey (Base64), and publicKeyHex
 */
export async function generateEd25519KeyPair(): Promise<{
  privateKey: string;
  publicKey: string;
  publicKeyHex: string;
}> {
  const keyPair = (await crypto.subtle.generateKey(
    { name: 'Ed25519' },
    true, // extractable
    ['sign', 'verify']
  )) as CryptoKeyPair;

  const privateKeyBuffer = await crypto.subtle.exportKey('raw', keyPair.privateKey);
  const publicKeyBuffer = await crypto.subtle.exportKey('raw', keyPair.publicKey);

  const privateKeyBytes = new Uint8Array(privateKeyBuffer as ArrayBuffer);
  const publicKeyBytes = new Uint8Array(publicKeyBuffer as ArrayBuffer);

  return {
    privateKey: base64Encode(privateKeyBytes),
    publicKey: base64Encode(publicKeyBytes),
    publicKeyHex: bytesToHex(publicKeyBytes),
  };
}

// ============================================================================
// Base64URL Helpers (RFC 4648)
// ============================================================================

/**
 * Encode bytes to Base64URL (no padding).
 */
function base64UrlEncode(bytes: Uint8Array): string {
  let binary = '';
  for (const byte of bytes) {
    binary += String.fromCharCode(byte);
  }
  return btoa(binary)
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/, '');
}

/**
 * Decode Base64URL to bytes.
 */
function base64UrlDecode(str: string): Uint8Array {
  // Restore standard Base64 characters
  let padded = str.replace(/-/g, '+').replace(/_/g, '/');

  // Add padding if needed
  while (padded.length % 4) {
    padded += '=';
  }

  const binary = atob(padded);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes;
}

/**
 * Decode standard Base64 to bytes.
 */
function base64Decode(base64: string): Uint8Array {
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes;
}

/**
 * Encode bytes to standard Base64.
 */
function base64Encode(bytes: Uint8Array): string {
  let binary = '';
  for (const byte of bytes) {
    binary += String.fromCharCode(byte);
  }
  return btoa(binary);
}

/**
 * Convert bytes to hex string.
 */
function bytesToHex(bytes: Uint8Array): string {
  return Array.from(bytes)
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('');
}
