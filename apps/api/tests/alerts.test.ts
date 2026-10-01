/**
 * Tests for the ops-alert webhook helper (B-3: MANUAL_REVIEW alerting).
 *
 * Design constraints under test:
 * - Receiver-agnostic: one JSON POST that Slack (`text`), Discord (`content`)
 *   and ntfy-style receivers can all consume.
 * - Fail-open: alerting must NEVER break the payment path — unset secret is
 *   a silent no-op, and a failing/unreachable receiver never throws.
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { sendOpsAlert } from '../src/lib/alerts';
import type { Env } from '../src/types/env';

const mockFetch = vi.fn();

beforeEach(() => {
  mockFetch.mockReset();
  mockFetch.mockResolvedValue({ ok: true, status: 200 });
  vi.stubGlobal('fetch', mockFetch);
  vi.spyOn(console, 'error').mockImplementation(() => {});
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

function envWith(webhook: string | undefined): Env {
  return { OPS_ALERT_WEBHOOK: webhook } as unknown as Env;
}

function envWithEmail(overrides: Partial<Env> = {}): Env {
  return {
    OPS_ALERT_EMAIL: 'ops@replimap.test',
    RESEND_API_KEY: 're_test_key',
    EMAIL_FROM: 'RepliMap <alerts@replimap.test>',
    ...overrides,
  } as unknown as Env;
}

function callFor(url: string): RequestInit {
  const call = mockFetch.mock.calls.find(([u]) => u === url);
  if (!call) throw new Error(`no fetch call to ${url}`);
  return call[1] as RequestInit;
}

describe('sendOpsAlert', () => {
  it('is a silent no-op when OPS_ALERT_WEBHOOK is not configured', async () => {
    await sendOpsAlert(envWith(undefined), 'MANUAL_REVIEW', 'detail');
    expect(mockFetch).not.toHaveBeenCalled();
  });

  it('POSTs a Slack/Discord-compatible JSON payload to the configured webhook', async () => {
    await sendOpsAlert(
      envWith('https://hooks.example.test/T000/B000'),
      'MANUAL_REVIEW',
      'Lifetime payment with UNRESOLVABLE plan — session=cs_live_x'
    );

    expect(mockFetch).toHaveBeenCalledTimes(1);
    const [url, init] = mockFetch.mock.calls[0] as [string, RequestInit];
    expect(url).toBe('https://hooks.example.test/T000/B000');
    expect(init.method).toBe('POST');
    expect((init.headers as Record<string, string>)['Content-Type']).toBe(
      'application/json'
    );
    const body = JSON.parse(init.body as string);
    // Same message under both keys: Slack reads `text`, Discord reads `content`.
    expect(body.text).toContain('MANUAL_REVIEW');
    expect(body.text).toContain('cs_live_x');
    expect(body.content).toBe(body.text);
  });

  it('never throws when the receiver is down (fail-open)', async () => {
    mockFetch.mockRejectedValue(new Error('ECONNREFUSED'));
    await expect(
      sendOpsAlert(envWith('https://hooks.example.test/dead'), 'TAG', 'msg')
    ).resolves.toBeUndefined();
  });

  it('never throws on a non-2xx receiver response', async () => {
    mockFetch.mockResolvedValue({ ok: false, status: 410 });
    await expect(
      sendOpsAlert(envWith('https://hooks.example.test/gone'), 'TAG', 'msg')
    ).resolves.toBeUndefined();
  });

  it('is a silent no-op when neither OPS_ALERT_WEBHOOK nor OPS_ALERT_EMAIL is configured', async () => {
    await sendOpsAlert(
      { OPS_ALERT_WEBHOOK: undefined, OPS_ALERT_EMAIL: undefined } as unknown as Env,
      'TAG',
      'detail'
    );
    expect(mockFetch).not.toHaveBeenCalled();
  });

  it('sends only email when only OPS_ALERT_EMAIL is configured', async () => {
    await sendOpsAlert(envWithEmail(), 'MANUAL_REVIEW', 'detail');

    expect(mockFetch).toHaveBeenCalledTimes(1);
    const init = callFor('https://api.resend.com/emails');
    const body = JSON.parse(init.body as string);
    expect(body.to).toEqual(['ops@replimap.test']);
    expect(body.subject).toBe('[RepliMap alert] MANUAL_REVIEW');
    expect(body.text).toContain('MANUAL_REVIEW');
    expect(body.text).toContain('detail');
    expect(body.html).toBeUndefined();
  });

  it('sends only the webhook when only OPS_ALERT_WEBHOOK is configured', async () => {
    await sendOpsAlert(
      { OPS_ALERT_WEBHOOK: 'https://hooks.example.test/T000/B000' } as unknown as Env,
      'MANUAL_REVIEW',
      'detail'
    );

    expect(mockFetch).toHaveBeenCalledTimes(1);
    expect(mockFetch.mock.calls[0][0]).toBe('https://hooks.example.test/T000/B000');
  });

  it('sends both channels when both OPS_ALERT_WEBHOOK and OPS_ALERT_EMAIL are configured', async () => {
    const env = envWithEmail({
      OPS_ALERT_WEBHOOK: 'https://hooks.example.test/T000/B000',
    } as Partial<Env>);

    await sendOpsAlert(env, 'MANUAL_REVIEW', 'detail');

    expect(mockFetch).toHaveBeenCalledTimes(2);
    expect(callFor('https://hooks.example.test/T000/B000')).toBeTruthy();
    expect(callFor('https://api.resend.com/emails')).toBeTruthy();
  });

  it('an email failure never throws and never blocks the webhook from firing', async () => {
    mockFetch.mockImplementation(async (url: string) => {
      if (url === 'https://api.resend.com/emails') {
        throw new Error('ECONNREFUSED');
      }
      return { ok: true, status: 200 };
    });

    const env = envWithEmail({
      OPS_ALERT_WEBHOOK: 'https://hooks.example.test/T000/B000',
    } as Partial<Env>);

    await expect(sendOpsAlert(env, 'TAG', 'msg')).resolves.toBeUndefined();
    expect(callFor('https://hooks.example.test/T000/B000')).toBeTruthy();
  });
});
