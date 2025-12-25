/**
 * RepliMap Feature Definitions
 *
 * Updated to include new features:
 * - deps (formerly blast)
 * - snapshot
 * - audit_fix (remediation generator)
 * - graph modes (full, security)
 */

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

  // Advanced analysis (PRO+/TEAM+)
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
}

export enum Plan {
  FREE = 'free',
  SOLO = 'solo',
  PRO = 'pro',
  TEAM = 'team',
  ENTERPRISE = 'enterprise',
}

// =============================================================================
// Feature Access Matrix by Plan
// =============================================================================

/**
 * Feature access matrix by plan
 *
 * Aligned with replimap-plan-feature-gate-prompt.md
 *
 * Key decisions for NEW features:
 * - AUDIT_FIX: SOLO+ (enhances audit, key Solo differentiator)
 * - SNAPSHOT: SOLO+ (alternative to drift for non-TF users)
 * - DEPS: TEAM+ (same as original BLAST - high-value feature)
 * - GRAPH_FULL/SECURITY: SOLO+ (premium graph modes)
 */
export const PLAN_FEATURES: Record<Plan, Feature[]> = {
  // FREE ($0/mo) - Experience value, limit output
  [Plan.FREE]: [
    Feature.SCAN,
    Feature.GRAPH,
    Feature.AUDIT,
    Feature.CLONE_GENERATE,
    Feature.EXPORT_JSON,
    Feature.SNAPSHOT,
    Feature.SNAPSHOT_DIFF,
  ],

  // SOLO ($29/mo, $199/year) - Full individual access
  [Plan.SOLO]: [
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
    Feature.EXPORT_JSON,
    Feature.EXPORT_HTML,
    Feature.EXPORT_MARKDOWN,
    Feature.EXPORT_TERRAFORM,
  ],

  // PRO ($79/mo, $599/year) - CI/CD and advanced analysis
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
    Feature.AUDIT_CI_MODE,
    Feature.CLONE_GENERATE,
    Feature.CLONE_DOWNLOAD,
    Feature.CLONE_FULL_PREVIEW,
    Feature.SNAPSHOT,
    Feature.SNAPSHOT_DIFF,
    Feature.DRIFT,
    Feature.COST,
    Feature.MULTI_ACCOUNT,
    Feature.EXPORT_JSON,
    Feature.EXPORT_HTML,
    Feature.EXPORT_MARKDOWN,
    Feature.EXPORT_TERRAFORM,
  ],

  // TEAM ($149/mo, $1,199/year) - Full platform
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
    Feature.COST,
    Feature.COST_EXPORT,
    Feature.MULTI_ACCOUNT,
    Feature.DEPS,
    Feature.DEPS_EXPORT,
    Feature.WEB_DASHBOARD,
    Feature.TEAM_COLLABORATION,
    Feature.EXPORT_JSON,
    Feature.EXPORT_HTML,
    Feature.EXPORT_MARKDOWN,
    Feature.EXPORT_TERRAFORM,
  ],

  // ENTERPRISE ($399/mo, $3,999/year) - Everything
  [Plan.ENTERPRISE]: Object.values(Feature) as Feature[],
};

// =============================================================================
// Usage Limits by Plan
// =============================================================================

/**
 * Usage limits by plan (per month)
 *
 * Core Philosophy:
 * - SCAN: Unlimited resources, limit FREQUENCY only (not resource count!)
 * - GRAPH: Free to view, watermark on export for FREE
 * - CLONE: Generate all, block DOWNLOAD for FREE
 * - AUDIT: Scan all, limit VISIBLE findings for FREE
 * - DRIFT: PRO+ feature (not in FREE or SOLO!)
 * - COST: PRO+ feature
 * - DEPS/BLAST: TEAM+ feature
 */
export const PLAN_LIMITS: Record<Plan, Record<string, number>> = {
  // FREE TIER ($0/mo)
  [Plan.FREE]: {
    scan_count: 3,
    resources_per_scan: -1,
    graph_count: -1,
    clone_count: -1,
    clone_preview_lines: 100,
    clone_download: 0,
    audit_count: -1,
    audit_visible_findings: 3,
    audit_fix_count: 0,
    snapshot_count: 1,
    snapshot_diff_count: 1,
    drift_count: 0,
    cost_count: 0,
    deps_count: 0,
    aws_accounts: 1,
    machines: 1,
  },

  // SOLO TIER ($29/mo, $199/year)
  [Plan.SOLO]: {
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
    drift_count: 0,
    cost_count: 0,
    deps_count: 0,
    aws_accounts: 1,
    machines: 2,
  },

  // PRO TIER ($79/mo, $599/year)
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
    drift_count: -1,
    cost_count: -1,
    deps_count: 0,
    aws_accounts: 3,
    machines: 3,
  },

  // TEAM TIER ($149/mo, $1,199/year)
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
  },

  // ENTERPRISE TIER ($399/mo, $3,999/year)
  [Plan.ENTERPRISE]: {
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
  },
};

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
    tier: Plan.FREE,
  },
  [Feature.GRAPH]: {
    name: 'Graph Visualization',
    description: 'Generate infrastructure dependency graphs',
    tier: Plan.FREE,
  },
  [Feature.GRAPH_FULL]: {
    name: 'Full Graph Mode',
    description: 'Show all resources without simplification (--all)',
    tier: Plan.SOLO,
    isNew: true,
  },
  [Feature.GRAPH_SECURITY]: {
    name: 'Security Graph Mode',
    description: 'Security-focused view with SG rules (--security)',
    tier: Plan.SOLO,
    isNew: true,
  },
  [Feature.CLONE_GENERATE]: {
    name: 'Infrastructure Cloning',
    description: 'Generate Terraform code to clone infrastructure',
    tier: Plan.FREE,
  },
  [Feature.CLONE_DOWNLOAD]: {
    name: 'Clone Download',
    description: 'Download generated Terraform code',
    tier: Plan.SOLO,
  },
  [Feature.AUDIT]: {
    name: 'Security Audit',
    description: 'Scan for security misconfigurations',
    tier: Plan.FREE,
  },
  [Feature.AUDIT_FIX]: {
    name: 'Audit Remediation',
    description: 'Auto-generate Terraform code to fix issues (--fix)',
    tier: Plan.SOLO,
    isNew: true,
  },
  [Feature.AUDIT_CI_MODE]: {
    name: 'Audit CI Mode',
    description: 'Use --fail-on-high in CI/CD pipelines',
    tier: Plan.PRO,
  },
  [Feature.DRIFT]: {
    name: 'Drift Detection',
    description: 'Compare AWS state vs Terraform state',
    tier: Plan.PRO,
  },
  [Feature.DRIFT_WATCH]: {
    name: 'Drift Watch Mode',
    description: 'Continuous drift monitoring with alerts',
    tier: Plan.TEAM,
  },
  [Feature.SNAPSHOT]: {
    name: 'Infrastructure Snapshot',
    description: 'Save infrastructure state for comparison (no Terraform needed)',
    tier: Plan.SOLO,
    isNew: true,
  },
  [Feature.SNAPSHOT_DIFF]: {
    name: 'Snapshot Comparison',
    description: 'Compare snapshots to detect changes over time',
    tier: Plan.SOLO,
    isNew: true,
  },
  [Feature.DEPS]: {
    name: 'Dependency Explorer',
    description: 'Explore resource dependencies and potential impact of changes',
    tier: Plan.TEAM,
    isRenamed: true,
    previousName: 'Blast Radius Analyzer',
  },
  [Feature.DEPS_EXPORT]: {
    name: 'Dependency Export',
    description: 'Export dependency analysis reports',
    tier: Plan.TEAM,
    isRenamed: true,
    previousName: 'Blast Radius Export',
  },
  [Feature.COST]: {
    name: 'Cost Estimation',
    description: 'Estimate infrastructure costs (±20% accuracy)',
    tier: Plan.PRO,
  },
  [Feature.COST_EXPORT]: {
    name: 'Cost Export',
    description: 'Export cost estimation reports',
    tier: Plan.TEAM,
  },
  [Feature.EXPORT_JSON]: {
    name: 'JSON Export',
    description: 'Export data as JSON',
    tier: Plan.FREE,
  },
  [Feature.EXPORT_HTML]: {
    name: 'HTML Export',
    description: 'Export reports as HTML',
    tier: Plan.SOLO,
  },
  [Feature.EXPORT_MARKDOWN]: {
    name: 'Markdown Export',
    description: 'Export reports as Markdown',
    tier: Plan.SOLO,
  },
  [Feature.EXPORT_TERRAFORM]: {
    name: 'Terraform Export',
    description: 'Export as Terraform code',
    tier: Plan.SOLO,
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
  return metadata?.tier ?? Plan.ENTERPRISE;
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
  cost: boolean;
  clone_download: boolean;
  audit_ci_mode: boolean;
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
    cost: features.includes(Feature.COST),
    clone_download: features.includes(Feature.CLONE_DOWNLOAD),
    audit_ci_mode: features.includes(Feature.AUDIT_CI_MODE),
  };
}
