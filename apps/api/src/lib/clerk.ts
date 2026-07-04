/**
 * Clerk session-token verification for Cloudflare Workers.
 *
 * Networkless-style verification: the caller sends their Clerk session token
 * as `Authorization: Bearer <jwt>`. We verify the RS256 signature against the
 * instance's published JWKS, pin the issuer, and check the time bounds. The
 * authoritative email is taken from the token's `email` claim when present
 * (requires a Clerk JWT template), otherwise resolved via the Clerk Backend
 * API using the token's subject.
 *
 * There is no Clerk SDK in this Worker; verification is implemented with the
 * Web Crypto API and the JWKS endpoint only.
 */

import type { Env } from '../types/env';

export interface ClerkIdentity {
  /** Clerk user id (the `sub` claim). */
  userId: string;
  /** Verified primary email, lowercased. */
  email: string;
}

interface JwtHeader {
  alg?: string;
  kid?: string;
  typ?: string;
}

interface JwtPayload {
  iss?: string;
  sub?: string;
  exp?: number;
  nbf?: number;
  email?: string;
}

// Allow a small clock skew when checking exp/nbf.
const CLOCK_SKEW_SECONDS = 60;

/** True when the server has the config needed to verify Clerk tokens. */
export function isClerkConfigured(env: Env): boolean {
  return Boolean(env.CLERK_ISSUER && env.CLERK_SECRET_KEY);
}

function base64UrlDecodeToBytes(str: string): Uint8Array {
  let padded = str.replace(/-/g, '+').replace(/_/g, '/');
  while (padded.length % 4) padded += '=';
  const binary = atob(padded);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  return bytes;
}

function base64UrlDecodeToJson<T>(str: string): T | null {
  try {
    return JSON.parse(new TextDecoder().decode(base64UrlDecodeToBytes(str)));
  } catch {
    return null;
  }
}

function extractBearerToken(request: Request): string | null {
  const header = request.headers.get('Authorization');
  if (!header) return null;
  const match = header.match(/^Bearer\s+(.+)$/i);
  return match ? match[1].trim() : null;
}

async function fetchJwks(
  issuer: string
): Promise<Array<JsonWebKey & { kid?: string }> | null> {
  const url = `${issuer.replace(/\/$/, '')}/.well-known/jwks.json`;
  const res = await fetch(url, { headers: { Accept: 'application/json' } });
  if (!res.ok) return null;
  const body = (await res.json()) as { keys?: Array<JsonWebKey & { kid?: string }> };
  return body.keys ?? null;
}

async function verifyJwtSignature(
  token: string,
  jwk: JsonWebKey
): Promise<{ header: JwtHeader; payload: JwtPayload } | null> {
  const parts = token.split('.');
  if (parts.length !== 3) return null;
  const [headerB64, payloadB64, signatureB64] = parts;

  const header = base64UrlDecodeToJson<JwtHeader>(headerB64);
  const payload = base64UrlDecodeToJson<JwtPayload>(payloadB64);
  if (!header || !payload) return null;
  if (header.alg !== 'RS256') return null;

  const key = await crypto.subtle.importKey(
    'jwk',
    jwk,
    { name: 'RSASSA-PKCS1-v1_5', hash: 'SHA-256' },
    false,
    ['verify']
  );

  const ok = await crypto.subtle.verify(
    'RSASSA-PKCS1-v1_5',
    key,
    base64UrlDecodeToBytes(signatureB64),
    new TextEncoder().encode(`${headerB64}.${payloadB64}`)
  );
  if (!ok) return null;

  return { header, payload };
}

async function resolveEmailFromBackend(
  env: Env,
  userId: string
): Promise<string | null> {
  const res = await fetch(
    `https://api.clerk.com/v1/users/${encodeURIComponent(userId)}`,
    { headers: { Authorization: `Bearer ${env.CLERK_SECRET_KEY}` } }
  );
  if (!res.ok) return null;

  const user = (await res.json()) as {
    primary_email_address_id?: string;
    email_addresses?: Array<{ id: string; email_address: string }>;
  };
  const addresses = user.email_addresses ?? [];
  const primary = addresses.find(
    (a) => a.id === user.primary_email_address_id
  );
  const chosen = primary ?? addresses[0];
  return chosen?.email_address ?? null;
}

/**
 * Verify a Clerk session token from the request's Authorization header.
 *
 * @returns the verified identity, or null when the token is missing, invalid,
 *          expired, from an untrusted issuer, or its email cannot be resolved.
 *          Callers MUST treat null as unauthenticated (401).
 *
 * Precondition: isClerkConfigured(env) === true. Callers must check this
 * first and fail closed (503) when Clerk is not configured.
 */
export async function verifyClerkSession(
  request: Request,
  env: Env
): Promise<ClerkIdentity | null> {
  const token = extractBearerToken(request);
  if (!token) return null;

  // Peek at the header to select the signing key before verifying.
  const parts = token.split('.');
  if (parts.length !== 3) return null;
  const header = base64UrlDecodeToJson<JwtHeader>(parts[0]);
  if (!header?.kid) return null;

  const keys = await fetchJwks(env.CLERK_ISSUER as string);
  if (!keys) return null;
  const jwk = keys.find((k) => k.kid === header.kid);
  if (!jwk) return null;

  const verified = await verifyJwtSignature(token, jwk);
  if (!verified) return null;
  const { payload } = verified;

  // Pin the issuer — never trust a token minted by another instance.
  if (!payload.iss || payload.iss !== env.CLERK_ISSUER) return null;
  if (!payload.sub) return null;

  const now = Math.floor(Date.now() / 1000);
  if (typeof payload.exp === 'number' && now > payload.exp + CLOCK_SKEW_SECONDS) {
    return null;
  }
  if (typeof payload.nbf === 'number' && now + CLOCK_SKEW_SECONDS < payload.nbf) {
    return null;
  }

  const email =
    typeof payload.email === 'string' && payload.email.includes('@')
      ? payload.email
      : await resolveEmailFromBackend(env, payload.sub);
  if (!email) return null;

  return { userId: payload.sub, email: email.toLowerCase() };
}
