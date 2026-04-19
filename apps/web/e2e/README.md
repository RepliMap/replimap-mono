# RepliMap Web — E2E Tests

Playwright-driven browser tests for the commercial payment flow.

## Layout

```
e2e/
├── README.md                       ← you are here
├── community-signup.spec.ts        ← free-tier signup + community license
├── pro-checkout.spec.ts            ← paid-tier Stripe checkout + license
└── fixtures/
    └── test-user.ts                ← Clerk sign-in/sign-up helpers
```

## Running

**Community signup only** (fully automated, no external services required beyond Clerk test mode):

```bash
cd apps/web
pnpm e2e community-signup
```

**Full flow** (requires Stripe CLI + wrangler + Clerk testing token):

```bash
# From the repo root:
./scripts/e2e-commercial-flow.sh
```

## Prerequisites

### 1. Clerk test mode

Tests use [`@clerk/testing`](https://clerk.com/docs/testing/playwright/overview)
to bypass Clerk's bot protection automatically. Two env vars are required
in `apps/web/.env.local` (same as normal dev):

- `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`
- `CLERK_SECRET_KEY`

Email verification is skipped because the test fixture uses `+clerk_test`
email addresses (e.g. `e2e+clerk_test+abc123@replimap-test.dev`). Clerk
recognises this suffix and uses a **fixed OTP of `424242`** instead of
sending a real email — see https://clerk.com/docs/testing/test-emails.

No extra token setup is needed.

### 2. Stripe CLI (for pro-checkout.spec.ts only)

```bash
# macOS
brew install stripe/stripe-cli/stripe

# Linux — see https://stripe.com/docs/stripe-cli
```

Then authenticate once:

```bash
stripe login
```

### 3. Local API (for pro-checkout.spec.ts only)

The Stripe webhook needs a listener. `scripts/e2e-commercial-flow.sh`
handles this automatically. To run manually:

```bash
# Terminal 1 — API
cd apps/api && pnpm dev

# Terminal 2 — Stripe webhook forwarder
stripe listen --forward-to localhost:8787/v1/webhooks/stripe \
  --events checkout.session.completed,customer.subscription.created,invoice.paid

# Terminal 3 — web + tests
cd apps/web && pnpm e2e pro-checkout
```

## Debugging

```bash
# Run with headed browser (watch what's happening)
pnpm e2e --headed

# Step through in UI mode
pnpm e2e:ui

# Show the HTML report after a run
pnpm exec playwright show-report
```

## Data isolation

Each test uses a unique email (`e2e+{uuid}@replimap-test.dev`). The API's
`findOrCreateUser` is idempotent, so re-runs never collide — they just
reuse the per-test user.

To reset the D1 data (local):

```bash
cd apps/api
wrangler d1 execute replimap-db --local --command \
  "DELETE FROM licenses WHERE user_id IN (SELECT id FROM user WHERE email LIKE 'e2e+%@replimap-test.dev'); \
   DELETE FROM user WHERE email LIKE 'e2e+%@replimap-test.dev';"
```
