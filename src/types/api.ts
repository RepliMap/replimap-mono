/**
 * API Request/Response types for RepliMap Backend
 */

// ============================================================================
// Request Types
// ============================================================================

export interface ValidateLicenseRequest {
  license_key: string;
  machine_id: string;
  cli_version?: string;
}

export interface ActivateLicenseRequest {
  license_key: string;
  machine_id: string;
  machine_name?: string;
}

export interface DeactivateLicenseRequest {
  license_key: string;
  machine_id: string;
}

export interface TrackAwsAccountRequest {
  license_key: string;
  aws_account_id: string;
  account_alias?: string;
}

// ============================================================================
// Response Types
// ============================================================================

export interface PlanFeatures {
  resources_per_scan: number; // -1 = unlimited
  scans_per_month: number;    // -1 = unlimited
  aws_accounts: number;
  machines: number;
  export_formats: string[];
}

export interface UsageInfo {
  scans_this_month: number;
  machines_active: number;
  machines_limit: number;
  aws_accounts_active?: number;
  aws_accounts_limit?: number;
}

export interface CliVersionInfo {
  status: 'ok' | 'deprecated' | 'unsupported';
  message?: string;
  latest_version: string;
  upgrade_url: string;
}

export interface ValidateLicenseResponse {
  valid: true;
  plan: string;
  status: string;
  features: PlanFeatures;
  usage: UsageInfo;
  expires_at: string | null;
  cache_until: string;
  cli_version?: CliVersionInfo;
}

export interface ActivateLicenseResponse {
  activated: true;
  plan: string;
  machines_used: number;
  machines_limit: number;
}

export interface DeactivateLicenseResponse {
  deactivated: true;
  machines_remaining: number;
}

export interface TrackAwsAccountResponse {
  tracked: true;
  is_new: boolean;
  aws_accounts_used: number;
  aws_accounts_limit: number;
}

// ============================================================================
// Error Response Types
// ============================================================================

export type ErrorCode =
  | 'LICENSE_NOT_FOUND'
  | 'LICENSE_EXPIRED'
  | 'LICENSE_CANCELED'
  | 'LICENSE_PAST_DUE'
  | 'LICENSE_REVOKED'
  | 'MACHINE_LIMIT_EXCEEDED'
  | 'MACHINE_CHANGE_LIMIT'
  | 'AWS_ACCOUNT_LIMIT_EXCEEDED'
  | 'RATE_LIMIT_EXCEEDED'
  | 'INVALID_REQUEST'
  | 'INVALID_LICENSE_FORMAT'
  | 'INVALID_MACHINE_FORMAT'
  | 'WEBHOOK_SIGNATURE_INVALID'
  | 'NOT_FOUND'
  | 'INTERNAL_ERROR';

export interface ErrorResponse {
  valid: false;
  error_code: ErrorCode;
  message: string;
  support_id?: string;
  action?: string;
  retry_after?: number;
  machines?: string[];
  limit?: number;
  resets_at?: string;
}

// ============================================================================
// Health Check
// ============================================================================

export interface HealthResponse {
  status: 'ok' | 'error';
  timestamp: string;
  version?: string;
}

// ============================================================================
// Union Types
// ============================================================================

export type LicenseValidationResult = ValidateLicenseResponse | ErrorResponse;
export type LicenseActivationResult = ActivateLicenseResponse | ErrorResponse;
export type LicenseDeactivationResult = DeactivateLicenseResponse | ErrorResponse;
export type AwsAccountTrackResult = TrackAwsAccountResponse | ErrorResponse;
