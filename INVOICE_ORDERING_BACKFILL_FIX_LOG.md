# Fix Log: First-Cycle Period Backfill Lost to Event Ordering (followups §5)

**Date:** 2026-07-05
**Scope:** `apps/api/src/handlers/stripe-webhook.ts` + ordering tests
**Status:** Fixed, validated on dev with real Stripe sandbox events. Prod deploy pending.

---

## 1. The bug

Stripe explicitly does not guarantee event delivery order. On both real
production purchases (2026-07-04) and twice during dev E2E validation,
`invoice.paid` arrived **before** `customer.subscription.created`:

- `handleInvoicePaid` found no license for the subscription → no-op'd
  ("No license found") — **but the event was still marked processed**.
- Event-level idempotency then rejected any redelivery of that event id.
- Net effect: the first billing cycle's period backfill was **permanently
  lost** — `current_period_end` stayed `null` and `current_period_start`
  kept the `nowISO()` fallback until the next renewal invoice (a month away).

Live evidence (first prod purchase, `sub_1TpSEPAM46G6RB9JY2OdOZhN`):
`invoice.paid` processed at `11:59:40.126Z`, license created at `.551Z`,
license ended up with `current_period_end = null` (see
`PROD_E2E_SMOKE_TEST_LOG.md`).

## 2. Root cause — deeper than pure ordering

The ordering race explains why `invoice.paid` couldn't backfill. But the
reason the backfill was *needed at all* is an API-version field move:

**On Stripe API ≥2025-03-31 (basil/clover), `current_period_start/end` moved
from the subscription top level to `subscription.items.data[]`.**

Verified against ground truth, not docs memory:
- Real sandbox subscription `sub_1TpNk4AKLIiL9hdw5SKhWU18`:
  `items.data[0].current_period_start = 1783149120`, `…end = 1785827520`,
  **no top-level fields**.
- Fresh subscription created during validation (`sub_1TpUgXAKLIiL9hdwYl4k3qY5`):
  API response shows `top-level current_period_start: None`, items carry
  `1783175809 → 1785854209`.
- Stripe docs reference `subscription_item_object-current_period_end`.

`handleSubscriptionCreated` only read the top-level fields → on every real
clover event it fell into the `nowISO()`/`undefined` fallback, and the
comment "invoice.paid will backfill accurate periods" made the system depend
on an event Stripe is free to deliver first. **The billing period was inside
the `customer.subscription.created` payload all along — the code just never
read it.**

## 3. Fix — both directions, B primary + A safety net

### B (primary): read the period from `items` — zero API calls

New `getSubscriptionPeriod(subscription)` resolves the period across API
versions (top-level first for <2025-03-31, `items.data[0].current_period_*`
fallback for clover). Used by **both** `handleSubscriptionCreated` and
`handleSubscriptionUpdated` (same extraction bug affected renewals/upgrades).

Why primary: the originally-proposed "fetch latest invoice" variant would add
an API call with its own failure mode. Reading the event's own payload is
deterministic, immediate, needs no graceful-degradation logic (if neither
location has the fields, behavior is exactly the old fallback), and matches
Stripe's documented guidance for out-of-order events.

### A (safety net): don't consume `invoice.paid` before the license exists

`handleInvoicePaid` now returns `{success, retry}`. When the invoice carries a
subscription id but no license exists yet, the dispatcher returns **500
without calling `markEventProcessed`** — mirroring the existing
`customer.subscription.created` retry path — so Stripe's redelivery is
processed for real.

- Scope guard: invoices with **no** subscription id still ack 200 (no retry
  storm for one-off invoices).
- Idempotency preserved: `invoice.paid` writes absolute period values (never
  extends), and a successfully processed event id is still deduplicated —
  verified by test (third delivery → `duplicate: true`).
- Why not A alone: Stripe's retry timing is undisclosed (live: exponential
  backoff up to 3 days; **sandbox: only 3 retries over a few hours**) — the
  period would stay wrong until an unbounded retry lands. With B, the period
  is correct immediately; A only restores the (rare) other effects of a raced
  `invoice.paid`.

## 4. TDD evidence

**RED** (`tests/stripe-webhook.test.ts`, new describe
"event ordering: invoice.paid before customer.subscription.created (§5)",
clover-shaped events mirroring real payloads):

```
4 failed | 1 passed
- clover subscription.created reads period from items   → start was nowISO, not items value
- raced sequence … still ends with real billing period  → current_period_end: null   ← the exact live loss
- invoice.paid with no license: 500, NOT marked …       → got 200 (event consumed)
- clover subscription.updated also sources from items   → stale values preserved
```

**GREEN:** all 5 pass. Full suite: **205/205**, typecheck + lint clean.
Pre-existing guards intact: P1-5 regression (update with no period fields
anywhere preserves existing values), 5-way concurrent lifetime burst,
duplicate-event dedup.

## 5. Dev validation — real Stripe sandbox events (2026-07-04)

Deployed working tree to the **dev worker** (`replimap-api`, version
`ae3962a7`; prod untouched). Created a real sandbox subscription via the
Stripe API (`cus_Up8yR70KrUQS75` + `pm_card_visa` +
`sub_1TpUgXAKLIiL9hdwYl4k3qY5`, sandbox Pro Monthly price). The race
**reproduced naturally on the first attempt** — `wrangler tail`:

```
14:36:51.865Z POST /v1/webhooks/stripe → 500   [A]
    [warn] [Stripe] invoice.paid for subscription sub_1TpUgX… arrived
           before its license exists. Triggering retry.
14:36:51.975Z POST /v1/webhooks/stripe → 200   [B]
    [log] [Stripe] Created license for subscription sub_1TpUgX…
14:37:07.146Z POST /v1/webhooks/stripe → 200   [A closes the loop]
```

Dev D1 (`replimap-dev`) after the sequence:

| field | pre-fix behavior | observed |
|---|---|---|
| `current_period_start` | `nowISO()` (≈created_at) | `2026-07-04T14:36:49.000Z` = **1783175809, the items value** |
| `current_period_end` | **null, permanently** | `2026-08-04T14:36:49.000Z` = **1785854209** ✅ |

`processed_events`: `customer.subscription.created` marked at `14:36:54Z`;
`invoice.paid` (`evt_1TpUgZAKLIiL9hdwd22bPnBo`) **absent after the 500**,
then marked at `14:37:07.639Z` when Stripe's retry (~15s later) processed it
for real. Both directions verified end-to-end on real events.

Note: the dev license resolved to plan `community` because the dev worker now
carries the **live** price mappings (post-`b39d4ac`) and the sandbox price id
no longer maps — orthogonal to this fix.

**Cleanup:** sandbox subscription canceled; dev D1 restored to baseline
(validation license/user/processed_events rows removed).

## 6. Rollout

- [x] Dev worker deployed + validated with real events
- [ ] Commit + deploy to prod (`pnpm deploy:prod`) — pending confirmation
- [ ] Post-prod: next real subscription purchase should land with
      `current_period_end` set; the raced `invoice.paid` (if any) should show
      one 500 then a successful retry in `wrangler tail --env prod`
