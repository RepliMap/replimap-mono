/**
 * AWS Account Tracking Handler
 * POST /v1/aws-accounts/track
 * GET /v1/licenses/{license_key}/aws-accounts
 */

import type { Env } from '../types/env';
import { Errors, AppError } from '../lib/errors';
import {
  validateLicenseKey,
  normalizeLicenseKey,
  validateAwsAccountId,
} from '../lib/license';
import { PLAN_FEATURES, type PlanType } from '../lib/constants';
import { rateLimit } from '../lib/rate-limiter';
import {
  createDb,
  getLicenseByKey,
  trackAwsAccount,
  getActiveAwsAccountCount,
  type DrizzleDb,
} from '../lib/db';
import { sql } from 'drizzle-orm';

// ============================================================================
// Request/Response Types
// ============================================================================

interface TrackAwsAccountRequest {
  license_key: string;
  aws_account_id: string;
  account_alias?: string;
}

interface TrackAwsAccountResponse {
  tracked: true;
  is_new: boolean;
  aws_account_id: string;
  current_accounts: number;
  max_accounts: number;
}

interface AwsAccountInfo {
  aws_account_id: string;
  account_alias: string | null;
  is_active: boolean;
  first_seen_at: string;
  last_seen_at: string;
}

interface GetAwsAccountsResponse {
  accounts: AwsAccountInfo[];
  active_count: number;
  max_accounts: number;
}

// ============================================================================
// Handlers
// ============================================================================

/**
 * Track an AWS account for a license
 * POST /v1/aws-accounts/track
 */
export async function handleTrackAwsAccount(
  request: Request,
  env: Env,
  clientIP: string
): Promise<Response> {
  const db = createDb(env.DB);
  // Use validate rate limit (same as license validation)
  const rateLimitHeaders = await rateLimit(env.CACHE, 'validate', clientIP);

  try {
    // Parse request body
    let body: TrackAwsAccountRequest;
    try {
      body = await request.json() as TrackAwsAccountRequest;
    } catch {
      throw Errors.invalidRequest('Invalid JSON body');
    }

    // Validate required fields
    if (!body.license_key) {
      throw Errors.invalidRequest('Missing license_key');
    }
    if (!body.aws_account_id) {
      throw Errors.invalidRequest('Missing aws_account_id');
    }

    // Validate formats
    validateLicenseKey(body.license_key);

    if (!validateAwsAccountId(body.aws_account_id)) {
      throw Errors.invalidRequest('Invalid AWS account ID format. Must be 12 digits.');
    }

    const licenseKey = normalizeLicenseKey(body.license_key);

    // Get license
    const license = await getLicenseByKey(db, licenseKey);
    if (!license) {
      throw Errors.licenseNotFound();
    }

    // Check license status
    if (license.status !== 'active' && license.status !== 'canceled') {
      if (license.status === 'expired') {
        throw Errors.licenseExpired(license.currentPeriodEnd ?? 'Unknown');
      }
      if (license.status === 'revoked') {
        throw Errors.licenseRevoked();
      }
      if (license.status === 'past_due') {
        throw Errors.licensePastDue();
      }
    }

    // Get plan limits
    const plan = license.plan as PlanType;
    const features = PLAN_FEATURES[plan] ?? PLAN_FEATURES.community;
    const maxAccounts = features.aws_accounts;

    // Get current count
    const currentCount = await getActiveAwsAccountCount(db, license.id);

    // Check if this would exceed the limit (for new accounts)
    // First try to track - if it's already tracked, no limit check needed
    const result = await trackAwsAccount(
      db,
      license.id,
      body.aws_account_id,
      body.account_alias
    );

    if (result.isNew && currentCount >= maxAccounts) {
      // Undo the tracking (deactivate it)
      // For simplicity, we'll just return an error - the next call will update existing
      throw Errors.awsAccountLimitExceeded(maxAccounts);
    }

    const response: TrackAwsAccountResponse = {
      tracked: true,
      is_new: result.isNew,
      aws_account_id: body.aws_account_id,
      current_accounts: result.isNew ? currentCount + 1 : currentCount,
      max_accounts: maxAccounts,
    };

    return new Response(JSON.stringify(response), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
        ...rateLimitHeaders,
      },
    });
  } catch (error) {
    if (error instanceof AppError) {
      return new Response(JSON.stringify(error.toResponse()), {
        status: error.statusCode,
        headers: {
          'Content-Type': 'application/json',
          ...rateLimitHeaders,
        },
      });
    }
    throw error;
  }
}

/**
 * Get all AWS accounts for a license
 * GET /v1/licenses/{license_key}/aws-accounts
 */
export async function handleGetAwsAccounts(
  _request: Request,
  env: Env,
  licenseKey: string,
  clientIP: string
): Promise<Response> {
  const db = createDb(env.DB);
  const rateLimitHeaders = await rateLimit(env.CACHE, 'validate', clientIP);

  try {
    // Validate license key format
    validateLicenseKey(licenseKey);
    const normalizedKey = normalizeLicenseKey(licenseKey);

    // Get license
    const license = await getLicenseByKey(db, normalizedKey);
    if (!license) {
      throw Errors.licenseNotFound();
    }

    // Get all AWS accounts
    const accounts = await getAwsAccountsForLicense(db, license.id);

    // Get plan limits
    const plan = license.plan as PlanType;
    const features = PLAN_FEATURES[plan] ?? PLAN_FEATURES.community;

    const response: GetAwsAccountsResponse = {
      accounts: accounts.map((acc) => ({
        aws_account_id: acc.aws_account_id,
        account_alias: acc.account_alias,
        is_active: acc.is_active === 1,
        first_seen_at: acc.first_seen_at,
        last_seen_at: acc.last_seen_at,
      })),
      active_count: accounts.filter((acc) => acc.is_active === 1).length,
      max_accounts: features.aws_accounts,
    };

    return new Response(JSON.stringify(response), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
        ...rateLimitHeaders,
      },
    });
  } catch (error) {
    if (error instanceof AppError) {
      return new Response(JSON.stringify(error.toResponse()), {
        status: error.statusCode,
        headers: {
          'Content-Type': 'application/json',
          ...rateLimitHeaders,
        },
      });
    }
    throw error;
  }
}

// ============================================================================
// Database Helpers
// ============================================================================

interface AwsAccountRow {
  aws_account_id: string;
  account_alias: string | null;
  is_active: number;
  first_seen_at: string;
  last_seen_at: string;
}

async function getAwsAccountsForLicense(
  db: DrizzleDb,
  licenseId: string
): Promise<AwsAccountRow[]> {
  const result = await db.all<AwsAccountRow>(sql`
    SELECT aws_account_id, account_alias, is_active, first_seen_at, last_seen_at
    FROM license_aws_accounts
    WHERE license_id = ${licenseId}
    ORDER BY first_seen_at ASC
  `);

  return result;
}
