# RepliMap Backend API

License validation, device management, billing, and licence administration API for the RepliMap CLI and dashboard.

Built on Cloudflare Workers + D1 (SQLite) with Drizzle ORM for global edge deployment.

## Features

### Core Functionality
- **License Validation** - Validate license keys, manage machine activations
- **Feature Gating** - Plan-based feature access control (limits are returned in the validate response)
- **Billing** - Stripe Checkout, Customer Portal and webhooks
- **Admin** - Licence administration, offline licence blobs, operational stats

### New Features (v2.0)

| Feature | Description | Minimum Plan |
|---------|-------------|--------------|
| **Dependency Explorer** | Explore resource dependencies and impact analysis | TEAM |
| **Audit Remediation** | Auto-generate Terraform fixes with `--fix` flag | SOLO |
| **Drift Snapshots** | Save/compare infrastructure state without Terraform | SOLO |
| **Graph Modes** | `--all` and `--security` filter modes | SOLO |
| **Cost Estimation** | Infrastructure cost estimates (±20% accuracy) | PRO |

## Architecture

```
replimap-backend/
├── src/
│   ├── index.ts              # Main router (Hono)
│   ├── features.ts           # Feature definitions & plan limits
│   ├── handlers/
│   │   ├── index.ts          # Handler exports
│   │   ├── validate-license.ts   # License validation
│   │   ├── billing.ts        # Stripe Checkout + Customer Portal
│   │   └── stripe-webhook.ts # Stripe webhook event handler
│   ├── lib/
│   │   ├── constants.ts      # Plan config, Stripe price IDs
│   │   ├── db.ts             # Drizzle ORM client
│   │   ├── crypto.ts         # License key generation/validation
│   │   ├── errors.ts         # Error handling
│   │   ├── retention.ts      # Daily data-retention job
│   │   └── rate-limiter.ts   # Rate limiting
│   ├── db/
│   │   └── schema.ts         # Drizzle ORM schema definitions
│   └── types/
│       ├── api.ts            # API types
│       ├── db.ts             # Database types
│       └── env.ts            # Cloudflare env bindings
├── migrations/
│   ├── 001_initial.sql       ... 008_add_lifetime_support.sql
├── schema.sql                # Full database schema
└── wrangler.toml             # Cloudflare config
```

## API Endpoints

### Billing & Checkout

```bash
# Create Stripe Checkout Session
POST /v1/checkout/session
```

**Request:**
```json
{
  "plan": "pro",
  "billing_period": "monthly",
  "email": "user@example.com",
  "success_url": "https://replimap.com/checkout/success",
  "cancel_url": "https://replimap.com/checkout?plan=pro&billing=monthly"
}
```

**Response:**
```json
{
  "checkout_url": "https://checkout.stripe.com/c/pay/cs_test_...",
  "session_id": "cs_test_..."
}
```

**Parameters:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `plan` | `pro \| team \| sovereign` | Yes | Target plan |
| `billing_period` | `monthly \| annual` | No | Default: `monthly` |
| `email` | string | Yes | Customer email |
| `success_url` | string | Yes | Redirect after payment |
| `cancel_url` | string | Yes | Redirect on cancel |

```bash
# Create Stripe Customer Portal Session
POST /v1/billing/portal
```

**Request:**
```json
{
  "license_key": "RM-XXXX-XXXX-XXXX-XXXX",
  "return_url": "https://replimap.com/dashboard"
}
```

**Response:**
```json
{
  "portal_url": "https://billing.stripe.com/p/session/..."
}
```

### Stripe Webhooks

```bash
POST /v1/webhooks/stripe
```

Handled events:
| Event | Action |
|-------|--------|
| `checkout.session.completed` | Create user + license (subscription or lifetime) |
| `customer.subscription.created` | Create/update license |
| `customer.subscription.updated` | Update plan, handle up/downgrade |
| `customer.subscription.deleted` | Cancel license |
| `invoice.paid` | Update payment record |
| `invoice.payment_failed` | Flag payment issue |
| `charge.refunded` | Revoke lifetime license |

### Admin Endpoints (require X-API-Key)

```bash
# Get system stats ("God Mode" for operational visibility)
GET /v1/admin/stats

# Response:
{
  "timestamp": "2025-01-15T12:00:00Z",
  "environment": "development",
  "version": "v1",
  "users": { "total": 150 },
  "licenses": { "total": 200, "active": 180 },
  "devices": { "active_7d": 95, "active_30d": 150 },
  "events": {
    "today": 500,
    "this_month": 12000,
    "top_types": [{"event_type": "scan", "total": 5000}, ...]
  }
}
```

#### Offline license blob (Sovereign, air-gapped hosts)

```bash
POST /v1/admin/licenses/{license_key}/offline-blob
GET  /v1/admin/licenses/{license_key}/offline-blobs   # issuance ledger (no blobs)
```

Issues a signed license blob bound to one machine, for a host that can never
reach the API. A blob cannot be revoked, so the endpoint is strict:

- `machine_id` is required: 32 lowercase hex chars (the CLI's machine fingerprint). No unbound blobs.
- `expires_at` is required: ISO-8601 with timezone, in the future, at most 400 days out. It becomes the signed `exp` exactly (no fallback); choose paid-through date plus at most 30 days.
- The license must be `sovereign` and usable (not revoked, expired, past due, or canceled past its period). Otherwise 4xx and nothing is signed.
- `503` if `LICENSE_SIGNING_KEY` is not configured (fails closed, unlike `/v1/license/validate`).
- `nbf` is backdated 48 hours from `iat` so a host with a slow clock can import the blob.
- Every issuance is recorded before the blob is returned: a `usage_logs` row (`action = 'activate'`, `metadata.kind = 'offline_issue'`, with `exp`, `nonce`, `kid`, `note`). No schema migration. The machine is NOT registered in `license_machines` and no `machine_changes` row is written, so offline issuance never counts toward abuse detection or the monthly device-change cap (and the device does not appear in the dashboard).

```bash
curl -sS -X POST "https://<api-host>/v1/admin/licenses/<LICENSE_KEY>/offline-blob" \
  -H "X-API-Key: <ADMIN_API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{"machine_id": "<32-lowercase-hex>", "expires_at": "<ISO-8601-UTC e.g. 2027-01-31T00:00:00Z>", "note": "<ticket or reason>"}'

# Response:
{ "license_blob": "<blob>", "machine_id": "<32-lowercase-hex>", "expires_at": "<ISO-8601-UTC>", "kid": "<signing key id>" }
```

### License Validation

```bash
POST /v1/license/validate
```

**Request:**
```json
{
  "license_key": "RM-XXXX-XXXX-XXXX-XXXX",
  "machine_id": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4",
  "product_version": "2.0.0"
}
```

**Response:**
```json
{
  "valid": true,
  "plan": "solo",
  "features": ["scan", "graph", "audit", "clone_generate", "audit_fix", "snapshot"],
  "new_features": {
    "audit_fix": true,
    "snapshot": true,
    "snapshot_diff": true,
    "deps": false,
    "graph_full": true,
    "graph_security": true,
    "drift": false,
    "cost": false
  },
  "limits": {
    "scan_count": 100,
    "audit_fix_count": 50,
    "snapshot_count": 20
  },
  "expires_at": "2026-01-15T00:00:00Z",
  "max_activations": 2,
  "current_activations": 1
}
```

## Plan Limits (v4.0)

| Feature | COMMUNITY | PRO | TEAM | SOVEREIGN |
|---------|-----------|-----|------|-----------|
| Scans | Unlimited | Unlimited | Unlimited | Unlimited |
| Resources/scan | Unlimited | Unlimited | Unlimited | Unlimited |
| AWS accounts | 1 | 3 | 10 | Unlimited |
| Machines | 1 | 2 | 10 | Unlimited |
| Export formats | JSON | JSON, TF, CSV, HTML, MD | + PDF | + PDF |
| Offline grace | 0 days | 7 days | 14 days | 30 days |
| Price (monthly) | $0 | $29 | $99 | $2,500 |
| Price (annual) | $0 | $290 | $990 | $25,000 |
| Lifetime | — | $199 | $499 | — |

Philosophy: **"Gate Output, Not Input"** — scanning is always free and unlimited.

## Deployment

### Prerequisites

- Node.js 18+
- Wrangler CLI (`npm install -g wrangler`)
- Cloudflare account

### Local Development

```bash
# Install dependencies
npm install

# Run locally
npm run dev
```

### Deploy to Cloudflare

```bash
# Login to Cloudflare
wrangler login

# Create D1 database
wrangler d1 create replimap-prod

# Update wrangler.toml with database_id

# Run migrations
wrangler d1 execute replimap-prod --remote --file=migrations/001_initial.sql
wrangler d1 execute replimap-prod --remote --file=migrations/002_usage_tracking.sql
wrangler d1 execute replimap-prod --remote --file=migrations/003_new_features.sql
wrangler d1 execute replimap-prod --remote --file=migrations/004_blast_to_deps_rename.sql
wrangler d1 execute replimap-prod --remote --file=migrations/005_add_usage_daily.sql
wrangler d1 execute replimap-prod --remote --file=migrations/006_add_last_seen_index.sql
wrangler d1 execute replimap-prod --remote --file=migrations/007_add_billing_index.sql
wrangler d1 execute replimap-prod --remote --file=migrations/008_add_lifetime_support.sql

# Deploy
wrangler deploy
```

### Security Hardening (v2.1)

The backend includes comprehensive security hardening:

- **Rate Limiting** - Per-endpoint rate limits with Retry-After headers
- **HMAC Machine Verification** - Verify CLI-generated machine IDs
- **Constant-Time Comparisons** - Prevent timing attacks on API keys
- **Zod Schema Validation** - Strict input validation on all endpoints
- **CI/CD Detection** - Separate device limits for CI/CD runners
- **Abuse Detection** - Detect license sharing via device patterns
- **JWT Lease Tokens** - Offline CLI operation (3-day validity)
- **Plan Downgrade Handling** - Deactivate devices on tier downgrade
- **Router-Level Admin Protection** - Defense in depth for `/v1/admin/*` endpoints

### Environment Variables

Set via `wrangler secret put <NAME>`:

| Variable | Description | Required |
|----------|-------------|----------|
| `STRIPE_SECRET_KEY` | Stripe API key (sk_test_ or sk_live_) | Yes (for billing) |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signing secret (whsec_) | Yes (for billing) |
| `ADMIN_API_KEY` | Admin endpoint auth | Yes |
| `STRIPE_PRO_LIFETIME_PRICE_ID` | Stripe price ID for Pro lifetime plan | No |
| `STRIPE_TEAM_LIFETIME_PRICE_ID` | Stripe price ID for Team lifetime plan | No |

## Database Schema

### Core Tables

- `user` - User accounts linked to Stripe customers (via `customer_id`)
- `licenses` - License records with plan, features, expiry
- `license_machines` - Machine activations per license
- `machine_changes` - Monthly machine change tracking
- `usage_logs` - Validation/activation log (retained 90 days, see Data retention)
- `usage_idempotency` - Idempotency keys (retained 7 days)
- `processed_events` - Webhook idempotency tracking

Legacy tables `license_aws_accounts`, `usage_events`, `usage_daily`, `snapshots` and `remediations` are kept in the schema (no destructive migration) but no endpoint writes to them any more; the retention job empties them on every run.

See `schema.sql` for complete schema.

## Data retention

A Cloudflare cron trigger (`0 3 * * *`, daily, dev and prod) runs `src/lib/retention.ts`. It enforces exactly this:

| Table | Rule |
|-------|------|
| `license_machines` | Rows with `is_active = 0` are deleted 90 days after `last_seen_at`. Active rows are never modified or deleted, however idle: the CLI contacts the server only on activation, so idle time does not mean a machine is unused. |
| `usage_logs` | Rows older than 90 days are deleted, except offline-licence issuance ledger rows (`action = 'activate'`, `metadata.kind = 'offline_issue'`), which are kept as the issuance audit trail. |
| `machine_changes` | Rows older than 90 days are deleted. |
| `usage_idempotency` | Rows older than 7 days are deleted. |
| `processed_events` | Rows older than 30 days are deleted. |
| `license_aws_accounts`, `usage_events`, `usage_daily`, `snapshots`, `remediations` | All rows are deleted on every run (no endpoint writes to these tables). |

Stored timestamps come in two formats (ISO `...T...Z` from JS, `YYYY-MM-DD HH:MM:SS` from SQLite defaults), so every comparison normalises the column with `datetime(col)`. Each step runs in isolation: a failing step is logged and reported through the ops alert helper (`RETENTION_STEP_FAILED`) and never stops the other steps. Account and licence records (`user`, `licenses`) are not covered by this job.

## Testing

```bash
# Run tests
npm test

# Type check
npm run typecheck
```

### Manual API Tests

```bash
# Health check
curl https://your-api.workers.dev/health

# Validate license
curl -X POST https://your-api.workers.dev/v1/license/validate \
  -H "Content-Type: application/json" \
  -d '{"license_key": "RM-XXXX-XXXX-XXXX-XXXX", "machine_id": "..."}'
```

## Changelog

### v2.4.0 (2026-03)

**Stripe Checkout Integration:**
- Replaced placeholder price IDs with real Stripe test price IDs
- Added `billing_period` support to `POST /v1/checkout/session` (monthly/annual)
- Billing period metadata tracked in Stripe checkout session
- Updated `PLAN_TO_STRIPE_PRICE` and `PLAN_TO_STRIPE_ANNUAL_PRICE` mappings
- Updated lifetime price mappings with real Stripe IDs

**Price IDs (Test Mode):**
| Plan | Monthly | Annual | Lifetime |
|------|---------|--------|----------|
| Pro ($29/$290/$199) | `price_1SiMYg...` | `price_1SiMqM...` | `price_1SnWdS...` |
| Team ($99/$990/$499) | `price_1SiMZv...` | `price_1SiMrJ...` | `price_1TFWke...` |

### v2.3.0 (2026-01)

**Lifetime Plan Support:**
- Added one-time payment (lifetime) license support alongside subscriptions
- Stripe webhook handles `checkout.session.completed` in both `subscription` and `payment` modes
- Lifetime licenses use `stripe_session_id` for idempotency (vs `stripe_subscription_id` for subscriptions)
- Added `charge.refunded` handler to revoke lifetime licenses on payment refund
- New license status: `revoked` with `revoked_at` and `revoked_reason` fields
- Plan type tracking: `free`, `monthly`, `annual`, `lifetime`

**Schema Changes:**
- Added `plan_type` column to licenses table
- Added `stripe_session_id` column (unique, for lifetime idempotency)
- Added `canceled_at`, `revoked_at`, `revoked_reason` status tracking columns

**Environment Variables:**
- `STRIPE_SOLO_LIFETIME_PRICE_ID` - Configure Solo plan lifetime price
- `STRIPE_PRO_LIFETIME_PRICE_ID` - Configure Pro plan lifetime price

**Migrations:**
- `008_add_lifetime_support.sql` - Schema changes for lifetime plans

### v2.2.0 (2025-12)

**Drizzle ORM Migration:**
- Migrated from raw D1 SQL strings to Drizzle ORM
- Type-safe database operations with `DrizzleD1Database<typeof schema>`
- Schema defined in `src/db/schema.ts` with proper TypeScript types
- All handlers updated to use `createDb(env.DB)` factory pattern
- Uses `sql` template literals for complex queries (performance-critical paths)
- `onConflictDoUpdate` for atomic upsert operations
- camelCase property names from Drizzle schema mappings

**Schema Changes:**
- Table `users` renamed to `user` (Drizzle convention)
- Column `stripe_customer_id` renamed to `customer_id`

**Dependencies:**
- Added `drizzle-orm` for type-safe database access

### v2.1.0 (2025-12)

**Security Hardening:**
- Zod schema validation on all endpoints
- HMAC machine signature verification
- Constant-time API key comparisons
- Rate limiting with Retry-After headers
- CI/CD device detection and separate limits
- Abuse detection via device patterns

**Architecture Improvements:**
- Telemetry aggregation (`usage_daily` table) - reduces DB bloat by 97%
- Hybrid quota reads for safe mid-month deployments
- Throttled `last_seen_at` updates (prevent write amplification)
- Scheduled cleanup for orphaned devices
- JWT lease tokens for offline CLI operation
- Router-level admin protection (defense in depth)
- Composite indexes for device and billing queries

**Admin Features:**
- `GET /v1/admin/stats` - Operational visibility endpoint
- Plan downgrade handling (auto-deactivate devices)
- Robust date handling (edge case fixes)

**Migrations:**
- `005_add_usage_daily.sql` - Telemetry aggregation table
- `006_add_last_seen_index.sql` - Index for device activity queries
- `007_add_billing_index.sql` - Composite index for quota/billing queries

### v2.0.0 (2025-01)

**New Features:**
- Dependency Explorer (renamed from Blast Radius)
- Audit Remediation (`--fix` flag support)
- Drift Snapshots (save/diff without Terraform)
- Graph filter modes (`--all`, `--security`)
- Cost Estimation with confidence levels

**API Changes:**
- Added `POST /v1/features/check` endpoint
- Added `GET /v1/features` endpoint
- Added `new_features` and `limits` to license validation response
- Added deprecation warnings for `blast*` event types
- Added `snapshot_save`, `snapshot_diff` event types
- Added `audit_fix` event type with metadata tracking

**Breaking Changes:**
- None (backward compatible with blast → deps mapping)

## License

Proprietary - RepliMap Inc.
