/**
 * Tests for license-key email delivery (lib/email.ts).
 *
 * Design constraints under test:
 * - Honest degrade: unconfigured RESEND_API_KEY/EMAIL_FROM never sends
 *   anything and never pretends to — {sent:false, reason:'email_not_configured'}.
 * - Never throws: provider failures (4xx/5xx, network error) resolve to
 *   {sent:false, reason:...} so a flaky email provider can never break a
 *   caller's own success path (payment webhook, API response).
 * - Sends the activation command and license key for every license passed.
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { sendLicenseKeyEmail } from '../src/lib/email';
import type { Env } from '../src/types/env';

const mockFetch = vi.fn();

beforeEach(() => {
  mockFetch.mockReset();
  vi.stubGlobal('fetch', mockFetch);
  vi.spyOn(console, 'error').mockImplementation(() => {});
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

function envWith(overrides: Partial<Env> = {}): Env {
  return {
    RESEND_API_KEY: 're_test_key',
    EMAIL_FROM: 'RepliMap <license@replimap.com>',
    ...overrides,
  } as unknown as Env;
}

const ONE_LICENSE = [{ plan: 'pro', licenseKey: 'RM-TEST-TEST-TEST-TEST' }];

describe('sendLicenseKeyEmail', () => {
  it('degrades honestly (no fetch, sent:false) when RESEND_API_KEY is unset', async () => {
    const result = await sendLicenseKeyEmail(
      envWith({ RESEND_API_KEY: undefined }),
      { to: 'buyer@example.com', licenses: ONE_LICENSE }
    );

    expect(mockFetch).not.toHaveBeenCalled();
    expect(result).toEqual({ sent: false, reason: 'email_not_configured' });
  });

  it('degrades honestly (no fetch, sent:false) when EMAIL_FROM is unset', async () => {
    const result = await sendLicenseKeyEmail(
      envWith({ EMAIL_FROM: undefined }),
      { to: 'buyer@example.com', licenses: ONE_LICENSE }
    );

    expect(mockFetch).not.toHaveBeenCalled();
    expect(result).toEqual({ sent: false, reason: 'email_not_configured' });
  });

  it('returns sent:false, reason:no_licenses for an empty license list without calling the provider', async () => {
    const result = await sendLicenseKeyEmail(envWith(), {
      to: 'buyer@example.com',
      licenses: [],
    });

    expect(mockFetch).not.toHaveBeenCalled();
    expect(result).toEqual({ sent: false, reason: 'no_licenses' });
  });

  it('POSTs to the Resend API with from/to/subject and the activation command when configured', async () => {
    mockFetch.mockResolvedValue(
      new Response(JSON.stringify({ id: 'email_123' }), { status: 200 })
    );

    const result = await sendLicenseKeyEmail(envWith(), {
      to: 'buyer@example.com',
      licenses: ONE_LICENSE,
    });

    expect(result).toEqual({ sent: true });
    expect(mockFetch).toHaveBeenCalledTimes(1);

    const [url, init] = mockFetch.mock.calls[0] as [string, RequestInit];
    expect(url).toBe('https://api.resend.com/emails');
    expect(init.method).toBe('POST');
    expect((init.headers as Record<string, string>).Authorization).toBe(
      'Bearer re_test_key'
    );

    const body = JSON.parse(init.body as string);
    expect(body.from).toBe('RepliMap <license@replimap.com>');
    expect(body.to).toEqual(['buyer@example.com']);
    expect(body.text).toContain('RM-TEST-TEST-TEST-TEST');
    expect(body.text).toContain('replimap license activate RM-TEST-TEST-TEST-TEST');
    expect(body.html).toContain('RM-TEST-TEST-TEST-TEST');
  });

  it('includes every license when multiple are passed', async () => {
    mockFetch.mockResolvedValue(new Response('{}', { status: 200 }));

    await sendLicenseKeyEmail(envWith(), {
      to: 'buyer@example.com',
      licenses: [
        { plan: 'pro', licenseKey: 'RM-AAAA-AAAA-AAAA-AAAA' },
        { plan: 'team', licenseKey: 'RM-BBBB-BBBB-BBBB-BBBB' },
      ],
    });

    const [, init] = mockFetch.mock.calls[0] as [string, RequestInit];
    const body = JSON.parse(init.body as string);
    expect(body.text).toContain('RM-AAAA-AAAA-AAAA-AAAA');
    expect(body.text).toContain('RM-BBBB-BBBB-BBBB-BBBB');
  });

  it('returns sent:false, reason:provider_error on a Resend 4xx response (never throws)', async () => {
    mockFetch.mockResolvedValue(
      new Response(JSON.stringify({ message: 'invalid api key' }), { status: 401 })
    );

    const result = await sendLicenseKeyEmail(envWith(), {
      to: 'buyer@example.com',
      licenses: ONE_LICENSE,
    });

    expect(result).toEqual({ sent: false, reason: 'provider_error' });
  });

  it('returns sent:false, reason:send_exception on a network error (never throws)', async () => {
    mockFetch.mockRejectedValue(new Error('ECONNREFUSED'));

    await expect(
      sendLicenseKeyEmail(envWith(), {
        to: 'buyer@example.com',
        licenses: ONE_LICENSE,
      })
    ).resolves.toEqual({ sent: false, reason: 'send_exception' });
  });
});
