/**
 * License Blob Signer — License Blob Format Contract v1
 *
 * Implements the exact wire format the real Python CLI verifier expects
 * (`replimap/licensing/verifier.py::LicenseVerifier`), as pinned by
 * `docs/security/license-blob-format.md` in the replimap repo (§1–§4, §8,
 * §11 adjudicated decisions). This is a *different* payload schema from the
 * pre-existing `signLicenseBlob`/`LicensePayload` pair in `./ed25519.ts` —
 * that module's payload (`license_key`/`status`/`machine_fingerprint`/...)
 * predates this contract and is not parseable by the real verifier (it has
 * no `lic` field, which `_parse_payload`'s `required_fields` hard-requires).
 * This module supersedes it for `/v1/license/validate`'s `license_blob`.
 *
 * Blob format: base64url(payload_bytes).base64url(signature_bytes), both
 * segments UNPADDED. Signature is Ed25519 over payload_bytes exactly as
 * transmitted (contract §1/§3).
 *
 * Canonicalization (contract §1): compact separators (`,`/`:`), keys sorted
 * alphabetically at every object level, non-ASCII escaped as `\uXXXX` — the
 * TS equivalent of Python's
 * `json.dumps(payload, separators=(",", ":"), sort_keys=True)`. The
 * verifier does not re-canonicalize to check the signature (it verifies the
 * raw transmitted bytes), so this only matters for byte-reproducible golden
 * vectors and cross-language audit diffing — but we still implement it
 * faithfully since golden vectors depend on it.
 */

import type { SecureLicenseLimits } from './ed25519';

// ============================================================================
// Types
// ============================================================================

/**
 * License blob payload — contract §2. Flat JSON object, `limits` is the
 * only nested field.
 */
export interface LicenseBlobPayload {
  /** Schema version. Always 1. */
  v: 1;
  /** Key ID used to sign — never rely on a verifier-side default. */
  kid: string;
  /** License key, e.g. "RM-PRO-1234-ABCD". */
  lic: string;
  /** One of community/pro/team/sovereign. */
  plan: string;
  /** Licensee email. Contract-required; empty string if unavailable. */
  email: string;
  /** Organization name. Recommended; empty string if unavailable. */
  org: string;
  /** Issued-at, unix seconds UTC. */
  iat: number;
  /** Expiry, unix seconds UTC. Always present per contract (§9 delta #1). */
  exp: number;
  /**
   * Not-before, unix seconds UTC. Backdated NBF_LEEWAY_SECONDS from iat so
   * clients with slightly slow clocks accept a freshly signed blob.
   */
  nbf: number;
  /** Informational/audit-trail only — not used for anti-replay. */
  nonce: string;
  /** Explicit feature grants beyond plan defaults. */
  features?: string[];
  /** Plan limit overrides. */
  limits?: SecureLicenseLimits;
  /** 32 lowercase hex chars — CLI's get_machine_fingerprint() output. */
  machine_id: string;
}

// ============================================================================
// Canonical JSON serialization (contract §1)
// ============================================================================

/**
 * Serialize a value the way Python's
 * `json.dumps(value, separators=(",", ":"), sort_keys=True)` would:
 * compact separators, alphabetically sorted object keys (recursively),
 * non-ASCII escaped as `\uXXXX` (matches `ensure_ascii=True`, the
 * `json.dumps` default).
 *
 * Only needs to support the JSON value shapes that actually appear in a
 * license payload: strings, finite numbers, booleans, null, arrays, and
 * plain objects.
 */
export function canonicalJSONStringify(value: unknown): string {
  if (value === null || value === undefined) {
    return 'null';
  }
  if (typeof value === 'boolean') {
    return value ? 'true' : 'false';
  }
  if (typeof value === 'number') {
    if (!Number.isFinite(value)) {
      throw new Error(`Cannot canonicalize non-finite number: ${value}`);
    }
    return String(value);
  }
  if (typeof value === 'string') {
    return canonicalJSONStringLiteral(value);
  }
  if (Array.isArray(value)) {
    return `[${value.map((item) => canonicalJSONStringify(item)).join(',')}]`;
  }
  if (typeof value === 'object') {
    const obj = value as Record<string, unknown>;
    const sortedKeys = Object.keys(obj).sort();
    const parts = sortedKeys.map(
      (key) => `${canonicalJSONStringLiteral(key)}:${canonicalJSONStringify(obj[key])}`
    );
    return `{${parts.join(',')}}`;
  }
  throw new Error(`Cannot canonicalize value of type ${typeof value}`);
}

/**
 * JSON-encode a single string with non-ASCII escaped as `\uXXXX`, operating
 * on UTF-16 code units (matches both JSON's own escaping rules and Python's
 * `ensure_ascii=True`, which also emits surrogate-pair `\uXXXX\uXXXX` for
 * non-BMP characters).
 */
function canonicalJSONStringLiteral(str: string): string {
  let out = '"';
  for (let i = 0; i < str.length; i++) {
    const ch = str[i];
    const code = str.charCodeAt(i);
    switch (ch) {
      case '"':
        out += '\\"';
        break;
      case '\\':
        out += '\\\\';
        break;
      case '\b':
        out += '\\b';
        break;
      case '\f':
        out += '\\f';
        break;
      case '\n':
        out += '\\n';
        break;
      case '\r':
        out += '\\r';
        break;
      case '\t':
        out += '\\t';
        break;
      default:
        if (code < 0x20 || code > 0x7e) {
          out += `\\u${code.toString(16).padStart(4, '0')}`;
        } else {
          out += ch;
        }
    }
  }
  return `${out}"`;
}

// ============================================================================
// Base64url helpers (unpadded — contract §1)
// ============================================================================

function base64UrlEncode(bytes: Uint8Array): string {
  let binary = '';
  for (const byte of bytes) {
    binary += String.fromCharCode(byte);
  }
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

/** Strip PEM armor/whitespace and base64-decode the body to raw DER bytes. */
function pemToDer(pem: string): Uint8Array {
  const body = pem
    .replace(/-----BEGIN [^-]+-----/g, '')
    .replace(/-----END [^-]+-----/g, '')
    .replace(/\s+/g, '');
  const binary = atob(body);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes;
}

// ============================================================================
// Signing
// ============================================================================

/**
 * Sign a license blob payload per contract §1/§3/§4.
 *
 * @param payload - Contract §2 payload (caller-assembled; use
 *   `buildContractLicensePayload` for the standard construction).
 * @param privateKeyPem - PEM-encoded PKCS8 Ed25519 private key text (the
 *   Worker secret's raw value — NOT base64-of-DER, the full
 *   "-----BEGIN PRIVATE KEY-----...-----END PRIVATE KEY-----" text).
 * @returns "base64url(payload_bytes).base64url(signature_bytes)", both
 *   segments unpadded.
 */
export async function signLicenseBlob(
  payload: LicenseBlobPayload,
  privateKeyPem: string
): Promise<string> {
  const payloadJson = canonicalJSONStringify(payload);
  const payloadBytes = new TextEncoder().encode(payloadJson);

  const der = pemToDer(privateKeyPem);
  const privateKey = await crypto.subtle.importKey(
    'pkcs8',
    der,
    { name: 'Ed25519' },
    false,
    ['sign']
  );

  const signature = await crypto.subtle.sign('Ed25519', privateKey, payloadBytes);

  const payloadB64 = base64UrlEncode(payloadBytes);
  const signatureB64 = base64UrlEncode(new Uint8Array(signature));

  return `${payloadB64}.${signatureB64}`;
}

// ============================================================================
// Payload assembly (adjudicated decisions — contract §11)
// ============================================================================

const SECONDS_PER_DAY = 86400;
/** Adjudication D fallback when the DB has no subscription period end. */
const FALLBACK_EXPIRY_DAYS = 365;

/**
 * Derive `exp` per contract §11 adjudication D: end of the current
 * subscription period (absolute, from the Worker's DB) plus the plan's
 * `offline_grace_days`. If the DB has no period end, fall back to
 * `now + 365 days`.
 *
 * Pure function — no wall-clock reads — for deterministic unit testing.
 */
export function deriveLicenseExpiry(
  currentPeriodEnd: string | null | undefined,
  offlineGraceDays: number,
  nowSeconds: number
): number {
  if (currentPeriodEnd) {
    const periodEndMs = Date.parse(currentPeriodEnd);
    if (!Number.isNaN(periodEndMs)) {
      return Math.floor(periodEndMs / 1000) + offlineGraceDays * SECONDS_PER_DAY;
    }
  }
  return nowSeconds + FALLBACK_EXPIRY_DAYS * SECONDS_PER_DAY;
}

/** Generate a `nonce` the same shape as the Python reference signer's
 * `secrets.token_hex(8)` — 16 lowercase hex chars. Informational only. */
export function generateLicenseNonce(): string {
  const bytes = new Uint8Array(8);
  crypto.getRandomValues(bytes);
  return Array.from(bytes)
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('');
}

/**
 * How far nbf is backdated from iat. A verifier whose clock lags the worker
 * by up to this much still accepts a just-signed blob ("License not valid
 * until ..." otherwise). The CLI verifier applies the same 300s leeway on its
 * side; the two are independent safety margins.
 */
export const NBF_LEEWAY_SECONDS = 300;

export interface BuildLicensePayloadInput {
  licenseKey: string;
  plan: string;
  machineId: string;
  kid: string;
  /** DB subscription period end (ISO string) — null/undefined if unknown. */
  currentPeriodEnd: string | null | undefined;
  offlineGraceDays: number;
  email?: string;
  org?: string;
  features?: string[];
  limits?: SecureLicenseLimits;
  /** Unix seconds; defaults to `Date.now()`. Overridable for tests. */
  now?: number;
  /** Overridable for deterministic tests; defaults to a fresh random nonce. */
  nonce?: string;
}

/**
 * Assemble a contract §2 payload from validation-time inputs. Pure aside
 * from its two overridable "current time"/"nonce" defaults.
 */
export function buildContractLicensePayload(
  input: BuildLicensePayloadInput
): LicenseBlobPayload {
  const now = input.now ?? Math.floor(Date.now() / 1000);
  const exp = deriveLicenseExpiry(input.currentPeriodEnd, input.offlineGraceDays, now);

  return {
    v: 1,
    kid: input.kid,
    lic: input.licenseKey,
    plan: input.plan,
    email: input.email ?? '',
    org: input.org ?? '',
    iat: now,
    exp,
    nbf: now - NBF_LEEWAY_SECONDS,
    nonce: input.nonce ?? generateLicenseNonce(),
    ...(input.features ? { features: input.features } : {}),
    ...(input.limits ? { limits: input.limits } : {}),
    machine_id: input.machineId,
  };
}
