/**
 * Database query helpers using Drizzle ORM
 *
 * All functions accept a typed Drizzle client instead of raw D1Database.
 * Handlers should use createDb(env.DB) to create the client.
 */

import { drizzle, type DrizzleD1Database } from 'drizzle-orm/d1';
import { eq, and, sql, desc, gte, like, or, count, sum } from 'drizzle-orm';
import * as schema from '../db/schema';
import { generateId, nowISO, normalizeLicenseKey, normalizeMachineId } from './license';

// Re-export types from schema for convenience
export type {
  License,
  LicenseMachine,
  User,
  UsageLog,
  ProcessedEvent,
  LicenseAwsAccount,
  UsageEvent,
  UsageDaily,
} from '../db/schema';

// ============================================================================
// Database Client Factory
// ============================================================================

export type DrizzleDb = DrizzleD1Database<typeof schema>;

/**
 * Create a typed Drizzle client from a D1Database binding.
 * Call this in your handler and pass the result to all db functions.
 *
 * @example
 * const db = createDb(env.DB);
 * const license = await getLicenseByKey(db, 'RM-XXXX-...');
 */
export const createDb = (d1: D1Database): DrizzleDb => drizzle(d1, { schema });

// ============================================================================
// Query Result Types (for complex aggregates)
// ============================================================================

export interface ValidateLicenseQueryResult {
  license_id: string;
  license_key: string;
  plan: 'free' | 'solo' | 'pro' | 'team';
  status: 'active' | 'canceled' | 'expired' | 'past_due' | 'revoked';
  current_period_end: string | null;
  active_machines: number;
  monthly_changes: number;
  active_aws_accounts: number;
  machine_is_active: number | null;
  machine_last_seen: string | null;
}

// ============================================================================
// License Queries
// ============================================================================

/**
 * Get license by key with machine and change counts.
 * Optimized query for the hot path (validation).
 *
 * NOTE: This uses raw SQL because Drizzle's relational queries don't support
 * inline subquery aggregates with correlated conditions. The performance of
 * a single indexed query is critical here.
 */
export async function getLicenseForValidation(
  db: DrizzleDb,
  licenseKey: string,
  machineId: string
): Promise<ValidateLicenseQueryResult | null> {
  const normalizedKey = normalizeLicenseKey(licenseKey);
  const normalizedMachineId = normalizeMachineId(machineId);

  // Use Drizzle's sql template for type-safe raw SQL
  const result = await db.get<ValidateLicenseQueryResult>(sql`
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
       WHERE lm.license_id = l.id AND lm.machine_id = ${normalizedMachineId}) as machine_is_active,
      (SELECT last_seen_at FROM license_machines lm
       WHERE lm.license_id = l.id AND lm.machine_id = ${normalizedMachineId}) as machine_last_seen
    FROM licenses l
    WHERE l.license_key = ${normalizedKey}
  `);

  return result ?? null;
}

/**
 * Get license by key (simple query)
 */
export async function getLicenseByKey(
  db: DrizzleDb,
  licenseKey: string
): Promise<schema.License | null> {
  const normalizedKey = normalizeLicenseKey(licenseKey);

  const result = await db.query.licenses.findFirst({
    where: eq(schema.licenses.licenseKey, normalizedKey),
  });

  return result ?? null;
}

/**
 * Get license by Stripe subscription ID
 */
export async function getLicenseBySubscriptionId(
  db: DrizzleDb,
  subscriptionId: string
): Promise<schema.License | null> {
  const result = await db.query.licenses.findFirst({
    where: eq(schema.licenses.stripeSubscriptionId, subscriptionId),
  });

  return result ?? null;
}

/**
 * Get all active machines for a license
 */
export async function getActiveMachines(
  db: DrizzleDb,
  licenseId: string
): Promise<schema.LicenseMachine[]> {
  const result = await db.query.licenseMachines.findMany({
    where: and(
      eq(schema.licenseMachines.licenseId, licenseId),
      eq(schema.licenseMachines.isActive, true)
    ),
    orderBy: desc(schema.licenseMachines.lastSeenAt),
  });

  return result;
}

/**
 * Get total count of ALL machines ever registered (active + inactive).
 * Used for abuse detection.
 */
export async function getTotalMachineCount(
  db: DrizzleDb,
  licenseId: string
): Promise<number> {
  const result = await db
    .select({ count: count() })
    .from(schema.licenseMachines)
    .where(eq(schema.licenseMachines.licenseId, licenseId));

  return result[0]?.count ?? 0;
}

/**
 * Get count of ACTIVE devices (seen in last N days).
 * Used for improved abuse detection.
 */
export async function getActiveDeviceCount(
  db: DrizzleDb,
  licenseId: string,
  daysBack: number = 7,
  excludeCI: boolean = true
): Promise<number> {
  const cutoffDate = new Date();
  cutoffDate.setDate(cutoffDate.getDate() - daysBack);
  const cutoffISO = cutoffDate.toISOString();

  if (excludeCI) {
    // Exclude CI patterns using raw SQL for LIKE conditions
    const result = await db.get<{ count: number }>(sql`
      SELECT COUNT(*) as count FROM license_machines
      WHERE license_id = ${licenseId}
        AND last_seen_at >= ${cutoffISO}
        AND machine_id NOT LIKE 'ci-%'
        AND machine_id NOT LIKE 'github-%'
        AND machine_id NOT LIKE 'gitlab-%'
        AND machine_id NOT LIKE '%-ci-%'
        AND machine_id NOT LIKE '%-runner-%'
    `);
    return result?.count ?? 0;
  }

  const result = await db
    .select({ count: count() })
    .from(schema.licenseMachines)
    .where(
      and(
        eq(schema.licenseMachines.licenseId, licenseId),
        gte(schema.licenseMachines.lastSeenAt, cutoffISO)
      )
    );

  return result[0]?.count ?? 0;
}

/**
 * Get count of NEW devices registered in last N hours.
 * Used for detecting rapid churn (key sharing).
 */
export async function getNewDeviceCount(
  db: DrizzleDb,
  licenseId: string,
  hoursBack: number = 24,
  excludeCI: boolean = true
): Promise<number> {
  const cutoffDate = new Date();
  cutoffDate.setHours(cutoffDate.getHours() - hoursBack);
  const cutoffISO = cutoffDate.toISOString();

  if (excludeCI) {
    const result = await db.get<{ count: number }>(sql`
      SELECT COUNT(*) as count FROM license_machines
      WHERE license_id = ${licenseId}
        AND first_seen_at >= ${cutoffISO}
        AND machine_id NOT LIKE 'ci-%'
        AND machine_id NOT LIKE 'github-%'
        AND machine_id NOT LIKE 'gitlab-%'
        AND machine_id NOT LIKE '%-ci-%'
        AND machine_id NOT LIKE '%-runner-%'
    `);
    return result?.count ?? 0;
  }

  const result = await db
    .select({ count: count() })
    .from(schema.licenseMachines)
    .where(
      and(
        eq(schema.licenseMachines.licenseId, licenseId),
        gte(schema.licenseMachines.firstSeenAt, cutoffISO)
      )
    );

  return result[0]?.count ?? 0;
}

/**
 * Get count of active CI devices for a license
 */
export async function getActiveCIDeviceCount(
  db: DrizzleDb,
  licenseId: string,
  daysBack: number = 30
): Promise<number> {
  const cutoffDate = new Date();
  cutoffDate.setDate(cutoffDate.getDate() - daysBack);
  const cutoffISO = cutoffDate.toISOString();

  const result = await db.get<{ count: number }>(sql`
    SELECT COUNT(*) as count FROM license_machines
    WHERE license_id = ${licenseId}
      AND last_seen_at >= ${cutoffISO}
      AND (
        machine_id LIKE 'ci-%'
        OR machine_id LIKE 'github-%'
        OR machine_id LIKE 'gitlab-%'
        OR machine_id LIKE '%-ci-%'
        OR machine_id LIKE '%-runner-%'
      )
  `);

  return result?.count ?? 0;
}

// ============================================================================
// License Mutations
// ============================================================================

/**
 * Create a new license
 */
export async function createLicense(
  db: DrizzleDb,
  data: {
    userId: string;
    licenseKey: string;
    plan: schema.LicensePlan;
    stripeSubscriptionId?: string;
    stripePriceId?: string;
    currentPeriodStart?: string;
    currentPeriodEnd?: string;
  }
): Promise<schema.License> {
  const id = generateId();
  const now = nowISO();

  await db.insert(schema.licenses).values({
    id,
    userId: data.userId,
    licenseKey: data.licenseKey,
    plan: data.plan,
    status: 'active',
    stripeSubscriptionId: data.stripeSubscriptionId ?? null,
    stripePriceId: data.stripePriceId ?? null,
    currentPeriodStart: data.currentPeriodStart ?? null,
    currentPeriodEnd: data.currentPeriodEnd ?? null,
    createdAt: now,
    updatedAt: now,
  });

  const result = await db.query.licenses.findFirst({
    where: eq(schema.licenses.id, id),
  });

  return result!;
}

/**
 * Update license status
 */
export async function updateLicenseStatus(
  db: DrizzleDb,
  licenseId: string,
  status: schema.LicenseStatus
): Promise<void> {
  await db
    .update(schema.licenses)
    .set({ status, updatedAt: nowISO() })
    .where(eq(schema.licenses.id, licenseId));
}

/**
 * Update license plan and period
 */
export async function updateLicensePlan(
  db: DrizzleDb,
  licenseId: string,
  data: {
    plan?: schema.LicensePlan;
    status?: schema.LicenseStatus;
    stripePriceId?: string;
    currentPeriodStart?: string;
    currentPeriodEnd?: string;
  }
): Promise<void> {
  const updates: Partial<schema.License> = { updatedAt: nowISO() };

  if (data.plan) updates.plan = data.plan;
  if (data.status) updates.status = data.status;
  if (data.stripePriceId) updates.stripePriceId = data.stripePriceId;
  if (data.currentPeriodStart) updates.currentPeriodStart = data.currentPeriodStart;
  if (data.currentPeriodEnd) updates.currentPeriodEnd = data.currentPeriodEnd;

  await db
    .update(schema.licenses)
    .set(updates)
    .where(eq(schema.licenses.id, licenseId));
}

// ============================================================================
// Machine Queries & Mutations
// ============================================================================

/**
 * Register a new machine for a license
 */
export async function registerMachine(
  db: DrizzleDb,
  licenseId: string,
  machineId: string,
  machineName?: string
): Promise<void> {
  const id = generateId();
  const now = nowISO();
  const normalizedMachineId = normalizeMachineId(machineId);

  await db.insert(schema.licenseMachines).values({
    id,
    licenseId,
    machineId: normalizedMachineId,
    machineName: machineName ?? null,
    isActive: true,
    firstSeenAt: now,
    lastSeenAt: now,
  });
}

/**
 * Update machine last_seen_at
 */
export async function updateMachineLastSeen(
  db: DrizzleDb,
  licenseId: string,
  machineId: string
): Promise<void> {
  const normalizedMachineId = normalizeMachineId(machineId);

  await db
    .update(schema.licenseMachines)
    .set({ lastSeenAt: nowISO() })
    .where(
      and(
        eq(schema.licenseMachines.licenseId, licenseId),
        eq(schema.licenseMachines.machineId, normalizedMachineId)
      )
    );
}

/**
 * Deactivate a machine
 */
export async function deactivateMachine(
  db: DrizzleDb,
  licenseId: string,
  machineId: string
): Promise<boolean> {
  const normalizedMachineId = normalizeMachineId(machineId);

  const result = await db
    .update(schema.licenseMachines)
    .set({ isActive: false })
    .where(
      and(
        eq(schema.licenseMachines.licenseId, licenseId),
        eq(schema.licenseMachines.machineId, normalizedMachineId),
        eq(schema.licenseMachines.isActive, true)
      )
    );

  return (result.meta?.changes ?? 0) > 0;
}

/**
 * Record a machine change (for monthly limit tracking)
 */
export async function recordMachineChange(
  db: DrizzleDb,
  licenseId: string,
  newMachineId: string,
  oldMachineId?: string
): Promise<void> {
  const id = generateId();
  const normalizedNewMachineId = normalizeMachineId(newMachineId);

  await db.insert(schema.machineChanges).values({
    id,
    licenseId,
    oldMachineId: oldMachineId ? normalizeMachineId(oldMachineId) : null,
    newMachineId: normalizedNewMachineId,
    changedAt: nowISO(),
  });
}

// ============================================================================
// User Queries & Mutations
// ============================================================================

/**
 * Find or create user by email.
 *
 * NOTE: The new schema uses `user` table (singular) and `customerId` (not stripe_customer_id).
 */
export async function findOrCreateUser(
  db: DrizzleDb,
  email: string,
  stripeCustomerId?: string
): Promise<schema.User> {
  const normalizedEmail = email.toLowerCase();

  // Try to find existing user
  let existingUser = await db.query.user.findFirst({
    where: eq(schema.user.email, normalizedEmail),
  });

  if (existingUser) {
    // Update Stripe customer ID if provided and different
    if (stripeCustomerId && existingUser.customerId !== stripeCustomerId) {
      await db
        .update(schema.user)
        .set({ customerId: stripeCustomerId, updatedAt: new Date() })
        .where(eq(schema.user.id, existingUser.id));
      existingUser = { ...existingUser, customerId: stripeCustomerId };
    }
    return existingUser;
  }

  // Create new user
  const id = generateId();
  const now = new Date();

  await db.insert(schema.user).values({
    id,
    name: normalizedEmail.split('@')[0], // Default name from email
    email: normalizedEmail,
    normalizedEmail,
    emailVerified: false,
    customerId: stripeCustomerId ?? null,
    createdAt: now,
    updatedAt: now,
  });

  const newUser = await db.query.user.findFirst({
    where: eq(schema.user.id, id),
  });

  return newUser!;
}

/**
 * Get user by Stripe customer ID
 */
export async function getUserByStripeCustomerId(
  db: DrizzleDb,
  stripeCustomerId: string
): Promise<schema.User | null> {
  const result = await db.query.user.findFirst({
    where: eq(schema.user.customerId, stripeCustomerId),
  });

  return result ?? null;
}

// ============================================================================
// Idempotency
// ============================================================================

/**
 * Check if an event has been processed
 */
export async function isEventProcessed(
  db: DrizzleDb,
  eventId: string
): Promise<boolean> {
  const result = await db.query.processedEvents.findFirst({
    where: eq(schema.processedEvents.eventId, eventId),
  });

  return result !== undefined;
}

/**
 * Mark an event as processed
 */
export async function markEventProcessed(
  db: DrizzleDb,
  eventId: string,
  eventType: string
): Promise<void> {
  await db
    .insert(schema.processedEvents)
    .values({
      eventId,
      eventType,
      processedAt: nowISO(),
    })
    .onConflictDoNothing();
}

// ============================================================================
// Usage Logging
// ============================================================================

/**
 * Log a usage event.
 *
 * NOTE: Metadata is now passed directly as an object — Drizzle handles JSON serialization.
 */
export async function logUsage(
  db: DrizzleDb,
  data: {
    licenseId: string;
    machineId?: string;
    action: schema.UsageAction;
    resourcesCount?: number;
    metadata?: Record<string, unknown>;
  }
): Promise<void> {
  const id = generateId();

  await db.insert(schema.usageLogs).values({
    id,
    licenseId: data.licenseId,
    machineId: data.machineId ? normalizeMachineId(data.machineId) : null,
    action: data.action,
    resourcesCount: data.resourcesCount ?? 0,
    metadata: data.metadata ?? null, // Drizzle handles JSON serialization
    createdAt: nowISO(),
  });
}

/**
 * Get usage count for a license this month
 */
export async function getMonthlyUsageCount(
  db: DrizzleDb,
  licenseId: string,
  action: string
): Promise<number> {
  const result = await db.get<{ count: number }>(sql`
    SELECT COUNT(*) as count FROM usage_logs
    WHERE license_id = ${licenseId} AND action = ${action}
    AND created_at >= datetime('now', 'start of month')
  `);

  return result?.count ?? 0;
}

// ============================================================================
// AWS Account Tracking
// ============================================================================

/**
 * Track an AWS account for a license (upsert pattern)
 */
export async function trackAwsAccount(
  db: DrizzleDb,
  licenseId: string,
  awsAccountId: string,
  accountAlias?: string
): Promise<{ isNew: boolean }> {
  const now = nowISO();

  // Try to update existing
  const updateResult = await db
    .update(schema.licenseAwsAccounts)
    .set({ lastSeenAt: now, isActive: true })
    .where(
      and(
        eq(schema.licenseAwsAccounts.licenseId, licenseId),
        eq(schema.licenseAwsAccounts.awsAccountId, awsAccountId)
      )
    );

  if ((updateResult.meta?.changes ?? 0) > 0) {
    return { isNew: false };
  }

  // Insert new
  const id = generateId();
  await db.insert(schema.licenseAwsAccounts).values({
    id,
    licenseId,
    awsAccountId,
    accountAlias: accountAlias ?? null,
    isActive: true,
    firstSeenAt: now,
    lastSeenAt: now,
  });

  return { isNew: true };
}

/**
 * Get active AWS account count for a license
 */
export async function getActiveAwsAccountCount(
  db: DrizzleDb,
  licenseId: string
): Promise<number> {
  const result = await db
    .select({ count: count() })
    .from(schema.licenseAwsAccounts)
    .where(
      and(
        eq(schema.licenseAwsAccounts.licenseId, licenseId),
        eq(schema.licenseAwsAccounts.isActive, true)
      )
    );

  return result[0]?.count ?? 0;
}

// ============================================================================
// Daily Usage Aggregation
// ============================================================================

/**
 * Record a usage event using daily aggregation (upsert pattern).
 * Uses Drizzle's onConflictDoUpdate for atomic increment.
 */
export async function recordDailyUsage(
  db: DrizzleDb,
  licenseId: string,
  eventType: string,
  resourceCount: number = 0
): Promise<void> {
  const today = new Date().toISOString().split('T')[0]; // YYYY-MM-DD
  const now = nowISO();

  await db
    .insert(schema.usageDaily)
    .values({
      id: generateId(),
      licenseId,
      date: today,
      eventType,
      count: 1,
      resourceCount,
      createdAt: now,
      updatedAt: now,
    })
    .onConflictDoUpdate({
      target: [schema.usageDaily.licenseId, schema.usageDaily.date, schema.usageDaily.eventType],
      set: {
        count: sql`${schema.usageDaily.count} + 1`,
        resourceCount: sql`${schema.usageDaily.resourceCount} + ${resourceCount}`,
        updatedAt: now,
      },
    });
}

/**
 * Get daily usage count for a specific event type this month.
 *
 * HYBRID READ: Reads from both legacy usage_events and new usage_daily
 * to avoid losing data during the transition period.
 */
export async function getDailyUsageCount(
  db: DrizzleDb,
  licenseId: string,
  eventType: string
): Promise<number> {
  const startOfMonth = new Date();
  startOfMonth.setDate(1);
  startOfMonth.setHours(0, 0, 0, 0);
  const startDate = startOfMonth.toISOString().split('T')[0];
  const startDateTime = startOfMonth.toISOString();

  // HYBRID READ: Sum from both legacy and new tables
  const [legacyResult, newResult] = await Promise.all([
    db.get<{ count: number }>(sql`
      SELECT COUNT(*) as count
      FROM usage_events
      WHERE license_id = ${licenseId} AND event_type = ${eventType} AND created_at >= ${startDateTime}
    `),
    db.get<{ total: number }>(sql`
      SELECT COALESCE(SUM(count), 0) as total
      FROM usage_daily
      WHERE license_id = ${licenseId} AND event_type = ${eventType} AND date >= ${startDate}
    `),
  ]);

  const legacyCount = legacyResult?.count ?? 0;
  const newCount = newResult?.total ?? 0;

  return legacyCount + newCount;
}

// ============================================================================
// Device Cleanup
// ============================================================================

/**
 * Wipe all devices for a license (hard delete).
 * Used when downgrading plans to enforce new device limits.
 */
export async function wipeAllDevices(
  db: DrizzleDb,
  licenseId: string
): Promise<number> {
  const result = await db
    .delete(schema.licenseMachines)
    .where(eq(schema.licenseMachines.licenseId, licenseId));

  return result.meta?.changes ?? 0;
}

/**
 * Deactivate all devices for a license (soft wipe).
 */
export async function deactivateAllDevices(
  db: DrizzleDb,
  licenseId: string
): Promise<number> {
  const result = await db
    .update(schema.licenseMachines)
    .set({ isActive: false })
    .where(
      and(
        eq(schema.licenseMachines.licenseId, licenseId),
        eq(schema.licenseMachines.isActive, true)
      )
    );

  return result.meta?.changes ?? 0;
}
