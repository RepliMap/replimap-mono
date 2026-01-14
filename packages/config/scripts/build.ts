#!/usr/bin/env tsx
/**
 * Code generation script for @replimap/config
 *
 * Reads JSON source files and generates:
 * - dist/index.ts (TypeScript exports)
 * - dist/config.py (Python dataclasses)
 *
 * Usage:
 *   pnpm build        # Generate files
 *   pnpm check        # Verify generated files are up to date
 */

import { readFileSync, writeFileSync, readdirSync, existsSync } from "node:fs";
import { createHash } from "node:crypto";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const ROOT = join(__dirname, "..");
const SRC_DIR = join(ROOT, "src");
const DIST_DIR = join(ROOT, "dist");

interface Plans {
  [key: string]: {
    price_monthly: number;
    scans_per_month: number | null;
    max_accounts?: number | null;
    features: string[];
    addons?: Record<string, number>;
  };
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
  plans: Plans;
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

  const plans = JSON.parse(plansContent) as Plans;
  const frameworks = JSON.parse(frameworksContent) as Frameworks;
  const resources = JSON.parse(resourcesContent) as Resources;

  // Compute hash from all source content
  const combinedContent = plansContent + frameworksContent + resourcesContent;
  const combinedHash = computeContentHash(combinedContent);

  return { plans, frameworks, resources, combinedHash };
}

function generateTypeScript(
  plans: Plans,
  frameworks: Frameworks,
  resources: Resources,
  hash: string
): string {
  const planNames = Object.keys(plans);
  const frameworkIds = Object.keys(frameworks.compliance_frameworks);
  const resourceCategories = Object.keys(resources.aws_resources);

  return `/**
 * @replimap/config - Auto-generated configuration
 * DO NOT EDIT - This file is generated from src/*.json
 *
 * Content Hash: ${hash}
 * Generated: ${new Date().toISOString()}
 */

// ============================================================================
// Version
// ============================================================================

export const CONFIG_VERSION = "${hash}" as const;

// ============================================================================
// Plans
// ============================================================================

export const PLAN_NAMES = [${planNames.map((n) => `"${n}"`).join(", ")}] as const;
export type PlanName = typeof PLAN_NAMES[number];

export interface PlanConfig {
  price_monthly: number;
  scans_per_month: number | null;
  max_accounts?: number | null;
  features: string[];
  addons?: Record<string, number>;
}

export const PLANS: Record<PlanName, PlanConfig> = ${JSON.stringify(plans, null, 2)} as const;

// ============================================================================
// Compliance Frameworks
// ============================================================================

export const FRAMEWORK_IDS = [${frameworkIds.map((id) => `"${id}"`).join(", ")}] as const;
export type FrameworkId = typeof FRAMEWORK_IDS[number];

export interface FrameworkConfig {
  name: string;
  region: string;
  description: string;
  controls_count: number;
}

export const COMPLIANCE_FRAMEWORKS: Record<FrameworkId, FrameworkConfig> = ${JSON.stringify(frameworks.compliance_frameworks, null, 2)} as const;

// ============================================================================
// AWS Resources
// ============================================================================

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

// ============================================================================
// Helper Functions
// ============================================================================

export function isPlanName(value: string): value is PlanName {
  return PLAN_NAMES.includes(value as PlanName);
}

export function isFrameworkId(value: string): value is FrameworkId {
  return FRAMEWORK_IDS.includes(value as FrameworkId);
}

export function isAwsResourceType(value: string): value is AwsResourceType {
  return ALL_AWS_RESOURCES.includes(value as AwsResourceType);
}

export function getPlanFeatures(plan: PlanName): string[] {
  const config = PLANS[plan];
  if (config.features.includes("*")) {
    // Return all possible features
    return ["basic_scan", "graph_preview", "terraform_download", "full_audit"];
  }
  return config.features;
}
`;
}

function generatePython(
  plans: Plans,
  frameworks: Frameworks,
  resources: Resources,
  hash: string
): string {
  const planNames = Object.keys(plans);
  const frameworkIds = Object.keys(frameworks.compliance_frameworks);
  const resourceCategories = Object.keys(resources.aws_resources);

  const plansDataclass = Object.entries(plans)
    .map(([name, config]) => {
      const addons = config.addons
        ? `{${Object.entries(config.addons)
            .map(([k, v]) => `"${k}": ${v}`)
            .join(", ")}}`
        : "None";
      return `    "${name}": PlanConfig(
        price_monthly=${config.price_monthly},
        scans_per_month=${config.scans_per_month === null ? "None" : config.scans_per_month},
        max_accounts=${config.max_accounts === undefined ? "None" : config.max_accounts === null ? "None" : config.max_accounts},
        features=${JSON.stringify(config.features)},
        addons=${addons},
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

  const allResources = Object.values(resources.aws_resources).flat();

  return `"""
@replimap/config - Auto-generated configuration
DO NOT EDIT - This file is generated from src/*.json

Content Hash: ${hash}
Generated: ${new Date().toISOString()}
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Literal, Optional


# ============================================================================
# Version
# ============================================================================

CONFIG_VERSION: str = "${hash}"


# ============================================================================
# Plans
# ============================================================================

PlanName = Literal[${planNames.map((n) => `"${n}"`).join(", ")}]

PLAN_NAMES: tuple[PlanName, ...] = (${planNames.map((n) => `"${n}"`).join(", ")},)


@dataclass(frozen=True)
class PlanConfig:
    """Configuration for a pricing plan."""
    price_monthly: int
    scans_per_month: Optional[int]
    max_accounts: Optional[int]
    features: list[str]
    addons: Optional[dict[str, int]] = None


PLANS: dict[PlanName, PlanConfig] = {
${plansDataclass},
}


# ============================================================================
# Compliance Frameworks
# ============================================================================

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


# ============================================================================
# AWS Resources
# ============================================================================

ResourceCategory = Literal[${resourceCategories.map((c) => `"${c}"`).join(", ")}]

RESOURCE_CATEGORIES: tuple[ResourceCategory, ...] = (${resourceCategories.map((c) => `"${c}"`).join(", ")},)

AWS_RESOURCES: dict[ResourceCategory, list[str]] = {
${resourcesDict},
}

ALL_AWS_RESOURCES: tuple[str, ...] = (
${allResources.map((r) => `    "${r}"`).join(",\n")},
)

AwsResourceType = Literal[${allResources.map((r) => `"${r}"`).join(", ")}]


# ============================================================================
# Helper Functions
# ============================================================================

def is_plan_name(value: str) -> bool:
    """Check if a string is a valid plan name."""
    return value in PLAN_NAMES


def is_framework_id(value: str) -> bool:
    """Check if a string is a valid framework ID."""
    return value in FRAMEWORK_IDS


def is_aws_resource_type(value: str) -> bool:
    """Check if a string is a valid AWS resource type."""
    return value in ALL_AWS_RESOURCES


def get_plan_features(plan: PlanName) -> list[str]:
    """Get the list of features for a plan."""
    config = PLANS[plan]
    if "*" in config.features:
        return ["basic_scan", "graph_preview", "terraform_download", "full_audit"]
    return list(config.features)
`;
}

function main(): void {
  const isCheck = process.argv.includes("--check");

  console.log("📦 @replimap/config code generation");
  console.log("=====================================");

  // Load JSON sources
  console.log("📖 Loading JSON sources...");
  const { plans, frameworks, resources, combinedHash } = loadJsonFiles();
  console.log(`   Content hash: ${combinedHash}`);

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
