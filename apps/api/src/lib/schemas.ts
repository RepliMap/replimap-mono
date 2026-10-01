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
  // NEW: CI/CD environment flag - enables ephemeral machine handling
  is_ci: z.boolean().optional(),
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
// License Deactivation Schema
// ============================================================================

export const deactivateLicenseRequestSchema = z.object({
  license_key: licenseKeySchema,
  machine_id: machineIdSchema,
}).strict();

export type DeactivateLicenseRequest = z.infer<typeof deactivateLicenseRequestSchema>;

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
// Telemetry Schema (Strict to prevent DoS)
// ============================================================================

export const telemetrySchema = z.object({
  scan_id: z.string().uuid(),
  duration_ms: z.number().nonnegative().max(3600000), // Max 1 hour
  resource_count: z.number().nonnegative().max(10000),
  region: z.string().max(30),
  status: z.enum(['success', 'failed']),
  error_code: z.string().max(100).optional(),
  cli_version: z.string().max(20).optional(),
}).strict();

export type TelemetryInput = z.infer<typeof telemetrySchema>;

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
