/**
 * Environment bindings for Cloudflare Workers
 */
export interface Env {
  // D1 Database
  DB: D1Database;

  // KV Namespace for rate limiting and caching
  CACHE: KVNamespace;

  // Secrets (set via wrangler secret put)
  STRIPE_SECRET_KEY: string;
  STRIPE_WEBHOOK_SECRET: string;
  ADMIN_API_KEY: string;

  // Stripe Lifetime Price IDs (optional - for one-time purchases)
  // These are one-time payment products, not subscriptions
  STRIPE_SOLO_LIFETIME_PRICE_ID?: string;  // Legacy - maps to pro
  STRIPE_PRO_LIFETIME_PRICE_ID?: string;
  STRIPE_TEAM_LIFETIME_PRICE_ID?: string;

  // Machine signature verification (optional - for enhanced security)
  // If set, CLI must send HMAC-SHA256 signature of machine_id
  MACHINE_SIGNATURE_SECRET?: string;

  // Lease token signing secret (optional - for offline mode support)
  // If set, includes a signed JWT in validate response that CLI can cache
  LEASE_TOKEN_SECRET?: string;

  // Ed25519 License Signing (required for license_blob generation)
  // Generate with: npx tsx scripts/generate-keys.ts
  // Store via: wrangler secret put ED25519_PRIVATE_KEY
  ED25519_PRIVATE_KEY: string;

  // Environment variables
  ENVIRONMENT: 'development' | 'production';
  CORS_ORIGIN: string;
  API_VERSION: string;
}

/**
 * Request context passed to handlers
 */
export interface RequestContext {
  env: Env;
  request: Request;
  clientIP: string;
}
