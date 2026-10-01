/**
 * Data retention (run by the daily cron trigger).
 *
 * Every step is isolated: one failing statement (for example a table that is
 * missing in some environment) never prevents the other steps from running.
 * Any failure is logged and reported through the ops alert helper.
 *
 * Timestamp formats: stored values are mixed. JS writes ISO strings
 * (`2026-10-01T12:00:00.000Z`) while column defaults and `datetime('now')`
 * write `2026-10-01 12:00:00`. Every comparison therefore normalises the
 * column with `datetime(col)` so both formats compare correctly.
 *
 * What is deliberately NOT done:
 * - Active `license_machines` rows are never modified or deleted. The CLI only
 *   contacts the server on activation, so idle time says nothing about
 *   whether a machine is still legitimately in use.
 * - Offline-license ledger rows in `usage_logs` (metadata kind =
 *   'offline_issue') are never purged. They are the issuance audit trail.
 */

import type { Env } from '../types/env';
import { sendOpsAlert } from './alerts';

/** Retention window for usage_logs, machine_changes and deactivated machines. */
export const RETENTION_DAYS = 90;
/** Retention window for usage_idempotency keys. */
export const IDEMPOTENCY_RETENTION_DAYS = 7;
/** Retention window for processed Stripe webhook event ids. */
export const PROCESSED_EVENTS_RETENTION_DAYS = 30;

/**
 * Tables no endpoint writes to any more. Rows are removed on every run so
 * that nothing written by earlier versions of the API lingers.
 */
export const ORPHAN_TABLES = [
  'license_aws_accounts',
  'usage_events',
  'usage_daily',
  'snapshots',
  'remediations',
] as const;

/** usage_logs rows written by the offline-blob endpoint (action 'activate'). */
const NOT_OFFLINE_LEDGER_ROW = `
  COALESCE(
    CASE WHEN action = 'activate' AND json_valid(metadata)
         THEN json_extract(metadata, '$.kind') END,
    ''
  ) != 'offline_issue'`;

interface RetentionStep {
  name: string;
  sql: string;
}

function buildSteps(): RetentionStep[] {
  const orphanSteps = ORPHAN_TABLES.map((table) => ({
    name: `purge ${table}`,
    sql: `DELETE FROM ${table}`,
  }));

  return [
    ...orphanSteps,
    {
      name: 'delete deactivated license_machines',
      sql: `DELETE FROM license_machines
            WHERE is_active = 0
              AND datetime(last_seen_at) < datetime('now', '-${RETENTION_DAYS} days')`,
    },
    {
      name: 'delete old usage_logs',
      sql: `DELETE FROM usage_logs
            WHERE datetime(created_at) < datetime('now', '-${RETENTION_DAYS} days')
              AND ${NOT_OFFLINE_LEDGER_ROW}`,
    },
    {
      name: 'delete old machine_changes',
      sql: `DELETE FROM machine_changes
            WHERE datetime(changed_at) < datetime('now', '-${RETENTION_DAYS} days')`,
    },
    {
      name: 'delete old usage_idempotency',
      sql: `DELETE FROM usage_idempotency
            WHERE datetime(created_at) < datetime('now', '-${IDEMPOTENCY_RETENTION_DAYS} days')`,
    },
    {
      name: 'delete old processed_events',
      sql: `DELETE FROM processed_events
            WHERE datetime(processed_at) < datetime('now', '-${PROCESSED_EVENTS_RETENTION_DAYS} days')`,
    },
  ];
}

export interface RetentionResult {
  deleted: Record<string, number>;
  failed: string[];
}

export async function runRetention(env: Env): Promise<RetentionResult> {
  const deleted: Record<string, number> = {};
  const failures: string[] = [];

  for (const step of buildSteps()) {
    try {
      const result = await env.DB.prepare(step.sql).run();
      deleted[step.name] = result.meta?.changes ?? 0;
      console.log(`[Cron] ${step.name}: ${deleted[step.name]} rows`);
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      failures.push(`${step.name}: ${message}`);
      console.error(`[Cron] Step failed (${step.name}):`, message);
    }
  }

  if (failures.length > 0) {
    await sendOpsAlert(
      env,
      'RETENTION_STEP_FAILED',
      `${failures.length} retention step(s) failed. ${failures.join(' | ')}`
    );
  }

  return { deleted, failed: failures };
}
