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
 * Per-plan entitlements as issued by the server (`features` object of
 * GET /v1/me/license). offline_grace_days is server-issued — the frontend
 * must never derive entitlement values from the plan name itself.
 */
export interface LicenseFeatures {
  resources_per_scan: number;
  scans_per_month: number;
  aws_accounts: number;
  machines: number;
  export_formats: string[];
  offline_grace_days: number;
}

/**
 * Usage statistics (`usage` object of GET /v1/me/license)
 */
export interface LicenseUsage {
  scans_this_month: number;
  machines_active: number;
  machines_limit: number;
  aws_accounts_active: number;
  aws_accounts_limit: number;
}

/** `subscription` object of GET /v1/me/license */
export interface LicenseSubscription {
  current_period_start: string | null;
  current_period_end: string | null;
  has_payment_method: boolean;
}

/**
 * License details as GET /v1/me/license actually returns them (mirrors
 * GetLicenseResponse in apps/api/src/handlers/user.ts — keep in sync).
 * Devices are NOT part of this payload; they come from GET /v1/me/machines.
 * Read derived display values via the helpers in `lib/license-view`.
 */
export interface LicenseDetails {
  license_key: string;
  plan: PlanName;
  status: LicenseStatus;
  features: LicenseFeatures;
  usage: LicenseUsage;
  subscription: LicenseSubscription;
  created_at: string;
}

/**
 * One device as GET /v1/me/machines returns it (mirrors MachineInfo in
 * apps/api/src/handlers/user.ts — keep in sync).
 */
export interface MachineInfo {
  /** Full machine id — required by the deactivate flow. */
  machine_id: string;
  machine_id_truncated: string;
  machine_name: string | null;
  is_active: boolean;
  first_seen_at: string;
  last_seen_at: string;
  fingerprint_type: string;
  ci_provider: string | null;
  ci_repo: string | null;
  container_type: string | null;
}

/** GET /v1/me/machines response envelope. */
export interface MachinesResponse {
  machines: MachineInfo[];
  active_count: number;
  /** Per-plan device cap (server-authoritative; -1 = unlimited). */
  limit: number;
  changes_this_month: number;
  changes_limit: number;
}

/**
 * Deactivate device request — /v1/license/deactivate expects `machine_id`
 * (unlike activate, which takes `machine_fingerprint`).
 */
export interface DeactivateRequest {
  license_key: string;
  machine_id: string;
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
