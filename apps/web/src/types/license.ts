/**
 * License Types for CLI Phase 3 Dashboard
 *
 * Fingerprint types:
 * - machine: Local development machine
 * - ci: CI/CD pipeline (GitHub Actions, GitLab CI, etc.)
 * - container: Container/Cloud IDE (Docker, Codespaces, etc.)
 */

export type FingerprintType = 'machine' | 'ci' | 'container';

export type LicenseStatus =
  | 'active'
  | 'canceled'
  | 'expired'
  | 'past_due'
  | 'revoked';

export type PlanName = 'community' | 'pro' | 'team' | 'sovereign';

/**
 * Device/machine fingerprint with metadata
 */
export interface Fingerprint {
  /** 32-char hex fingerprint */
  fingerprint: string;
  /** Type of fingerprint */
  type: FingerprintType;
  /** Last seen timestamp (ISO 8601) */
  last_seen: string;
  /** CI provider name (for ci type) */
  ci_provider?: string | null;
  /** CI repository (for ci type) */
  ci_repo?: string | null;
  /** Container type (for container type) */
  container_type?: string | null;
}

/**
 * License details returned by /v1/me/license
 */
export interface LicenseDetails {
  /** Truncated license key (RM-XXXX-...) */
  license_key: string;
  /** Plan name */
  plan: PlanName;
  /** License status */
  status: LicenseStatus;
  /** Expiration date (ISO 8601) or null for lifetime */
  expires_at: string | null;
  /** Offline grace period in days */
  offline_grace_days: number;
  /** List of activated devices */
  fingerprints: Fingerprint[];
}

/**
 * Usage statistics
 */
export interface LicenseUsage {
  scans_this_month: number;
  machines_active: number;
  machines_limit: number;
  aws_accounts_active: number;
  aws_accounts_limit: number;
}

/**
 * Deactivate device request
 */
export interface DeactivateRequest {
  license_key: string;
  machine_fingerprint: string;
}

/**
 * Deactivate device response
 */
export interface DeactivateResponse {
  deactivated: boolean;
  machines_remaining: number;
}

/**
 * API error response
 */
export interface ApiErrorResponse {
  error: string;
  message: string;
  details?: Record<string, unknown>;
}
