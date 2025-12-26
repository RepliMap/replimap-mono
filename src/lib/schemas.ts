/**
 * Zod Validation Schemas - The Sovereign Input Gate
 *
 * All input from the CLI is hostile until validated.
 * These schemas are the contract between the CLI and Backend.
 */

import { z } from 'zod';

// ============================================================================
// Constants (matching existing patterns)
// ============================================================================

/** License key format: RM-XXXX-XXXX-XXXX-XXXX (uppercase alphanumeric) */
const LICENSE_KEY_REGEX = /^RM-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$/;

/** Machine ID format: 32 character lowercase hex */
const MACHINE_ID_REGEX = /^[a-f0-9]{32}$/;

/** AWS Account ID format: 12 digits */
const AWS_ACCOUNT_ID_REGEX = /^\d{12}$/;

/** Semver version format (e.g., 1.0.0, 2.1.3) */
const SEMVER_REGEX = /^\d+\.\d+\.\d+(?:-[a-zA-Z0-9.]+)?$/;

// ============================================================================
// Base Field Schemas (reusable building blocks)
// ============================================================================

export const licenseKeySchema = z.string()
  .min(1, 'License key is required')
  .transform((val) => val.trim().toUpperCase())
  .refine((val) => LICENSE_KEY_REGEX.test(val), {
    message: 'Invalid license key format. Expected: RM-XXXX-XXXX-XXXX-XXXX',
  });

export const machineIdSchema = z.string()
  .min(1, 'Machine ID is required')
  .transform((val) => val.trim().toLowerCase())
  .refine((val) => MACHINE_ID_REGEX.test(val), {
    message: 'Invalid machine ID format. Expected: 32 character hex string',
  });

export const cliVersionSchema = z.string()
  .optional()
  .transform((val) => val?.trim())
  .refine((val) => !val || SEMVER_REGEX.test(val), {
    message: 'Invalid version format. Expected: semver (e.g., 1.0.0)',
  });

export const machineNameSchema = z.string()
  .max(255, 'Machine name too long')
  .optional()
  .transform((val) => val?.trim().slice(0, 255));

export const awsAccountIdSchema = z.string()
  .transform((val) => val.trim())
  .refine((val) => AWS_ACCOUNT_ID_REGEX.test(val), {
    message: 'Invalid AWS Account ID format. Expected: 12 digit number',
  });

// ============================================================================
// Machine Signature Schema (HMAC verification)
// ============================================================================

export const machineSignatureSchema = z.string()
  .min(1, 'Machine signature is required')
  .max(128, 'Machine signature too long')
  .refine((val) => /^[a-f0-9]{64}$/.test(val), {
    message: 'Invalid machine signature format. Expected: 64 character hex (SHA-256)',
  });

// ============================================================================
// License Validation Request Schema
// ============================================================================

export const validateLicenseRequestSchema = z.object({
  license_key: licenseKeySchema,
  machine_id: machineIdSchema,
  cli_version: cliVersionSchema,
  machine_name: machineNameSchema,
  // NEW: HMAC signature for machine verification
  machine_signature: machineSignatureSchema.optional(),
  // Timestamp for replay protection (optional for backward compatibility)
  timestamp: z.number()
    .int()
    .positive()
    .optional()
    .refine((val) => {
      if (!val) return true;
      // Reject requests older than 5 minutes or in the future by more than 1 minute
      const now = Date.now();
      const fiveMinutesAgo = now - (5 * 60 * 1000);
      const oneMinuteAhead = now + (60 * 1000);
      return val >= fiveMinutesAgo && val <= oneMinuteAhead;
    }, {
      message: 'Request timestamp is out of valid range (too old or too far in the future)',
    }),
}).strict();

export type ValidateLicenseRequest = z.infer<typeof validateLicenseRequestSchema>;

// ============================================================================
// License Activation/Deactivation Schemas
// ============================================================================

export const activateLicenseRequestSchema = z.object({
  license_key: licenseKeySchema,
  machine_id: machineIdSchema,
  machine_name: machineNameSchema,
}).strict();

export type ActivateLicenseRequest = z.infer<typeof activateLicenseRequestSchema>;

export const deactivateLicenseRequestSchema = z.object({
  license_key: licenseKeySchema,
  machine_id: machineIdSchema,
}).strict();

export type DeactivateLicenseRequest = z.infer<typeof deactivateLicenseRequestSchema>;

// ============================================================================
// Usage Tracking Schemas
// ============================================================================

/** Valid event types for usage tracking */
const VALID_EVENT_TYPES = [
  'scan', 'graph', 'graph_full', 'graph_security', 'clone',
  'audit', 'audit_fix',
  'drift', 'snapshot_save', 'snapshot_diff', 'snapshot_list', 'snapshot_delete',
  'deps', 'deps_explore', 'deps_export',
  // DEPRECATED: Accept but map to 'deps' equivalents
  'blast', 'blast_analyze', 'blast_export',
  'cost', 'cost_export',
  'export_json', 'export_html', 'export_markdown', 'export_terraform',
] as const;

export const eventTypeSchema = z.enum(VALID_EVENT_TYPES);

export const trackEventRequestSchema = z.object({
  license_key: licenseKeySchema,
  event_type: eventTypeSchema,
  region: z.string().max(64).optional(),
  vpc_id: z.string().max(64).optional(),
  // Bounded resource count to prevent abuse
  resource_count: z.number()
    .int()
    .min(0, 'resource_count must be non-negative')
    .max(100000, 'resource_count exceeds maximum (100,000)')
    .optional(),
  // Bounded duration to prevent abuse
  duration_ms: z.number()
    .int()
    .min(0, 'duration_ms must be non-negative')
    .max(86400000, 'duration_ms exceeds maximum (24 hours)')
    .optional(),
  // Metadata with size limit
  metadata: z.record(z.string(), z.unknown())
    .optional()
    .refine((val) => {
      if (!val) return true;
      // Limit metadata size to 4KB when serialized
      const serialized = JSON.stringify(val);
      return serialized.length <= 4096;
    }, {
      message: 'Metadata exceeds maximum size (4KB)',
    }),
}).strict();

export type TrackEventRequest = z.infer<typeof trackEventRequestSchema>;

// ============================================================================
// Usage Sync Schema
// ============================================================================

export const syncUsageRequestSchema = z.object({
  license_key: licenseKeySchema,
  machine_id: machineIdSchema,
  usage: z.object({
    scans_count: z.number().int().min(0).max(10000).optional(),
    resources_scanned: z.number().int().min(0).max(1000000).optional(),
    terraform_generations: z.number().int().min(0).max(10000).optional(),
  }),
  period: z.string()
    .regex(/^\d{4}-\d{2}$/, 'Period must be in YYYY-MM format')
    .optional(),
  idempotency_key: z.string().max(128).optional(),
}).strict();

export type SyncUsageRequest = z.infer<typeof syncUsageRequestSchema>;

// ============================================================================
// Check Quota Schema
// ============================================================================

export const checkQuotaRequestSchema = z.object({
  license_key: licenseKeySchema,
  operation: z.enum(['scans', 'resources']),
  amount: z.number().int().min(1).max(10000).optional().default(1),
}).strict();

export type CheckQuotaRequest = z.infer<typeof checkQuotaRequestSchema>;

// ============================================================================
// AWS Account Tracking Schema
// ============================================================================

export const trackAwsAccountRequestSchema = z.object({
  license_key: licenseKeySchema,
  aws_account_id: awsAccountIdSchema,
  region: z.string().max(64).optional(),
  machine_id: machineIdSchema.optional(),
}).strict();

export type TrackAwsAccountRequest = z.infer<typeof trackAwsAccountRequestSchema>;

// ============================================================================
// Checkout Session Schema
// ============================================================================

export const createCheckoutRequestSchema = z.object({
  email: z.string().email('Invalid email address'),
  plan: z.enum(['solo', 'pro', 'team']),
  billing_cycle: z.enum(['monthly', 'annual']).optional().default('monthly'),
  success_url: z.string().url('Invalid success URL').optional(),
  cancel_url: z.string().url('Invalid cancel URL').optional(),
}).strict();

export type CreateCheckoutRequest = z.infer<typeof createCheckoutRequestSchema>;

// ============================================================================
// Billing Portal Schema
// ============================================================================

export const createBillingPortalRequestSchema = z.object({
  license_key: licenseKeySchema,
  return_url: z.string().url('Invalid return URL').optional(),
}).strict();

export type CreateBillingPortalRequest = z.infer<typeof createBillingPortalRequestSchema>;

// ============================================================================
// Admin Schemas
// ============================================================================

export const createLicenseRequestSchema = z.object({
  email: z.string().email('Invalid email address'),
  plan: z.enum(['free', 'solo', 'pro', 'team']),
  stripe_customer_id: z.string().optional(),
  stripe_subscription_id: z.string().optional(),
}).strict();

export type CreateLicenseRequest = z.infer<typeof createLicenseRequestSchema>;

// ============================================================================
// Right-Sizer Suggestions Schema (Production)
// ============================================================================

/** Supported resource types for right-sizer */
const RIGHTSIZER_RESOURCE_TYPES = [
  'aws_instance',
  'aws_db_instance',
  'aws_elasticache_cluster',
  'aws_elasticache_replication_group',
  'aws_launch_template',
] as const;

/** Downgrade strategy options */
const DOWNGRADE_STRATEGIES = ['conservative', 'aggressive'] as const;

export const rightSizerResourceSchema = z.object({
  resource_id: z.string().min(1).max(256),
  resource_type: z.enum(RIGHTSIZER_RESOURCE_TYPES),
  instance_type: z.string().min(1).max(50),
  region: z.string().min(1).max(30),
  multi_az: z.boolean().optional(),
  storage_type: z.string().max(20).optional(),
  storage_size_gb: z.number().nonnegative().max(65536).optional(),
  iops: z.number().nonnegative().max(256000).optional(),
});

export const rightSizerRequestSchema = z.object({
  resources: z.array(rightSizerResourceSchema)
    .min(1, 'At least one resource is required')
    .max(500, 'Maximum 500 resources per request'),
  strategy: z.enum(DOWNGRADE_STRATEGIES).default('conservative'),
  target_env: z.enum(['dev', 'staging', 'test']).optional(),
}).strict();

export type RightSizerResourceInput = z.infer<typeof rightSizerResourceSchema>;
export type RightSizerRequest = z.infer<typeof rightSizerRequestSchema>;

// ============================================================================
// Feature Check Schema
// ============================================================================

export const checkFeatureRequestSchema = z.object({
  license_key: licenseKeySchema,
  feature: z.string().min(1).max(64),
}).strict();

export type CheckFeatureRequest = z.infer<typeof checkFeatureRequestSchema>;

// ============================================================================
// Validation Helper
// ============================================================================

/**
 * Safely parse and validate a request body with Zod schema.
 * Returns a Result type for explicit error handling.
 */
export function parseRequest<T>(
  schema: z.ZodSchema<T>,
  data: unknown
): { success: true; data: T } | { success: false; error: string } {
  const result = schema.safeParse(data);
  if (result.success) {
    return { success: true, data: result.data };
  }
  // Format error message
  const errorMessages = result.error.issues.map((issue) => {
    const path = issue.path.join('.');
    return path ? `${path}: ${issue.message}` : issue.message;
  }).join('; ');
  return { success: false, error: errorMessages };
}
