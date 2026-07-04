/**
 * Clerk session-token test harness.
 *
 * Mints REAL RS256 JWTs signed by a freshly generated RSA keypair, and stubs
 * `fetch` so the production `verifyClerkSession` code path runs unmodified:
 *   - GET {issuer}/.well-known/jwks.json  → the harness JWKS (real public key)
 *   - GET https://api.clerk.com/v1/users/{id} → a user object with email
 *
 * Nothing in the verification logic is mocked — we generate a genuine key,
 * publish its JWKS, and sign genuine tokens, exactly as the real-Stripe-HMAC
 * harness does for webhooks.
 */

import { vi } from 'vitest';

export const TEST_CLERK_ISSUER = 'https://clerk.test.replimap.example';
export const TEST_CLERK_SECRET_KEY = 'sk_test_clerk_harness_secret';
const TEST_KID = 'test-key-1';

function base64UrlEncode(bytes: Uint8Array): string {
  let binary = '';
  for (const b of bytes) binary += String.fromCharCode(b);
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

function jsonToB64Url(obj: unknown): string {
  return base64UrlEncode(new TextEncoder().encode(JSON.stringify(obj)));
}

export interface ClerkHarness {
  issuer: string;
  secretKey: string;
  /** Mint a signed session token for a given user id + email. */
  mintToken: (opts: {
    userId: string;
    email?: string;
    issuer?: string;
    expiresInSeconds?: number;
    notBeforeSeconds?: number;
  }) => Promise<string>;
  /** Install the fetch stub (JWKS + Clerk backend users). Returns the spy. */
  installFetchStub: (opts?: {
    /** Map of userId → primary email for the backend-API fallback. */
    users?: Record<string, string>;
  }) => ReturnType<typeof vi.fn>;
}

export async function createClerkHarness(): Promise<ClerkHarness> {
  const keyPair = (await crypto.subtle.generateKey(
    {
      name: 'RSASSA-PKCS1-v1_5',
      modulusLength: 2048,
      publicExponent: new Uint8Array([1, 0, 1]),
      hash: 'SHA-256',
    },
    true,
    ['sign', 'verify']
  )) as CryptoKeyPair;

  const publicJwk = await crypto.subtle.exportKey('jwk', keyPair.publicKey);
  const jwks = {
    keys: [{ ...publicJwk, kid: TEST_KID, use: 'sig', alg: 'RS256' }],
  };

  async function mintToken(opts: {
    userId: string;
    email?: string;
    issuer?: string;
    expiresInSeconds?: number;
    notBeforeSeconds?: number;
  }): Promise<string> {
    const now = Math.floor(Date.now() / 1000);
    const header = { alg: 'RS256', typ: 'JWT', kid: TEST_KID };
    const payload: Record<string, unknown> = {
      iss: opts.issuer ?? TEST_CLERK_ISSUER,
      sub: opts.userId,
      iat: now,
      nbf: now - (opts.notBeforeSeconds ?? 5),
      exp: now + (opts.expiresInSeconds ?? 3600),
    };
    if (opts.email !== undefined) payload.email = opts.email;

    const signingInput = `${jsonToB64Url(header)}.${jsonToB64Url(payload)}`;
    const signature = await crypto.subtle.sign(
      'RSASSA-PKCS1-v1_5',
      keyPair.privateKey,
      new TextEncoder().encode(signingInput)
    );
    return `${signingInput}.${base64UrlEncode(new Uint8Array(signature))}`;
  }

  function installFetchStub(opts: { users?: Record<string, string> } = {}) {
    const jwksUrl = `${TEST_CLERK_ISSUER}/.well-known/jwks.json`;
    const spy = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url === jwksUrl) {
        return new Response(JSON.stringify(jwks), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        });
      }
      const userMatch = url.match(
        /^https:\/\/api\.clerk\.com\/v1\/users\/([^/?]+)$/
      );
      if (userMatch) {
        const userId = decodeURIComponent(userMatch[1]);
        const email = opts.users?.[userId];
        if (!email) {
          return new Response(JSON.stringify({ errors: [] }), { status: 404 });
        }
        return new Response(
          JSON.stringify({
            id: userId,
            primary_email_address_id: 'idn_primary',
            email_addresses: [
              { id: 'idn_primary', email_address: email },
              { id: 'idn_other', email_address: `other+${userId}@example.com` },
            ],
          }),
          { status: 200, headers: { 'Content-Type': 'application/json' } }
        );
      }
      return new Response('unexpected fetch: ' + url, { status: 500 });
    });
    vi.stubGlobal('fetch', spy);
    return spy;
  }

  return {
    issuer: TEST_CLERK_ISSUER,
    secretKey: TEST_CLERK_SECRET_KEY,
    mintToken,
    installFetchStub,
  };
}
