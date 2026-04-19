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

## Common failures

| Symptom | Likely cause | Fix |
|---|---|---|
| `/checkout/success` sticks on "Creating your license…" forever | `stripe listen` not running, or webhook secret mismatch | Check `apps/api` logs for signature errors; restart harness |
| `/checkout` returns "Payment system not configured" | `STRIPE_SECRET_KEY` missing in wrangler | `wrangler secret put STRIPE_SECRET_KEY` or set in `.dev.vars` |
| Clerk sign-up rate-limited | Missing `CLERK_TESTING_TOKEN` | See `apps/web/e2e/README.md` |
| Dashboard shows "No License Found" after sign-up | API unreachable from SSR, or Clerk email missing | Check `apps/web` server logs; verify `NEXT_PUBLIC_API_URL` |
| `/v1/license/activate` returns 429 | Rate limiter triggered | Wait 60s or reset KV cache |
