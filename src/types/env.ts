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
