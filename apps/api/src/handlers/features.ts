/**
 * Feature Information Handlers
 *
 * GET /v1/features - Get all features info
 * POST /v1/features/check - Check feature access for a license
 */

import type { Env } from '../types/env';
import { Errors, AppError } from '../lib/errors';
import { validateLicenseKey, normalizeLicenseKey } from '../lib/license';
import { rateLimit } from '../lib/rate-limiter';
import { createDb } from '../lib/db';
import { getLicenseByKey } from '../lib/db';
import {
  Feature,
  Plan,
  PLAN_FEATURES,
  PLAN_LIMITS,
  FEATURE_METADATA,
  getFeatureFlags,
  planHasFeature,
  getRequiredPlan,
  getNewFeatures,
  getRenamedFeatures,
} from '../features';
import {
  getRenameInfo,
  normalizeFeature,
  isDeprecatedFeature,
  getFeatureDeprecationWarning,
} from '../utils/event-compat';

// =============================================================================
// Response Types
// =============================================================================

interface FeatureInfo {
  id: string;
  name: string;
  description: string;
  tier: string;
  available: boolean;
  isNew?: boolean;
  isRenamed?: boolean;
  previousName?: string;
}

interface FeaturesResponse {
  plan: string;
  features: {
    core: FeatureInfo[];
    security: FeatureInfo[];
    change_detection: FeatureInfo[];
    impact_analysis: FeatureInfo[];
    cost: FeatureInfo[];
    export: FeatureInfo[];
  };
  new_features: FeatureInfo[];
  renamed_features: FeatureInfo[];
}

interface CheckFeatureRequest {
  license_key: string;
  feature: string;
}

interface CheckFeatureResponse {
  allowed: boolean;
  feature: string;
  current_plan: string;
  required_plan?: string;
  feature_info?: FeatureInfo;
  deprecation_warning?: string;
  upgrade_url?: string;
}

// =============================================================================
// Handlers
// =============================================================================

/**
 * Get all features info
 * GET /v1/features
 */
export async function handleGetFeatures(
  request: Request,
  env: Env,
  clientIP: string
): Promise<Response> {
  const db = createDb(env.DB);
  const rateLimitHeaders = await rateLimit(env.CACHE, 'validate', clientIP);

  try {
    // Check if license key provided
    const licenseKey = request.headers.get('X-License-Key');
    let plan: Plan = Plan.FREE;

    if (licenseKey) {
      try {
        validateLicenseKey(licenseKey);
        const normalizedKey = normalizeLicenseKey(licenseKey);
        const license = await getLicenseByKey(db, normalizedKey);
        if (license) {
          plan = license.plan as Plan;
        }
      } catch {
        // Invalid license key - default to FREE
      }
    }

    const allowedFeatures = PLAN_FEATURES[plan] || [];

    // Build feature info list
    const allFeatures: FeatureInfo[] = Object.entries(FEATURE_METADATA)
      .filter(([, meta]) => meta !== undefined)
      .map(([key, meta]) => ({
        id: key,
        name: meta!.name,
        description: meta!.description,
        tier: meta!.tier,
        available: allowedFeatures.includes(key as Feature),
        isNew: meta!.isNew,
        isRenamed: meta!.isRenamed,
        previousName: meta!.previousName,
      }));

    // Group by category
    const grouped = {
      core: allFeatures.filter((f) =>
        ['scan', 'scan_unlimited_frequency', 'graph', 'graph_full', 'graph_security', 'clone_generate', 'clone_download'].includes(f.id)
      ),
      security: allFeatures.filter((f) => f.id.startsWith('audit')),
      change_detection: allFeatures.filter((f) =>
        ['drift', 'drift_watch', 'drift_alerts', 'snapshot', 'snapshot_diff'].includes(f.id)
      ),
      impact_analysis: allFeatures.filter((f) => f.id.startsWith('deps')),
      cost: allFeatures.filter((f) => f.id.startsWith('cost')),
      export: allFeatures.filter((f) => f.id.startsWith('export')),
    };

    const renameInfo = getRenameInfo();

    const response: FeaturesResponse & { renamed_features_info: typeof renameInfo } = {
      plan,
      features: grouped,
      new_features: allFeatures.filter((f) => f.isNew),
      renamed_features: allFeatures.filter((f) => f.isRenamed),
      renamed_features_info: renameInfo,
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

/**
 * Check feature access for a license
 * POST /v1/features/check
 */
export async function handleCheckFeature(
  request: Request,
  env: Env,
  clientIP: string
): Promise<Response> {
  const db = createDb(env.DB);
  const rateLimitHeaders = await rateLimit(env.CACHE, 'validate', clientIP);

  try {
    // Parse request body
    let body: CheckFeatureRequest;
    try {
      body = (await request.json()) as CheckFeatureRequest;
    } catch {
      throw Errors.invalidRequest('Invalid JSON body');
    }

    if (!body.license_key) {
      throw Errors.invalidRequest('Missing license_key');
    }
    if (!body.feature) {
      throw Errors.invalidRequest('Missing feature');
    }

    validateLicenseKey(body.license_key);
    const licenseKey = normalizeLicenseKey(body.license_key);

    // Normalize feature name (handle deprecated names)
    let feature = body.feature;
    let deprecationWarning: string | undefined;

    if (isDeprecatedFeature(feature)) {
      deprecationWarning = getFeatureDeprecationWarning(feature);
      feature = normalizeFeature(feature);
    }

    // Get license
    const license = await getLicenseByKey(db, licenseKey);
    if (!license) {
      throw Errors.licenseNotFound();
    }

    const plan = license.plan as Plan;
    const featureEnum = feature as Feature;
    const allowed = planHasFeature(plan, featureEnum);
    const requiredPlan = getRequiredPlan(featureEnum);
    const metadata = FEATURE_METADATA[featureEnum];

    const featureInfo: FeatureInfo | undefined = metadata
      ? {
          id: feature,
          name: metadata.name,
          description: metadata.description,
          tier: metadata.tier,
          available: allowed,
          isNew: metadata.isNew,
          isRenamed: metadata.isRenamed,
          previousName: metadata.previousName,
        }
      : undefined;

    const response: CheckFeatureResponse = {
      allowed,
      feature,
      current_plan: plan,
      required_plan: allowed ? undefined : requiredPlan,
      feature_info: featureInfo,
      deprecation_warning: deprecationWarning,
      upgrade_url: allowed ? undefined : `https://replimap.dev/pricing?feature=${feature}`,
    };

    return new Response(JSON.stringify(response), {
      status: allowed ? 200 : 403,
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

/**
 * Get feature flags for API info endpoint
 * GET /v1/features/flags
 */
export async function handleGetFeatureFlags(
  request: Request,
  env: Env,
  clientIP: string
): Promise<Response> {
  const db = createDb(env.DB);
  const rateLimitHeaders = await rateLimit(env.CACHE, 'validate', clientIP);

  try {
    const licenseKey = request.headers.get('X-License-Key');
    let plan: Plan = Plan.FREE;

    if (licenseKey) {
      try {
        validateLicenseKey(licenseKey);
        const normalizedKey = normalizeLicenseKey(licenseKey);
        const license = await getLicenseByKey(db, normalizedKey);
        if (license) {
          plan = license.plan as Plan;
        }
      } catch {
        // Invalid license key - default to FREE
      }
    }

    const flags = getFeatureFlags(plan);
    const limits = PLAN_LIMITS[plan];

    return new Response(
      JSON.stringify({
        plan,
        flags,
        limits,
        new_features: getNewFeatures(),
        renamed_features: getRenamedFeatures(),
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json', ...rateLimitHeaders },
      }
    );
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
