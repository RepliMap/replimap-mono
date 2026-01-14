/**
 * RepliMap Pricing Configuration v3.2
 *
 * Gate Philosophy: "Gate Output, Not Input"
 * - Scanning is unlimited (resources per scan)
 * - Frequency is limited for free tier (3/month)
 * - Output (download, export, details) is gated
 */

export type PlanName = "free" | "solo" | "pro" | "team" | "enterprise";
export type BillingPeriod = "monthly" | "annual" | "lifetime";

export interface PlanPrice {
  monthly: number;
  annual: number;
  lifetime: number | null;
}

export interface PlanFeature {
  text: string;
  included: boolean;
  badge?: string;
}

export interface Plan {
  name: string;
  price: PlanPrice;
  description: string;
  features: PlanFeature[];
  cta: string;
  highlighted: boolean;
  hasLifetime: boolean;
}

export const PLANS: Record<PlanName, Plan> = {
  free: {
    name: "Free",
    price: { monthly: 0, annual: 0, lifetime: null },
    description: "For evaluators exploring their infrastructure",
    features: [
      { text: "Unlimited resources per scan", included: true },
      { text: "3 full scans per month", included: true },
      { text: "1 AWS account", included: true },
      { text: "Graph visualization", included: true },
      { text: "Code preview (100 lines)", included: true },
      { text: "Code download", included: false },
      { text: "Full remediation", included: false },
      { text: "Report export", included: false },
    ],
    cta: "Get Started",
    highlighted: false,
    hasLifetime: false,
  },
  solo: {
    name: "Solo",
    price: { monthly: 49, annual: 490, lifetime: 299 },
    description: "For individual DevOps professionals",
    features: [
      { text: "Everything in Free", included: true },
      { text: "Unlimited scans", included: true },
      { text: "Full code download", included: true },
      { text: "Complete remediation steps", included: true },
      { text: "HTML report export", included: true },
      { text: "5 snapshots (7-day retention)", included: true },
      { text: "Email support (48h SLA)", included: true },
      { text: "Drift detection", included: false },
    ],
    cta: "Start Solo",
    highlighted: false,
    hasLifetime: true,
  },
  pro: {
    name: "Pro",
    price: { monthly: 99, annual: 990, lifetime: 499 },
    description: "For senior engineers with multi-account needs",
    features: [
      { text: "Everything in Solo", included: true },
      { text: "3 AWS accounts", included: true },
      { text: "Drift detection", included: true },
      { text: "CI/CD integration", included: true },
      { text: "PDF report export", included: true },
      { text: "15 snapshots (30-day retention)", included: true },
      { text: "Remediate beta access", included: true, badge: "Priority" },
      { text: "Email support (24h SLA)", included: true },
    ],
    cta: "Start Pro",
    highlighted: true,
    hasLifetime: true,
  },
  team: {
    name: "Team",
    price: { monthly: 199, annual: 1990, lifetime: null },
    description: "For teams with compliance needs",
    features: [
      { text: "Everything in Pro", included: true },
      { text: "10 AWS accounts", included: true },
      { text: "Trust Center (audit logging)", included: true },
      { text: "API call recording", included: true },
      { text: "JSON report export", included: true },
      { text: "30 snapshots (90-day retention)", included: true },
      { text: "Email support (12h SLA)", included: true },
      { text: "Compliance mapping", included: false },
    ],
    cta: "Start Team",
    highlighted: false,
    hasLifetime: false,
  },
  enterprise: {
    name: "Enterprise",
    price: { monthly: 500, annual: 5000, lifetime: null },
    description: "For banks and regulated industries",
    features: [
      { text: "Everything in Team", included: true },
      { text: "Unlimited AWS accounts", included: true },
      { text: "APRA CPS 234 mapping", included: true },
      { text: "RBNZ BS11 mapping", included: true },
      { text: "Essential Eight assessment", included: true },
      { text: "Digital signatures (SHA256)", included: true },
      { text: "Tamper-evident reports", included: true },
      { text: "4h SLA support", included: true },
    ],
    cta: "Contact Sales",
    highlighted: false,
    hasLifetime: false,
  },
};

export const ENTERPRISE_FEATURES = [
  "Unlimited AWS accounts",
  "APRA CPS 234 mapping",
  "RBNZ BS11 mapping",
  "Essential Eight assessment",
  "Digital signatures (SHA256)",
  "Tamper-evident reports",
  "Unlimited snapshots (1-year retention)",
  "4h SLA support",
];

export function formatPrice(
  amount: number,
  period: BillingPeriod
): string {
  if (amount === 0) return "Free";

  const formattedAmount = `$${amount}`;

  switch (period) {
    case "monthly":
      return `${formattedAmount}/mo`;
    case "annual":
      return `${formattedAmount}/yr`;
    case "lifetime":
      return `${formattedAmount}`;
    default:
      return formattedAmount;
  }
}

export function getPeriodLabel(period: BillingPeriod): string {
  switch (period) {
    case "monthly":
      return "per month";
    case "annual":
      return "per year";
    case "lifetime":
      return "one-time";
    default:
      return "";
  }
}

export function getAnnualSavings(plan: Plan): number {
  if (!plan.price.annual || !plan.price.monthly) return 0;
  const monthlyTotal = plan.price.monthly * 12;
  return monthlyTotal - plan.price.annual;
}

export function getLifetimeBreakeven(plan: Plan): number {
  if (!plan.price.lifetime || !plan.price.monthly) return 0;
  return Math.ceil(plan.price.lifetime / plan.price.monthly);
}
