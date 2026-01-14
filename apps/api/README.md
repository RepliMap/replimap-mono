# RepliMap Backend API

License validation, feature gating, and usage tracking API for RepliMap CLI.

Built on Cloudflare Workers + D1 (SQLite) with Drizzle ORM for global edge deployment.

## Features

### Core Functionality
- **License Validation** - Validate license keys, manage machine activations
- **Feature Gating** - Plan-based feature access control
- **Usage Tracking** - Track feature usage with monthly limits
- **Admin Metrics** - Usage analytics and reporting

### New Features (v2.0)

| Feature | Description | Minimum Plan |
|---------|-------------|--------------|
| **Dependency Explorer** | Explore resource dependencies and impact analysis | TEAM |
| **Audit Remediation** | Auto-generate Terraform fixes with `--fix` flag | SOLO |
| **Drift Snapshots** | Save/compare infrastructure state without Terraform | SOLO |
| **Graph Modes** | `--all` and `--security` filter modes | SOLO |
| **Cost Estimation** | Infrastructure cost estimates (±20% accuracy) | PRO |

### Backward Compatibility

The "Blast Radius" feature has been renamed to "Dependency Explorer":

| Old Command | New Command | Notes |
|-------------|-------------|-------|
| `replimap blast analyze` | `replimap deps explore` | Full replacement |
| `replimap blast export` | `replimap deps export` | Full replacement |

The API accepts deprecated event types (`blast`, `blast_analyze`, `blast_export`) and automatically maps them to the new names, returning deprecation warnings.

## Architecture

```
replimap-backend/
├── src/
│   ├── index.ts              # Main router
│   ├── features.ts           # Feature definitions & plan limits
│   ├── handlers/
│   │   ├── index.ts          # Handler exports
│   │   ├── validate-license.ts   # License validation
│   │   ├── usage.ts          # Usage tracking & limits
│   │   ├── features.ts       # Feature info endpoints
│   │   └── metrics.ts        # Admin metrics
│   ├── lib/
│   │   ├── db.ts             # Drizzle ORM client & database operations
│   │   ├── crypto.ts         # License key generation/validation
│   │   ├── errors.ts         # Error handling
│   │   └── helpers.ts        # Utility functions
│   ├── db/
│   │   └── schema.ts         # Drizzle ORM schema definitions
│   ├── types/
│   │   ├── api.ts            # API types
│   │   └── db.ts             # Database types
│   └── utils/
│       └── event-compat.ts   # Blast → Deps compatibility layer
├── migrations/
│   ├── 001_initial.sql
│   ├── 002_usage_tracking.sql
│   ├── 003_new_features.sql
│   ├── 004_blast_to_deps_rename.sql
│   ├── 005_add_usage_daily.sql     # Telemetry aggregation table
│   ├── 006_add_last_seen_index.sql # Device activity queries
│   ├── 007_add_billing_index.sql   # Quota/billing queries
│   └── 008_add_lifetime_support.sql # Lifetime plan support
├── schema.sql                # Full database schema
└── wrangler.toml             # Cloudflare config
```

## API Endpoints

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

### Feature Check

```bash
POST /v1/features/check
```

**Request:**
```json
{
  "license_key": "RM-XXXX-XXXX-XXXX-XXXX",
  "feature": "audit_fix"
}
```

**Response (allowed):**
```json
{
  "allowed": true,
  "feature": "audit_fix",
  "current_plan": "solo",
  "feature_info": {
    "id": "audit_fix",
    "name": "Audit Remediation",
    "description": "Auto-generate Terraform code to fix issues (--fix)",
    "tier": "solo",
    "available": true,
    "isNew": true
  }
}
```

**Response (denied):**
```json
{
  "allowed": false,
  "feature": "deps",
  "current_plan": "solo",
  "required_plan": "team",
  "feature_info": {
    "id": "deps",
    "name": "Dependency Explorer",
    "tier": "team",
    "available": false,
    "isRenamed": true,
    "previousName": "Blast Radius Analyzer"
  },
  "upgrade_url": "https://replimap.dev/pricing?feature=deps"
}
```

### Feature Catalog

```bash
GET /v1/features
```

Returns complete feature catalog organized by category, with `new_features` and `renamed_features` arrays.

### Usage Tracking

```bash
POST /v1/usage/track
```

**Request:**
```json
{
  "license_key": "RM-XXXX-XXXX-XXXX-XXXX",
  "event_type": "audit_fix",
  "region": "us-west-2",
  "metadata": {
    "total_findings": 10,
    "total_fixable": 8,
    "files_generated": 3
  }
}
```

**Response:**
```json
{
  "success": true,
  "event_id": "abc123...",
  "remaining": 49
}
```

**With deprecated event type:**
```json
{
  "success": true,
  "event_id": "abc123...",
  "remaining": null,
  "deprecation_warning": "Warning: 'blast' is deprecated. Use 'deps' instead.",
  "mapped_to": "deps"
}
```

### Snapshot Tracking

```bash
POST /v1/usage/track
```

**Request:**
```json
{
  "license_key": "RM-XXXX-XXXX-XXXX-XXXX",
  "event_type": "snapshot_save",
  "region": "us-east-1",
  "metadata": {
    "snapshot_name": "prod-baseline-2025-01",
    "resource_count": 150,
    "vpc_id": "vpc-abc123"
  }
}
```

## Event Types

| Event Type | Description | Plan |
|------------|-------------|------|
| `scan` | Infrastructure scan | FREE |
| `graph` | Graph generation | FREE |
| `graph_full` | Full graph mode (--all) | SOLO |
| `graph_security` | Security graph mode | SOLO |
| `audit` | Security audit | FREE |
| `audit_fix` | Remediation generation | SOLO |
| `snapshot_save` | Save snapshot | SOLO |
| `snapshot_diff` | Compare snapshots | SOLO |
| `drift` | Drift detection | PRO |
| `deps` | Dependency explorer | TEAM |
| `deps_explore` | Dependency analysis | TEAM |
| `deps_export` | Export dependencies | TEAM |
| `cost` | Cost estimation | PRO |

### Deprecated Event Types

| Deprecated | Maps To | Removal Date |
|------------|---------|--------------|
| `blast` | `deps` | 2025-06-01 |
| `blast_analyze` | `deps_explore` | 2025-06-01 |
| `blast_export` | `deps_export` | 2025-06-01 |

## Plan Limits

| Feature | FREE | SOLO | PRO | TEAM | ENTERPRISE |
|---------|------|------|-----|------|------------|
| Scans/month | 10 | 100 | 500 | ∞ | ∞ |
| Audit fixes | 0 | 50 | 200 | ∞ | ∞ |
| Snapshots | 0 | 20 | 100 | ∞ | ∞ |
| Dependencies | 0 | 0 | 0 | ∞ | ∞ |
| Machine limit | 1 | 2 | 5 | 20 | ∞ |

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
- **Telemetry Aggregation** - Efficient usage counting (upsert pattern)
- **Router-Level Admin Protection** - Defense in depth for `/v1/admin/*` endpoints
- **Hybrid Quota Reads** - Safe mid-month deployments (sum from legacy + new tables)

### Environment Variables

Set via `wrangler secret put <NAME>`:

| Variable | Description | Required |
|----------|-------------|----------|
| `STRIPE_SECRET_KEY` | Stripe API key | No |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook secret | No |
| `ADMIN_API_KEY` | Admin endpoint auth | Yes |
| `STRIPE_SOLO_LIFETIME_PRICE_ID` | Stripe price ID for Solo lifetime plan | No |
| `STRIPE_PRO_LIFETIME_PRICE_ID` | Stripe price ID for Pro lifetime plan | No |

## Database Schema

### Core Tables

- `user` - User accounts linked to Stripe customers (via `customer_id`)
- `licenses` - License records with plan, features, expiry
- `license_machines` - Machine activations per license
- `machine_changes` - Monthly machine change tracking
- `usage_events` - Detailed event log with metadata
- `usage_daily` - Aggregated daily usage counts (efficient counting)
- `snapshots` - Infrastructure snapshot records
- `remediations` - Audit fix generation records
- `processed_events` - Webhook idempotency tracking

See `schema.sql` for complete schema.

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

# Check feature access
curl -X POST https://your-api.workers.dev/v1/features/check \
  -H "Content-Type: application/json" \
  -d '{"license_key": "RM-XXXX-XXXX-XXXX-XXXX", "feature": "audit_fix"}'

# Track usage
curl -X POST https://your-api.workers.dev/v1/usage/track \
  -H "Content-Type: application/json" \
  -d '{"license_key": "...", "event_type": "audit_fix", "region": "us-west-2"}'
```

## Changelog

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
