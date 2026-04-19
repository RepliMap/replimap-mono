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

**Status:** Idempotency is verified by unit tests (`isEventProcessed` / `markEventProcessed`) and by the e2e harness's happy-path webhook delivery. Not stress-tested.

**Why it matters:** Production Stripe retries events aggressively (up to 3 days with exponential backoff). Local `stripe listen` delivers each event exactly once — fundamentally different behaviour. A bug that surfaces only under retries won't be caught by current tests.

**How to do it:**
- Write a script that resends the same `evt_...` to `/v1/webhooks/stripe` N times concurrently (e.g. 50).
- Assert: exactly one license row created, exactly one `processed_events` row, no 5xx responses.
- Also test event ordering permutations: `subscription.created` → `checkout.session.completed`, reversed, interleaved with `invoice.paid`.
- Could live in `apps/api/tests/webhook-stress.test.ts` using miniflare, or as a shell script that hits a local wrangler instance.

**Estimate:** ~3h. Schedule before the first real paying customers at volume (>100 subs/day).

---

## 4. Verify `RATE_LIMIT_DISABLED` is NOT set in production

**Status:** Flag added for local e2e only (`apps/api/src/lib/rate-limiter.ts`). Production deploy must not carry it.

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

## Tracking

These intentionally live in the repo rather than a project tracker — they're tightly coupled to the commercial-flow commits and need to stay discoverable when someone greps for `RATE_LIMIT_DISABLED` or `handleResendKey`. If any one of them grows beyond ~half a day of work, promote to a GitHub issue and link from here.
