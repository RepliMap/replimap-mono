# Commercial Payment Flow — End-to-End Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Wire the existing License API + Stripe Checkout + webhook machinery into a usable commercial flow: visitors can buy Pro/Team from the landing page, receive a license key within seconds of payment, and free-tier users get an auto-provisioned Community license on sign-up. One automated end-to-end test exercises the full happy path.

**Architecture:**
- Frontend (Next.js on Vercel) — landing CTAs route to `/checkout?plan=X&billing=Y` (Pro/Team) or `/sign-up` (Community). `/checkout/success?session_id=X` polls a new API endpoint for the just-created license and displays the key + activation instructions.
- API (Cloudflare Workers + D1) — already has `/v1/checkout/session`, `/v1/license/activate`, and `/v1/webhooks/stripe`. We add three small endpoints: `GET /v1/checkout/session/:id/license` (post-payment license lookup), `POST /v1/license/provision-community` (free-tier signup), and `GET /v1/users/by-email/:email/license` (dashboard linking).
- Email is NOT in scope for this iteration — license is delivered via the success page UI (and persisted on the dashboard). A follow-up can add Resend integration using the existing `handleResendKey` hook.

**Tech Stack:** Next.js 15 (App Router), Clerk (auth), Cloudflare Workers (Hono-free), D1 (SQLite via drizzle-orm), Stripe Checkout + Webhooks, Playwright (new, for e2e), Vitest (existing, for unit/integration).

---

## Current-State Audit (what's already done)

| Piece | Status | Location |
|---|---|---|
| `POST /v1/license/activate` | ✅ Complete | `apps/api/src/handlers/activate-license.ts` |
| `POST /v1/checkout/session` | ✅ Complete | `apps/api/src/handlers/billing.ts` |
| `POST /v1/billing/portal` | ✅ Complete | `apps/api/src/handlers/billing.ts` |
| `POST /v1/webhooks/stripe` | ✅ Complete (8 events) | `apps/api/src/handlers/stripe-webhook.ts` |
| Real Stripe price IDs | ✅ Wired | `apps/api/src/lib/constants.ts` |
| `.env.local` with test keys | ✅ Present | `apps/web/.env.local` |
| `/checkout` page | ✅ Complete | `apps/web/src/app/checkout/page.tsx` |
| `/checkout/success` page | ⚠️ Static ("License activating...") | `apps/web/src/app/checkout/success/page.tsx` |
| Clerk middleware on `/checkout(.*)` | ✅ | `apps/web/src/middleware.ts` |
| Unit tests (billing, webhook) | ✅ Vitest | `apps/api/tests/*.test.ts` |
| **Landing CTAs → checkout** | ❌ Still Tally form | `hero.tsx`, `pricing.tsx`, `header.tsx`, `call-to-action.tsx` |
| **Community auto-provision** | ❌ Missing | — |
| **License display on success page** | ❌ Missing | — |
| **Dashboard → license linkage** | ⚠️ Broken (Clerk user id vs email) | `apps/web/src/app/dashboard/page.tsx:23` + `apps/web/src/lib/api.ts:136` |
| **Playwright e2e** | ❌ Not installed | — |

---

## Design Decisions (the "why")

### 1. How do we link Clerk user → API user → license?
The API stores users by `(email, stripe_customer_id)`. Clerk stores users by `(clerk_user_id, email)`. **We use email as the join key.** This avoids a Clerk webhook dependency and works even if a user pays before signing up (Stripe creates user by email; sign-up later finds it).

### 2. How does the success page get the license key?
Options considered:
- A) Poll `GET /v1/me/license?email=X` — but user may have multiple licenses and we need the one from *this* session.
- B) Query by `session_id` from the URL — **chosen**. The webhook populates `licenses.stripe_session_id` for lifetime purchases; for subscriptions we'll also stamp it in `handleSubscriptionCreated` via the customer→session linkage (actually: `checkout.session.completed` stores the session_id on the user's stripe_customer_id; `subscription.created` can look up the session from customer). Simpler: **when the frontend hits the success page, look up license by customer email + latest `created_at`**, since the webhook races may take a few seconds.
- C) Hybrid — **final choice**: new endpoint `GET /v1/checkout/session/:session_id/license` that (a) looks up `getLicenseBySessionId` (lifetime path), falls back to (b) looking up the user by the session's customer_email and returning their most recent active license (subscription path). Idempotent, no PII leak (session_id acts as the auth token; the requester already has it from the Stripe redirect).

### 3. How do we handle webhook lag on the success page?
Poll with exponential backoff: 0ms → 1s → 2s → 4s → 8s (total ~15s, covers >99% of webhook delivery latency). Show "Creating your license…" state until resolved, then swap to the license key display. If still unresolved after 20s, show a "Check your email" fallback with manual refresh.

### 4. Community tier provisioning — when?
On first visit to `/dashboard`. Server-side render: `currentUser()` → email → `POST /v1/license/provision-community` (idempotent) → read it back. This avoids needing a Clerk webhook and works cleanly on sign-up redirect.

### 5. Email delivery of license key?
**Out of scope for this iteration.** The license is visible on `/checkout/success`, `/dashboard`, and `/dashboard/license`. The existing `handleResendKey` in `user.ts` already has the structure for adding Resend/SendGrid later. Adding email now requires: a secret, a sending domain, SPF/DKIM, and template management — all of which can wait.

### 6. E2E test — how much do we automate?
- **Fully automated**: free-tier sign-up → community license → activation API
- **Partially automated**: Stripe checkout flow. Playwright can fill the Stripe-hosted card form, but webhook delivery in local dev requires `stripe listen --forward-to localhost:8787`. We write a harness script (`scripts/e2e-commercial-flow.sh`) that starts `wrangler dev` + `next dev` + `stripe listen` as background processes, runs Playwright, and tears down.
- **Manual fallback**: Document the exact test card + URLs in `docs/testing/commercial-flow.md` for when the harness is flaky.

---

## Task Breakdown

### Phase 1 — API endpoints (30 min)

---

### Task 1: DB helper `getLicenseByUserEmailLatest`

**Files:**
- Modify: `apps/api/src/lib/db.ts` (add new helper near line 835)
- Test: `apps/api/tests/db.test.ts` (may not exist — if not, add to `helpers.ts` coverage later)

**Step 1: Skim existing helpers to match style**

Read `apps/api/src/lib/db.ts:820-870` for the `getLicenseBySessionId` pattern.

**Step 2: Add helper**

```typescript
// apps/api/src/lib/db.ts — near getLicenseBySessionId (~line 835)

export async function getLicenseByUserEmailLatest(
  db: DrizzleDb,
  email: string
): Promise<typeof schema.licenses.$inferSelect | null> {
  const normalizedEmail = email.toLowerCase();
  const row = await db.query.licenses.findFirst({
    where: (licenses, { inArray, eq, and }) =>
      and(
        inArray(
          licenses.userId,
          db.select({ id: schema.users.id })
            .from(schema.users)
            .where(eq(schema.users.email, normalizedEmail))
        ),
        eq(licenses.status, 'active')
      ),
    orderBy: (licenses, { desc }) => desc(licenses.createdAt),
  });
  return row ?? null;
}
```

**Step 3: Commit**

```bash
git add apps/api/src/lib/db.ts
git commit -m "feat(api): add getLicenseByUserEmailLatest helper"
```

---

### Task 2: New endpoint `GET /v1/checkout/session/:session_id/license`

**Files:**
- Create: `apps/api/src/handlers/checkout-license.ts`
- Modify: `apps/api/src/handlers/index.ts` (re-export)
- Modify: `apps/api/src/index.ts` (route handler)
- Test: `apps/api/tests/checkout-license.test.ts`

**Step 1: Write the failing test**

```typescript
// apps/api/tests/checkout-license.test.ts
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { handleGetCheckoutLicense } from '../src/handlers/checkout-license';
import { createMockEnv, createRequest, parseResponse } from './helpers';

const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('GET /v1/checkout/session/:id/license', () => {
  it('returns license_key when session has a lifetime license', async () => {
    // ...mock getLicenseBySessionId returns license with key RM-XXXX-...
    const env = createMockEnv();
    const request = createRequest('GET', '/v1/checkout/session/cs_test_123/license');
    const response = await handleGetCheckoutLicense(request, env, '127.0.0.1', 'cs_test_123');
    expect(response.status).toBe(200);
    const body = await parseResponse<{ license_key: string; plan: string }>(response);
    expect(body.license_key).toMatch(/^RM-/);
  });

  it('falls back to latest license by customer email when session_id not stamped on license', async () => {
    // Subscription path: webhook stores license via subscription.created, no session_id
    // We fetch the session from Stripe, get customer_email, look up user's latest license
    // ...mock Stripe /checkout/sessions/:id and getLicenseByUserEmailLatest
  });

  it('returns 404 when no license found within retry window', async () => {
    // ...no license, no user
  });

  it('returns 400 when session_id is malformed', async () => {
    const env = createMockEnv();
    const request = createRequest('GET', '/v1/checkout/session/invalid!id/license');
    const response = await handleGetCheckoutLicense(request, env, '127.0.0.1', 'invalid!id');
    expect(response.status).toBe(400);
  });
});
```

**Step 2: Run test to verify it fails**

```bash
cd apps/api && pnpm test -- checkout-license
```
Expected: FAIL (handler does not exist).

**Step 3: Implement the handler**

```typescript
// apps/api/src/handlers/checkout-license.ts
import type { Env } from '../types/env';
import { Errors, AppError } from '../lib/errors';
import { rateLimit } from '../lib/rate-limiter';
import { createDb, getLicenseBySessionId, getLicenseByUserEmailLatest } from '../lib/db';

const SESSION_ID_PATTERN = /^cs_(test|live)_[A-Za-z0-9]+$/;

export async function handleGetCheckoutLicense(
  request: Request,
  env: Env,
  clientIP: string,
  sessionId: string
): Promise<Response> {
  const rateLimitHeaders = await rateLimit(env.CACHE, 'validate', clientIP);
  try {
    if (!SESSION_ID_PATTERN.test(sessionId)) {
      throw Errors.invalidRequest('Invalid session_id format');
    }
    const db = createDb(env.DB);

    // Path A: lifetime purchase — license stamped with session_id
    let license = await getLicenseBySessionId(db, sessionId);

    // Path B: subscription — license has subscription_id, not session_id.
    // Fetch session from Stripe to get customer_email, then find latest license.
    if (!license && env.STRIPE_SECRET_KEY) {
      const stripeRes = await fetch(`https://api.stripe.com/v1/checkout/sessions/${sessionId}`, {
        headers: { Authorization: `Bearer ${env.STRIPE_SECRET_KEY}` },
      });
      if (stripeRes.ok) {
        const session = await stripeRes.json() as { customer_email?: string; customer_details?: { email?: string } };
        const email = session.customer_email ?? session.customer_details?.email;
        if (email) {
          license = await getLicenseByUserEmailLatest(db, email);
        }
      }
    }

    if (!license) {
      return new Response(
        JSON.stringify({ error: 'NOT_READY', message: 'License is still being created. Please retry in a moment.' }),
        { status: 404, headers: { 'Content-Type': 'application/json', ...rateLimitHeaders } }
      );
    }

    return new Response(
      JSON.stringify({
        license_key: license.licenseKey,
        plan: license.plan,
        status: license.status,
        plan_type: license.planType,
      }),
      { status: 200, headers: { 'Content-Type': 'application/json', ...rateLimitHeaders } }
    );
  } catch (error) {
    if (error instanceof AppError) {
      return new Response(JSON.stringify(error.toResponse()), {
        status: error.statusCode,
        headers: { 'Content-Type': 'application/json', ...rateLimitHeaders },
      });
    }
    throw error;
  }
}
```

**Step 4: Wire the route**

```typescript
// apps/api/src/index.ts — in the router (~line 210)

const sessionLicenseMatch = path.match(/^\/v1\/checkout\/session\/([^/]+)\/license$/);
if (sessionLicenseMatch && method === 'GET') {
  response = await handleGetCheckoutLicense(request, env, clientIP, sessionLicenseMatch[1]);
}
```

And export from `apps/api/src/handlers/index.ts`.

**Step 5: Run tests**

```bash
cd apps/api && pnpm test -- checkout-license
```
Expected: PASS.

**Step 6: Commit**

```bash
git add apps/api/src/handlers/checkout-license.ts apps/api/src/handlers/index.ts apps/api/src/index.ts apps/api/tests/checkout-license.test.ts
git commit -m "feat(api): add GET /v1/checkout/session/:id/license for post-payment lookup"
```

---

### Task 3: New endpoint `POST /v1/license/provision-community`

**Files:**
- Create: `apps/api/src/handlers/provision-community.ts`
- Modify: `apps/api/src/handlers/index.ts` + `apps/api/src/index.ts`
- Test: `apps/api/tests/provision-community.test.ts`

**Step 1: Test first** (RED)

```typescript
describe('POST /v1/license/provision-community', () => {
  it('creates a new community license when user has none', async () => {
    // Request: { email: 'new@x.com' }
    // Expected: 200, returns license_key, plan: 'community', status: 'active'
  });

  it('is idempotent — returns existing active community license', async () => {
    // Pre-seed a community license; re-call; expect SAME license_key
  });

  it('never overwrites a paid license', async () => {
    // User has active 'pro' license; call provision; expect 200 with the existing pro license or a no-op flag
  });

  it('rejects malformed email', async () => { /* 400 */ });
  it('rate-limits aggressive callers', async () => { /* 429 */ });
});
```

**Step 2: Implement**

```typescript
// apps/api/src/handlers/provision-community.ts
import type { Env } from '../types/env';
import { Errors, AppError } from '../lib/errors';
import { rateLimit } from '../lib/rate-limiter';
import { generateLicenseKey, nowISO } from '../lib/license';
import { createDb, findOrCreateUser, createLicense, getLicenseByUserEmailLatest } from '../lib/db';
import { LIFETIME_EXPIRY } from '../lib/constants';

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export async function handleProvisionCommunity(
  request: Request,
  env: Env,
  clientIP: string
): Promise<Response> {
  const rateLimitHeaders = await rateLimit(env.CACHE, 'activate', clientIP);
  try {
    const body = await request.json() as { email?: string };
    if (!body.email || !EMAIL_RE.test(body.email)) {
      throw Errors.invalidRequest('Invalid email');
    }
    const email = body.email.toLowerCase();
    const db = createDb(env.DB);

    // Idempotency: return existing active license (community OR paid — don't overwrite)
    const existing = await getLicenseByUserEmailLatest(db, email);
    if (existing) {
      return new Response(
        JSON.stringify({
          license_key: existing.licenseKey,
          plan: existing.plan,
          status: existing.status,
          created: false,
        }),
        { status: 200, headers: { 'Content-Type': 'application/json', ...rateLimitHeaders } }
      );
    }

    // Create user + community license
    const user = await findOrCreateUser(db, email, null);
    const licenseKey = generateLicenseKey();
    await createLicense(db, {
      userId: user.id,
      licenseKey,
      plan: 'community',
      planType: 'free',
      currentPeriodStart: nowISO(),
      currentPeriodEnd: LIFETIME_EXPIRY,
    });

    return new Response(
      JSON.stringify({ license_key: licenseKey, plan: 'community', status: 'active', created: true }),
      { status: 201, headers: { 'Content-Type': 'application/json', ...rateLimitHeaders } }
    );
  } catch (error) {
    if (error instanceof AppError) {
      return new Response(JSON.stringify(error.toResponse()), {
        status: error.statusCode,
        headers: { 'Content-Type': 'application/json', ...rateLimitHeaders },
      });
    }
    throw error;
  }
}
```

Note: `findOrCreateUser` currently expects `(db, email, stripeCustomerId)`. Verify it accepts `null` for customer_id; if not, adjust signature or add an overload.

**Step 3-5: Wire route, run tests (GREEN), commit.**

```bash
git commit -m "feat(api): add POST /v1/license/provision-community for free-tier auto-signup"
```

---

### Phase 2 — Frontend: wire up the actual Buy flow (45 min)

---

### Task 4: Add `getCheckoutLicense` + `provisionCommunityLicense` to web api client

**Files:**
- Modify: `apps/web/src/lib/api.ts`

**Step 1: Add the two functions**

```typescript
// apps/web/src/lib/api.ts — append to the Checkout/Billing section

interface CheckoutLicenseResponse {
  license_key: string;
  plan: string;
  status: string;
  plan_type?: string;
}

export async function getCheckoutLicense(sessionId: string): Promise<CheckoutLicenseResponse> {
  return request<CheckoutLicenseResponse>(`/v1/checkout/session/${encodeURIComponent(sessionId)}/license`, {
    method: 'GET',
    cache: 'no-store',
  });
}

interface ProvisionCommunityResponse {
  license_key: string;
  plan: string;
  status: string;
  created: boolean;
}

export async function provisionCommunityLicense(email: string): Promise<ProvisionCommunityResponse> {
  return request<ProvisionCommunityResponse>('/v1/license/provision-community', {
    method: 'POST',
    body: JSON.stringify({ email }),
  });
}
```

**Step 2: Commit**

```bash
git add apps/web/src/lib/api.ts
git commit -m "feat(web): add getCheckoutLicense + provisionCommunityLicense API client fns"
```

---

### Task 5: `/checkout/success` — poll for license, display key

**Files:**
- Modify: `apps/web/src/app/checkout/success/page.tsx`

**Step 1: Replace the static success page with a polling-aware client component**

Key changes:
- Read `session_id` from URL `?session_id=cs_test_…`.
- Poll `getCheckoutLicense(sessionId)` with backoff [0, 1s, 2s, 4s, 8s], stop on 200 or after ~15s.
- When resolved, render a prominent "Your license key" block with copy-to-clipboard.
- While polling, keep the "License activating…" badge but with a spinner.
- If timed out, show: "Your payment was received but your license is still being created. Refresh this page or check your email in a minute." + refresh button.

```typescript
// apps/web/src/app/checkout/success/page.tsx (sketch — full code in implementation)
'use client';
import { useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { getCheckoutLicense } from '@/lib/api';

const BACKOFF_MS = [0, 1000, 2000, 4000, 8000, 8000]; // ~23s total

export default function CheckoutSuccessPage() {
  const sessionId = useSearchParams().get('session_id');
  const [license, setLicense] = useState<{ license_key: string; plan: string } | null>(null);
  const [state, setState] = useState<'pending' | 'ready' | 'timeout' | 'no-session'>('pending');
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!sessionId) { setState('no-session'); return; }
    let cancelled = false;
    (async () => {
      for (const delay of BACKOFF_MS) {
        if (cancelled) return;
        if (delay > 0) await new Promise(r => setTimeout(r, delay));
        try {
          const l = await getCheckoutLicense(sessionId);
          if (!cancelled) { setLicense(l); setState('ready'); return; }
        } catch { /* keep polling */ }
      }
      if (!cancelled) setState('timeout');
    })();
    return () => { cancelled = true; };
  }, [sessionId]);

  // ...render three states: pending (spinner + "License activating…"), ready (show key + 3-step onboarding), timeout (refresh prompt)
}
```

**Step 2: Keep the existing 3-step quickstart section for the `ready` state, but insert the license-key reveal block above step 1. Add copy button.**

**Step 3: Manually verify UI states in browser (pending/ready/timeout).**

**Step 4: Commit**

```bash
git commit -m "feat(web): poll for and display license key on checkout success page"
```

---

### Task 6: Dashboard — link Clerk user to license via email

**Files:**
- Modify: `apps/web/src/lib/api.ts` (replace `getUserLicenseKey` to use email, or add `getOrProvisionCommunity`)
- Modify: `apps/web/src/app/dashboard/page.tsx`
- Modify: `apps/web/src/app/dashboard/license/page.tsx`

**Step 1: Replace Clerk-user-id lookup with email-based provisioning**

```typescript
// apps/web/src/lib/api.ts — replace getUserLicenseKey
export async function getOrProvisionLicenseKey(email: string): Promise<string | null> {
  try {
    const result = await provisionCommunityLicense(email);
    return result.license_key;
  } catch (err) {
    if (err instanceof ApiError) return null;
    throw err;
  }
}
```

Mark old `getUserLicenseKey` as deprecated or remove if no other callers (grep first).

**Step 2: Dashboard uses email**

```typescript
// apps/web/src/app/dashboard/page.tsx
const email = user.emailAddresses[0]?.emailAddress;
const licenseKey = email ? await getOrProvisionLicenseKey(email) : null;
```

**Step 3: Verify dashboard renders correctly for a fresh user (no license) + paying user.**

**Step 4: Commit**

```bash
git commit -m "fix(web): link Clerk user to license via email, auto-provision community"
```

---

### Phase 3 — Landing page: switch CTAs to Buy / Sign-up (30 min)

---

### Task 7: Create shared `ctaLinks.ts` helper

**Files:**
- Create: `apps/web/src/lib/cta-links.ts`

**Step 1: Write the helper**

```typescript
// apps/web/src/lib/cta-links.ts
import type { PlanName, BillingPeriod } from './pricing';

export function checkoutHref(plan: Exclude<PlanName, 'community' | 'sovereign'>, billing: BillingPeriod = 'monthly'): string {
  return `/checkout?plan=${plan}&billing=${billing}`;
}

export function freeSignupHref(source: string): string {
  return `/sign-up?redirect_url=/dashboard&source=${encodeURIComponent(source)}`;
}

export const SOVEREIGN_CONTACT = 'mailto:david@replimap.com?subject=RepliMap Sovereign Inquiry';
```

**Step 2: Commit**

---

### Task 8: Update `hero.tsx` — primary CTA → `/sign-up`, add secondary "See Pricing"

**Files:** `apps/web/src/components/hero.tsx`

**Change:**
```tsx
// BEFORE
<a href={`${TALLY_FORM_URL}?source=hero`}>
  <Button>Get Started Free</Button>
</a>

// AFTER
<Button asChild className="...">
  <Link href={freeSignupHref('hero')}>Get Started Free <ArrowRight /></Link>
</Button>
```
Keep the "View on GitHub" button unchanged.

**Commit.**

---

### Task 9: Update `pricing.tsx` — route Pro/Team CTAs to `/checkout`, Community to `/sign-up`

**Files:** `apps/web/src/components/pricing.tsx`

**Change the CTA block (lines ~125-149) to route by plan key + billingPeriod:**

```tsx
const href = plan.key === 'community'
  ? freeSignupHref('pricing_community')
  : checkoutHref(plan.key as 'pro' | 'team', billingPeriod);

const isLifetimeUnavailable = billingPeriod === 'lifetime' && !plan.hasLifetime;
// Render disabled button if lifetime unavailable, else Link to href
```

Also handle lifetime → `checkoutHref(plan.key, 'lifetime')` — but API currently only supports monthly/annual in `handleCreateCheckout`. **Sub-task 9a: extend `handleCreateCheckout` to accept `billing_period: 'lifetime'` and select from `STRIPE_LIFETIME_PRICE_TO_PLAN`. Update unit test.**

**Commit the UI change + API extension as two separate commits.**

---

### Task 10: Update `header.tsx` + `call-to-action.tsx`

**Files:**
- `apps/web/src/components/header.tsx` (nav "Get Started" CTA + mobile menu)
- `apps/web/src/components/call-to-action.tsx` (bottom-of-page CTA)

Replace `TALLY_FORM_URL` usages with `freeSignupHref('nav' | 'nav_mobile' | 'footer_cta')`.

Leave `TALLY_FORM_URL` itself in `waitlist-modal.tsx` (if it's still used elsewhere for Sovereign contact — verify with grep; otherwise delete).

**Commit.**

---

### Phase 4 — Automated end-to-end test (60-90 min)

---

### Task 11: Install Playwright in `apps/web`

**Step 1:**
```bash
cd apps/web && pnpm add -D @playwright/test && pnpm exec playwright install chromium
```

**Step 2: Create `apps/web/playwright.config.ts`**
```typescript
import { defineConfig, devices } from '@playwright/test';
export default defineConfig({
  testDir: './e2e',
  timeout: 60_000,
  retries: 0,
  reporter: [['list']],
  use: { baseURL: 'http://localhost:3000', trace: 'on-first-retry' },
  projects: [{ name: 'chromium', use: devices['Desktop Chrome'] }],
  webServer: { command: 'pnpm dev', url: 'http://localhost:3000', reuseExistingServer: true },
});
```

**Step 3:** Add script to `package.json`: `"e2e": "playwright test"`.

**Commit.**

---

### Task 12: E2E test — community signup flow (fully automated)

**File:** `apps/web/e2e/community-signup.spec.ts`

**Flow:**
1. Visit `/`.
2. Click "Get Started Free" in hero.
3. Land on Clerk `/sign-up`. Fill email with `e2e+{timestamp}@replimap-test.dev` + password.
4. Submit → Clerk dev mode may auto-verify. If OTP required, read from Clerk test dashboard or use Clerk's testing mode helpers (see https://clerk.com/docs/testing/playwright).
5. Land on `/dashboard`. Expect license card with `plan: community`, a license key matching `/^RM-/`.
6. Hit `/v1/license/activate` directly with the key + a fake fingerprint (32-char hex); expect 200 + `license_blob`.

**Note:** Clerk testing requires env-var configuration. Document in `apps/web/e2e/README.md`.

**Commit.**

---

### Task 13: E2E test — Pro checkout flow (semi-automated, requires `stripe listen`)

**File:** `apps/web/e2e/pro-checkout.spec.ts`

**Prereq:** Stripe CLI installed (`stripe listen --forward-to localhost:8787/v1/webhooks/stripe --events checkout.session.completed,customer.subscription.created,invoice.paid`).

**Flow:**
1. Sign in as a pre-created test user (fixture).
2. Navigate `/checkout?plan=pro&billing=monthly`.
3. Click "Continue to Payment".
4. On Stripe-hosted page: fill `4242 4242 4242 4242`, future expiry, any CVC, any ZIP.
5. Stripe redirects back to `/checkout/success?session_id=cs_test_…`.
6. Wait for license-key reveal (up to 15s polling).
7. Assert license key visible, matches `/^RM-/`, plan = "Pro".
8. Copy key, call `/v1/license/activate` with it — expect 200.

**Commit.**

---

### Task 14: Harness script `scripts/e2e-commercial-flow.sh`

**File:** `scripts/e2e-commercial-flow.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

# Start wrangler dev (API) in background
(cd apps/api && pnpm dev --port 8787 --local) &
API_PID=$!

# Start stripe listen in background
stripe listen --forward-to localhost:8787/v1/webhooks/stripe \
  --events checkout.session.completed,customer.subscription.created,customer.subscription.updated,invoice.paid,invoice.payment_failed,charge.refunded &
STRIPE_PID=$!

# Run Playwright (webServer in config starts next dev)
(cd apps/web && pnpm e2e) || EXIT=$?

# Cleanup
kill $API_PID $STRIPE_PID 2>/dev/null || true
wait 2>/dev/null || true
exit ${EXIT:-0}
```

**Step:** `chmod +x scripts/e2e-commercial-flow.sh` + commit.

---

### Task 15: Manual smoke test + docs

**File:** `docs/testing/commercial-flow.md`

Document:
- Prereqs (Stripe CLI, Playwright, Clerk test env)
- How to run `./scripts/e2e-commercial-flow.sh`
- How to manually test each flow with test card numbers
- How to inspect D1 state after a test run (`wrangler d1 execute replimap-db --local --command "SELECT * FROM licenses ORDER BY created_at DESC LIMIT 5"`)
- How to reset test data

**Commit.**

---

## Acceptance Criteria

- [ ] Landing hero "Get Started Free" routes to `/sign-up`, not Tally.
- [ ] Pricing card "Start Pro Trial" routes to `/checkout?plan=pro&billing=monthly`.
- [ ] Pricing card "Start Team Trial" routes to `/checkout?plan=team&billing=monthly`.
- [ ] Lifetime toggle on pricing routes to `/checkout?plan=X&billing=lifetime`.
- [ ] Community tile on pricing routes to `/sign-up`.
- [ ] Header + bottom CTA updated to sign-up.
- [ ] `/sign-up` → `/dashboard` shows community license within 2 seconds of first visit.
- [ ] `/checkout` → Stripe → `/checkout/success?session_id=X` shows the license key within 15 seconds of payment.
- [ ] License key from success page works against `/v1/license/activate`.
- [ ] `apps/api/tests` green — including new tests for `checkout-license`, `provision-community`.
- [ ] `apps/web/e2e/community-signup.spec.ts` passes with only `pnpm dev` running.
- [ ] `./scripts/e2e-commercial-flow.sh` runs the full Pro checkout flow end-to-end.

---

## Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Stripe webhook delay exceeds 15s polling window | Increase backoff to 30s; show a "refresh" button as escape hatch. |
| Clerk test-mode email verification blocks e2e | Use Clerk's `testingToken` pattern documented in their Playwright guide. |
| D1 test isolation — parallel e2e runs collide | Each test uses unique email (`e2e+{uuid}@…`); D1 writes idempotent via `findOrCreateUser`. |
| `findOrCreateUser` may not accept null `customer_id` | Task 3 explicitly verifies this; adjust signature if needed. |
| Sovereign plan still has placeholder price IDs in `PLAN_TO_STRIPE_PRICE` | Out of scope — Sovereign stays on "Request Demo" mailto; no checkout button. |
| Email delivery of license key not implemented | Documented as follow-up; success page + dashboard cover the MVP need. |

---

## Out of Scope (explicit non-goals)

- Email delivery via Resend / SendGrid (documented as follow-up — wire into `handleResendKey`).
- Sovereign plan self-serve checkout (requires Stripe products + enterprise contract flow).
- Subscription upgrade/downgrade UI (Stripe Customer Portal handles this).
- Clerk webhook integration for user lifecycle (email-based linking is sufficient).
