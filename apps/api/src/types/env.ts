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

  // Clerk session-token verification (required for authenticated endpoints
  // like /v1/license/provision-community). CLERK_ISSUER is the instance's
  // Frontend API origin (the `iss` claim + JWKS host); CLERK_SECRET_KEY is
  // used to resolve a user's email via the Clerk Backend API when the session
  // token carries no email claim.
  CLERK_ISSUER?: string;
  CLERK_SECRET_KEY?: string;

  // Stripe Lifetime Price IDs (optional - for one-time purchases)
  // These are one-time payment products, not subscriptions
  STRIPE_SOLO_LIFETIME_PRICE_ID?: string;  // Legacy - maps to pro
  STRIPE_PRO_LIFETIME_PRICE_ID?: string;
  STRIPE_TEAM_LIFETIME_PRICE_ID?: string;

  // Resend email delivery (optional — lib/email.ts). Both must be set for
  // license-key emails to actually send; if either is missing,
  // sendLicenseKeyEmail() degrades honestly to {sent:false,
  // reason:'email_not_configured'} rather than pretending to have sent
  // anything. RESEND_API_KEY: Resend API key (re_...). EMAIL_FROM: verified
  // sender, e.g. "RepliMap <license@replimap.com>".
  RESEND_API_KEY?: string;
  EMAIL_FROM?: string;

  // Ops alert webhook (optional — lib/alerts.ts). Receives a JSON POST
  // ({text, content}: Slack/Discord/generic-compatible) for critical
  // operational signals, e.g. [Stripe][MANUAL_REVIEW] payments that issued
  // no license. Unset = alerting is a silent no-op (fail-open).
  OPS_ALERT_WEBHOOK?: string;

  // Ops alert email (optional — lib/alerts.ts). When set, sendOpsAlert()
  // also emails the same message (subject "[RepliMap alert] <tag>", plain
  // text body) via lib/email.ts's Resend sender — so it additionally
  // requires RESEND_API_KEY + EMAIL_FROM to actually deliver. Independent
  // of OPS_ALERT_WEBHOOK: either, both, or neither may be configured, and
  // each channel fails open on its own. Not a secret (no credential), but
  // fine to set as one. e.g. "ops@replimap.com".
  OPS_ALERT_EMAIL?: string;

  // Machine signature verification (optional - for enhanced security)
  // If set, CLI must send HMAC-SHA256 signature of machine_id
  MACHINE_SIGNATURE_SECRET?: string;

  // Ed25519 License Signing (required for license_blob generation)
  // Generate with: npx tsx scripts/generate-keys.ts
  // Store via: wrangler secret put ED25519_PRIVATE_KEY
  ED25519_PRIVATE_KEY: string;

  // License Blob Format Contract v1 signing key (lib/license-blob-signer.ts).
  // PEM-encoded PKCS8 Ed25519 private key text. Optional by design: when
  // unset, /v1/license/validate fails OPEN — it omits `license_blob` from
  // an otherwise-normal response rather than 500ing (see contract §7,
  // docs/security/license-blob-format.md in the replimap repo).
  // Store via: wrangler secret put LICENSE_SIGNING_KEY
  LICENSE_SIGNING_KEY?: string;

  // Key ID (`kid`) recorded in signed license blobs. Optional — falls back
  // to DEFAULT_LICENSE_SIGNING_KID (lib/constants.ts) when unset.
  LICENSE_SIGNING_KID?: string;

  // Environment variables
  ENVIRONMENT: 'development' | 'production';
  CORS_ORIGIN: string;
  // Comma-separated exact web origins allowed in checkout success_url /
  // cancel_url (POST /v1/checkout/session). Fail-closed: unset, empty or '*'
  // rejects every checkout creation request.
  CHECKOUT_ALLOWED_ORIGINS?: string;
  API_VERSION: string;

  // Set to 'true' in local dev to bypass rate limiting during e2e runs.
  // Must NEVER be set in production — rate limits are our DoS defence.
  RATE_LIMIT_DISABLED?: string;
}

/**
 * Request context passed to handlers
 */
export interface RequestContext {
  env: Env;
  request: Request;
  clientIP: string;
}
