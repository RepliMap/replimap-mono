/**
 * E2E: negative checks for the authenticated checkout API.
 *
 *   - create without a token            → 401
 *   - create with an off-allowlist URL  → 400
 *   - lookup without a token            → 401
 *   - lookup of a created-but-unpaid session (the original exploit)
 *     must not return a license key     → 404
 */

import { test, expect } from '@playwright/test'
import {
  createTestUser,
  setupClerkForPage,
  CLERK_TEST_OTP,
} from './fixtures/test-user'

test.describe('Checkout API auth (negative)', () => {
  test.setTimeout(120_000)

  test('rejects anonymous/off-origin requests and never leaks an unpaid license', async ({
    page,
    request,
  }) => {
    await setupClerkForPage(page)
    const user = createTestUser()
    const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8787'
    const appUrl = process.env.E2E_BASE_URL ?? 'http://localhost:3100'

    await page.goto('/sign-up')
    await page.getByLabel(/email/i).first().fill(user.email)
    await page.getByLabel(/password/i).first().fill(user.password)
    await page.getByRole('button', { name: /continue|sign up/i }).first().click()
    const otpInput = page
      .getByRole('textbox', { name: /verification code|code/i })
      .first()
    try {
      await otpInput.waitFor({ timeout: 10_000 })
      await otpInput.fill(CLERK_TEST_OTP)
      const verifyBtn = page.getByRole('button', { name: /continue|verify/i }).first()
      if (await verifyBtn.isVisible().catch(() => false)) await verifyBtn.click()
    } catch {
      // Auto-verified
    }
    await page.waitForURL(/\/dashboard/, { timeout: 30_000 })

    await page.waitForFunction(
      () => !!(window as unknown as { Clerk?: { session?: unknown } }).Clerk?.session,
      undefined,
      { timeout: 30_000 }
    )
    const token = await page.evaluate(
      async () =>
        (
          window as unknown as {
            Clerk?: { session?: { getToken: () => Promise<string | null> } }
          }
        ).Clerk?.session?.getToken() ?? null
    )
    expect(token).toBeTruthy()
    const auth = { Authorization: `Bearer ${token}` }

    const goodBody = {
      plan: 'pro',
      billing_period: 'lifetime',
      success_url: `${appUrl}/checkout/success`,
      cancel_url: `${appUrl}/checkout`,
    }

    const anonCreate = await request.post(`${apiUrl}/v1/checkout/session`, {
      data: goodBody,
    })
    expect(anonCreate.status()).toBe(401)

    const evil = await request.post(`${apiUrl}/v1/checkout/session`, {
      headers: auth,
      data: { ...goodBody, success_url: 'https://evil.example/x' },
    })
    expect(evil.status()).toBe(400)

    const anonLookup = await request.get(
      `${apiUrl}/v1/checkout/session/cs_test_x/license`
    )
    expect(anonLookup.status()).toBe(401)

    // Original exploit: create a session, look it up before paying.
    const created = await request.post(`${apiUrl}/v1/checkout/session`, {
      headers: auth,
      data: goodBody,
    })
    expect(created.status()).toBe(200)
    const { session_id: sessionId } = (await created.json()) as {
      session_id: string
    }
    const unpaid = await request.get(
      `${apiUrl}/v1/checkout/session/${sessionId}/license`,
      { headers: auth }
    )
    expect(unpaid.status()).toBe(404)
    expect(await unpaid.text()).not.toContain('license_key')
  })
})
