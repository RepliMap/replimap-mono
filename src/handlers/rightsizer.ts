/**
 * Right-Sizer API Handler
 *
 * POST /v1/rightsizer/suggestions
 *
 * Analyzes AWS resources and provides downgrade suggestions
 * for cost optimization in dev/staging environments.
 *
 * This is a PAID feature requiring Solo plan or higher.
 */

import type { Env } from '../types/env';
import { AppError, Errors } from '../lib/errors';
import { validateLicenseKey, normalizeLicenseKey, generateId, nowISO } from '../lib/license';
import { getLicenseByKey } from '../lib/db';
import { rateLimit } from '../lib/rate-limiter';
import { Plan } from '../features';
import {
  ResourceCategory,
  DowngradeStrategy,
  calculateMonthlyCost,
  getDowngradeRecommendation,
} from '../data/rightsizer-rules';

// =============================================================================
// Request/Response Types
// =============================================================================

interface ResourceSummary {
  resource_id: string;
  resource_type: 'aws_instance' | 'aws_db_instance' | 'aws_elasticache_cluster' | 'aws_elasticache_replication_group';
  instance_type: string;
  region: string;
  multi_az?: boolean;
  storage_type?: string;
  engine?: string;
}

interface RightSizerRequest {
  resources: ResourceSummary[];
  strategy?: DowngradeStrategy;
  target_env?: 'dev' | 'staging' | 'test';
}

interface ResourceSuggestion {
  resource_id: string;
  resource_type: string;
  original_type: string;
  original_monthly_cost: number;
  recommended_type: string;
  recommended_monthly_cost: number;
  monthly_savings: number;
  annual_savings: number;
  savings_percentage: number;
  reason: string;
  warnings: string[];
  confidence: 'high' | 'medium' | 'low';
}

interface RightSizerResponse {
  success: true;
  suggestions: ResourceSuggestion[];
  summary: {
    total_resources: number;
    resources_with_suggestions: number;
    total_current_monthly: number;
    total_recommended_monthly: number;
    total_monthly_savings: number;
    total_annual_savings: number;
    savings_percentage: number;
  };
  generated_at: string;
  strategy_used: string;
}

// =============================================================================
// Validation
// =============================================================================

const SUPPORTED_RESOURCE_TYPES = [
  'aws_instance',
  'aws_db_instance',
  'aws_elasticache_cluster',
  'aws_elasticache_replication_group',
] as const;

const VALID_STRATEGIES: DowngradeStrategy[] = ['conservative', 'moderate', 'aggressive'];

/**
 * Map Terraform resource type to internal category
 */
function mapResourceType(resourceType: string): ResourceCategory | null {
  switch (resourceType) {
    case 'aws_instance':
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

/**
 * Validate request body
 */
function validateRequest(body: unknown): { valid: true; data: RightSizerRequest } | { valid: false; error: string } {
  if (!body || typeof body !== 'object') {
    return { valid: false, error: 'Request body must be a JSON object' };
  }

  const req = body as Record<string, unknown>;

  // Validate resources array
  if (!Array.isArray(req.resources)) {
    return { valid: false, error: 'resources must be an array' };
  }

  if (req.resources.length === 0) {
    return { valid: false, error: 'resources array cannot be empty' };
  }

  if (req.resources.length > 100) {
    return { valid: false, error: 'Maximum 100 resources per request' };
  }

  // Validate strategy
  if (req.strategy !== undefined) {
    if (typeof req.strategy !== 'string' || !VALID_STRATEGIES.includes(req.strategy as DowngradeStrategy)) {
      return { valid: false, error: `strategy must be one of: ${VALID_STRATEGIES.join(', ')}` };
    }
  }

  // Validate each resource
  for (let i = 0; i < req.resources.length; i++) {
    const resource = req.resources[i];
    if (!resource || typeof resource !== 'object') {
      return { valid: false, error: `resources[${i}] must be an object` };
    }

    const r = resource as Record<string, unknown>;

    if (!r.resource_id || typeof r.resource_id !== 'string') {
      return { valid: false, error: `resources[${i}].resource_id is required and must be a string` };
    }

    if (!r.resource_type || typeof r.resource_type !== 'string') {
      return { valid: false, error: `resources[${i}].resource_type is required and must be a string` };
    }

    if (!SUPPORTED_RESOURCE_TYPES.includes(r.resource_type as typeof SUPPORTED_RESOURCE_TYPES[number])) {
      return {
        valid: false,
        error: `resources[${i}].resource_type '${r.resource_type}' is not supported. Supported: ${SUPPORTED_RESOURCE_TYPES.join(', ')}`,
      };
    }

    if (!r.instance_type || typeof r.instance_type !== 'string') {
      return { valid: false, error: `resources[${i}].instance_type is required and must be a string` };
    }

    if (!r.region || typeof r.region !== 'string') {
      return { valid: false, error: `resources[${i}].region is required and must be a string` };
    }
  }

  return {
    valid: true,
    data: {
      resources: req.resources as ResourceSummary[],
      strategy: (req.strategy as DowngradeStrategy) ?? 'conservative',
      target_env: req.target_env as RightSizerRequest['target_env'],
    },
  };
}

// =============================================================================
// Core Logic
// =============================================================================

/**
 * Process a single resource and generate suggestion
 */
function processResource(
  resource: ResourceSummary,
  strategy: DowngradeStrategy
): ResourceSuggestion | null {
  const category = mapResourceType(resource.resource_type);
  if (!category) return null;

  // Get current cost
  const currentCost = calculateMonthlyCost(resource.instance_type, category, resource.region);
  if (currentCost === null) {
    // Unknown instance type - skip silently
    return null;
  }

  // Get downgrade recommendation
  const recommendation = getDowngradeRecommendation(resource.instance_type, category, strategy);
  if (!recommendation) {
    // No downgrade available (already at minimum)
    return null;
  }

  // Calculate recommended cost
  const recommendedCost = calculateMonthlyCost(recommendation.target, category, resource.region);
  if (recommendedCost === null) {
    return null;
  }

  const monthlySavings = currentCost - recommendedCost;
  if (monthlySavings <= 0) {
    // No savings - skip
    return null;
  }

  const savingsPercentage = Math.round((monthlySavings / currentCost) * 100);

  return {
    resource_id: resource.resource_id,
    resource_type: resource.resource_type,
    original_type: resource.instance_type,
    original_monthly_cost: currentCost,
    recommended_type: recommendation.target,
    recommended_monthly_cost: recommendedCost,
    monthly_savings: Math.round(monthlySavings * 100) / 100,
    annual_savings: Math.round(monthlySavings * 12 * 100) / 100,
    savings_percentage: savingsPercentage,
    reason: recommendation.reason,
    warnings: recommendation.warnings,
    confidence: recommendation.confidence,
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
    // 1. Extract license key from Authorization header
    const authHeader = request.headers.get('Authorization');
    if (!authHeader) {
      throw Errors.unauthorized('Authorization header required. Use: Authorization: Bearer <license_key>');
    }

    const licenseKey = authHeader.replace(/^Bearer\s+/i, '').trim();
    if (!licenseKey) {
      throw Errors.unauthorized('License key required in Authorization header');
    }

    // 2. Validate license key format
    validateLicenseKey(licenseKey);
    const normalizedKey = normalizeLicenseKey(licenseKey);

    // 3. Get license from database
    const license = await getLicenseByKey(env.DB, normalizedKey);
    if (!license) {
      throw Errors.licenseNotFound();
    }

    // 4. Check license status
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

    // 5. Check if plan includes rightsizer feature (Solo+)
    const plan = license.plan as Plan;
    const allowedPlans: Plan[] = [Plan.SOLO, Plan.PRO, Plan.TEAM, Plan.ENTERPRISE];

    if (!allowedPlans.includes(plan)) {
      return new Response(
        JSON.stringify({
          success: false,
          error_code: 'FEATURE_NOT_AVAILABLE',
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

    // 6. Parse and validate request body
    let body: unknown;
    try {
      body = await request.json();
    } catch {
      throw Errors.invalidRequest('Request body must be valid JSON');
    }

    const validation = validateRequest(body);
    if (!validation.valid) {
      throw Errors.invalidRequest(validation.error);
    }

    const requestData = validation.data;
    const strategy = requestData.strategy ?? 'conservative';

    // 7. Process each resource
    const suggestions: ResourceSuggestion[] = [];
    let totalCurrentMonthly = 0;
    let totalRecommendedMonthly = 0;

    for (const resource of requestData.resources) {
      const suggestion = processResource(resource, strategy);

      if (suggestion) {
        suggestions.push(suggestion);
        totalCurrentMonthly += suggestion.original_monthly_cost;
        totalRecommendedMonthly += suggestion.recommended_monthly_cost;
      } else {
        // Resource has no suggestion - still count its cost if we can
        const category = mapResourceType(resource.resource_type);
        if (category) {
          const cost = calculateMonthlyCost(resource.instance_type, category, resource.region);
          if (cost !== null) {
            totalCurrentMonthly += cost;
            totalRecommendedMonthly += cost; // No change
          }
        }
      }
    }

    const totalMonthlySavings = totalCurrentMonthly - totalRecommendedMonthly;
    const savingsPercentage =
      totalCurrentMonthly > 0 ? Math.round((totalMonthlySavings / totalCurrentMonthly) * 100) : 0;

    // 8. Log usage event
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
          strategy,
          total_savings: totalMonthlySavings,
        }),
        nowISO()
      ).run();
    } catch (err) {
      // Non-critical - log but don't fail
      console.error('Failed to log rightsizer usage:', err);
    }

    // 9. Build response
    const response: RightSizerResponse = {
      success: true,
      suggestions,
      summary: {
        total_resources: requestData.resources.length,
        resources_with_suggestions: suggestions.length,
        total_current_monthly: Math.round(totalCurrentMonthly * 100) / 100,
        total_recommended_monthly: Math.round(totalRecommendedMonthly * 100) / 100,
        total_monthly_savings: Math.round(totalMonthlySavings * 100) / 100,
        total_annual_savings: Math.round(totalMonthlySavings * 12 * 100) / 100,
        savings_percentage: savingsPercentage,
      },
      generated_at: nowISO(),
      strategy_used: strategy,
    };

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
    throw error;
  }
}
