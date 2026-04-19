"use client"

import { useState } from "react"
import { useUser } from "@clerk/nextjs"
import { useSearchParams } from "next/navigation"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Check, ArrowLeft, Loader2, Terminal, Shield } from "lucide-react"
import { PLANS, type PlanName, type BillingPeriod } from "@/lib/pricing"
import { createCheckoutSession } from "@/lib/api"

const VALID_PLANS: PlanName[] = ["pro", "team"]
const VALID_BILLING: BillingPeriod[] = ["monthly", "annual", "lifetime"]

export default function CheckoutPage() {
  const { user, isLoaded } = useUser()
  const searchParams = useSearchParams()

  const planParam = searchParams.get("plan") as PlanName | null
  const billingParam = (searchParams.get("billing") as BillingPeriod | null) || "monthly"

  const [billingPeriod, setBillingPeriod] = useState<BillingPeriod>(
    VALID_BILLING.includes(billingParam) ? billingParam : "monthly"
  )
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Validate plan
  if (!planParam || !VALID_PLANS.includes(planParam)) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center pt-20">
        <div className="text-center max-w-md px-4">
          <h1 className="text-2xl font-bold text-foreground mb-4">Invalid Plan</h1>
          <p className="text-muted-foreground mb-6">
            Please select a plan from the pricing page.
          </p>
          <Button asChild>
            <Link href="/#pricing">View Pricing</Link>
          </Button>
        </div>
      </div>
    )
  }

  const plan = PLANS[planParam]

  // Lifetime-unavailable guard: redirect user back to pricing if they hit
  // /checkout?plan=X&billing=lifetime for a plan with no lifetime offer.
  const lifetimeUnavailable =
    billingPeriod === "lifetime" && !plan.hasLifetime

  const price =
    billingPeriod === "lifetime"
      ? plan.price.lifetime ?? 0
      : billingPeriod === "annual"
        ? plan.price.annual
        : plan.price.monthly

  const period =
    billingPeriod === "lifetime"
      ? "one-time"
      : billingPeriod === "annual"
        ? "per year"
        : "per month"

  const monthlySavings =
    billingPeriod === "annual" && plan.price.monthly > 0
      ? `$${(plan.price.monthly * 12 - plan.price.annual) / 12}/mo savings`
      : null

  const handleCheckout = async () => {
    if (!user) return

    setLoading(true)
    setError(null)

    try {
      const email = user.primaryEmailAddress?.emailAddress
      if (!email) {
        setError("No email address found on your account.")
        setLoading(false)
        return
      }

      const appUrl = process.env.NEXT_PUBLIC_APP_URL || window.location.origin
      const result = await createCheckoutSession({
        plan: planParam as "pro" | "team",
        billing_period: billingPeriod as "monthly" | "annual" | "lifetime",
        email,
        success_url: `${appUrl}/checkout/success`,
        cancel_url: `${appUrl}/checkout?plan=${planParam}&billing=${billingPeriod}`,
      })

      // Redirect to Stripe hosted checkout
      window.location.href = result.checkout_url
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to create checkout session"
      setError(message)
      setLoading(false)
    }
  }

  if (!isLoaded) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background pt-20">
      <div className="max-w-2xl mx-auto px-4 py-12">
        {/* Back link */}
        <Link
          href="/#pricing"
          className="inline-flex items-center gap-2 text-muted-foreground hover:text-foreground text-sm mb-8 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to pricing
        </Link>

        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-foreground mb-2">
            {billingPeriod === "lifetime" ? "Buy" : "Subscribe to"} RepliMap {plan.name}
          </h1>
          <p className="text-muted-foreground">{plan.description}</p>
        </div>

        {/* Lifetime unavailable guard */}
        {lifetimeUnavailable && (
          <div className="rounded-lg border border-yellow-500/50 bg-yellow-500/5 p-4 mb-6 text-sm text-yellow-200">
            Lifetime pricing isn&apos;t available for the {plan.name} plan.{" "}
            <button
              type="button"
              onClick={() => setBillingPeriod("monthly")}
              className="underline hover:text-yellow-100"
            >
              Switch to monthly
            </button>{" "}
            or{" "}
            <Link href="/#pricing" className="underline hover:text-yellow-100">
              pick a different plan
            </Link>
            .
          </div>
        )}

        {/* Plan Card */}
        <div className="rounded-2xl border border-border bg-card/50 p-6 mb-6">
          {/* Billing Toggle */}
          <div className="flex items-center gap-2 mb-6">
            <button
              onClick={() => setBillingPeriod("monthly")}
              className={`rounded-md px-4 py-2 text-sm font-medium transition-colors ${
                billingPeriod === "monthly"
                  ? "bg-emerald-500 text-white"
                  : "text-muted-foreground hover:text-foreground bg-muted"
              }`}
            >
              Monthly
            </button>
            <button
              onClick={() => setBillingPeriod("annual")}
              className={`rounded-md px-4 py-2 text-sm font-medium transition-colors flex items-center gap-1 ${
                billingPeriod === "annual"
                  ? "bg-emerald-500 text-white"
                  : "text-muted-foreground hover:text-foreground bg-muted"
              }`}
            >
              Annual
              <span className="text-xs opacity-75">(2 months free)</span>
            </button>
            {plan.hasLifetime && (
              <button
                onClick={() => setBillingPeriod("lifetime")}
                className={`rounded-md px-4 py-2 text-sm font-medium transition-colors flex items-center gap-1 ${
                  billingPeriod === "lifetime"
                    ? "bg-gradient-to-r from-yellow-500 to-orange-500 text-white"
                    : "text-muted-foreground hover:text-foreground bg-muted"
                }`}
              >
                Lifetime
              </button>
            )}
          </div>

          {/* Price */}
          <div className="flex items-baseline gap-2 mb-1">
            <span className="text-4xl font-bold text-foreground">${price}</span>
            <span className="text-muted-foreground">{period}</span>
          </div>
          {monthlySavings && (
            <Badge variant="outline" className="border-emerald-500/50 text-emerald-400 mb-4">
              {monthlySavings}
            </Badge>
          )}

          {/* Divider */}
          <div className="border-t border-border my-6" />

          {/* Features */}
          <h3 className="text-sm font-medium text-foreground mb-3">What&apos;s included:</h3>
          <ul className="space-y-2 mb-6">
            {plan.features
              .filter((f) => f.included)
              .map((feature, i) => (
                <li key={i} className="flex items-start gap-2 text-sm">
                  <Check className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
                  <span className="text-muted-foreground">{feature.text}</span>
                </li>
              ))}
          </ul>
        </div>

        {/* Checkout details */}
        <div className="rounded-2xl border border-border bg-card/50 p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <span className="text-muted-foreground">Plan</span>
            <span className="text-foreground font-medium">RepliMap {plan.name}</span>
          </div>
          <div className="flex items-center justify-between mb-4">
            <span className="text-muted-foreground">Billing</span>
            <span className="text-foreground font-medium capitalize">{billingPeriod}</span>
          </div>
          <div className="flex items-center justify-between mb-4">
            <span className="text-muted-foreground">Account</span>
            <span className="text-foreground font-medium">
              {user?.primaryEmailAddress?.emailAddress}
            </span>
          </div>
          <div className="border-t border-border my-4" />
          <div className="flex items-center justify-between">
            <span className="text-foreground font-semibold">Total</span>
            <span className="text-foreground font-bold text-xl">
              ${price}
              <span className="text-sm font-normal text-muted-foreground ml-1">
                {billingPeriod === "lifetime"
                  ? "one-time"
                  : billingPeriod === "annual"
                    ? "/yr"
                    : "/mo"}
              </span>
            </span>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="rounded-lg border border-red-500/50 bg-red-500/10 p-4 mb-6">
            <p className="text-sm text-red-400">{error}</p>
          </div>
        )}

        {/* CTA */}
        <Button
          onClick={handleCheckout}
          disabled={loading || lifetimeUnavailable}
          className="w-full h-12 bg-emerald-500 hover:bg-emerald-600 text-white text-base"
        >
          {loading ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Redirecting to payment...
            </>
          ) : (
            `Continue to Payment — $${price}${
              billingPeriod === "lifetime"
                ? " one-time"
                : billingPeriod === "annual"
                  ? "/yr"
                  : "/mo"
            }`
          )}
        </Button>

        {/* Trust signals */}
        <div className="mt-6 flex flex-col items-center gap-3 text-xs text-muted-foreground">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-1">
              <Shield className="w-3 h-3" />
              <span>Secure checkout by Stripe</span>
            </div>
            <div className="flex items-center gap-1">
              <Terminal className="w-3 h-3" />
              <span>Cancel anytime</span>
            </div>
          </div>
          <p>Your data never leaves your machine. RepliMap runs 100% locally.</p>
        </div>
      </div>
    </div>
  )
}
