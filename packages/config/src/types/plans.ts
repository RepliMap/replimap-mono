/**
 * RepliMap v4.0 Plan Type Definitions
 * Philosophy: "Gate Output, Not Input"
 *
 * Key principle: Let users see everything, charge when they want to take it away.
 */

// =============================================================================
// Core Types
// =============================================================================

export type PlanId = 'community' | 'pro' | 'team' | 'sovereign';
export type BillingCycle = 'monthly' | 'yearly' | 'lifetime';
export type ExportFormat = 'json' | 'terraform' | 'csv' | 'pdf' | 'html' | 'markdown';

// =============================================================================
// Plan Configuration
// =============================================================================

export interface PlanPricing {
  /** Price in cents per month */
  monthly: number;
  /** Price in cents per year */
  yearly: number;
  /** One-time lifetime price in cents (null if not available) */
  lifetime: number | null;
  /** Stripe price ID for monthly billing */
  stripeMonthly: string | null;
  /** Stripe price ID for yearly billing */
  stripeYearly: string | null;
  /** Stripe price ID for lifetime purchase */
  stripeLifetime: string | null;
}

export interface PlanLimits {
  /** Scans per month (-1 = unlimited) */
  scansPerMonth: number;
  /** Resources per scan (-1 = unlimited) */
  resourcesPerScan: number;
  /** Maximum AWS accounts */
  awsAccounts: number;
  /** Maximum team members */
  teamMembers: number;
  /** History retention in days (-1 = unlimited) */
  historyRetentionDays: number;
  /** Maximum machines that can be activated */
  machines: number;
}

export interface PlanFeatures {
  // ══════════════════════════════════════════════════════════════════════════
  // VIEW (INPUT) - Mostly all true - Let users see full value
  // ══════════════════════════════════════════════════════════════════════════
  basicScanning: boolean;
  dependencyGraph: boolean;
  costAnalysis: boolean;
  complianceView: boolean;
  securityScore: boolean;

  // ══════════════════════════════════════════════════════════════════════════
  // EXPORT (OUTPUT) - Core monetization layer
  // ══════════════════════════════════════════════════════════════════════════
  exportJson: boolean;
  /** Include upgrade prompts in JSON export for free users */
  exportJsonMetadata: boolean;
  exportTerraform: boolean;
  exportCsv: boolean;
  exportPdf: boolean;
  exportHtml: boolean;
  exportMarkdown: boolean;
  /** true = has watermark on exports */
  graphExportWatermark: boolean;

  // ══════════════════════════════════════════════════════════════════════════
  // GRAPH MODES
  // ══════════════════════════════════════════════════════════════════════════
  graphFull: boolean;
  graphSecurity: boolean;

  // ══════════════════════════════════════════════════════════════════════════
  // AUDIT FEATURES
  // ══════════════════════════════════════════════════════════════════════════
  auditFullFindings: boolean;
  auditFix: boolean;
  auditReportExport: boolean;
  auditCiMode: boolean;

  // ══════════════════════════════════════════════════════════════════════════
  // COMPLIANCE - Tiered unlocking
  // ══════════════════════════════════════════════════════════════════════════
  complianceReportsCis: boolean;
  complianceReportsSoc2: boolean;
  complianceReportsApra: boolean;
  complianceReportsDora: boolean;
  complianceReportsEssential8: boolean;
  customComplianceMapping: boolean;

  // ══════════════════════════════════════════════════════════════════════════
  // AUTOMATION
  // ══════════════════════════════════════════════════════════════════════════
  apiAccess: boolean;
  customRules: boolean;
  driftDetection: boolean;
  driftWatch: boolean;
  cicdIntegration: boolean;

  // ══════════════════════════════════════════════════════════════════════════
  // ADVANCED ANALYSIS
  // ══════════════════════════════════════════════════════════════════════════
  deps: boolean;
  depsExport: boolean;
  cost: boolean;
  costExport: boolean;
  snapshot: boolean;
  snapshotDiff: boolean;

  // ══════════════════════════════════════════════════════════════════════════
  // TEAM COLLABORATION - TEAM differentiator
  // ══════════════════════════════════════════════════════════════════════════
  driftAlertsSlack: boolean;
  driftAlertsTeams: boolean;
  driftAlertsWebhook: boolean;
  multiAccount: boolean;
  teamCollaboration: boolean;

  // ══════════════════════════════════════════════════════════════════════════
  // ENTERPRISE SECURITY - SOVEREIGN exclusive
  // ══════════════════════════════════════════════════════════════════════════
  sso: boolean;
  dedicatedSupport: boolean;
  airGapDeployment: boolean;
  /** SHA256 signed reports */
  reportSignature: boolean;
  tamperEvidentAuditTrail: boolean;
  whiteLabeling: boolean;

  // ══════════════════════════════════════════════════════════════════════════
  // SUPPORT
  // ══════════════════════════════════════════════════════════════════════════
  prioritySupport: boolean;
  /** SLA response time in hours (null = no SLA) */
  supportSlaHours: number | null;
}

export interface PlanUI {
  /** Call-to-action button text */
  cta: string;
  /** Badge to display (e.g., "Most Popular") */
  badge: string | null;
  /** Whether to visually highlight this plan */
  highlight: boolean;
}

export interface PlanAddOn {
  id: string;
  name: string;
  description: string;
  /** Price in cents per month */
  priceMonthly: number;
}

export interface PlanConfig {
  id: PlanId;
  name: string;
  tagline: string;
  description: string;
  pricing: PlanPricing;
  limits: PlanLimits;
  features: PlanFeatures;
  ui: PlanUI;
  addOns?: PlanAddOn[];
}

// =============================================================================
// Legacy Plan Migration
// =============================================================================

/** Maps old plan names to new v4.0 plan IDs */
export const LEGACY_PLAN_MIGRATIONS: Record<string, PlanId> = {
  free: 'community',
  solo: 'pro',      // Solo users get upgraded to PRO
  enterprise: 'sovereign',
} as const;

/** Old plan names that need migration */
export const LEGACY_PLAN_NAMES = ['free', 'solo', 'enterprise'] as const;
export type LegacyPlanName = typeof LEGACY_PLAN_NAMES[number];

// =============================================================================
// Upgrade Prompts
// =============================================================================

export interface UpgradePrompt {
  id: string;
  title: string;
  message: string;
  currentPlan: PlanId;
  requiredPlan: PlanId;
  price: string;
  cta: string;
  ctaUrl: string;
  benefits: string[];
}

// =============================================================================
// JSON Export Metadata
// =============================================================================

export interface JsonExportMetadata {
  generator: string;
  version: string;
  planId: string;
  exportedAt: string;
  upgradeUrl: string;
  upgradeNote: string;
  features: {
    available: string[];
    locked: string[];
  };
}
