/**
 * Ops alerting — push critical operational signals to a human.
 *
 * Motivation (checklist §1.5 / followups B-3): `[Stripe][MANUAL_REVIEW]`
 * means money was received but no license could be issued. A console.error
 * in a Worker nobody tails is not an alert; this helper POSTs the same
 * signal to a webhook a human actually sees, and/or emails it.
 *
 * Design:
 * - Receiver-agnostic: single JSON POST carrying the message under both
 *   `text` (Slack incoming webhook) and `content` (Discord webhook); plain
 *   webhook receivers (ntfy, PagerDuty events proxy, custom) can read either.
 * - Email channel (`OPS_ALERT_EMAIL`, via lib/email.ts's Resend sender) is
 *   independent of the webhook: either, both, or neither may be configured.
 * - Fail-open by contract, per channel: an unset `OPS_ALERT_WEBHOOK` /
 *   `OPS_ALERT_EMAIL` is a silent no-op for that channel, and NO failure of
 *   either receiver may ever propagate into the caller, or block the other
 *   channel — alerting must never break payment processing. Failures are
 *   logged with the ALERT_DELIVERY_FAILED token so they remain greppable.
 */

import type { Env } from '../types/env';
import { sendPlainTextEmail } from './email';

const ALERT_TIMEOUT_MS = 5_000;

/**
 * Send the alert to the configured webhook. Resolves (never rejects)
 * regardless of receiver availability.
 */
async function sendWebhookAlert(
  env: Env,
  tag: string,
  message: string
): Promise<void> {
  const webhook = env.OPS_ALERT_WEBHOOK;
  if (!webhook) return;

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

/**
 * Send the alert by email via lib/email.ts. Resolves (never rejects)
 * regardless of provider availability — mirrors sendWebhookAlert's
 * fail-open contract so an email outage never blocks the webhook (or
 * vice versa).
 */
async function sendEmailAlert(
  env: Env,
  tag: string,
  message: string
): Promise<void> {
  const to = env.OPS_ALERT_EMAIL;
  if (!to) return;

  try {
    const result = await sendPlainTextEmail(env, {
      to,
      subject: `[RepliMap alert] ${tag}`,
      text: message,
    });
    if (!result.sent) {
      console.error(
        `[Alerts][ALERT_DELIVERY_FAILED] Email reason=${result.reason} for tag=${tag}`
      );
    }
  } catch (error) {
    // sendPlainTextEmail already resolves rather than rejects, but guard
    // here too so a future change to that contract can never throw into
    // the payment path.
    console.error(
      `[Alerts][ALERT_DELIVERY_FAILED] ${error instanceof Error ? error.message : String(error)} for tag=${tag}`
    );
  }
}

/**
 * Send an operational alert to every configured channel (webhook, email,
 * both, or neither). Resolves (never rejects) regardless of any channel's
 * availability; each channel is independently fail-open.
 */
export async function sendOpsAlert(
  env: Env,
  tag: string,
  detail: string
): Promise<void> {
  const message = `[RepliMap][${tag}] ${detail}`;

  await Promise.all([
    sendWebhookAlert(env, tag, message),
    sendEmailAlert(env, tag, message),
  ]);
}
