/**
 * Ops alerting — push critical operational signals to a human.
 *
 * Motivation (checklist §1.5 / followups B-3): `[Stripe][MANUAL_REVIEW]`
 * means money was received but no license could be issued. A console.error
 * in a Worker nobody tails is not an alert; this helper POSTs the same
 * signal to a webhook a human actually sees.
 *
 * Design:
 * - Receiver-agnostic: single JSON POST carrying the message under both
 *   `text` (Slack incoming webhook) and `content` (Discord webhook); plain
 *   webhook receivers (ntfy, PagerDuty events proxy, custom) can read either.
 * - Fail-open by contract: an unset `OPS_ALERT_WEBHOOK` is a silent no-op,
 *   and NO failure of the receiver may ever propagate into the caller —
 *   alerting must never break payment processing. Failures are logged with
 *   the ALERT_DELIVERY_FAILED token so they remain greppable.
 */

import type { Env } from '../types/env';

const ALERT_TIMEOUT_MS = 5_000;

/**
 * Send an operational alert to the configured webhook. Resolves (never
 * rejects) regardless of receiver availability.
 */
export async function sendOpsAlert(
  env: Env,
  tag: string,
  detail: string
): Promise<void> {
  const webhook = env.OPS_ALERT_WEBHOOK;
  if (!webhook) return;

  const message = `[RepliMap][${tag}] ${detail}`;

  try {
    const response = await fetch(webhook, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: message, content: message }),
      signal: AbortSignal.timeout(ALERT_TIMEOUT_MS),
    });
    if (!response.ok) {
      console.error(
        `[Alerts][ALERT_DELIVERY_FAILED] Webhook responded ${response.status} for tag=${tag}`
      );
    }
  } catch (error) {
    console.error(
      `[Alerts][ALERT_DELIVERY_FAILED] ${error instanceof Error ? error.message : String(error)} for tag=${tag}`
    );
  }
}
