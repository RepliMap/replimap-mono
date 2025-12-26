/**
 * Database query helpers for D1
 */

import type {
  LicenseRow,
  LicenseMachineRow,
  UserRow,
  ValidateLicenseQueryResult,
} from '../types';
import { generateId, nowISO, normalizeLicenseKey, normalizeMachineId } from './license';

// ============================================================================
// License Queries
// ============================================================================

/**
 * Get license by key with machine and change counts
 * Optimized query for the hot path (validation)
 */
export async function getLicenseForValidation(
  db: D1Database,
  licenseKey: string,
  machineId: string
): Promise<ValidateLicenseQueryResult | null> {
  const normalizedKey = normalizeLicenseKey(licenseKey);
  const normalizedMachineId = normalizeMachineId(machineId);

  const result = await db.prepare(`
    SELECT
      l.id as license_id,
      l.license_key,
      l.plan,
      l.status,
      l.current_period_end,
      -- Count active machines
      (SELECT COUNT(*) FROM license_machines lm
       WHERE lm.license_id = l.id AND lm.is_active = 1) as active_machines,
      -- Count machine changes this month
      (SELECT COUNT(*) FROM machine_changes mc
       WHERE mc.license_id = l.id
       AND mc.changed_at >= datetime('now', 'start of month')) as monthly_changes,
      -- Count active AWS accounts
      (SELECT COUNT(*) FROM license_aws_accounts la
       WHERE la.license_id = l.id AND la.is_active = 1) as active_aws_accounts,
      -- Check if this specific machine is already registered
      (SELECT is_active FROM license_machines lm
       WHERE lm.license_id = l.id AND lm.machine_id = ?) as machine_is_active,
      (SELECT last_seen_at FROM license_machines lm
       WHERE lm.license_id = l.id AND lm.machine_id = ?) as machine_last_seen
    FROM licenses l
    WHERE l.license_key = ?
  `).bind(normalizedMachineId, normalizedMachineId, normalizedKey).first<ValidateLicenseQueryResult>();

  return result ?? null;
}

/**
 * Get license by key (simple query)
 */
export async function getLicenseByKey(
  db: D1Database,
  licenseKey: string
): Promise<LicenseRow | null> {
  const normalizedKey = normalizeLicenseKey(licenseKey);

  const result = await db.prepare(`
    SELECT * FROM licenses WHERE license_key = ?
  `).bind(normalizedKey).first<LicenseRow>();

  return result ?? null;
}

/**
 * Get license by Stripe subscription ID
 */
export async function getLicenseBySubscriptionId(
  db: D1Database,
  subscriptionId: string
): Promise<LicenseRow | null> {
  const result = await db.prepare(`
    SELECT * FROM licenses WHERE stripe_subscription_id = ?
  `).bind(subscriptionId).first<LicenseRow>();

  return result ?? null;
}

/**
 * Get all active machines for a license
 */
export async function getActiveMachines(
  db: D1Database,
  licenseId: string
): Promise<LicenseMachineRow[]> {
  const result = await db.prepare(`
    SELECT * FROM license_machines
    WHERE license_id = ? AND is_active = 1
    ORDER BY last_seen_at DESC
  `).bind(licenseId).all<LicenseMachineRow>();

  return result.results;
}

/**
 * Get total count of ALL machines ever registered (active + inactive)
 * Used for abuse detection - if a license has been used on 50+ devices,
 * it's likely being shared.
 */
export async function getTotalMachineCount(
  db: D1Database,
  licenseId: string
): Promise<number> {
  const result = await db.prepare(`
    SELECT COUNT(*) as count FROM license_machines
    WHERE license_id = ?
  `).bind(licenseId).first<{ count: number }>();

  return result?.count ?? 0;
}

// ============================================================================
// License Mutations
// ============================================================================

/**
 * Create a new license
 */
export async function createLicense(
  db: D1Database,
  data: {
    userId: string;
    licenseKey: string;
    plan: string;
    stripeSubscriptionId?: string;
    stripePriceId?: string;
    currentPeriodStart?: string;
    currentPeriodEnd?: string;
  }
): Promise<LicenseRow> {
  const id = generateId();
  const now = nowISO();

  await db.prepare(`
    INSERT INTO licenses (
      id, user_id, license_key, plan, status,
      stripe_subscription_id, stripe_price_id,
      current_period_start, current_period_end,
      created_at, updated_at
    ) VALUES (?, ?, ?, ?, 'active', ?, ?, ?, ?, ?, ?)
  `).bind(
    id,
    data.userId,
    data.licenseKey,
    data.plan,
    data.stripeSubscriptionId ?? null,
    data.stripePriceId ?? null,
    data.currentPeriodStart ?? null,
    data.currentPeriodEnd ?? null,
    now,
    now
  ).run();

  return (await db.prepare('SELECT * FROM licenses WHERE id = ?').bind(id).first<LicenseRow>())!;
}

/**
 * Update license status
 */
export async function updateLicenseStatus(
  db: D1Database,
  licenseId: string,
  status: string
): Promise<void> {
  await db.prepare(`
    UPDATE licenses SET status = ?, updated_at = ? WHERE id = ?
  `).bind(status, nowISO(), licenseId).run();
}

/**
 * Update license plan and period
 */
export async function updateLicensePlan(
  db: D1Database,
  licenseId: string,
  data: {
    plan?: string;
    status?: string;
    stripePriceId?: string;
    currentPeriodStart?: string;
    currentPeriodEnd?: string;
  }
): Promise<void> {
  const sets: string[] = ['updated_at = ?'];
  const values: (string | null)[] = [nowISO()];

  if (data.plan) {
    sets.push('plan = ?');
    values.push(data.plan);
  }
  if (data.status) {
    sets.push('status = ?');
    values.push(data.status);
  }
  if (data.stripePriceId) {
    sets.push('stripe_price_id = ?');
    values.push(data.stripePriceId);
  }
  if (data.currentPeriodStart) {
    sets.push('current_period_start = ?');
    values.push(data.currentPeriodStart);
  }
  if (data.currentPeriodEnd) {
    sets.push('current_period_end = ?');
    values.push(data.currentPeriodEnd);
  }

  values.push(licenseId);

  await db.prepare(`
    UPDATE licenses SET ${sets.join(', ')} WHERE id = ?
  `).bind(...values).run();
}

// ============================================================================
// Machine Queries & Mutations
// ============================================================================

/**
 * Register a new machine for a license
 */
export async function registerMachine(
  db: D1Database,
  licenseId: string,
  machineId: string,
  machineName?: string
): Promise<void> {
  const id = generateId();
  const now = nowISO();
  const normalizedMachineId = normalizeMachineId(machineId);

  await db.prepare(`
    INSERT INTO license_machines (
      id, license_id, machine_id, machine_name, is_active, first_seen_at, last_seen_at
    ) VALUES (?, ?, ?, ?, 1, ?, ?)
  `).bind(id, licenseId, normalizedMachineId, machineName ?? null, now, now).run();
}

/**
 * Update machine last_seen_at
 */
export async function updateMachineLastSeen(
  db: D1Database,
  licenseId: string,
  machineId: string
): Promise<void> {
  const normalizedMachineId = normalizeMachineId(machineId);

  await db.prepare(`
    UPDATE license_machines SET last_seen_at = ?
    WHERE license_id = ? AND machine_id = ?
  `).bind(nowISO(), licenseId, normalizedMachineId).run();
}

/**
 * Deactivate a machine
 */
export async function deactivateMachine(
  db: D1Database,
  licenseId: string,
  machineId: string
): Promise<boolean> {
  const normalizedMachineId = normalizeMachineId(machineId);

  const result = await db.prepare(`
    UPDATE license_machines SET is_active = 0
    WHERE license_id = ? AND machine_id = ? AND is_active = 1
  `).bind(licenseId, normalizedMachineId).run();

  return result.meta.changes > 0;
}

/**
 * Record a machine change (for monthly limit tracking)
 */
export async function recordMachineChange(
  db: D1Database,
  licenseId: string,
  newMachineId: string,
  oldMachineId?: string
): Promise<void> {
  const id = generateId();
  const normalizedNewMachineId = normalizeMachineId(newMachineId);

  await db.prepare(`
    INSERT INTO machine_changes (id, license_id, old_machine_id, new_machine_id, changed_at)
    VALUES (?, ?, ?, ?, ?)
  `).bind(
    id,
    licenseId,
    oldMachineId ? normalizeMachineId(oldMachineId) : null,
    normalizedNewMachineId,
    nowISO()
  ).run();
}

// ============================================================================
// User Queries & Mutations
// ============================================================================

/**
 * Find or create user by email
 */
export async function findOrCreateUser(
  db: D1Database,
  email: string,
  stripeCustomerId?: string
): Promise<UserRow> {
  // Try to find existing user
  let user = await db.prepare(`
    SELECT * FROM users WHERE email = ?
  `).bind(email.toLowerCase()).first<UserRow>();

  if (user) {
    // Update Stripe customer ID if provided and different
    if (stripeCustomerId && user.stripe_customer_id !== stripeCustomerId) {
      await db.prepare(`
        UPDATE users SET stripe_customer_id = ?, updated_at = ? WHERE id = ?
      `).bind(stripeCustomerId, nowISO(), user.id).run();
      user.stripe_customer_id = stripeCustomerId;
    }
    return user;
  }

  // Create new user
  const id = generateId();
  const now = nowISO();

  await db.prepare(`
    INSERT INTO users (id, email, stripe_customer_id, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?)
  `).bind(id, email.toLowerCase(), stripeCustomerId ?? null, now, now).run();

  return (await db.prepare('SELECT * FROM users WHERE id = ?').bind(id).first<UserRow>())!;
}

/**
 * Get user by Stripe customer ID
 */
export async function getUserByStripeCustomerId(
  db: D1Database,
  stripeCustomerId: string
): Promise<UserRow | null> {
  const result = await db.prepare(`
    SELECT * FROM users WHERE stripe_customer_id = ?
  `).bind(stripeCustomerId).first<UserRow>();

  return result ?? null;
}

// ============================================================================
// Idempotency
// ============================================================================

/**
 * Check if an event has been processed
 */
export async function isEventProcessed(
  db: D1Database,
  eventId: string
): Promise<boolean> {
  const result = await db.prepare(`
    SELECT 1 FROM processed_events WHERE event_id = ?
  `).bind(eventId).first();

  return result !== null;
}

/**
 * Mark an event as processed
 */
export async function markEventProcessed(
  db: D1Database,
  eventId: string,
  eventType: string
): Promise<void> {
  await db.prepare(`
    INSERT OR IGNORE INTO processed_events (event_id, event_type, processed_at)
    VALUES (?, ?, ?)
  `).bind(eventId, eventType, nowISO()).run();
}

// ============================================================================
// Usage Logging
// ============================================================================

/**
 * Log a usage event
 */
export async function logUsage(
  db: D1Database,
  data: {
    licenseId: string;
    machineId?: string;
    action: 'validate' | 'activate' | 'deactivate' | 'scan';
    resourcesCount?: number;
    metadata?: Record<string, unknown>;
  }
): Promise<void> {
  const id = generateId();

  await db.prepare(`
    INSERT INTO usage_logs (id, license_id, machine_id, action, resources_count, metadata, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
  `).bind(
    id,
    data.licenseId,
    data.machineId ? normalizeMachineId(data.machineId) : null,
    data.action,
    data.resourcesCount ?? 0,
    data.metadata ? JSON.stringify(data.metadata) : null,
    nowISO()
  ).run();
}

/**
 * Get usage count for a license this month
 */
export async function getMonthlyUsageCount(
  db: D1Database,
  licenseId: string,
  action: string
): Promise<number> {
  const result = await db.prepare(`
    SELECT COUNT(*) as count FROM usage_logs
    WHERE license_id = ? AND action = ?
    AND created_at >= datetime('now', 'start of month')
  `).bind(licenseId, action).first<{ count: number }>();

  return result?.count ?? 0;
}

// ============================================================================
// AWS Account Tracking
// ============================================================================

/**
 * Track an AWS account for a license
 */
export async function trackAwsAccount(
  db: D1Database,
  licenseId: string,
  awsAccountId: string,
  accountAlias?: string
): Promise<{ isNew: boolean }> {
  const now = nowISO();

  // Try to update existing
  const updateResult = await db.prepare(`
    UPDATE license_aws_accounts
    SET last_seen_at = ?, is_active = 1
    WHERE license_id = ? AND aws_account_id = ?
  `).bind(now, licenseId, awsAccountId).run();

  if (updateResult.meta.changes > 0) {
    return { isNew: false };
  }

  // Insert new
  const id = generateId();
  await db.prepare(`
    INSERT INTO license_aws_accounts (
      id, license_id, aws_account_id, account_alias, is_active, first_seen_at, last_seen_at
    ) VALUES (?, ?, ?, ?, 1, ?, ?)
  `).bind(id, licenseId, awsAccountId, accountAlias ?? null, now, now).run();

  return { isNew: true };
}

/**
 * Get active AWS account count for a license
 */
export async function getActiveAwsAccountCount(
  db: D1Database,
  licenseId: string
): Promise<number> {
  const result = await db.prepare(`
    SELECT COUNT(*) as count FROM license_aws_accounts
    WHERE license_id = ? AND is_active = 1
  `).bind(licenseId).first<{ count: number }>();

  return result?.count ?? 0;
}
