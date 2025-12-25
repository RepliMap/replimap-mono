# RepliMap Backend API - License Validation Status Audit

**Generated:** 2025-12-25
**Repository:** replimap-backend
**Stack:** Cloudflare Workers + D1 (SQLite) + Stripe

---

## 1. Project Structure Overview

```
replimap-backend/
├── src/
│   ├── index.ts              # Main router (entry point)
│   ├── features.ts           # Feature definitions & plan limits
│   ├── handlers/
│   │   ├── validate-license.ts   # License validation (HOT PATH)
│   │   ├── activate-license.ts   # Machine activation
│   │   ├── deactivate-license.ts # Machine deactivation
│   │   ├── usage.ts              # Usage tracking & limits
│   │   ├── features.ts           # Feature info endpoints
│   │   ├── billing.ts            # Stripe checkout/portal
│   │   ├── stripe-webhook.ts     # Subscription lifecycle
│   │   ├── admin.ts              # Admin endpoints
│   │   ├── user.ts               # User self-service
│   │   ├── aws-accounts.ts       # AWS account tracking
│   │   └── metrics.ts            # Analytics endpoints
│   ├── lib/
│   │   ├── constants.ts          # Plan configs, rate limits
│   │   ├── db.ts                 # Database operations
│   │   ├── license.ts            # Key generation/validation
│   │   ├── errors.ts             # Error handling
│   │   └── rate-limiter.ts       # Rate limiting
│   ├── types/
│   │   ├── api.ts                # Request/response types
│   │   ├── db.ts                 # Database row types
│   │   └── env.ts                # Environment bindings
│   └── utils/
│       └── event-compat.ts       # Blast → Deps compatibility
├── schema.sql                    # Full database schema
├── migrations/                   # SQL migrations
└── wrangler.toml                 # Cloudflare deployment config
```

---

## 2. API Endpoints Summary

### Public Endpoints (No Auth)

| Method | Endpoint | Description | Status |
|--------|----------|-------------|--------|
| POST | `/v1/license/validate` | Validate license & bind machine (HOT PATH) | ✅ Implemented |
| POST | `/v1/license/activate` | Explicitly activate license on machine | ✅ Implemented |
| POST | `/v1/license/deactivate` | Deactivate license from machine | ✅ Implemented |
| POST | `/v1/checkout/session` | Create Stripe Checkout session | ✅ Implemented |
| POST | `/v1/billing/portal` | Create Stripe Customer Portal session | ✅ Implemented |
| POST | `/v1/webhooks/stripe` | Handle Stripe subscription events | ✅ Implemented |
| GET | `/health` | Health check | ✅ Implemented |
| GET | `/` | API info | ✅ Implemented |

### User Self-Service Endpoints (auth via license_key)

| Method | Endpoint | Description | Status |
|--------|----------|-------------|--------|
| GET | `/v1/me/license` | Get own license details | ✅ Implemented |
| GET | `/v1/me/machines` | Get machines for own license | ✅ Implemented |
| POST | `/v1/me/resend-key` | Resend license key via email | ✅ Implemented |

### Feature Endpoints

| Method | Endpoint | Description | Status |
|--------|----------|-------------|--------|
| GET | `/v1/features` | Get all features info | ✅ Implemented |
| POST | `/v1/features/check` | Check feature access | ✅ Implemented |
| GET | `/v1/features/flags` | Get feature flags for license | ✅ Implemented |

### Usage Tracking Endpoints

| Method | Endpoint | Description | Status |
|--------|----------|-------------|--------|
| POST | `/v1/usage/sync` | Sync usage data | ✅ Implemented |
| POST | `/v1/usage/track` | Track feature usage event | ✅ Implemented |
| GET | `/v1/usage/{license_key}` | Get usage for license | ✅ Implemented |
| GET | `/v1/usage/{license_key}/history` | Get usage history | ✅ Implemented |
| POST | `/v1/usage/check-quota` | Check quota availability | ✅ Implemented |

### AWS Account Endpoints

| Method | Endpoint | Description | Status |
|--------|----------|-------------|--------|
| POST | `/v1/aws-accounts/track` | Track AWS account usage | ✅ Implemented |
| GET | `/v1/licenses/{key}/aws-accounts` | Get AWS accounts for license | ✅ Implemented |

### Metrics Endpoints (require X-API-Key)

| Method | Endpoint | Description | Status |
|--------|----------|-------------|--------|
| GET | `/v1/metrics/adoption` | Feature adoption metrics | ✅ Implemented |
| GET | `/v1/metrics/conversion` | Conversion metrics | ✅ Implemented |
| GET | `/v1/metrics/remediation-impact` | Remediation impact | ✅ Implemented |
| GET | `/v1/metrics/snapshot-usage` | Snapshot usage metrics | ✅ Implemented |
| GET | `/v1/metrics/deps-usage` | Dependency explorer metrics | ✅ Implemented |

### Admin Endpoints (require X-API-Key)

| Method | Endpoint | Description | Status |
|--------|----------|-------------|--------|
| POST | `/v1/admin/licenses` | Create a new license | ✅ Implemented |
| GET | `/v1/admin/licenses/{key}` | Get license details | ✅ Implemented |
| POST | `/v1/admin/licenses/{key}/revoke` | Revoke a license | ✅ Implemented |

---

## 3. License Validation Mechanism

### Validation Flow (`POST /v1/license/validate`)

```
1. Rate limiting check (100 req/min per IP)
2. Parse & validate license_key format (RM-XXXX-XXXX-XXXX-XXXX)
3. Parse & validate machine_id format (32 char hex)
4. Query license with all related data:
   - License status, plan, expiry
   - Active machine count
   - Monthly machine changes
   - AWS accounts count
5. Check license status (active, canceled, expired, past_due, revoked)
6. Handle machine binding:
   - If already active: update last_seen
   - If deactivated: reactivate (counts as change)
   - If new: check limits, register
7. Log usage event
8. Return validation response with:
   - Plan features
   - Usage counts
   - Feature flags (new_features)
   - Extended limits
   - Cache duration (24h default)
   - CLI version compatibility
```

### License Key Format

- Pattern: `RM-XXXX-XXXX-XXXX-XXXX` (uppercase alphanumeric)
- Generated with cryptographically secure random values
- Stored normalized (uppercase, trimmed)

### Machine ID Format

- 32-character lowercase hexadecimal
- Derived from hardware/system identifiers on CLI side

### Error Handling

| Error Code | Description | HTTP Status |
|------------|-------------|-------------|
| `LICENSE_NOT_FOUND` | License key not found | 404 |
| `LICENSE_EXPIRED` | License has expired | 403 |
| `LICENSE_CANCELED` | License canceled | 403 |
| `LICENSE_PAST_DUE` | Payment past due | 403 |
| `LICENSE_REVOKED` | License revoked by admin | 403 |
| `MACHINE_LIMIT_EXCEEDED` | Too many machines | 403 |
| `MACHINE_CHANGE_LIMIT` | 3 changes/month limit | 429 |
| `RATE_LIMIT_EXCEEDED` | Too many requests | 429 |

---

## 4. Plan Definitions & Feature Gating

### Plans

| Plan | Price | Max Machines | Max AWS Accounts |
|------|-------|--------------|------------------|
| FREE | $0 | 1 | 1 |
| SOLO | $49/mo | 2 | 1 |
| PRO | $99/mo | 3 | 3 |
| TEAM | $199/mo | 10 | 10 |
| ENTERPRISE | $499+/mo | Unlimited | Unlimited |

### Feature Matrix

| Feature | FREE | SOLO | PRO | TEAM | ENTERPRISE |
|---------|------|------|-----|------|------------|
| `scan` | ✅ (3/mo) | ✅ ∞ | ✅ ∞ | ✅ ∞ | ✅ ∞ |
| `graph` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `graph_full` | ❌ | ✅ | ✅ | ✅ | ✅ |
| `graph_security` | ❌ | ✅ | ✅ | ✅ | ✅ |
| `clone_generate` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `clone_download` | ❌ | ✅ | ✅ | ✅ | ✅ |
| `audit` | ✅ (3 findings) | ✅ ∞ | ✅ ∞ | ✅ ∞ | ✅ ∞ |
| `audit_fix` | ❌ | ✅ | ✅ | ✅ | ✅ |
| `audit_ci_mode` | ❌ | ❌ | ✅ | ✅ | ✅ |
| `snapshot` | ✅ (1) | ✅ ∞ | ✅ ∞ | ✅ ∞ | ✅ ∞ |
| `snapshot_diff` | ✅ (1) | ✅ ∞ | ✅ ∞ | ✅ ∞ | ✅ ∞ |
| `drift` | ❌ | ❌ | ✅ | ✅ | ✅ |
| `drift_watch` | ❌ | ❌ | ❌ | ✅ | ✅ |
| `deps` | ❌ | ❌ | ❌ | ✅ | ✅ |
| `cost` | ❌ | ❌ | ✅ | ✅ | ✅ |
| `multi_account` | ❌ | ❌ | ✅ | ✅ | ✅ |
| `sso` | ❌ | ❌ | ❌ | ❌ | ✅ |

### Usage Limits (per month)

| Limit Key | FREE | SOLO | PRO | TEAM |
|-----------|------|------|-----|------|
| `scan_count` | 3 | -1 (∞) | -1 | -1 |
| `audit_visible_findings` | 3 | -1 | -1 | -1 |
| `clone_preview_lines` | 100 | -1 | -1 | -1 |
| `audit_fix_count` | 0 | -1 | -1 | -1 |
| `snapshot_count` | 1 | -1 | -1 | -1 |
| `drift_count` | 0 | 0 | -1 | -1 |
| `deps_count` | 0 | 0 | 0 | -1 |
| `cost_count` | 0 | 0 | -1 | -1 |

---

## 5. Data Models

### Users Table

```sql
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    stripe_customer_id TEXT UNIQUE,
    created_at TEXT,
    updated_at TEXT
);
```

### Licenses Table

```sql
CREATE TABLE licenses (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id),
    license_key TEXT UNIQUE NOT NULL,
    plan TEXT NOT NULL DEFAULT 'free',   -- free|solo|pro|team
    status TEXT NOT NULL DEFAULT 'active', -- active|canceled|expired|past_due|revoked
    stripe_subscription_id TEXT UNIQUE,
    stripe_price_id TEXT,
    current_period_start TEXT,
    current_period_end TEXT,
    created_at TEXT,
    updated_at TEXT
);
```

### Machine Bindings

```sql
CREATE TABLE license_machines (
    id TEXT PRIMARY KEY,
    license_id TEXT NOT NULL REFERENCES licenses(id),
    machine_id TEXT NOT NULL,
    machine_name TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    first_seen_at TEXT,
    last_seen_at TEXT,
    UNIQUE(license_id, machine_id)
);
```

### Usage Events (New Tracking)

```sql
CREATE TABLE usage_events (
    id TEXT PRIMARY KEY,
    license_id TEXT NOT NULL REFERENCES licenses(id),
    event_type TEXT NOT NULL,
    region TEXT,
    vpc_id TEXT,
    resource_count INTEGER,
    duration_ms INTEGER,
    metadata TEXT,              -- JSON string
    original_event_type TEXT,   -- For deprecated event tracking
    created_at TEXT
);
```

### Snapshots Table

```sql
CREATE TABLE snapshots (
    id TEXT PRIMARY KEY,
    license_id TEXT NOT NULL REFERENCES licenses(id),
    name TEXT NOT NULL,
    region TEXT NOT NULL,
    vpc_id TEXT,
    resource_count INTEGER,
    profile TEXT,
    replimap_version TEXT,
    storage_type TEXT DEFAULT 'local',
    storage_path TEXT,
    created_at TEXT
);
```

### Remediations Table

```sql
CREATE TABLE remediations (
    id TEXT PRIMARY KEY,
    license_id TEXT NOT NULL REFERENCES licenses(id),
    audit_id TEXT,
    region TEXT NOT NULL,
    total_findings INTEGER,
    total_fixable INTEGER,
    total_manual INTEGER,
    files_generated INTEGER,
    created_at TEXT
);
```

---

## 6. External Service Integrations

### Stripe Integration ✅

**Status:** Fully Implemented

| Component | Endpoint | Status |
|-----------|----------|--------|
| Checkout Session | `POST /v1/checkout/session` | ✅ |
| Customer Portal | `POST /v1/billing/portal` | ✅ |
| Webhook Handler | `POST /v1/webhooks/stripe` | ✅ |

**Webhook Events Handled:**
- `checkout.session.completed` - Create user if needed
- `customer.subscription.created` - Create license
- `customer.subscription.updated` - Update plan/status
- `customer.subscription.deleted` - Mark canceled
- `invoice.paid` - Update period dates
- `invoice.payment_failed` - Mark past_due
- `customer.deleted` - Expire all licenses

**Stripe Price IDs (configured in `constants.ts`):**
- Solo: `price_1SiMWsAKLIiL9hdweoTnH17A`
- Pro: `price_1SiMYgAKLIiL9hdwZLjLUOPm`
- Team: `price_1SiMZvAKLIiL9hdw8LAIvjrS`

### AWS Pricing API

**Status:** Not Implemented (for cost estimation feature)

The backend tracks AWS accounts per license but does not currently integrate with AWS Pricing API for cost estimation. This is done client-side in the CLI.

---

## 7. Configuration

### Environment Variables (via wrangler.toml)

| Variable | Development | Production |
|----------|-------------|------------|
| `ENVIRONMENT` | "development" | "production" |
| `CORS_ORIGIN` | "*" | "https://replimap.io" |
| `API_VERSION` | "v1" | "v1" |

### Secrets (via `wrangler secret put`)

| Secret | Required | Description |
|--------|----------|-------------|
| `STRIPE_SECRET_KEY` | No | Stripe API key |
| `STRIPE_WEBHOOK_SECRET` | No | Stripe webhook signing secret |
| `ADMIN_API_KEY` | Yes | Admin endpoint authentication |

### Rate Limiting

| Endpoint Type | Requests | Window |
|--------------|----------|--------|
| `validate` | 100 | 60 seconds |
| `activate` | 10 | 60 seconds |
| `deactivate` | 10 | 60 seconds |

---

## 8. Backward Compatibility

### Blast → Deps Rename

The "Blast Radius" feature has been renamed to "Dependency Explorer":

| Old Event | New Event | Status |
|-----------|-----------|--------|
| `blast` | `deps` | ✅ Auto-mapped |
| `blast_analyze` | `deps_explore` | ✅ Auto-mapped |
| `blast_export` | `deps_export` | ✅ Auto-mapped |

**Deprecation Timeline:**
- Current: Accepted with warning
- Removal: 2025-06-01

**API Response Example:**
```json
{
  "success": true,
  "event_id": "abc123",
  "deprecation_warning": "Warning: 'blast' is deprecated. Use 'deps' instead.",
  "mapped_to": "deps"
}
```

---

## 9. CLI Integration Points

### What CLI Should Call

1. **On Startup:** `POST /v1/license/validate`
   - Returns plan, features, limits, cache_until
   - CLI should cache response until `cache_until`

2. **On Feature Use:** `POST /v1/usage/track`
   - Track each feature usage
   - Returns remaining quota

3. **For Feature Check:** `POST /v1/features/check`
   - Check if specific feature is allowed
   - Returns upgrade URL if not allowed

### Response Fields for CLI

The `/v1/license/validate` response includes:

```typescript
{
  valid: true,
  plan: string,
  status: string,
  features: {
    resources_per_scan: number,
    scans_per_month: number,
    aws_accounts: number,
    machines: number,
    export_formats: string[]
  },
  usage: {
    scans_this_month: number,
    machines_active: number,
    machines_limit: number,
    aws_accounts_active: number,
    aws_accounts_limit: number
  },
  expires_at: string | null,
  cache_until: string,
  cli_version?: {
    status: 'ok' | 'deprecated' | 'unsupported',
    message?: string,
    latest_version: string,
    upgrade_url: string
  },
  new_features: {
    audit_fix: boolean,
    snapshot: boolean,
    snapshot_diff: boolean,
    deps: boolean,
    graph_full: boolean,
    graph_security: boolean,
    drift: boolean,
    drift_watch: boolean,
    cost: boolean,
    clone_download: boolean,
    audit_ci_mode: boolean
  },
  limits: {
    audit_fix_count: number,
    snapshot_count: number,
    snapshot_diff_count: number,
    drift_count: number,
    deps_count: number,
    cost_count: number,
    clone_preview_lines: number,
    audit_visible_findings: number
  }
}
```

---

## 10. Missing Features / Gap Analysis

### What's NOT Implemented

| Feature | Description | Priority | Notes |
|---------|-------------|----------|-------|
| **Pass Mechanism** | One-time feature access passes | P2 | Not in current architecture |
| **Right-Sizer API** | AWS resource right-sizing | P0 | Would require AWS Pricing API |
| **Tagging API** | Resource tagging recommendations | P1 | Not planned |
| **Email Notifications** | License expiry alerts | P3 | Would need email service |
| **Self-hosted License Server** | On-premise deployment | P4 | Enterprise only |

### Potential Improvements

1. **Pass Mechanism**
   - Would require new table for passes
   - API: `POST /v1/passes/validate`, `POST /v1/passes/redeem`
   - Needs purchase flow integration

2. **Price Adjustments**
   - Solo currently at $49, discussed reducing to $29
   - Would need Stripe product updates
   - Update `PLAN_PRICES` in constants.ts

3. **AWS Cost Integration**
   - Currently cost estimation is CLI-side only
   - Could add `POST /v1/cost/estimate` endpoint
   - Would require AWS Pricing API credentials

---

## 11. Recommended Implementation Order

### Phase 1: Price & Plan Adjustments
1. Update Stripe products for new pricing
2. Update `PLAN_TO_STRIPE_PRICE` mapping in backend
3. Update `PLAN_PRICES` for display
4. Test subscription flow

### Phase 2: Right-Sizer API (if needed)
1. Add AWS Pricing API credentials to secrets
2. Create `/v1/rightsizer/analyze` endpoint
3. Add usage tracking for right-sizer
4. CLI integration

### Phase 3: Pass Mechanism (if needed)
1. Design pass table schema
2. Add `passes` table to schema.sql
3. Create pass handlers
4. Integrate with Stripe for pass purchases

### Phase 4: Tagging API (if needed)
1. Design tagging rules storage
2. Add tagging analysis endpoint
3. CLI integration

---

## 12. Summary

| Category | Status |
|----------|--------|
| **License Validation** | ✅ Complete |
| **Feature Gating** | ✅ Complete |
| **Usage Tracking** | ✅ Complete |
| **Stripe Integration** | ✅ Complete |
| **Machine Binding** | ✅ Complete |
| **AWS Account Tracking** | ✅ Complete |
| **Metrics & Analytics** | ✅ Complete |
| **Admin Endpoints** | ✅ Complete |
| **Backward Compatibility** | ✅ Complete (blast→deps) |
| **Pass Mechanism** | ❌ Not Implemented |
| **Right-Sizer API** | ❌ Not Implemented |
| **Tagging API** | ❌ Not Implemented |

The backend is **production-ready** for current feature set. Additional features (passes, right-sizer, tagging) would require new endpoint development.
