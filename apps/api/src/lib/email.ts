/**
 * License key email delivery — Resend HTTP API.
 *
 * Design (2026-07 fix — replaces the previously-stubbed `sendEmail` in
 * handlers/user.ts that unconditionally returned {sent:true} without
 * sending anything):
 * - Plain `fetch` call to the Resend HTTP API. No SDK dependency — this is
 *   a Cloudflare Worker, and a single POST doesn't warrant one.
 * - Honest degrade: if RESEND_API_KEY or EMAIL_FROM is unset, this returns
 *   {sent:false, reason:'email_not_configured'} instead of throwing or
 *   pretending to have sent anything. Callers decide how to surface that.
 * - Never throws: provider failures resolve to {sent:false, reason:...} so
 *   a flaky email provider can never break a payment webhook or an API
 *   response. Mirrors the fail-open contract of lib/alerts.ts.
 */

import type { Env } from '../types/env';
import { REPLIMAP_URLS } from './constants';

const RESEND_API_URL = 'https://api.resend.com/emails';
const EMAIL_TIMEOUT_MS = 10_000;

export interface LicenseEmailInfo {
  plan: string;
  licenseKey: string;
}

export interface SendLicenseKeyEmailResult {
  sent: boolean;
  /** Present when sent=false — machine-readable reason, safe to expose to API callers. */
  reason?: 'email_not_configured' | 'no_licenses' | 'provider_error' | 'send_exception';
}

export interface SendEmailResult {
  sent: boolean;
  /** Present when sent=false — machine-readable reason. */
  reason?: 'email_not_configured' | 'provider_error' | 'send_exception';
}

/**
 * Low-level Resend POST shared by every email sender in this module.
 * Resolves (never rejects) regardless of provider availability.
 */
async function postEmail(
  env: Env,
  params: { to: string; subject: string; text: string; html?: string }
): Promise<SendEmailResult> {
  if (!env.RESEND_API_KEY || !env.EMAIL_FROM) {
    return { sent: false, reason: 'email_not_configured' };
  }

  try {
    const response = await fetch(RESEND_API_URL, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${env.RESEND_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        from: env.EMAIL_FROM,
        to: [params.to],
        subject: params.subject,
        text: params.text,
        ...(params.html ? { html: params.html } : {}),
      }),
      signal: AbortSignal.timeout(EMAIL_TIMEOUT_MS),
    });

    if (!response.ok) {
      const detail = await response.text().catch(() => '');
      console.error(
        `[Email][SEND_FAILED] Resend responded ${response.status}: ${detail.slice(0, 500)}`
      );
      return { sent: false, reason: 'provider_error' };
    }

    return { sent: true };
  } catch (error) {
    console.error(
      `[Email][SEND_FAILED] ${error instanceof Error ? error.message : String(error)}`
    );
    return { sent: false, reason: 'send_exception' };
  }
}

/**
 * Send an email containing one or more license keys to the given address.
 *
 * Resolves (never rejects) regardless of provider availability — callers
 * (webhook handlers, the resend-key endpoint) must never let this fail their
 * own success path.
 */
export async function sendLicenseKeyEmail(
  env: Env,
  params: { to: string; licenses: LicenseEmailInfo[] }
): Promise<SendLicenseKeyEmailResult> {
  if (!env.RESEND_API_KEY || !env.EMAIL_FROM) {
    return { sent: false, reason: 'email_not_configured' };
  }

  if (params.licenses.length === 0) {
    return { sent: false, reason: 'no_licenses' };
  }

  const { subject, text, html } = buildLicenseEmailContent(params.licenses);
  return postEmail(env, { to: params.to, subject, text, html });
}

/**
 * Send a plain-text email (no license content). Used by lib/alerts.ts to
 * mirror an ops alert over email when OPS_ALERT_EMAIL is configured.
 *
 * Same fail-open contract as sendLicenseKeyEmail: resolves, never rejects.
 */
export async function sendPlainTextEmail(
  env: Env,
  params: { to: string; subject: string; text: string }
): Promise<SendEmailResult> {
  return postEmail(env, params);
}

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function buildLicenseEmailContent(licenses: LicenseEmailInfo[]): {
  subject: string;
  text: string;
  html: string;
} {
  const subject =
    licenses.length === 1
      ? `Your RepliMap ${capitalize(licenses[0].plan)} license key`
      : 'Your RepliMap license keys';

  const textBlocks = licenses
    .map(
      (l) =>
        `Plan: ${capitalize(l.plan)}\n` +
        `License key: ${l.licenseKey}\n` +
        `Activate: replimap license activate ${l.licenseKey}`
    )
    .join('\n\n');

  const text =
    `Here ${licenses.length === 1 ? 'is your RepliMap license key' : 'are your RepliMap license keys'}.\n\n` +
    `${textBlocks}\n\n` +
    `Dashboard: ${REPLIMAP_URLS.dashboard}\n`;

  const htmlBlocks = licenses
    .map(
      (l) => `
        <div style="margin: 16px 0; padding: 16px; border: 1px solid #e2e8f0; border-radius: 8px;">
          <p style="margin: 0 0 8px; color: #64748b; font-size: 13px; text-transform: uppercase;">${escapeHtml(capitalize(l.plan))} plan</p>
          <code style="display: block; padding: 12px; background: #0f172a; color: #34d399; border-radius: 6px; font-size: 14px; letter-spacing: 0.05em;">${escapeHtml(l.licenseKey)}</code>
          <p style="margin: 12px 0 0; color: #475569; font-size: 13px;">Activate with:</p>
          <code style="display: block; padding: 8px 12px; background: #f1f5f9; border-radius: 6px; font-size: 13px;">replimap license activate ${escapeHtml(l.licenseKey)}</code>
        </div>`
    )
    .join('');

  const html = `
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 480px; margin: 0 auto;">
      <h1 style="font-size: 18px; color: #0f172a;">Your RepliMap license ${licenses.length === 1 ? 'key' : 'keys'}</h1>
      ${htmlBlocks}
      <p style="margin-top: 24px;">
        <a href="${REPLIMAP_URLS.dashboard}" style="color: #10b981;">View your dashboard</a>
      </p>
    </div>`;

  return { subject, text, html };
}

function capitalize(value: string): string {
  return value.length === 0 ? value : value.charAt(0).toUpperCase() + value.slice(1);
}
