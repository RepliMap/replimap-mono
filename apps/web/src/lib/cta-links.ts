/**
 * CTA Link Builders
 *
 * Single source of truth for where "Get Started Free", "Start Pro Trial",
 * and other landing-page CTAs route to. Keeps tracking sources consistent
 * and lets us swap destinations (Tally form → checkout → something else)
 * without hunting through every component.
 */

import type { PlanName, BillingPeriod } from "./pricing"

export type CheckoutPlan = Exclude<PlanName, "community" | "sovereign">

/**
 * Build a Stripe-checkout link for a paid plan.
 * Community and Sovereign are handled separately (free signup and
 * enterprise contact, respectively).
 */
export function checkoutHref(
  plan: CheckoutPlan,
  billing: BillingPeriod = "monthly"
): string {
  return `/checkout?plan=${plan}&billing=${billing}`
}

/**
 * Build a Clerk sign-up link that redirects to the dashboard on success.
 * The `source` param is passed through to analytics so we can attribute
 * where the sign-up originated (hero, pricing_community, nav, etc.).
 */
export function freeSignupHref(source: string): string {
  return `/sign-up?redirect_url=${encodeURIComponent("/dashboard")}&source=${encodeURIComponent(source)}`
}

/**
 * Enterprise contact — Sovereign tier is never self-serve.
 * Kept as a constant so the email + subject line stay consistent.
 */
export const SOVEREIGN_CONTACT =
  "mailto:david@replimap.com?subject=RepliMap Sovereign Inquiry"
