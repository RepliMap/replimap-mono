#!/usr/bin/env tsx
/**
 * Code generation script for @replimap/config v4.0
 *
 * Reads JSON source files and generates:
 * - dist/index.ts (TypeScript exports)
 * - dist/config.py (Python dataclasses)
 *
 * Philosophy: "Gate Output, Not Input"
 *
 * Usage:
 *   pnpm build        # Generate files
 *   pnpm check        # Verify generated files are up to date
 */

import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { createHash } from "node:crypto";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const ROOT = join(__dirname, "..");
const SRC_DIR = join(ROOT, "src");
const DIST_DIR = join(ROOT, "dist");

// =============================================================================
// Type Definitions for v4.0 Plans
// =============================================================================

interface PlanUI {
  cta: string;
  badge: string | null;
  highlight: boolean;
}

interface PlanAddOn {
  name: string;
  description: string;
  price_monthly: number;
}

interface PlanConfigV4 {
  name: string;
  tagline: string;
  description: string;
  price_monthly: number;
  price_yearly: number;
  price_lifetime: number | null;
  scans_per_month: number | null;
  resources_per_scan: number | null;
  aws_accounts: number | null;
  team_members: number | null;
  machines: number | null;
  history_retention_days: number | null;
  features: string[];
  ui: PlanUI;
  addons?: Record<string, PlanAddOn>;
}

interface PlansV4 {
  [key: string]: PlanConfigV4;
}

interface Framework {
  name: string;
  region: string;
  description: string;
  controls_count: number;
}

interface Frameworks {
  compliance_frameworks: Record<string, Framework>;
}

interface Resources {
  aws_resources: Record<string, string[]>;
}

function computeContentHash(content: string): string {
  return createHash("sha256").update(content).digest("hex").slice(0, 12);
}

function loadJsonFiles(): {
  plans: PlansV4;
  frameworks: Frameworks;
  resources: Resources;
  combinedHash: string;
} {
  const plansContent = readFileSync(join(SRC_DIR, "plans.json"), "utf-8");
  const frameworksContent = readFileSync(
    join(SRC_DIR, "frameworks.json"),
    "utf-8"
  );
  const resourcesContent = readFileSync(
    join(SRC_DIR, "resources.json"),
    "utf-8"
  );

  const plans = JSON.parse(plansContent) as PlansV4;
  const frameworks = JSON.parse(frameworksContent) as Frameworks;
  const resources = JSON.parse(resourcesContent) as Resources;

  // Compute hash from all source content
  const combinedContent = plansContent + frameworksContent + resourcesContent;
  const combinedHash = computeContentHash(combinedContent);

  return { plans, frameworks, resources, combinedHash };
}

function generateTypeScript(
  plans: PlansV4,
  frameworks: Frameworks,
  resources: Resources,
  hash: string
): string {
  const planNames = Object.keys(plans);
  const frameworkIds = Object.keys(frameworks.compliance_frameworks);
  const resourceCategories = Object.keys(resources.aws_resources);

  // Collect all unique features from all plans
  const allFeatures = new Set<string>();
  for (const plan of Object.values(plans)) {
    for (const feature of plan.features) {
      if (feature !== "*" && !feature.startsWith("!")) {
        allFeatures.add(feature);
      }
    }
  }

  return `/**
 * @replimap/config v4.0 - Auto-generated configuration
 * DO NOT EDIT - This file is generated from src/*.json
 *
 * Philosophy: "Gate Output, Not Input"
 * - Unlimited scans for all tiers
 * - Charge when users export/download
 *
 * Content Hash: ${hash}
 */

// =============================================================================
// Version
// =============================================================================

export const CONFIG_VERSION = "${hash}" as const;

// =============================================================================
// Plan Types
// =============================================================================

export const PLAN_NAMES = [${planNames.map((n) => `"${n}"`).join(", ")}] as const;
export type PlanName = typeof PLAN_NAMES[number];

/** Legacy plan names that map to v4.0 plans */
export const LEGACY_PLAN_MIGRATIONS: Record<string, PlanName> = {
  free: "community",
  solo: "pro",
  enterprise: "sovereign",
} as const;

export type LegacyPlanName = "free" | "solo" | "enterprise";

export interface PlanUI {
  cta: string;
  badge: string | null;
  highlight: boolean;
}

export interface PlanAddOn {
  name: string;
  description: string;
  /** Price in cents per month */
  price_monthly: number;
}

export interface PlanConfig {
  name: string;
  tagline: string;
  description: string;
  /** Price in cents per month */
  price_monthly: number;
  /** Price in cents per year */
  price_yearly: number;
  /** Price in cents for lifetime (null if not available) */
  price_lifetime: number | null;
  /** Scans per month (null = unlimited) */
  scans_per_month: number | null;
  /** Resources per scan (null = unlimited) */
  resources_per_scan: number | null;
  /** Maximum AWS accounts (null = unlimited) */
  aws_accounts: number | null;
  /** Maximum team members (null = unlimited) */
  team_members: number | null;
  /** Maximum machines (null = unlimited) */
  machines: number | null;
  /** History retention in days (null = unlimited) */
  history_retention_days: number | null;
  /** Feature flags - "*" means all features, "!feature" means excluded */
  features: string[];
  ui: PlanUI;
  addons?: Record<string, PlanAddOn>;
}

export const PLANS: Record<PlanName, PlanConfig> = ${JSON.stringify(plans, null, 2)} as const;

// =============================================================================
// Features
// =============================================================================

export const ALL_FEATURES = [
${Array.from(allFeatures)
  .sort()
  .map((f) => `  "${f}"`)
  .join(",\n")}
] as const;

export type FeatureName = typeof ALL_FEATURES[number];

// =============================================================================
// Compliance Frameworks
// =============================================================================

export const FRAMEWORK_IDS = [${frameworkIds.map((id) => `"${id}"`).join(", ")}] as const;
export type FrameworkId = typeof FRAMEWORK_IDS[number];

export interface FrameworkConfig {
  name: string;
  region: string;
  description: string;
  controls_count: number;
}

export const COMPLIANCE_FRAMEWORKS: Record<FrameworkId, FrameworkConfig> = ${JSON.stringify(frameworks.compliance_frameworks, null, 2)} as const;

// =============================================================================
// AWS Resources
// =============================================================================

export const RESOURCE_CATEGORIES = [${resourceCategories.map((c) => `"${c}"`).join(", ")}] as const;
export type ResourceCategory = typeof RESOURCE_CATEGORIES[number];

export const AWS_RESOURCES: Record<ResourceCategory, readonly string[]> = ${JSON.stringify(resources.aws_resources, null, 2)} as const;

export const ALL_AWS_RESOURCES = [
${Object.values(resources.aws_resources)
  .flat()
  .map((r) => `  "${r}"`)
  .join(",\n")}
] as const;

export type AwsResourceType = typeof ALL_AWS_RESOURCES[number];

// =============================================================================
// Helper Functions
// =============================================================================

export function isPlanName(value: string): value is PlanName {
  return PLAN_NAMES.includes(value as PlanName);
}

export function isLegacyPlanName(value: string): value is LegacyPlanName {
  return value in LEGACY_PLAN_MIGRATIONS;
}

/**
 * Normalize a plan name, converting legacy names to v4.0 names
 */
export function normalizePlanName(value: string): PlanName {
  if (isPlanName(value)) return value;
  if (isLegacyPlanName(value)) return LEGACY_PLAN_MIGRATIONS[value];
  return "community"; // Default to community for unknown plans
}

export function isFrameworkId(value: string): value is FrameworkId {
  return FRAMEWORK_IDS.includes(value as FrameworkId);
}

export function isAwsResourceType(value: string): value is AwsResourceType {
  return ALL_AWS_RESOURCES.includes(value as AwsResourceType);
}

/**
 * Check if a plan has a specific feature
 */
export function planHasFeature(plan: PlanName, feature: string): boolean {
  const config = PLANS[plan];

  // Check for "*" (all features)
  if (config.features.includes("*")) {
    // Check if explicitly excluded
    return !config.features.includes(\`!\${feature}\`);
  }

  return config.features.includes(feature);
}

/**
 * Get all features for a plan (resolving "*" and "!" modifiers)
 */
export function getPlanFeatures(plan: PlanName): string[] {
  const config = PLANS[plan];

  if (config.features.includes("*")) {
    // All features except excluded ones
    const excluded = config.features
      .filter(f => f.startsWith("!"))
      .map(f => f.slice(1));
    return ALL_FEATURES.filter(f => !excluded.includes(f));
  }

  return config.features.filter(f => !f.startsWith("!"));
}

/**
 * Check if a limit is unlimited (null or -1)
 */
export function isUnlimited(value: number | null): boolean {
  return value === null || value === -1;
}

/**
 * Format a limit for display
 */
export function formatLimit(value: number | null): string {
  if (isUnlimited(value)) return "Unlimited";
  return value!.toLocaleString();
}

/**
 * Format price in dollars from cents
 */
export function formatPrice(cents: number): string {
  if (cents === 0) return "Free";
  return \`$\${(cents / 100).toLocaleString()}\`;
}

/**
 * Get the minimum plan required for a feature
 */
export function getRequiredPlanForFeature(feature: string): PlanName {
  for (const planName of PLAN_NAMES) {
    if (planHasFeature(planName, feature)) {
      return planName;
    }
  }
  return "sovereign"; // Default to highest tier
}

/**
 * Get upgrade path from current plan
 */
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
// Plan Comparison
// =============================================================================

export const PLAN_RANK: Record<PlanName | LegacyPlanName, number> = {
  // v4.0 plans
  community: 0,
  pro: 1,
  team: 2,
  sovereign: 3,
  // Legacy plans (mapped to their v4.0 equivalents)
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
`;
}

function generatePython(
  plans: PlansV4,
  frameworks: Frameworks,
  resources: Resources,
  hash: string
): string {
  const planNames = Object.keys(plans);
  const frameworkIds = Object.keys(frameworks.compliance_frameworks);
  const resourceCategories = Object.keys(resources.aws_resources);

  // Collect all unique features
  const allFeatures = new Set<string>();
  for (const plan of Object.values(plans)) {
    for (const feature of plan.features) {
      if (feature !== "*" && !feature.startsWith("!")) {
        allFeatures.add(feature);
      }
    }
  }

  const plansDataclass = Object.entries(plans)
    .map(([name, config]) => {
      const addonsStr = config.addons
        ? `{${Object.entries(config.addons)
            .map(
              ([k, v]) =>
                `"${k}": PlanAddOn(name="${v.name}", description="${v.description}", price_monthly=${v.price_monthly})`
            )
            .join(", ")}}`
        : "None";

      const uiStr = `PlanUI(cta="${config.ui.cta}", badge=${config.ui.badge ? `"${config.ui.badge}"` : "None"}, highlight=${config.ui.highlight ? "True" : "False"})`;

      return `    "${name}": PlanConfig(
        name="${config.name}",
        tagline="${config.tagline}",
        description="${config.description.replace(/'/g, "\\'")}",
        price_monthly=${config.price_monthly},
        price_yearly=${config.price_yearly},
        price_lifetime=${config.price_lifetime === null ? "None" : config.price_lifetime},
        scans_per_month=${config.scans_per_month === null ? "None" : config.scans_per_month},
        resources_per_scan=${config.resources_per_scan === null ? "None" : config.resources_per_scan},
        aws_accounts=${config.aws_accounts === null ? "None" : config.aws_accounts},
        team_members=${config.team_members === null ? "None" : config.team_members},
        machines=${config.machines === null ? "None" : config.machines},
        history_retention_days=${config.history_retention_days === null ? "None" : config.history_retention_days},
        features=${JSON.stringify(config.features)},
        ui=${uiStr},
        addons=${addonsStr},
    )`;
    })
    .join(",\n");

  const frameworksDataclass = Object.entries(frameworks.compliance_frameworks)
    .map(
      ([id, config]) => `    "${id}": FrameworkConfig(
        name="${config.name}",
        region="${config.region}",
        description="${config.description}",
        controls_count=${config.controls_count},
    )`
    )
    .join(",\n");

  const resourcesDict = Object.entries(resources.aws_resources)
    .map(([category, types]) => `    "${category}": ${JSON.stringify(types)}`)
    .join(",\n");

  const allResourcesList = Object.values(resources.aws_resources).flat();

  return `"""
@replimap/config v4.0 - Auto-generated configuration
DO NOT EDIT - This file is generated from src/*.json

Philosophy: "Gate Output, Not Input"
- Unlimited scans for all tiers
- Charge when users export/download

Content Hash: ${hash}
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Literal, Optional


# =============================================================================
# Version
# =============================================================================

CONFIG_VERSION: str = "${hash}"


# =============================================================================
# Plan Types
# =============================================================================

PlanName = Literal[${planNames.map((n) => `"${n}"`).join(", ")}]
LegacyPlanName = Literal["free", "solo", "enterprise"]

PLAN_NAMES: tuple[PlanName, ...] = (${planNames.map((n) => `"${n}"`).join(", ")},)

LEGACY_PLAN_MIGRATIONS: dict[LegacyPlanName, PlanName] = {
    "free": "community",
    "solo": "pro",
    "enterprise": "sovereign",
}


@dataclass(frozen=True)
class PlanUI:
    """UI configuration for a plan."""
    cta: str
    badge: Optional[str]
    highlight: bool


@dataclass(frozen=True)
class PlanAddOn:
    """Configuration for a plan add-on."""
    name: str
    description: str
    price_monthly: int  # cents


@dataclass(frozen=True)
class PlanConfig:
    """Configuration for a pricing plan."""
    name: str
    tagline: str
    description: str
    price_monthly: int  # cents
    price_yearly: int  # cents
    price_lifetime: Optional[int]  # cents, None if not available
    scans_per_month: Optional[int]  # None = unlimited
    resources_per_scan: Optional[int]  # None = unlimited
    aws_accounts: Optional[int]  # None = unlimited
    team_members: Optional[int]  # None = unlimited
    machines: Optional[int]  # None = unlimited
    history_retention_days: Optional[int]  # None = unlimited
    features: list[str]
    ui: PlanUI
    addons: Optional[dict[str, PlanAddOn]] = None


PLANS: dict[PlanName, PlanConfig] = {
${plansDataclass},
}


# =============================================================================
# Features
# =============================================================================

ALL_FEATURES: tuple[str, ...] = (
${Array.from(allFeatures)
  .sort()
  .map((f) => `    "${f}"`)
  .join(",\n")},
)

FeatureName = Literal[${Array.from(allFeatures)
    .sort()
    .map((f) => `"${f}"`)
    .join(", ")}]


# =============================================================================
# Compliance Frameworks
# =============================================================================

FrameworkId = Literal[${frameworkIds.map((id) => `"${id}"`).join(", ")}]

FRAMEWORK_IDS: tuple[FrameworkId, ...] = (${frameworkIds.map((id) => `"${id}"`).join(", ")},)


@dataclass(frozen=True)
class FrameworkConfig:
    """Configuration for a compliance framework."""
    name: str
    region: str
    description: str
    controls_count: int


COMPLIANCE_FRAMEWORKS: dict[FrameworkId, FrameworkConfig] = {
${frameworksDataclass},
}


# =============================================================================
# AWS Resources
# =============================================================================

ResourceCategory = Literal[${resourceCategories.map((c) => `"${c}"`).join(", ")}]

RESOURCE_CATEGORIES: tuple[ResourceCategory, ...] = (${resourceCategories.map((c) => `"${c}"`).join(", ")},)

AWS_RESOURCES: dict[ResourceCategory, list[str]] = {
${resourcesDict},
}

ALL_AWS_RESOURCES: tuple[str, ...] = (
${allResourcesList.map((r) => `    "${r}"`).join(",\n")},
)

AwsResourceType = Literal[${allResourcesList.map((r) => `"${r}"`).join(", ")}]


# =============================================================================
# Helper Functions
# =============================================================================

def is_plan_name(value: str) -> bool:
    """Check if a string is a valid plan name."""
    return value in PLAN_NAMES


def is_legacy_plan_name(value: str) -> bool:
    """Check if a string is a legacy plan name."""
    return value in LEGACY_PLAN_MIGRATIONS


def normalize_plan_name(value: str) -> PlanName:
    """Normalize a plan name, converting legacy names to v4.0 names."""
    if is_plan_name(value):
        return value  # type: ignore
    if is_legacy_plan_name(value):
        return LEGACY_PLAN_MIGRATIONS[value]  # type: ignore
    return "community"


def is_framework_id(value: str) -> bool:
    """Check if a string is a valid framework ID."""
    return value in FRAMEWORK_IDS


def is_aws_resource_type(value: str) -> bool:
    """Check if a string is a valid AWS resource type."""
    return value in ALL_AWS_RESOURCES


def plan_has_feature(plan: PlanName, feature: str) -> bool:
    """Check if a plan has a specific feature."""
    config = PLANS[plan]

    # Check for "*" (all features)
    if "*" in config.features:
        # Check if explicitly excluded
        return f"!{feature}" not in config.features

    return feature in config.features


def get_plan_features(plan: PlanName) -> list[str]:
    """Get all features for a plan (resolving * and ! modifiers)."""
    config = PLANS[plan]

    if "*" in config.features:
        # All features except excluded ones
        excluded = [f[1:] for f in config.features if f.startswith("!")]
        return [f for f in ALL_FEATURES if f not in excluded]

    return [f for f in config.features if not f.startswith("!")]


def is_unlimited(value: Optional[int]) -> bool:
    """Check if a limit is unlimited (None or -1)."""
    return value is None or value == -1


def format_limit(value: Optional[int]) -> str:
    """Format a limit for display."""
    if is_unlimited(value):
        return "Unlimited"
    return f"{value:,}"


def format_price(cents: int) -> str:
    """Format price in dollars from cents."""
    if cents == 0:
        return "Free"
    return f"\${cents / 100:,.0f}"


def get_required_plan_for_feature(feature: str) -> PlanName:
    """Get the minimum plan required for a feature."""
    for plan_name in PLAN_NAMES:
        if plan_has_feature(plan_name, feature):
            return plan_name
    return "sovereign"


def get_upgrade_path(current_plan: PlanName) -> Optional[PlanName]:
    """Get upgrade path from current plan."""
    upgrade_paths: dict[PlanName, Optional[PlanName]] = {
        "community": "pro",
        "pro": "team",
        "team": "sovereign",
        "sovereign": None,
    }
    return upgrade_paths.get(current_plan)


# =============================================================================
# Plan Comparison
# =============================================================================

PLAN_RANK: dict[str, int] = {
    # v4.0 plans
    "community": 0,
    "pro": 1,
    "team": 2,
    "sovereign": 3,
    # Legacy plans
    "free": 0,
    "solo": 1,
    "enterprise": 3,
}


def is_plan_upgrade(from_plan: str, to_plan: str) -> bool:
    """Check if changing plans is an upgrade."""
    from_rank = PLAN_RANK.get(normalize_plan_name(from_plan), 0)
    to_rank = PLAN_RANK.get(normalize_plan_name(to_plan), 0)
    return to_rank > from_rank


def is_plan_downgrade(from_plan: str, to_plan: str) -> bool:
    """Check if changing plans is a downgrade."""
    from_rank = PLAN_RANK.get(normalize_plan_name(from_plan), 0)
    to_rank = PLAN_RANK.get(normalize_plan_name(to_plan), 0)
    return to_rank < from_rank
`;
}

function main(): void {
  const isCheck = process.argv.includes("--check");

  console.log("📦 @replimap/config v4.0 code generation");
  console.log("=========================================");

  // Load JSON sources
  console.log("📖 Loading JSON sources...");
  const { plans, frameworks, resources, combinedHash } = loadJsonFiles();
  console.log(`   Content hash: ${combinedHash}`);
  console.log(`   Plans: ${Object.keys(plans).join(", ")}`);

  // Generate code
  console.log("⚙️  Generating TypeScript...");
  const tsCode = generateTypeScript(plans, frameworks, resources, combinedHash);

  console.log("🐍 Generating Python...");
  const pyCode = generatePython(plans, frameworks, resources, combinedHash);

  const tsPath = join(DIST_DIR, "index.ts");
  const pyPath = join(DIST_DIR, "config.py");

  if (isCheck) {
    // Check mode: verify generated files match
    console.log("🔍 Checking generated files...");

    let hasChanges = false;

    if (!existsSync(tsPath)) {
      console.error("❌ dist/index.ts does not exist");
      hasChanges = true;
    } else {
      const existingTs = readFileSync(tsPath, "utf-8");
      if (existingTs !== tsCode) {
        console.error("❌ dist/index.ts is out of date");
        hasChanges = true;
      } else {
        console.log("✅ dist/index.ts is up to date");
      }
    }

    if (!existsSync(pyPath)) {
      console.error("❌ dist/config.py does not exist");
      hasChanges = true;
    } else {
      const existingPy = readFileSync(pyPath, "utf-8");
      if (existingPy !== pyCode) {
        console.error("❌ dist/config.py is out of date");
        hasChanges = true;
      } else {
        console.log("✅ dist/config.py is up to date");
      }
    }

    if (hasChanges) {
      console.error(
        "\n❌ Generated files are out of date. Run 'pnpm build' to regenerate."
      );
      process.exit(1);
    }

    console.log("\n✅ All generated files are up to date!");
  } else {
    // Build mode: write files
    console.log("💾 Writing dist/index.ts...");
    writeFileSync(tsPath, tsCode);

    console.log("💾 Writing dist/config.py...");
    writeFileSync(pyPath, pyCode);

    console.log("\n✅ Code generation complete!");
    console.log(`   Version: ${combinedHash}`);
  }
}

main();
