# Commercial Flow — Follow-ups

Items deliberately scoped out of the 2026-04-19 commercial-flow work but worth tracking.

## 1. Email delivery of license key

**Status:** Not implemented. License is surfaced only via `/checkout/success` (polling) and `/dashboard`.

**Why deferred:** Wiring an email provider needs a verified sending domain, SPF/DKIM setup, template management, and a secret. The success page + dashboard cover the MVP need.

**How to do it:**
- Pick provider (Resend is the lightest — one HTTP call, free tier 3k/mo).
- Store `RESEND_API_KEY` in `wrangler secret put`.
- Wire into the existing hook at `apps/api/src/handlers/user.ts::handleResendKey` (already scaffolded with a TODO).
- Also call on `checkout.session.completed` / `customer.subscription.created` success paths in `stripe-webhook.ts` so new purchases get an email receipt with the key.
- Add an e2e check: subscribe, poll an inbox webhook (e.g. maildev or Resend's own webhook), assert the key appeared.

**Estimate:** ~2h including template + test.

---

## 2. Team tier e2e spec

**Status:** No dedicated spec. Team shares Pro's subscription code path.

**Why deferred:** The checkout, webhook, and activate code paths for Team are identical to Pro — only the price ID and machine-limit differ. The `billing.test.ts` unit tests cover the price-ID mapping.

**Trigger to implement:** If Team ever grows behaviour that diverges from Pro (e.g. seat-based billing, invoicing, team admin UI), clone `pro-checkout.spec.ts` to `team-checkout.spec.ts` and assert on team-specific fields.

**Estimate:** ~30min (mostly copy-paste).

---

## 3. Webhook idempotency stress test

**Status (updated 2026-07-04):** Idempotency is now genuinely covered by
`apps/api/tests/stripe-webhook.test.ts` against the real `handleStripeWebhook`
handler and a real (Miniflare D1) database: sequential redelivery of the same
`evt_` id, 5× concurrent redelivery of the same event, and redelivery of the
same subscription/session under *different* event ids (relies on
`UNIQUE(stripe_subscription_id)` and the `UNIQUE(stripe_session_id)` index
restored by migration 012). Historical note: before 2026-07-04 this section
claimed unit-test coverage that did not exist — the old stripe-webhook.test.ts
never invoked the handler.

Still NOT covered: high-volume stress (50+ concurrent), event-ordering
permutations (`subscription.created` before `checkout.session.completed`,
interleaved `invoice.paid`), and redelivery through a real `wrangler dev`
HTTP stack rather than direct handler invocation.

**Why it matters:** Production Stripe retries events aggressively (up to 3 days with exponential backoff). Local `stripe listen` delivers each event exactly once — fundamentally different behaviour. A bug that surfaces only under retries won't be caught by current tests.

**How to do it:**
- Write a script that resends the same `evt_...` to `/v1/webhooks/stripe` N times concurrently (e.g. 50).
- Assert: exactly one license row created, exactly one `processed_events` row, no 5xx responses.
- Also test event ordering permutations: `subscription.created` → `checkout.session.completed`, reversed, interleaved with `invoice.paid`.
- Could live in `apps/api/tests/webhook-stress.test.ts` using miniflare, or as a shell script that hits a local wrangler instance.

**Estimate:** ~3h. Schedule before the first real paying customers at volume (>100 subs/day).

---

## 4. Verify `RATE_LIMIT_DISABLED` is NOT set in production

**Status: ✅ VERIFIED + CI-GUARDED (2026-07-09).** `wrangler secret list --env prod` has no such entry; `apps/api/wrangler.toml` contains no occurrence; CI (`.github/workflows/ci.yml`) now greps `wrangler.toml` and fails the build on any occurrence. The `DEV_BYPASS_RATE_LIMIT` rename suggestion was not taken — the CI guard covers the same risk without touching existing dev/test references.

**Original note:** Flag added for local e2e only (`apps/api/src/lib/rate-limiter.ts`). Production deploy must not carry it.

**How to verify:**
```bash
# Check prod secrets — RATE_LIMIT_DISABLED should not appear
wrangler secret list --env prod

# Check prod vars in wrangler.toml — the [env.prod] section should not reference it
grep -n "RATE_LIMIT_DISABLED" apps/api/wrangler.toml
```

Add a CI guard that fails the build if `RATE_LIMIT_DISABLED` appears in `wrangler.toml` outside a clearly-marked dev section, or in any deploy manifest targeting prod.

**Also:** consider renaming to `DEV_BYPASS_RATE_LIMIT` so the name itself is a tripwire — a production reviewer seeing that name would immediately question it.

**Estimate:** ~20min (verify + add CI check).

---

## 5. First-cycle period backfill can be lost to event ordering

**Status (2026-07-05): FIXED** — see `INVOICE_ORDERING_BACKFILL_FIX_LOG.md`
for the full reproduction, root-cause analysis, and dev validation evidence.

Originally observed live on dev during E2E validation Item 3 and again on both
real production purchases (2026-07-04): Stripe delivered `invoice.paid`
*before* `customer.subscription.created`; the license didn't exist yet, so
`handleInvoicePaid` no-op'd but still marked the event processed —
permanently losing the first cycle's period backfill (`current_period_end`
stuck at null).

**Fix shipped (both proposed directions, B primary + A safety net):**
- **B (primary, zero API calls):** root cause turned out to be an API-version
  field move — on ≥2025-03-31 (basil/clover) the billing period lives on
  `subscription.items.data[].current_period_*`, not the subscription top
  level, so the period was *in the event all along* and the code never read
  it. `getSubscriptionPeriod()` now reads top-level with an items fallback;
  `handleSubscriptionCreated` and `handleSubscriptionUpdated` both use it.
  The first cycle's period is now self-contained in the subscription event —
  no dependence on `invoice.paid` ordering or Stripe retry timing at all.
- **A (safety net):** `handleInvoicePaid` no longer consumes the event when
  the license doesn't exist yet — it returns 500 *without* marking the event
  processed (mirrors the existing subscription.created retry path), so
  Stripe's redelivery processes it for real. Scoped strictly to
  subscription-bearing invoices; non-subscription invoices still ack 200.
  Chosen as backup, not primary, because Stripe's retry timing is
  undisclosed (live: ≤3 days exponential backoff; sandbox: only 3 retries).

**Dev validation (2026-07-04, real sandbox events):** the race reproduced
naturally on the first attempt (`invoice.paid` 110ms ahead) — invoice.paid
500'd unmarked, subscription.created created the license with the real
period from items (`current_period_end` correctly set, not null), and
Stripe's retry ~15s later processed invoice.paid for real. Covered by 5
ordering-permutation tests in `tests/stripe-webhook.test.ts`.

---

## 6. Dashboard license detail: device list always shows 0

**Status (2026-07-05): FIXED & DEPLOYED TO PROD** (together with §7 — API
worker version `90bfc4ca`, web via Vercel; `features.offline_grace_days`
verified live on prod with a real license key). `/v1/me/machines` now
returns the full `machine_id` plus the
migration-010 fingerprint metadata (`fingerprint_type`/`ci_provider`/
`ci_repo`/`container_type`); the dashboard loads devices browser-side via a
new `useMachines` hook and renders them through `machinesToFingerprints()`.
The Remove button's request body was also fixed (`machine_id`, not
`machine_fingerprint` — the deactivate endpoint never accepted the latter).
Device caps are now server-issued everywhere (`limit` from /v1/me/machines,
`usage.machines_limit` from /v1/me/license); the web-side `getMachinesLimit`
plan map was deleted. Owner-scoping (license-key possession) was audited and
pinned by regression tests: a key can only ever list/deactivate its own
license's machines (`tests/me-endpoints.test.ts`).

<details><summary>Original report (2026-07-05, pre-fix)</summary>

**Status (2026-07-05):** Open. Surfaced right after the dashboard was moved to
client-side fetching (commit `e6bd1c9`) and the `.fingerprints` crash was fixed
(`7b829cd`). The `/dashboard/license` page now renders without crashing but the
"Active Devices" count and the device list are always empty/0.

**Root cause:** `GET /v1/me/license` (Worker `handleGetOwnLicense`) does **not**
return a `fingerprints` array — it returns `features` / `usage` / `subscription`
/ `created_at`. The device list lives in a **separate** endpoint,
`GET /v1/me/machines` (Worker `handleGetOwnMachines`, already implemented). The
frontend `LicenseDetails` type used to (incorrectly) declare `fingerprints` as
required; `7b829cd` made it optional and centralized a `?? []` fallback in
`apps/web/src/lib/license-view.ts`, so a missing array reads as 0 instead of
crashing. That is correct crash-handling but the real device list is still never
fetched.

**How to fix:**
- In the client license flow (`apps/web/src/hooks/useLicense.ts` or the detail
  page), additionally call `GET /v1/me/machines?license_key=...` and feed the
  returned machines into `DeviceList` / `activeDeviceCount`.
- `usage.machines_active` from `/v1/me/license` gives the *count* already, so at
  minimum the "Active Devices" number can be sourced from there without a second
  request; the full list still needs `/v1/me/machines`.
- Note these calls are now browser-side (see item context), so they must stay
  off Vercel SSR to avoid Cloudflare Bot Fight Mode (same reason as `e6bd1c9`).

**Estimate:** ~1–1.5h (fetch + wire into DeviceList + a hook test).

</details>

---

## 7. Dashboard license detail: "undefined Days Grace" / "Expires: Never"

**Status (2026-07-05): FIXED & DEPLOYED TO PROD** (together with §6 — API
worker version `90bfc4ca`, web via Vercel). Resolution per confirmed
decisions:
- `offline_grace_days` is now **server-issued**: added additively as
  `features.offline_grace_days` on `/v1/me/license`, sourced from the
  authoritative per-plan `OFFLINE_GRACE_DAYS` map (features.ts: 0/7/14/365),
  failing closed to 0 for unknown plans. The frontend reads it via
  `graceDays()` and never derives entitlements from the plan name.
- Expiry display is **status-dependent** (frontend `expiresAt()` helper):
  active → "Never"; canceled/past_due → the paid-through date from
  `subscription.current_period_end`.
- The frontend `LicenseDetails` type was realigned to the real response shape
  (nested `features`/`usage`/`subscription`) with a keep-in-sync note against
  `GetLicenseResponse`.

<details><summary>Original report (2026-07-05, pre-fix)</summary>

**Status (2026-07-05):** Open. Same `/v1/me/license` ↔ `LicenseDetails` contract
drift as item 6, but non-crashing (cosmetic).

**Root cause:** `LicenseDetails` declares `offline_grace_days` and `expires_at`,
but `/v1/me/license` returns neither. At runtime `offline_grace_days` is
`undefined` → `GracePeriodInfo` renders "undefined Days Grace"; `expires_at` is
`undefined` → `LicenseCard` shows "Never" for every license.

**How to fix (choose one):**
- **Frontend mapping:** derive these from fields the endpoint *does* return —
  `subscription.current_period_end` for the expiry, and `offline_grace_days`
  from the plan (there's a `GRACE_PERIOD_DAYS` / per-plan notion in
  `apps/api/src/lib/constants.ts`; expose it via `features` or map client-side).
- **Backend:** add `offline_grace_days` and `expires_at` directly to the
  `/v1/me/license` response so the frontend type finally matches reality
  (preferred — kills the drift at the source; update `GetLicenseResponse` in
  `apps/api/src/handlers/user.ts` and the frontend `LicenseDetails` together).

**Estimate:** ~1h (backend option, incl. keeping the two types in sync).

</details>

---

## 8. `/v1/me/*` passes the license key as a URL query parameter (secrets-in-URL)

**Type:** Security hardening — a secrets-in-URL anti-pattern, **not** a routine
task. Under the current "key = credential" authorization model, a RepliMap
license key is functionally a password. Passing it as a `?license_key=...`
query parameter means it leaks into places URLs routinely end up: server/CDN
access logs, browser history, and potentially third parties via the `Referer`
header. This is the same "authorization model strength" theme as the P0
`provision-community` auth fix.

**Scope:** all `/v1/me/*` endpoints that key off the license key —
`GET /v1/me/license`, `GET /v1/me/machines`, and (by extension of the same
model) the deactivate flow. Note deactivate already takes the key in the POST
body, so it's the two GETs that put the key in the URL.

**Status:** Pre-existing design — **not introduced or widened** by the
followups #6/#7 work (that change returns the full `machine_id`, which is a
device id, not the license key; it does not add any key-exposure surface).
Owner-scoping within the current model was audited and is tight (queries filter
on `license_id`; deactivate filters on `license_id AND machine_id`, so a key
can only ever touch its own license's machines).

**Two hardening directions (future decision):**
- **(a) Minimal:** move the key out of the URL — into an `Authorization`
  header or the POST body — so it no longer lands in logs/history/Referer. Keeps
  the "key = credential" model; small, localized change to the handlers +
  the browser `api.ts` calls.
- **(b) Strong model:** require a Clerk session token **and** verify the
  token identity owns the license (token↔license binding), so the key alone is
  no longer a sufficient credential. More thorough, larger change — same theme
  as the `provision-community` P0 rework.

**Recommendation:** does NOT block launch (the exposure existed before and is
unchanged by recent work), but **evaluate before onboarding real paying users
at volume** — the more real customers, the larger the exposure surface as keys
accumulate in logs and histories. Direction (a) is the cheap risk reducer;
(b) is the durable fix.

**Estimate:** (a) ~1–2h incl. tests; (b) ~half-day+ incl. binding logic and
migration of the dashboard/CLI auth story.

---

## Tracking

These intentionally live in the repo rather than a project tracker — they're tightly coupled to the commercial-flow commits and need to stay discoverable when someone greps for `RATE_LIMIT_DISABLED` or `handleResendKey`. If any one of them grows beyond ~half a day of work, promote to a GitHub issue and link from here.
