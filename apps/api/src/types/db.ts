/**
 * Database row types for D1 (SQLite)
 */

// ============================================================================
// Table Row Types
// ============================================================================

export interface UserRow {
  id: string;
  email: string;
  stripe_customer_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface LicenseRow {
  id: string;
  user_id: string;
  license_key: string;
  plan: 'free' | 'solo' | 'pro' | 'team';
  status: 'active' | 'canceled' | 'expired' | 'past_due' | 'revoked';
  stripe_subscription_id: string | null;
  stripe_price_id: string | null;
  current_period_start: string | null;
  current_period_end: string | null;
  created_at: string;
  updated_at: string;
}

export interface LicenseMachineRow {
  id: string;
  license_id: string;
  machine_id: string;
  machine_name: string | null;
  is_active: number; // SQLite uses 0/1 for boolean
  first_seen_at: string;
  last_seen_at: string;
}

export interface MachineChangeRow {
  id: string;
  license_id: string;
  old_machine_id: string | null;
  new_machine_id: string;
  changed_at: string;
}

export interface UsageLogRow {
  id: string;
  license_id: string;
  machine_id: string | null;
  action: 'validate' | 'activate' | 'deactivate' | 'scan';
  resources_count: number;
  metadata: string | null; // JSON string
  created_at: string;
}

export interface ProcessedEventRow {
  event_id: string;
  event_type: string;
  processed_at: string;
}

export interface LicenseAwsAccountRow {
  id: string;
  license_id: string;
  aws_account_id: string;
  account_alias: string | null;
  is_active: number; // SQLite uses 0/1 for boolean
  first_seen_at: string;
  last_seen_at: string;
}

// ============================================================================
// Join/Aggregate Types
// ============================================================================

export interface LicenseWithMachineCount extends LicenseRow {
  active_machines: number;
}

export interface LicenseWithDetails extends LicenseRow {
  active_machines: number;
  monthly_changes: number;
  active_aws_accounts: number;
}

export interface MachineInfo {
  machine_id: string;
  machine_name: string | null;
  is_active: boolean;
  first_seen_at: string;
  last_seen_at: string;
}

// ============================================================================
// Query Result Types
// ============================================================================

export interface ValidateLicenseQueryResult {
  // License fields
  license_id: string;
  license_key: string;
  plan: 'free' | 'solo' | 'pro' | 'team';
  status: 'active' | 'canceled' | 'expired' | 'past_due' | 'revoked';
  current_period_end: string | null;
  // Aggregated fields
  active_machines: number;
  monthly_changes: number;
  active_aws_accounts: number;
  // Machine binding for this specific machine
  machine_is_active: number | null;
  machine_last_seen: string | null;
}

// =============================================================================
// NEW: Feature Usage Tables
// =============================================================================

export interface UsageEventRow {
  id: string;
  license_id: string;
  event_type: string;
  region: string | null;
  vpc_id: string | null;
  resource_count: number;
  duration_ms: number | null;
  metadata: string | null; // JSON string
  original_event_type: string | null; // For deprecated event tracking
  created_at: string;
}

export interface SnapshotRow {
  id: string;
  license_id: string;
  name: string;
  region: string;
  vpc_id: string | null;
  resource_count: number;
  profile: string | null;
  replimap_version: string | null;
  storage_type: string;
  storage_path: string | null;
  created_at: string;
}

export interface RemediationRow {
  id: string;
  license_id: string;
  audit_id: string | null;
  region: string;
  total_findings: number;
  total_fixable: number;
  total_manual: number;
  files_generated: number;
  created_at: string;
}

export interface MigrationLogRow {
  id: number;
  migration_name: string;
  executed_at: string;
  notes: string | null;
}
