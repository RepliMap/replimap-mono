# Commercial Payment Flow — Testing Guide

Manual and automated test procedures for the end-to-end commercial flow
(landing page CTAs → Clerk sign-up → Stripe checkout → license delivery
→ CLI activation).

## Architecture summary

```
┌──────────────┐    ┌──────────┐    ┌─────────┐    ┌──────────┐
│ Landing page │───▶│  Clerk   │───▶│/checkout│───▶│  Stripe  │
│ CTAs         │    │ sign-up  │    │  page   │    │ Checkout │
└──────────────┘    └────┬─────┘    └─────────┘    └────┬─────┘
                         │                               │
                         ▼                               ▼
                  ┌────────────┐                   ┌──────────┐
                  │  Dashboard │                   │  Stripe  │
                  │ (community │                   │ Webhook  │
                  │  license)  │                   └────┬─────┘
                  └────────────┘                        │
                                                        ▼
                                            ┌──────────────────────┐
                                            │ /checkout/success    │
                                            │  polls for license   │
                                            └──────────────────────┘
```

## Prerequisites

- `pnpm install` at repo root
- Stripe CLI installed (and authenticated — either `stripe login` or `stripe --api-key sk_test_...`)
- `apps/web/.env.local` populated with:
  - `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` + `CLERK_SECRET_KEY` (from your Clerk dashboard)
  - `STRIPE_SECRET_KEY` (sk_test_...)
  - `STRIPE_WEBHOOK_SECRET` (whsec_...) — captured automatically by the harness script
  - `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` (pk_test_...)
  - `NEXT_PUBLIC_API_URL=http://localhost:8787`
  - `STRIPE_PRO_*_PRICE_ID` / `STRIPE_TEAM_*_PRICE_ID` (monthly/annual/lifetime)
- `apps/api/.dev.vars` populated with the same secrets + `CORS_ORIGIN` that includes the Playwright port + `RATE_LIMIT_DISABLED=true`
- Local D1 bootstrapped via migrations:
  ```bash
  cd apps/api && pnpm exec wrangler d1 migrations apply replimap-dev --local
  ```
  Migration `011_drizzle_schema_bootstrap.sql` creates the Better-Auth `user` table and updates the `licenses` plan enum to the v4 values (community/pro/team/sovereign).

**Clerk test mode:** e2e tests use [`@clerk/testing`](https://clerk.com/docs/testing/playwright/overview), which bypasses Clerk bot protection automatically using only the publishable + secret keys. No extra token or dashboard configuration is needed. Email verification is skipped because tests use `+clerk_test` email addresses (Clerk's test OTP is always `424242`).

## Stripe test cards

| Card | Scenario |
|---|---|
| `4242 4242 4242 4242` | Success — default happy path |
| `4000 0000 0000 9995` | Insufficient funds (declined) |
| `4000 0025 0000 3155` | Requires 3DS authentication |
| `4000 0000 0000 0069` | Expired card |

Any future expiry (e.g., `12 / 35`), any 3-digit CVC, any ZIP.

## Automated run (happy path)

```bash
# From repo root
./scripts/e2e-commercial-flow.sh
```

This boots everything (wrangler + stripe listen + next dev) and runs
both Playwright specs. Artifacts (traces, videos, screenshots) land in
`apps/web/test-results/` on failure.

To run one spec only:

```bash
./scripts/e2e-commercial-flow.sh community-signup
./scripts/e2e-commercial-flow.sh pro-checkout
./scripts/e2e-commercial-flow.sh lifetime-checkout
```

**What each spec covers:**

| Spec | Flow | External services |
|---|---|---|
| `community-signup` (UI) | Landing → sign-up → dashboard → community license visible | Clerk only |
| `community-signup` (API) | Direct `POST /v1/license/provision-community` + idempotency | none |
| `pro-checkout` | Sign-up → `/checkout?plan=pro&billing=monthly` → Stripe → success page shows license → activate via API | Clerk + Stripe + webhook |
| `lifetime-checkout` | Sign-up → `/checkout?plan=pro&billing=lifetime` → Stripe (`mode=payment`) → success page shows license with `plan_type=lifetime` → activate | Clerk + Stripe + webhook |

## Manual walkthrough

### 1. Free tier (community)

1. Start the web app: `cd apps/web && pnpm dev`
2. Open http://localhost:3000/
3. Click **Get Started Free** in the hero
4. Complete Clerk sign-up with any email
5. You should land on `/dashboard` with a **Community** license card
6. Click "View License Details" → verify the license key is displayed (`RM-...`)

### 2. Paid tier (Pro, monthly)

1. Ensure wrangler + stripe listen + next dev are all running
2. Sign in as any existing Clerk user (or sign up fresh)
3. Go to http://localhost:3000/#pricing
4. Click **Start Pro Trial** on the Pro card
5. On `/checkout?plan=pro&billing=monthly`, verify the price shows $29/mo
6. Click **Continue to Payment** — redirects to Stripe Checkout
7. Fill the test card (`4242 4242 4242 4242`, 12/35, 123, any email)
8. Stripe redirects to `/checkout/success?session_id=cs_test_...`
9. Within ~10s the page should swap from "Creating your license…" to the license key reveal
10. Verify the Stripe CLI terminal shows: `checkout.session.completed`, `customer.subscription.created`, `invoice.paid`
11. Copy the license key and activate:

    ```bash
    curl -X POST http://localhost:8787/v1/license/activate \
      -H "Content-Type: application/json" \
      -d '{
        "license_key": "RM-XXXX-XXXX-XXXX-XXXX",
        "machine_fingerprint": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "machine_name": "dev-machine",
        "fingerprint_type": "developer_workstation"
      }'
    ```

    Expect 200 with a `license_blob` (Ed25519-signed token).

### 3. Lifetime tier (Pro Lifetime)

1. On the pricing page, click the **Lifetime** toggle
2. Click **Start Pro Trial** (or equivalent CTA)
3. `/checkout?plan=pro&billing=lifetime` should show $199 one-time
4. Continue to Stripe — verify Stripe page shows "Pay RepliMap $199" (no recurring)
5. Pay with test card
6. Success page shows license key
7. In Stripe CLI terminal, verify `charge.refunded` handler: issue a refund from the Stripe Dashboard test mode, confirm the license status flips to `revoked` in D1

## Inspecting D1 state

```bash
cd apps/api

# List recent licenses
wrangler d1 execute replimap-db --local --command \
  "SELECT license_key, plan, status, plan_type, created_at FROM licenses ORDER BY created_at DESC LIMIT 10"

# Check users
wrangler d1 execute replimap-db --local --command \
  "SELECT id, email, customer_id, created_at FROM user ORDER BY created_at DESC LIMIT 10"

# See processed webhook events (idempotency log)
wrangler d1 execute replimap-db --local --command \
  "SELECT event_id, event_type, processed_at FROM processed_events ORDER BY processed_at DESC LIMIT 10"
```

## Resetting test data

```bash
cd apps/api

# Delete all e2e test users + their licenses
wrangler d1 execute replimap-db --local --command \
  "DELETE FROM license_machines WHERE license_id IN (SELECT id FROM licenses WHERE user_id IN (SELECT id FROM user WHERE email LIKE 'e2e+%@replimap-test.dev')); \
   DELETE FROM licenses WHERE user_id IN (SELECT id FROM user WHERE email LIKE 'e2e+%@replimap-test.dev'); \
   DELETE FROM user WHERE email LIKE 'e2e+%@replimap-test.dev'"
```

## Production Rollback Playbook

> Assume prod D1 is `replimap-prod` and prod worker is `replimap-api-prod`. Replace `--local` with `--remote --env prod` in all wrangler commands below. Stripe Dashboard links default to live mode unless noted.

### Scenario 1 — User paid but license wasn't delivered

Symptom: customer emails saying they paid but `/checkout/success` never revealed a key, or the dashboard shows "No License".

```bash
# 1. Did the webhook reach us at all?
#    Stripe Dashboard → Developers → Webhooks → https://api.replimap.com/v1/webhooks/stripe
#    Check "Recent deliveries" for the session_id; look for 4xx/5xx responses.

# 2. Do we have the user?
wrangler d1 execute replimap-prod --remote --env prod --command \
  "SELECT id, email, customer_id FROM user WHERE email = 'customer@example.com'"

# 3. Was the webhook event received and marked processed?
wrangler d1 execute replimap-prod --remote --env prod --command \
  "SELECT event_id, event_type, processed_at FROM processed_events
   WHERE event_id = 'evt_...' OR processed_at > datetime('now', '-1 hour')
   ORDER BY processed_at DESC LIMIT 10"

# 4. Does a license exist for that session/customer?
wrangler d1 execute replimap-prod --remote --env prod --command \
  "SELECT license_key, plan, status, stripe_session_id, stripe_subscription_id, created_at
   FROM licenses WHERE stripe_session_id = 'cs_live_...'
      OR user_id IN (SELECT id FROM user WHERE email = 'customer@example.com')
   ORDER BY created_at DESC LIMIT 5"

# 5. Manual re-delivery from Stripe:
#    Dashboard → Developers → Events → find the checkout.session.completed / customer.subscription.created
#    → "Resend event". Our webhook is idempotent on event_id.

# 6. If event_id was already marked processed but no license exists (stuck state),
#    delete the idempotency row and resend:
wrangler d1 execute replimap-prod --remote --env prod --command \
  "DELETE FROM processed_events WHERE event_id = 'evt_...'"

# 7. Last resort — manual license creation (customer_id required):
wrangler d1 execute replimap-prod --remote --env prod --command \
  "INSERT INTO licenses (id, user_id, license_key, plan, plan_type, status,
                         stripe_subscription_id, stripe_price_id,
                         current_period_start, current_period_end,
                         created_at, updated_at)
   VALUES (lower(hex(randomblob(16))),
           (SELECT id FROM user WHERE email = 'customer@example.com'),
           'RM-XXXX-XXXX-XXXX-XXXX', 'pro', 'monthly', 'active',
           'sub_...', 'price_...',
           datetime('now'), datetime('now', '+30 days'),
           datetime('now'), datetime('now'))"
# Then email the license_key to the customer.
```

### Scenario 2 — Double payment (duplicate license)

Symptom: customer has two active licenses for the same plan, or their Stripe account shows two successful payments close together.

```bash
# 1. Find duplicates
wrangler d1 execute replimap-prod --remote --env prod --command \
  "SELECT l.id, l.license_key, l.plan, l.status, l.stripe_subscription_id,
          l.stripe_session_id, l.created_at
   FROM licenses l
   WHERE l.user_id = (SELECT id FROM user WHERE email = 'customer@example.com')
     AND l.status = 'active'
   ORDER BY l.created_at DESC"

# 2. Refund the duplicate charge in Stripe:
#    Dashboard → Payments → find the extra payment intent
#    → "Refund payment" (full refund)
#    This fires charge.refunded → our webhook revokes the lifetime license
#    automatically. For subscriptions, ALSO cancel the subscription:
#    Dashboard → Customers → find customer → Subscriptions → Cancel immediately

# 3. For subscription duplicates, revoke the newer (kept-in-error) license manually
#    if the cancel webhook hasn't fired yet:
wrangler d1 execute replimap-prod --remote --env prod --command \
  "UPDATE licenses
   SET status = 'revoked',
       revoked_at = datetime('now'),
       revoked_reason = 'Duplicate charge refunded: pi_...',
       updated_at = datetime('now')
   WHERE id = 'lic_duplicate_...'"

# 4. Deactivate any machines bound to the revoked license
wrangler d1 execute replimap-prod --remote --env prod --command \
  "UPDATE license_machines SET is_active = 0 WHERE license_id = 'lic_duplicate_...'"

# 5. Verify the customer retains exactly one active license
wrangler d1 execute replimap-prod --remote --env prod --command \
  "SELECT COUNT(*) FROM licenses
   WHERE user_id = (SELECT id FROM user WHERE email = 'customer@example.com')
     AND status = 'active'"
```

### Scenario 3 — Migration 011 fails on production D1

Symptom: `pnpm exec wrangler d1 migrations apply replimap-prod --remote --env prod` fails mid-transaction.

**Important:** Production D1 is already on the Drizzle schema (user/session/account/verification exist, licenses plan enum already v4). Migration 011 is designed to be a near no-op there. If it's failing, something is unexpected — **do not force**.

```bash
# 1. Check which migrations have been recorded
wrangler d1 migrations list replimap-prod --remote --env prod

# 2. Inspect actual prod schema before touching anything
wrangler d1 execute replimap-prod --remote --env prod --command \
  "SELECT type, name FROM sqlite_master
   WHERE name IN ('user','users','session','account','verification','licenses','license_machine_counts')
   ORDER BY type, name"

# 3. If migration 011 is already marked applied but the run errored,
#    remove its row so a fixed version can be re-applied:
wrangler d1 execute replimap-prod --remote --env prod --command \
  "DELETE FROM d1_migrations WHERE name = '011_drizzle_schema_bootstrap.sql'"

# 4. If a partial rebuild left licenses_new orphaned (mid-migration crash),
#    check whether rows exist and decide to keep or drop:
wrangler d1 execute replimap-prod --remote --env prod --command \
  "SELECT COUNT(*) FROM licenses_new"   # error = doesn't exist (clean)
wrangler d1 execute replimap-prod --remote --env prod --command \
  "DROP TABLE IF EXISTS licenses_new"   # only if confirmed empty / orphaned

# 5. If `license_machine_counts` view was dropped but not recreated:
wrangler d1 execute replimap-prod --remote --env prod --command \
  "CREATE VIEW IF NOT EXISTS license_machine_counts AS
   SELECT l.id AS license_id, l.license_key, l.plan, l.status,
          COUNT(CASE WHEN lm.is_active = 1 THEN 1 END) AS active_machines
   FROM licenses l
   LEFT JOIN license_machines lm ON l.id = lm.license_id
   GROUP BY l.id"

# 6. D1 supports time-travel restore (30-day retention). If everything is broken:
#    https://developers.cloudflare.com/d1/reference/time-travel/
#    wrangler d1 time-travel restore replimap-prod --timestamp '2026-04-19T00:00:00Z' --env prod
#    WARNING: this replaces the DB; coordinate with on-call.
```

## Common failures

| Symptom | Likely cause | Fix |
|---|---|---|
| `/checkout/success` sticks on "Creating your license…" forever | `stripe listen` not running, or webhook secret mismatch | Check `apps/api` logs for signature errors; restart harness |
| `/checkout` returns "Payment system not configured" | `STRIPE_SECRET_KEY` missing in wrangler | `wrangler secret put STRIPE_SECRET_KEY` or set in `.dev.vars` |
| Clerk sign-up rate-limited | Missing `CLERK_TESTING_TOKEN` | See `apps/web/e2e/README.md` |
| Dashboard shows "No License Found" after sign-up | API unreachable from SSR, or Clerk email missing | Check `apps/web` server logs; verify `NEXT_PUBLIC_API_URL` |
| `/v1/license/activate` returns 429 | Rate limiter triggered | Wait 60s or reset KV cache |
