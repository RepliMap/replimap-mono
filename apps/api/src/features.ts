/**
 * RepliMap Feature Definitions v4.0
 *
 * Philosophy: "Gate Output, Not Input"
 * - Unlimited scans for all tiers
 * - Unlimited resources per scan
 * - Charge when users export/download
 *
 * Tier Structure:
 * - COMMUNITY ($0): Full visibility, JSON export with metadata
 * - PRO ($29): Terraform/CSV export, API access
 * - TEAM ($99): Drift alerts, compliance reports, CI/CD
 * - SOVEREIGN ($2,500): SSO, signed reports, air-gap, white-labeling
 */

import type { SecureLicenseLimits } from './lib/ed25519';

// =============================================================================
// Feature Enum
// =============================================================================

export enum Feature {
  // Core features (available to all with limits)
  SCAN = 'scan',
  SCAN_UNLIMITED_FREQUENCY = 'scan_unlimited_frequency',

  GRAPH = 'graph',
  GRAPH_FULL = 'graph_full',
  GRAPH_SECURITY = 'graph_security',
  GRAPH_EXPORT_NO_WATERMARK = 'graph_export_no_watermark',

  CLONE_GENERATE = 'clone_generate',
  CLONE_DOWNLOAD = 'clone_download',
  CLONE_FULL_PREVIEW = 'clone_full_preview',

  // Audit features
  AUDIT = 'audit',
  AUDIT_FULL_FINDINGS = 'audit_full_findings',
  AUDIT_FIX = 'audit_fix',
  AUDIT_REPORT_EXPORT = 'audit_report_export',
  AUDIT_CI_MODE = 'audit_ci_mode',

  // Change detection features
  DRIFT = 'drift',
  DRIFT_WATCH = 'drift_watch',
  DRIFT_ALERTS = 'drift_alerts',

  SNAPSHOT = 'snapshot',
  SNAPSHOT_DIFF = 'snapshot_diff',

  // Advanced analysis
  DEPS = 'deps',
  DEPS_EXPORT = 'deps_export',

  COST = 'cost',
  COST_EXPORT = 'cost_export',

  // Account & team features
  MULTI_ACCOUNT = 'multi_account',
  WEB_DASHBOARD = 'web_dashboard',
  TEAM_COLLABORATION = 'team_collaboration',
  SSO = 'sso',

  // Export features
  EXPORT_JSON = 'export_json',
  EXPORT_HTML = 'export_html',
  EXPORT_MARKDOWN = 'export_markdown',
  EXPORT_TERRAFORM = 'export_terraform',
  EXPORT_CSV = 'export_csv',
  EXPORT_PDF = 'export_pdf',

  // Compliance features
  COMPLIANCE_CIS = 'compliance_cis',
  COMPLIANCE_SOC2 = 'compliance_soc2',
  COMPLIANCE_APRA = 'compliance_apra',
  COMPLIANCE_DORA = 'compliance_dora',
  COMPLIANCE_ESSENTIAL8 = 'compliance_essential8',
  COMPLIANCE_CUSTOM = 'compliance_custom',

  // Enterprise features
  REPORT_SIGNATURE = 'report_signature',
  TAMPER_EVIDENT_AUDIT = 'tamper_evident_audit',
  AIR_GAP_DEPLOYMENT = 'air_gap_deployment',
  WHITE_LABELING = 'white_labeling',
  DEDICATED_SUPPORT = 'dedicated_support',
}

export enum Plan {
  COMMUNITY = 'community',
  PRO = 'pro',
  TEAM = 'team',
  SOVEREIGN = 'sovereign',
}

// =============================================================================
// Feature Access Matrix by Plan
// =============================================================================

/**
 * Feature access matrix by plan
 *
 * v4.0 Philosophy: "Gate Output, Not Input"
 *
 * Key decisions:
 * - COMMUNITY: Can VIEW everything, but exports are limited
 * - PRO: Unlocks Terraform/CSV export, API access, full audit
 * - TEAM: Unlocks drift alerts, compliance reports, CI/CD
 * - SOVEREIGN: Unlocks SSO, signed reports, air-gap, white-labeling
 */
export const PLAN_FEATURES: Record<Plan, Feature[]> = {
  // COMMUNITY ($0/mo) - Full visibility, gated output
  [Plan.COMMUNITY]: [
    Feature.SCAN,
    Feature.SCAN_UNLIMITED_FREQUENCY,  // v4.0: Unlimited scans for all!
    Feature.GRAPH,
    Feature.AUDIT,
    Feature.CLONE_GENERATE,
    Feature.EXPORT_JSON,
    Feature.SNAPSHOT,
    Feature.SNAPSHOT_DIFF,
    Feature.COST,  // v4.0: Can VIEW cost analysis
    Feature.DEPS,  // v4.0: Can VIEW dependency graph
  ],

  // PRO ($29/mo) - Export your infrastructure as code
  [Plan.PRO]: [
    Feature.SCAN,
    Feature.SCAN_UNLIMITED_FREQUENCY,
    Feature.GRAPH,
    Feature.GRAPH_FULL,
    Feature.GRAPH_SECURITY,
    Feature.GRAPH_EXPORT_NO_WATERMARK,
    Feature.AUDIT,
    Feature.AUDIT_FULL_FINDINGS,
    Feature.AUDIT_FIX,
    Feature.AUDIT_REPORT_EXPORT,
    Feature.CLONE_GENERATE,
    Feature.CLONE_DOWNLOAD,
    Feature.CLONE_FULL_PREVIEW,
    Feature.SNAPSHOT,
    Feature.SNAPSHOT_DIFF,
    Feature.DEPS,
    Feature.DEPS_EXPORT,
    Feature.COST,
    Feature.COST_EXPORT,
    Feature.MULTI_ACCOUNT,
    Feature.EXPORT_JSON,
    Feature.EXPORT_HTML,
    Feature.EXPORT_MARKDOWN,
    Feature.EXPORT_TERRAFORM,
    Feature.EXPORT_CSV,
  ],

  // TEAM ($99/mo) - Continuous compliance for your organization
  [Plan.TEAM]: [
    Feature.SCAN,
    Feature.SCAN_UNLIMITED_FREQUENCY,
    Feature.GRAPH,
    Feature.GRAPH_FULL,
    Feature.GRAPH_SECURITY,
    Feature.GRAPH_EXPORT_NO_WATERMARK,
    Feature.AUDIT,
    Feature.AUDIT_FULL_FINDINGS,
    Feature.AUDIT_FIX,
    Feature.AUDIT_REPORT_EXPORT,
    Feature.AUDIT_CI_MODE,
    Feature.CLONE_GENERATE,
    Feature.CLONE_DOWNLOAD,
    Feature.CLONE_FULL_PREVIEW,
    Feature.SNAPSHOT,
    Feature.SNAPSHOT_DIFF,
    Feature.DRIFT,
    Feature.DRIFT_WATCH,
    Feature.DRIFT_ALERTS,
    Feature.DEPS,
    Feature.DEPS_EXPORT,
    Feature.COST,
    Feature.COST_EXPORT,
    Feature.MULTI_ACCOUNT,
    Feature.WEB_DASHBOARD,
    Feature.TEAM_COLLABORATION,
    Feature.COMPLIANCE_CIS,
    Feature.COMPLIANCE_SOC2,
    Feature.EXPORT_JSON,
    Feature.EXPORT_HTML,
    Feature.EXPORT_MARKDOWN,
    Feature.EXPORT_TERRAFORM,
    Feature.EXPORT_CSV,
    Feature.EXPORT_PDF,
  ],

  // SOVEREIGN ($2,500/mo) - Data sovereignty for regulated industries
  [Plan.SOVEREIGN]: Object.values(Feature) as Feature[],
};

// =============================================================================
// Usage Limits by Plan
// =============================================================================

/**
 * Usage limits by plan (per month)
 *
 * v4.0 Philosophy:
 * - SCAN: Unlimited frequency and resources for ALL tiers
 * - GRAPH: Free to view, watermark on export for COMMUNITY
 * - CLONE: Generate all, block DOWNLOAD for COMMUNITY
 * - AUDIT: Scan all, limit VISIBLE findings for COMMUNITY
 */
export const PLAN_LIMITS: Record<Plan, Record<string, number>> = {
  // COMMUNITY TIER ($0/mo) - Unlimited scans, gated exports
  [Plan.COMMUNITY]: {
    scan_count: -1,              // v4.0: UNLIMITED scans
    resources_per_scan: -1,      // v4.0: UNLIMITED resources
    graph_count: -1,
    clone_count: -1,
    clone_preview_lines: 100,    // Limited preview
    clone_download: 0,           // No download
    audit_count: -1,
    audit_visible_findings: 3,   // See 3 findings, upgrade for more
    audit_fix_count: 0,
    snapshot_count: 3,
    snapshot_diff_count: 3,
    drift_count: 0,
    cost_count: -1,              // v4.0: Can VIEW cost
    deps_count: -1,              // v4.0: Can VIEW deps
    aws_accounts: 1,
    machines: 1,
    history_retention_days: 7,
    offline_grace_days: 0,       // Must be online
  },

  // PRO TIER ($29/mo)
  [Plan.PRO]: {
    scan_count: -1,
    resources_per_scan: -1,
    graph_count: -1,
    clone_count: -1,
    clone_preview_lines: -1,
    clone_download: 1,
    audit_count: -1,
    audit_visible_findings: -1,
    audit_fix_count: -1,
    snapshot_count: -1,
    snapshot_diff_count: -1,
    drift_count: 0,              // No drift detection in PRO
    cost_count: -1,
    deps_count: -1,
    aws_accounts: 3,
    machines: 2,
    history_retention_days: 90,
    offline_grace_days: 7,       // 7 days offline grace
  },

  // TEAM TIER ($99/mo)
  [Plan.TEAM]: {
    scan_count: -1,
    resources_per_scan: -1,
    graph_count: -1,
    clone_count: -1,
    clone_preview_lines: -1,
    clone_download: 1,
    audit_count: -1,
    audit_visible_findings: -1,
    audit_fix_count: -1,
    snapshot_count: -1,
    snapshot_diff_count: -1,
    drift_count: -1,
    cost_count: -1,
    deps_count: -1,
    aws_accounts: 10,
    machines: 10,
    team_members: 5,
    history_retention_days: 365,
    offline_grace_days: 14,      // 14 days offline grace
  },

  // SOVEREIGN TIER ($2,500/mo)
  [Plan.SOVEREIGN]: {
    scan_count: -1,
    resources_per_scan: -1,
    graph_count: -1,
    clone_count: -1,
    clone_preview_lines: -1,
    clone_download: 1,
    audit_count: -1,
    audit_visible_findings: -1,
    audit_fix_count: -1,
    snapshot_count: -1,
    snapshot_diff_count: -1,
    drift_count: -1,
    cost_count: -1,
    deps_count: -1,
    aws_accounts: -1,
    machines: -1,
    team_members: -1,
    history_retention_days: -1,
    offline_grace_days: 365,     // 365 days offline grace (air-gap support)
  },
};

// =============================================================================
// Offline Grace Days by Plan
// =============================================================================

/**
 * Offline grace period (days) by plan.
 *
 * When CLI cannot connect to the server:
 * - COMMUNITY: Must be online (0 days)
 * - PRO: 7 days grace
 * - TEAM: 14 days grace
 * - SOVEREIGN: 365 days grace (air-gap deployment support)
 */
export const OFFLINE_GRACE_DAYS: Record<Plan, number> = {
  [Plan.COMMUNITY]: 0,
  [Plan.PRO]: 7,
  [Plan.TEAM]: 14,
  [Plan.SOVEREIGN]: 365,
} as const;

// =============================================================================
// Feature Metadata
// =============================================================================

export interface FeatureMetadata {
  name: string;
  description: string;
  tier: Plan;
  isNew?: boolean;
  isRenamed?: boolean;
  previousName?: string;
}

export const FEATURE_METADATA: Partial<Record<Feature, FeatureMetadata>> = {
  [Feature.SCAN]: {
    name: 'Infrastructure Scan',
    description: 'Scan AWS resources in a region or VPC',
    tier: Plan.COMMUNITY,
  },
  [Feature.GRAPH]: {
    name: 'Graph Visualization',
    description: 'Generate infrastructure dependency graphs',
    tier: Plan.COMMUNITY,
  },
  [Feature.GRAPH_FULL]: {
    name: 'Full Graph Mode',
    description: 'Show all resources without simplification (--all)',
    tier: Plan.PRO,
  },
  [Feature.GRAPH_SECURITY]: {
    name: 'Security Graph Mode',
    description: 'Security-focused view with SG rules (--security)',
    tier: Plan.PRO,
  },
  [Feature.CLONE_GENERATE]: {
    name: 'Infrastructure Cloning',
    description: 'Generate Terraform code to clone infrastructure',
    tier: Plan.COMMUNITY,
  },
  [Feature.CLONE_DOWNLOAD]: {
    name: 'Clone Download',
    description: 'Download generated Terraform code',
    tier: Plan.PRO,
  },
  [Feature.AUDIT]: {
    name: 'Security Audit',
    description: 'Scan for security misconfigurations',
    tier: Plan.COMMUNITY,
  },
  [Feature.AUDIT_FIX]: {
    name: 'Audit Remediation',
    description: 'Auto-generate Terraform code to fix issues (--fix)',
    tier: Plan.PRO,
  },
  [Feature.AUDIT_CI_MODE]: {
    name: 'Audit CI Mode',
    description: 'Use --fail-on-high in CI/CD pipelines',
    tier: Plan.TEAM,
  },
  [Feature.DRIFT]: {
    name: 'Drift Detection',
    description: 'Compare AWS state vs Terraform state',
    tier: Plan.TEAM,
  },
  [Feature.DRIFT_WATCH]: {
    name: 'Drift Watch Mode',
    description: 'Continuous drift monitoring',
    tier: Plan.TEAM,
  },
  [Feature.DRIFT_ALERTS]: {
    name: 'Drift Alerts',
    description: 'Slack/Teams/Webhook notifications for drift',
    tier: Plan.TEAM,
  },
  [Feature.SNAPSHOT]: {
    name: 'Infrastructure Snapshot',
    description: 'Save infrastructure state for comparison',
    tier: Plan.COMMUNITY,
  },
  [Feature.SNAPSHOT_DIFF]: {
    name: 'Snapshot Comparison',
    description: 'Compare snapshots to detect changes over time',
    tier: Plan.COMMUNITY,
  },
  [Feature.DEPS]: {
    name: 'Dependency Explorer',
    description: 'Explore resource dependencies and blast radius',
    tier: Plan.COMMUNITY,  // v4.0: VIEW is free
  },
  [Feature.DEPS_EXPORT]: {
    name: 'Dependency Export',
    description: 'Export dependency analysis reports',
    tier: Plan.PRO,
  },
  [Feature.COST]: {
    name: 'Cost Estimation',
    description: 'Estimate infrastructure costs',
    tier: Plan.COMMUNITY,  // v4.0: VIEW is free
  },
  [Feature.COST_EXPORT]: {
    name: 'Cost Export',
    description: 'Export cost estimation reports',
    tier: Plan.PRO,
  },
  [Feature.EXPORT_JSON]: {
    name: 'JSON Export',
    description: 'Export data as JSON',
    tier: Plan.COMMUNITY,
  },
  [Feature.EXPORT_HTML]: {
    name: 'HTML Export',
    description: 'Export reports as HTML',
    tier: Plan.PRO,
  },
  [Feature.EXPORT_MARKDOWN]: {
    name: 'Markdown Export',
    description: 'Export reports as Markdown',
    tier: Plan.PRO,
  },
  [Feature.EXPORT_TERRAFORM]: {
    name: 'Terraform Export',
    description: 'Export as Terraform code',
    tier: Plan.PRO,
  },
  [Feature.EXPORT_CSV]: {
    name: 'CSV Export',
    description: 'Export data as CSV for spreadsheets',
    tier: Plan.PRO,
  },
  [Feature.EXPORT_PDF]: {
    name: 'PDF Export',
    description: 'Export reports as PDF',
    tier: Plan.TEAM,
  },
  [Feature.COMPLIANCE_CIS]: {
    name: 'CIS Benchmark',
    description: 'CIS Benchmark compliance reports',
    tier: Plan.TEAM,
  },
  [Feature.COMPLIANCE_SOC2]: {
    name: 'SOC2 Compliance',
    description: 'SOC2 compliance mapping',
    tier: Plan.TEAM,
  },
  [Feature.COMPLIANCE_APRA]: {
    name: 'APRA CPS 234',
    description: 'Australian prudential regulation compliance',
    tier: Plan.SOVEREIGN,
  },
  [Feature.COMPLIANCE_DORA]: {
    name: 'DORA Compliance',
    description: 'EU Digital Operational Resilience Act',
    tier: Plan.SOVEREIGN,
  },
  [Feature.COMPLIANCE_ESSENTIAL8]: {
    name: 'Essential Eight',
    description: 'Australian Cyber Security Centre maturity assessment',
    tier: Plan.SOVEREIGN,
  },
  [Feature.COMPLIANCE_CUSTOM]: {
    name: 'Custom Compliance',
    description: 'Create custom compliance frameworks',
    tier: Plan.SOVEREIGN,
  },
  [Feature.SSO]: {
    name: 'Single Sign-On',
    description: 'SAML/OIDC integration',
    tier: Plan.SOVEREIGN,
  },
  [Feature.REPORT_SIGNATURE]: {
    name: 'Signed Reports',
    description: 'SHA256 digital signatures for audit evidence',
    tier: Plan.SOVEREIGN,
  },
  [Feature.TAMPER_EVIDENT_AUDIT]: {
    name: 'Tamper-Evident Audit',
    description: 'Immutable audit trail for compliance',
    tier: Plan.SOVEREIGN,
  },
  [Feature.AIR_GAP_DEPLOYMENT]: {
    name: 'Air-Gap Deployment',
    description: 'Deploy in isolated networks with zero external connections',
    tier: Plan.SOVEREIGN,
  },
  [Feature.WHITE_LABELING]: {
    name: 'White-Labeling',
    description: 'Remove RepliMap branding for client deliverables',
    tier: Plan.SOVEREIGN,
  },
  [Feature.DEDICATED_SUPPORT]: {
    name: 'Dedicated Support',
    description: 'Named account manager',
    tier: Plan.SOVEREIGN,
  },
};

// =============================================================================
// Helper Functions
// =============================================================================

/**
 * Check if a plan has access to a feature
 */
export function planHasFeature(plan: Plan, feature: Feature): boolean {
  const features = PLAN_FEATURES[plan];
  return features?.includes(feature) ?? false;
}

/**
 * Get the minimum required plan for a feature
 */
export function getRequiredPlan(feature: Feature): Plan {
  const metadata = FEATURE_METADATA[feature];
  return metadata?.tier ?? Plan.SOVEREIGN;
}

/**
 * Get usage limit for a plan and limit key
 */
export function getLimit(plan: Plan, limitKey: string): number {
  const limits = PLAN_LIMITS[plan];
  return limits?.[limitKey] ?? 0;
}

/**
 * Check if a limit is unlimited (-1)
 */
export function isUnlimited(limit: number): boolean {
  return limit === -1;
}

/**
 * Normalize a plan name to a valid v4.0 plan type
 */
export function normalizePlan(plan: string): Plan {
  const lower = plan.toLowerCase();

  if (Object.values(Plan).includes(lower as Plan)) {
    return lower as Plan;
  }

  return Plan.COMMUNITY; // Default to community for unknown plans
}

/**
 * Get all new features
 */
export function getNewFeatures(): Feature[] {
  return Object.entries(FEATURE_METADATA)
    .filter(([, meta]) => meta?.isNew)
    .map(([key]) => key as Feature);
}

/**
 * Get all renamed features
 */
export function getRenamedFeatures(): Feature[] {
  return Object.entries(FEATURE_METADATA)
    .filter(([, meta]) => meta?.isRenamed)
    .map(([key]) => key as Feature);
}

/**
 * Feature flags interface for API responses
 */
export interface FeatureFlagsType {
  audit_fix: boolean;
  snapshot: boolean;
  snapshot_diff: boolean;
  deps: boolean;
  graph_full: boolean;
  graph_security: boolean;
  drift: boolean;
  drift_watch: boolean;
  drift_alerts: boolean;
  cost: boolean;
  clone_download: boolean;
  audit_ci_mode: boolean;
  export_terraform: boolean;
  export_csv: boolean;
  export_pdf: boolean;
  compliance_cis: boolean;
  compliance_soc2: boolean;
  compliance_apra: boolean;
  compliance_dora: boolean;
  sso: boolean;
  report_signature: boolean;
  air_gap: boolean;
  white_labeling: boolean;
}

/**
 * Get feature flags for a plan (for API responses)
 */
export function getFeatureFlags(plan: Plan): FeatureFlagsType {
  const features = PLAN_FEATURES[plan] ?? [];
  return {
    audit_fix: features.includes(Feature.AUDIT_FIX),
    snapshot: features.includes(Feature.SNAPSHOT),
    snapshot_diff: features.includes(Feature.SNAPSHOT_DIFF),
    deps: features.includes(Feature.DEPS),
    graph_full: features.includes(Feature.GRAPH_FULL),
    graph_security: features.includes(Feature.GRAPH_SECURITY),
    drift: features.includes(Feature.DRIFT),
    drift_watch: features.includes(Feature.DRIFT_WATCH),
    drift_alerts: features.includes(Feature.DRIFT_ALERTS),
    cost: features.includes(Feature.COST),
    clone_download: features.includes(Feature.CLONE_DOWNLOAD),
    audit_ci_mode: features.includes(Feature.AUDIT_CI_MODE),
    export_terraform: features.includes(Feature.EXPORT_TERRAFORM),
    export_csv: features.includes(Feature.EXPORT_CSV),
    export_pdf: features.includes(Feature.EXPORT_PDF),
    compliance_cis: features.includes(Feature.COMPLIANCE_CIS),
    compliance_soc2: features.includes(Feature.COMPLIANCE_SOC2),
    compliance_apra: features.includes(Feature.COMPLIANCE_APRA),
    compliance_dora: features.includes(Feature.COMPLIANCE_DORA),
    sso: features.includes(Feature.SSO),
    report_signature: features.includes(Feature.REPORT_SIGNATURE),
    air_gap: features.includes(Feature.AIR_GAP_DEPLOYMENT),
    white_labeling: features.includes(Feature.WHITE_LABELING),
  };
}

// =============================================================================
// License Blob Helpers
// =============================================================================

/**
 * Build SecureLicenseLimits for license blob signing.
 * Maps plan limits to the structure expected by CLI.
 */
export function buildSecureLicenseLimits(plan: Plan): SecureLicenseLimits {
  const limits = PLAN_LIMITS[plan] ?? PLAN_LIMITS[Plan.COMMUNITY];

  return {
    max_accounts: limits.aws_accounts ?? 1,
    max_regions: -1, // Unlimited
    max_resources_per_scan: limits.resources_per_scan ?? -1,
    max_concurrent_scans: 1,
    max_scans_per_day: limits.scan_count === -1 ? -1 : Math.ceil((limits.scan_count ?? 3) / 30),
    offline_grace_days: limits.offline_grace_days ?? 0,
  };
}

/**
 * Get enabled features as string array for license blob.
 */
export function getEnabledFeatures(plan: Plan): string[] {
  return (PLAN_FEATURES[plan] ?? []).map((f) => f.toString());
}

// =============================================================================
// Plan Comparison
// =============================================================================

export const PLAN_RANK: Record<Plan, number> = {
  [Plan.COMMUNITY]: 0,
  [Plan.PRO]: 1,
  [Plan.TEAM]: 2,
  [Plan.SOVEREIGN]: 3,
};

export function isPlanUpgrade(from: string, to: string): boolean {
  const fromPlan = normalizePlan(from);
  const toPlan = normalizePlan(to);
  return PLAN_RANK[toPlan] > PLAN_RANK[fromPlan];
}

export function isPlanDowngrade(from: string, to: string): boolean {
  const fromPlan = normalizePlan(from);
  const toPlan = normalizePlan(to);
  return PLAN_RANK[toPlan] < PLAN_RANK[fromPlan];
}

export function getUpgradePath(currentPlan: Plan): Plan | null {
  const upgradePaths: Record<Plan, Plan | null> = {
    [Plan.COMMUNITY]: Plan.PRO,
    [Plan.PRO]: Plan.TEAM,
    [Plan.TEAM]: Plan.SOVEREIGN,
    [Plan.SOVEREIGN]: null,
  };
  return upgradePaths[currentPlan];
}
