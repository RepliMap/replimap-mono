/**
 * RepliMap Pricing Configuration v4.0
 *
 * Philosophy: "Gate Output, Not Input"
 * - Unlimited scans for all tiers
 * - Unlimited resources per scan
 * - Charge when users export/download
 *
 * Tier Structure (single source of truth: CLI repo technical-reference.md matrix):
 * - COMMUNITY ($0): full scan/graph/resource .tf files, coverage summary
 * - PRO ($29): imports.tf scaffold, audit report export, full coverage list
 * - TEAM ($99): CI --fail-on, Trust Center report, 10 devices
 * - SOVEREIGN ($2,500): air-gapped activation by signed license file, APRA/RBNZ/NZISM
 *   compliance packs
 */

export type PlanName = "community" | "pro" | "team" | "sovereign";
export type BillingPeriod = "monthly" | "annual" | "lifetime";

/** Legacy plan names that map to v4.0 plans */
export type LegacyPlanName = "free" | "solo" | "enterprise";

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
  tagline: string;
  price: PlanPrice;
  description: string;
  features: PlanFeature[];
  cta: string;
  highlighted: boolean;
  hasLifetime: boolean;
  badge: string | null;
  /** Offline grace period in days */
  offlineGraceDays: number;
}

/**
 * Sovereign-tier feature claims — single source of truth.
 *
 * Ratified against the CLI repo Pricing/Feature Matrix. Digital signatures and
 * white-label reports are intentionally not claimed: the CLI has no
 * implementation for them. Do not add claims here (DORA, Essential Eight, etc.) without a matrix
 * update first — the matrix is the source of truth for claims, not this
 * file. Both PLANS.sovereign.features and SOVEREIGN_FEATURES are derived
 * from this array so the two lists cannot drift apart again.
 */
const SOVEREIGN_FEATURE_CLAIMS = [
  "Air-gapped activation by signed license file (issued on request)",
  "APRA CPS 234 / RBNZ BS11 / NZISM compliance packs",
  "Dedicated support (4h SLA)",
] as const;

export const PLANS: Record<PlanName, Plan> = {
  community: {
    name: "Community",
    tagline: "See everything. Free.",
    price: { monthly: 0, annual: 0, lifetime: null },
    description: "Scan a full account, map every dependency, and generate real Terraform — free.",
    offlineGraceDays: 0,
    features: [
      { text: "Unlimited scans, unlimited resources", included: true },
      { text: "1 AWS account", included: true },
      { text: "Interactive dependency graph (self-contained HTML)", included: true },
      { text: "Terraform resource files — full account", included: true },
      { text: "IaC coverage summary (unmanaged counts)", included: true },
      { text: "Audit score + terminal summary", included: true },
      { text: "Requires internet connection", included: true, badge: "Online only" },
      { text: "imports.tf import scaffold", included: false },
      { text: "Audit HTML report / SOC 2 evidence export", included: false },
      { text: "Full unmanaged-resource list + coverage.json", included: false },
    ],
    cta: "Get Started Free",
    highlighted: false,
    hasLifetime: false,
    badge: null,
  },
  pro: {
    name: "Pro",
    tagline: "The contractor deliverable",
    price: { monthly: 29, annual: 290, lifetime: 199 },
    description: "The two things in a client hand-off: an import-ready scaffold and the audit evidence.",
    offlineGraceDays: 7,
    features: [
      { text: "Everything in Community", included: true },
      { text: "Unlimited AWS accounts (fair use)", included: true },
      { text: "imports.tf — import scaffold for the whole account", included: true },
      { text: "Audit HTML report + SOC 2 evidence export", included: true },
      { text: "Full unmanaged-resource list + coverage.json", included: true },
      { text: "Graph export without watermark", included: true },
      { text: "7 days offline grace period", included: true },
      { text: "48h email support SLA", included: true },
      { text: "2 activated devices", included: true },
      { text: "CI mode with blocking checks (--fail-on)", included: false },
    ],
    cta: "Start Pro",
    highlighted: true,
    hasLifetime: true,
    badge: "Most Popular",
  },
  team: {
    name: "Team",
    tagline: "Organization delivery",
    price: { monthly: 99, annual: 990, lifetime: 499 },
    description: "For consultancies and platform teams that deliver as an organization.",
    offlineGraceDays: 14,
    features: [
      { text: "Everything in Pro", included: true },
      { text: "10 activated devices", included: true },
      { text: "CI mode with blocking checks (--fail-on)", included: true },
      { text: "Trust Center report (audit trail of the AWS API calls RepliMap made)", included: true },
      { text: "14 days offline grace period", included: true },
      { text: "24h priority support SLA", included: true },
      { text: "Air-gapped activation by signed license file", included: false },
    ],
    cta: "Start Team",
    highlighted: false,
    hasLifetime: true,
    badge: null,
  },
  sovereign: {
    name: "Sovereign",
    tagline: "Data sovereignty for regulated industries",
    price: { monthly: 2500, annual: 25000, lifetime: null },
    description: "When your regulator asks 'Where does the data go?', the answer is: Nowhere.",
    offlineGraceDays: 30,
    features: [
      { text: "Everything in Team", included: true },
      { text: "30 days offline grace", included: true },
      ...SOVEREIGN_FEATURE_CLAIMS.map((text) => ({ text, included: true })),
    ],
    cta: "Request Demo",
    highlighted: false,
    hasLifetime: false,
    badge: "Sovereign Grade",
  },
};

export const SOVEREIGN_FEATURES: readonly string[] = SOVEREIGN_FEATURE_CLAIMS;

// =============================================================================
// Legacy Plan Migration
// =============================================================================

export const LEGACY_PLAN_MIGRATIONS: Record<LegacyPlanName, PlanName> = {
  free: "community",
  solo: "pro",
  enterprise: "sovereign",
};

/**
 * Normalize a plan name, converting legacy names to v4.0 names
 */
export function normalizePlanName(plan: string): PlanName {
  const lower = plan.toLowerCase();
  if (lower in PLANS) return lower as PlanName;
  if (lower in LEGACY_PLAN_MIGRATIONS) {
    return LEGACY_PLAN_MIGRATIONS[lower as LegacyPlanName];
  }
  return "community"; // Default to community for unknown plans
}

/**
 * Check if a plan name is a legacy plan
 */
export function isLegacyPlan(plan: string): boolean {
  return plan.toLowerCase() in LEGACY_PLAN_MIGRATIONS;
}

// =============================================================================
// Helper Functions
// =============================================================================

export function formatPrice(
  amount: number,
  period: BillingPeriod
): string {
  if (amount === 0) return "Free";

  const formattedAmount = `$${amount.toLocaleString()}`;

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

// =============================================================================
// Plan Comparison
// =============================================================================

export const PLAN_RANK: Record<PlanName | LegacyPlanName, number> = {
  // v4.0 plans
  community: 0,
  pro: 1,
  team: 2,
  sovereign: 3,
  // Legacy plans
  free: 0,
  solo: 1,
  enterprise: 3,
};

export function isPlanUpgrade(from: string, to: string): boolean {
  const fromRank = PLAN_RANK[normalizePlanName(from)] ?? 0;
  const toRank = PLAN_RANK[normalizePlanName(to)] ?? 0;
  return toRank > fromRank;
}

export function isPlanDowngrade(from: string, to: string): boolean {
  const fromRank = PLAN_RANK[normalizePlanName(from)] ?? 0;
  const toRank = PLAN_RANK[normalizePlanName(to)] ?? 0;
  return toRank < fromRank;
}

export function getUpgradePath(currentPlan: PlanName): PlanName | null {
  const upgradePaths: Record<PlanName, PlanName | null> = {
    community: "pro",
    pro: "team",
    team: "sovereign",
    sovereign: null,
  };
  return upgradePaths[currentPlan];
}

// =============================================================================
// Offline Grace Days
// =============================================================================

/**
 * Get offline grace days for a plan
 */
export function getOfflineGraceDays(plan: string): number {
  const normalized = normalizePlanName(plan);
  return PLANS[normalized]?.offlineGraceDays ?? 0;
}

/**
 * Get offline grace label for display
 */
export function getOfflineGraceLabel(plan: string): string {
  const days = getOfflineGraceDays(plan);
  if (days === 0) return "Requires internet";
  return `${days} days grace`;
}
