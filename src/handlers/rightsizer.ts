/**
 * Right-Sizer API Handler (Production Ready)
 *
 * POST /v1/rightsizer/suggestions
 *
 * Features:
 * - Architecture-safe downgrades (no x86 ↔ ARM for EC2)
 * - License validation (mandatory for paid feature)
 * - Storage optimization (io1/gp2 → gp3)
 * - Multi-AZ removal for dev environments
 * - Skipped resources tracking (transparency)
 *
 * This is a PAID feature requiring Solo plan or higher.
 */

import type { Env } from '../types/env';
import { AppError, Errors } from '../lib/errors';
import { validateLicenseKey, normalizeLicenseKey, generateId, nowISO } from '../lib/license';
import { getLicenseByKey } from '../lib/db';
import { rateLimit } from '../lib/rate-limiter';
import { Plan } from '../features';
import { rightSizerRequestSchema, parseRequest, type RightSizerResourceInput } from '../lib/schemas';
import { checkVersionHeader, logError } from '../lib/security';
import {
  ResourceCategory,
  DowngradeStrategy,
  SkipReason,
  SIZE_HIERARCHY,
  getInstanceSpec,
  getInstanceCatalog,
  calculateMonthlyInstanceCost,
  calculateStorageMonthlyCost,
  getDevRecommendation,
  InstanceSpec,
} from '../data/rightsizer-rules';

// =============================================================================
// Request/Response Types
// =============================================================================

// Use the Zod-inferred type for resources
type ResourceInput = RightSizerResourceInput;

interface SavingsBreakdown {
  instance: number;
  storage: number;
  multi_az: number;
}

interface ResourceSuggestion {
  resource_id: string;
  resource_type: string;
  current: {
    instance_type: string;
    monthly_cost: number;
    storage_type?: string;
    storage_monthly?: number;
    multi_az?: boolean;
  };
  recommended: {
    instance_type: string;
    monthly_cost: number;
    storage_type?: string;
    storage_monthly?: number;
    multi_az: boolean;
  };
  monthly_savings: number;
  annual_savings: number;
  savings_percentage: number;
  savings_breakdown: SavingsBreakdown;
  actions: string[];
  warnings: string[];
  confidence: 'high' | 'medium' | 'low';
}

interface SkippedResource {
  resource_id: string;
  resource_type: string;
  instance_type: string;
  reason: string;
}

interface RightSizerResponse {
  success: true;
  suggestions: ResourceSuggestion[];
  skipped: SkippedResource[];
  summary: {
    total_resources: number;
    resources_with_suggestions: number;
    resources_skipped: number;
    total_current_monthly: number;
    total_recommended_monthly: number;
    total_monthly_savings: number;
    total_annual_savings: number;
    savings_percentage: number;
    savings_breakdown: SavingsBreakdown;
  };
  generated_at: string;
  strategy_used: string;
}

// =============================================================================
// Validation (now uses Zod schemas from lib/schemas.ts)
// =============================================================================

/**
 * Map Terraform resource type to internal category
 */
function mapResourceType(resourceType: string): ResourceCategory | null {
  switch (resourceType) {
    case 'aws_instance':
    case 'aws_launch_template':
      return 'ec2';
    case 'aws_db_instance':
      return 'rds';
    case 'aws_elasticache_cluster':
    case 'aws_elasticache_replication_group':
      return 'elasticache';
    default:
      return null;
  }
}

// =============================================================================
// Core Logic
// =============================================================================

interface ProcessResult {
  suggestion: ResourceSuggestion | null;
  skipReason: string | null;
}

/**
 * Get instance recommendation with architecture safety
 * CRITICAL: For EC2, never switch between x86 and ARM
 */
function getInstanceRecommendation(
  current: InstanceSpec,
  resourceCategory: ResourceCategory,
  strategy: DowngradeStrategy
): { target: InstanceSpec; actions: string[]; warnings: string[] } | null {

  const instances = getInstanceCatalog(resourceCategory);
  const actions: string[] = [];
  const warnings: string[] = [];

  // CRITICAL: Preserve architecture for EC2 (AMI compatibility)
  const targetArch = current.architecture;

  if (resourceCategory === 'ec2') {
    actions.push(`Preserved ${targetArch} architecture for AMI compatibility`);
  }

  // Strategy 1: Switch to burstable T-series (for non-burstable instances)
  if (!current.is_burstable) {
    const minMemory = strategy === 'conservative'
      ? current.memory_gb * 0.5
      : current.memory_gb * 0.25;

    const devRecType = getDevRecommendation(resourceCategory, minMemory, targetArch);

    if (devRecType && instances[devRecType]) {
      const target = instances[devRecType];

      if (target.hourly_usd < current.hourly_usd) {
        actions.push(`Switch to burstable instance (${current.type} → ${target.type})`);

        if (target.memory_gb < current.memory_gb) {
          warnings.push(`Memory reduced from ${current.memory_gb}GB to ${target.memory_gb}GB`);
        }
        if (target.vcpu < current.vcpu) {
          warnings.push(`vCPU reduced from ${current.vcpu} to ${target.vcpu}`);
        }
        if (strategy === 'aggressive') {
          warnings.push('Aggressive downgrade - verify application requirements');
        }

        return { target, actions, warnings };
      }
    }
  }

  // Strategy 2: Same family, smaller size
  const currentSizeIndex = SIZE_HIERARCHY.indexOf(current.size);
  if (currentSizeIndex <= 0) {
    return null;
  }

  const stepsDown = strategy === 'conservative' ? 1 : 2;
  const targetSizeIndex = Math.max(0, currentSizeIndex - stepsDown);
  const targetSize = SIZE_HIERARCHY[targetSizeIndex];

  const targetType = `${current.family}.${targetSize}`;

  if (instances[targetType]) {
    const target = instances[targetType];

    // Safety check: ensure architecture matches
    if (target.architecture !== targetArch) {
      return null;
    }

    actions.push(`Downgrade instance size (${current.size} → ${targetSize})`);

    if (stepsDown > 1) {
      warnings.push('Multiple size downgrade - verify requirements');
    }

    return { target, actions, warnings };
  }

  return null;
}

/**
 * Process a single resource and generate suggestion or skip reason
 */
function processResource(
  resource: ResourceInput,
  strategy: DowngradeStrategy
): ProcessResult {

  const category = mapResourceType(resource.resource_type);
  if (!category) {
    return { suggestion: null, skipReason: SkipReason.UNSUPPORTED_RESOURCE_TYPE };
  }

  const currentInstance = getInstanceSpec(resource.instance_type, category);
  if (!currentInstance) {
    return { suggestion: null, skipReason: `${SkipReason.UNKNOWN_INSTANCE_TYPE}: ${resource.instance_type}` };
  }

  const region = resource.region;
  const actions: string[] = [];
  const warnings: string[] = [];

  // ─────────────────────────────────────────────────────────────────────────
  // Calculate current costs
  // ─────────────────────────────────────────────────────────────────────────

  const currentInstanceCost = calculateMonthlyInstanceCost(currentInstance.hourly_usd, region);
  let currentTotalInstanceCost = currentInstanceCost;

  // Multi-AZ doubles the instance cost
  if (resource.multi_az) {
    currentTotalInstanceCost *= 2;
  }

  // Storage cost (RDS only)
  let currentStorageCost = 0;
  let recommendedStorageCost = 0;
  let recommendedStorageType = resource.storage_type;

  if (category === 'rds' && resource.storage_type && resource.storage_size_gb) {
    currentStorageCost = calculateStorageMonthlyCost(
      resource.storage_type,
      resource.storage_size_gb,
      resource.iops || 0
    );

    // Recommend gp3 for io1/gp2 (cheaper and better performance)
    if (resource.storage_type === 'io1' || resource.storage_type === 'gp2') {
      recommendedStorageType = 'gp3';
      recommendedStorageCost = calculateStorageMonthlyCost('gp3', resource.storage_size_gb, 0);
      actions.push(`Change storage type (${resource.storage_type} → gp3)`);
    } else {
      recommendedStorageCost = currentStorageCost;
    }
  }

  // ─────────────────────────────────────────────────────────────────────────
  // Get instance recommendation
  // ─────────────────────────────────────────────────────────────────────────

  const recommendation = getInstanceRecommendation(currentInstance, category, strategy);

  // Check if any savings possible
  const hasStorageSavings = currentStorageCost > recommendedStorageCost;
  const hasMultiAzSavings = resource.multi_az === true;

  if (!recommendation && !hasStorageSavings && !hasMultiAzSavings) {
    // Determine specific skip reason
    if (currentInstance.is_burstable && SIZE_HIERARCHY.indexOf(currentInstance.size) <= 1) {
      return { suggestion: null, skipReason: SkipReason.ALREADY_MINIMUM_SIZE };
    }
    if (currentInstance.is_burstable) {
      return { suggestion: null, skipReason: SkipReason.ALREADY_BURSTABLE };
    }
    return { suggestion: null, skipReason: SkipReason.NO_SAVINGS_POSSIBLE };
  }

  const targetInstance = recommendation?.target || currentInstance;
  const recommendedInstanceCost = calculateMonthlyInstanceCost(targetInstance.hourly_usd, region);

  if (recommendation) {
    actions.push(...recommendation.actions);
    warnings.push(...recommendation.warnings);
  }

  // ─────────────────────────────────────────────────────────────────────────
  // Multi-AZ optimization
  // ─────────────────────────────────────────────────────────────────────────

  const recommendedMultiAz = false;
  if (resource.multi_az) {
    actions.push('Disable Multi-AZ deployment (not required for dev/staging)');
  }

  // ─────────────────────────────────────────────────────────────────────────
  // Calculate savings
  // ─────────────────────────────────────────────────────────────────────────

  const instanceSavings = currentTotalInstanceCost - recommendedInstanceCost;
  const storageSavings = currentStorageCost - recommendedStorageCost;
  const multiAzSavings = resource.multi_az ? currentInstanceCost : 0;

  const totalCurrentCost = currentTotalInstanceCost + currentStorageCost;
  const totalRecommendedCost = recommendedInstanceCost + recommendedStorageCost;
  const totalSavings = totalCurrentCost - totalRecommendedCost;

  if (totalSavings <= 0) {
    return { suggestion: null, skipReason: SkipReason.NO_SAVINGS_POSSIBLE };
  }

  const savingsPercentage = Math.round((totalSavings / totalCurrentCost) * 100);

  // Determine confidence level
  let confidence: 'high' | 'medium' | 'low' = 'high';
  if (strategy === 'aggressive') confidence = 'medium';
  if (savingsPercentage > 80) confidence = 'medium';
  if (savingsPercentage > 90) confidence = 'low';

  return {
    suggestion: {
      resource_id: resource.resource_id,
      resource_type: resource.resource_type,
      current: {
        instance_type: resource.instance_type,
        monthly_cost: Math.round(totalCurrentCost * 100) / 100,
        storage_type: resource.storage_type,
        storage_monthly: currentStorageCost > 0 ? currentStorageCost : undefined,
        multi_az: resource.multi_az,
      },
      recommended: {
        instance_type: targetInstance.type,
        monthly_cost: Math.round(totalRecommendedCost * 100) / 100,
        storage_type: recommendedStorageType,
        storage_monthly: recommendedStorageCost > 0 ? recommendedStorageCost : undefined,
        multi_az: recommendedMultiAz,
      },
      monthly_savings: Math.round(totalSavings * 100) / 100,
      annual_savings: Math.round(totalSavings * 12 * 100) / 100,
      savings_percentage: savingsPercentage,
      savings_breakdown: {
        instance: Math.round(instanceSavings * 100) / 100,
        storage: Math.round(storageSavings * 100) / 100,
        multi_az: Math.round(multiAzSavings * 100) / 100,
      },
      actions,
      warnings,
      confidence,
    },
    skipReason: null,
  };
}

// =============================================================================
// Handler
// =============================================================================

/**
 * POST /v1/rightsizer/suggestions
 *
 * Analyze resources and return downgrade suggestions
 */
export async function handleRightSizerSuggestions(
  request: Request,
  env: Env,
  clientIP: string
): Promise<Response> {
  // Rate limiting (use 'validate' tier)
  const rateLimitHeaders = await rateLimit(env.CACHE, 'validate', clientIP);

  try {
    // ═══════════════════════════════════════════════════════════════════════
    // 1. LICENSE VALIDATION (MANDATORY)
    // ═══════════════════════════════════════════════════════════════════════

    const authHeader = request.headers.get('Authorization');
    if (!authHeader) {
      throw Errors.unauthorized('Authorization header required. Use: Authorization: Bearer <license_key>');
    }

    const licenseKey = authHeader.replace(/^Bearer\s+/i, '').trim();
    if (!licenseKey) {
      throw Errors.unauthorized('License key required in Authorization header');
    }

    // Validate license key format
    validateLicenseKey(licenseKey);
    const normalizedKey = normalizeLicenseKey(licenseKey);

    // Get license from database
    const license = await getLicenseByKey(env.DB, normalizedKey);
    if (!license) {
      throw Errors.licenseNotFound();
    }

    // Check license status
    if (license.status === 'expired') {
      throw Errors.licenseExpired(license.current_period_end ?? 'unknown');
    }
    if (license.status === 'canceled') {
      throw Errors.licenseCanceled(license.current_period_end ?? 'unknown');
    }
    if (license.status === 'past_due') {
      throw Errors.licensePastDue();
    }
    if (license.status === 'revoked') {
      throw Errors.licenseRevoked();
    }

    // Check if plan includes rightsizer feature (Solo+)
    const plan = license.plan as Plan;
    const allowedPlans: Plan[] = [Plan.SOLO, Plan.PRO, Plan.TEAM, Plan.ENTERPRISE];

    if (!allowedPlans.includes(plan)) {
      return new Response(
        JSON.stringify({
          success: false,
          error: 'UPGRADE_REQUIRED',
          message: 'Right-Sizer requires Solo plan or higher',
          current_plan: plan,
          required_plan: 'solo',
          upgrade_url: 'https://replimap.dev/pricing',
        }),
        {
          status: 403,
          headers: { 'Content-Type': 'application/json', ...rateLimitHeaders },
        }
      );
    }

    // ═══════════════════════════════════════════════════════════════════════
    // 2. REQUEST VALIDATION (Zod schema prevents DoS via large payloads)
    // ═══════════════════════════════════════════════════════════════════════

    // Check version header for warnings
    const cliVersionHeader = request.headers.get('X-Replimap-Version');
    const versionWarning = checkVersionHeader(cliVersionHeader);

    let rawBody: unknown;
    try {
      rawBody = await request.json();
    } catch {
      throw Errors.invalidRequest('Request body must be valid JSON');
    }

    // Validate with Zod schema (max 500 resources, strict field validation)
    const validation = parseRequest(rightSizerRequestSchema, rawBody);
    if (!validation.success) {
      throw Errors.invalidRequest(validation.error);
    }

    const requestData = validation.data;
    const strategy = requestData.strategy ?? 'conservative';

    // ═══════════════════════════════════════════════════════════════════════
    // 3. PROCESS RESOURCES
    // ═══════════════════════════════════════════════════════════════════════

    const suggestions: ResourceSuggestion[] = [];
    const skipped: SkippedResource[] = [];
    let totalCurrentMonthly = 0;
    let totalRecommendedMonthly = 0;
    const totalBreakdown: SavingsBreakdown = { instance: 0, storage: 0, multi_az: 0 };

    for (const resource of requestData.resources) {
      const result = processResource(resource, strategy);

      if (result.suggestion) {
        suggestions.push(result.suggestion);
        totalCurrentMonthly += result.suggestion.current.monthly_cost;
        totalRecommendedMonthly += result.suggestion.recommended.monthly_cost;
        totalBreakdown.instance += result.suggestion.savings_breakdown.instance;
        totalBreakdown.storage += result.suggestion.savings_breakdown.storage;
        totalBreakdown.multi_az += result.suggestion.savings_breakdown.multi_az;
      } else if (result.skipReason) {
        skipped.push({
          resource_id: resource.resource_id,
          resource_type: resource.resource_type,
          instance_type: resource.instance_type,
          reason: result.skipReason,
        });
      }
    }

    const totalMonthlySavings = totalCurrentMonthly - totalRecommendedMonthly;
    const savingsPercentage =
      totalCurrentMonthly > 0 ? Math.round((totalMonthlySavings / totalCurrentMonthly) * 100) : 0;

    // ═══════════════════════════════════════════════════════════════════════
    // 4. LOG USAGE EVENT
    // ═══════════════════════════════════════════════════════════════════════

    try {
      await env.DB.prepare(`
        INSERT INTO usage_events (
          id, license_id, event_type, metadata, created_at
        ) VALUES (?, ?, ?, ?, ?)
      `).bind(
        generateId(),
        license.id,
        'rightsizer_analyze',
        JSON.stringify({
          resources_count: requestData.resources.length,
          suggestions_count: suggestions.length,
          skipped_count: skipped.length,
          strategy,
          total_savings: totalMonthlySavings,
        }),
        nowISO()
      ).run();
    } catch (err) {
      // Non-critical - log but don't fail
      console.error('Failed to log rightsizer usage:', err);
    }

    // ═══════════════════════════════════════════════════════════════════════
    // 5. BUILD RESPONSE
    // ═══════════════════════════════════════════════════════════════════════

    const response: RightSizerResponse & {
      _warning?: { message: string; upgrade_command: string };
    } = {
      success: true,
      suggestions,
      skipped,
      summary: {
        total_resources: requestData.resources.length,
        resources_with_suggestions: suggestions.length,
        resources_skipped: skipped.length,
        total_current_monthly: Math.round(totalCurrentMonthly * 100) / 100,
        total_recommended_monthly: Math.round(totalRecommendedMonthly * 100) / 100,
        total_monthly_savings: Math.round(totalMonthlySavings * 100) / 100,
        total_annual_savings: Math.round(totalMonthlySavings * 12 * 100) / 100,
        savings_percentage: savingsPercentage,
        savings_breakdown: {
          instance: Math.round(totalBreakdown.instance * 100) / 100,
          storage: Math.round(totalBreakdown.storage * 100) / 100,
          multi_az: Math.round(totalBreakdown.multi_az * 100) / 100,
        },
      },
      generated_at: nowISO(),
      strategy_used: strategy,
    };

    // Add version warning if outdated CLI
    if (versionWarning) {
      response._warning = {
        message: versionWarning.message,
        upgrade_command: versionWarning.upgrade_command,
      };
    }

    return new Response(JSON.stringify(response), {
      status: 200,
      headers: { 'Content-Type': 'application/json', ...rateLimitHeaders },
    });
  } catch (error) {
    if (error instanceof AppError) {
      return new Response(JSON.stringify(error.toResponse()), {
        status: error.statusCode,
        headers: { 'Content-Type': 'application/json', ...rateLimitHeaders },
      });
    }
    // Log error but don't expose internals
    logError('rightsizer/suggestions', error);
    throw error;
  }
}
