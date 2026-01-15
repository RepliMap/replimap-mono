"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Check, X, Sparkles, Shield } from "lucide-react"
import { PLANS, SOVEREIGN_FEATURES, type PlanName, type BillingPeriod } from "@/lib/pricing"

const TALLY_FORM_URL = "https://tally.so/r/2EaYae"

// Transform PLANS object to array for rendering, excluding sovereign (shown separately)
const plansList = (Object.entries(PLANS) as [PlanName, (typeof PLANS)[PlanName]][])
  .filter(([key]) => key !== "sovereign")
  .map(([key, plan]) => ({
    key,
    ...plan,
    // Transform price object to display strings
    price: {
      monthly: plan.price.monthly === 0 ? "$0" : `$${plan.price.monthly}`,
      annual: plan.price.annual === 0 ? "$0" : `$${plan.price.annual}`,
      lifetime: plan.price.lifetime ? `$${plan.price.lifetime}` : null,
    },
    period: {
      monthly: plan.price.monthly === 0 ? "forever" : "per month",
      annual: plan.price.annual === 0 ? "forever" : "per year",
      lifetime: plan.price.lifetime ? "one-time" : null,
    },
  }))

export function Pricing() {
  const [billingPeriod, setBillingPeriod] = useState<BillingPeriod>("monthly")

  return (
    <section id="pricing" className="py-20 bg-background">
      <div className="max-w-7xl mx-auto px-4">
        {/* Header */}
        <div className="text-center mb-8">
          <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-4">
            Simple, transparent pricing
          </h2>
          <p className="text-muted-foreground">
            Unlimited scanning. Pay only when you export.
          </p>
        </div>

        {/* Billing Toggle */}
        <div className="flex justify-center mb-12">
          <div className="inline-flex items-center gap-1 p-1 bg-muted rounded-lg">
            <button
              onClick={() => setBillingPeriod("monthly")}
              className={`${
                billingPeriod === "monthly"
                  ? "bg-emerald-500 text-white"
                  : "text-muted-foreground hover:text-foreground"
              } rounded-md px-4 py-2 text-sm font-medium transition-colors`}
            >
              Monthly
            </button>
            <button
              onClick={() => setBillingPeriod("annual")}
              className={`${
                billingPeriod === "annual"
                  ? "bg-emerald-500 text-white"
                  : "text-muted-foreground hover:text-foreground"
              } rounded-md px-4 py-2 text-sm font-medium transition-colors flex items-center gap-1`}
            >
              Annual
              <span className="text-xs opacity-75">(2 months free)</span>
            </button>
            <button
              onClick={() => setBillingPeriod("lifetime")}
              className={`${
                billingPeriod === "lifetime"
                  ? "bg-gradient-to-r from-yellow-500 to-orange-500 text-white"
                  : "text-muted-foreground hover:text-foreground"
              } rounded-md px-4 py-2 text-sm font-medium transition-colors flex items-center gap-1`}
            >
              <Sparkles className="w-3 h-3" />
              Lifetime
            </button>
          </div>
        </div>

        {/* Pricing Cards - 3 columns (Community, Pro, Team) */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-5xl mx-auto">
          {plansList.map((plan) => (
            <div
              key={plan.key}
              className={`rounded-2xl p-6 flex flex-col ${
                plan.highlighted
                  ? "bg-gradient-to-b from-emerald-500/20 to-cyan-500/10 border-2 border-emerald-500/50 lg:scale-105"
                  : "bg-card/50 border border-border"
              }`}
            >
              {/* Badges */}
              <div className="flex gap-2 mb-3 min-h-[28px]">
                {plan.badge && (
                  <Badge className="bg-emerald-500 text-white">{plan.badge}</Badge>
                )}
                {billingPeriod === "lifetime" && plan.hasLifetime && (
                  <Badge className="bg-gradient-to-r from-yellow-500 to-orange-500 text-white border-0">
                    Early Bird
                  </Badge>
                )}
              </div>

              {/* Plan Name & Tagline */}
              <h3 className="text-xl font-bold text-foreground mb-1">{plan.name}</h3>
              <p className="text-sm text-muted-foreground mb-4">{plan.tagline}</p>

              {/* Price */}
              <div className="mb-2">
                <span className="text-3xl font-bold text-foreground">
                  {plan.price[billingPeriod] ?? plan.price.monthly}
                </span>
                <span className="text-muted-foreground ml-2 text-sm">
                  {plan.period[billingPeriod] ?? plan.period.monthly}
                </span>
              </div>

              {/* Description */}
              <p className="text-muted-foreground text-sm mt-2 mb-6">{plan.description}</p>

              {/* CTA Button */}
              {billingPeriod === "lifetime" && !plan.hasLifetime ? (
                <Button
                  disabled
                  className="w-full mb-6"
                  variant="outline"
                >
                  No Lifetime Option
                </Button>
              ) : (
                <a
                  href={`${TALLY_FORM_URL}?source=pricing_${plan.key}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block w-full mb-6"
                >
                  <Button
                    className={`w-full ${
                      plan.highlighted ? "bg-emerald-500 hover:bg-emerald-600 text-white" : ""
                    }`}
                    variant={plan.highlighted ? "default" : "outline"}
                  >
                    {plan.cta}
                  </Button>
                </a>
              )}

              {/* Features List */}
              <ul className="space-y-3 flex-1">
                {plan.features.map((feature, featureIndex) => (
                  <li key={featureIndex} className="flex items-start gap-2 text-sm">
                    {feature.included ? (
                      <>
                        <Check className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
                        <span className="text-muted-foreground">
                          {feature.text}
                          {feature.badge && (
                            <Badge
                              variant="outline"
                              className="ml-1.5 text-[10px] py-0 border-emerald-500/50 text-emerald-400"
                            >
                              {feature.badge}
                            </Badge>
                          )}
                        </span>
                      </>
                    ) : (
                      <>
                        <X className="w-4 h-4 text-muted-foreground/50 flex-shrink-0 mt-0.5" />
                        <span className="text-muted-foreground/50">{feature.text}</span>
                      </>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Sovereign Banner */}
        <div className="mt-12 rounded-2xl p-8 bg-gradient-to-r from-purple-900/30 to-indigo-900/30 border border-purple-500/30">
          <div className="flex flex-col lg:flex-row items-center gap-8">
            <div className="lg:w-1/3">
              <Badge className="mb-3 bg-purple-500/20 text-purple-400 border-purple-500/50">
                <Shield className="w-3 h-3 mr-1" />
                Sovereign Grade
              </Badge>
              <h3 className="text-2xl font-bold text-foreground mb-2">Sovereign</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Data sovereignty for regulated industries
              </p>
              <div className="mb-4">
                <span className="text-3xl font-bold text-foreground">From $2,500</span>
                <span className="text-muted-foreground ml-2">/month</span>
              </div>
              <p className="text-xs text-muted-foreground">
                When your regulator asks &ldquo;Where does the data go?&rdquo;, the answer is: Nowhere.
              </p>
            </div>
            <div className="lg:w-1/2 grid grid-cols-2 gap-4">
              {SOVEREIGN_FEATURES.map((feature, index) => (
                <div key={index} className="flex items-start gap-2">
                  <Check className="w-4 h-4 text-purple-400 flex-shrink-0 mt-0.5" />
                  <span className="text-muted-foreground text-sm">{feature}</span>
                </div>
              ))}
            </div>
            <div className="lg:w-auto">
              <Button asChild className="bg-purple-500 hover:bg-purple-600 text-white">
                <a href="mailto:david@replimap.com?subject=RepliMap Sovereign Inquiry">
                  Request Demo
                </a>
              </Button>
            </div>
          </div>
        </div>

        {/* Philosophy Note */}
        <div className="mt-12 text-center">
          <p className="text-muted-foreground text-sm max-w-2xl mx-auto">
            Unlimited scanning. Pay only when you export. Your data never leaves your machine.
          </p>
        </div>
      </div>
    </section>
  )
}
