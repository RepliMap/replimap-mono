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
  STRIPE_SOLO_LIFETIME_PRICE_ID?: string;
  STRIPE_PRO_LIFETIME_PRICE_ID?: string;

  // Machine signature verification (optional - for enhanced security)
  // If set, CLI must send HMAC-SHA256 signature of machine_id
  MACHINE_SIGNATURE_SECRET?: string;

  // Lease token signing secret (optional - for offline mode support)
  // If set, includes a signed JWT in validate response that CLI can cache
  LEASE_TOKEN_SECRET?: string;

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
