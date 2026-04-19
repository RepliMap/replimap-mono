/**
 * E2E: Pro tier checkout flow (requires stripe listen + local API).
 *
 * Covers:
 *   Sign in → /checkout?plan=pro&billing=monthly → Stripe hosted page
 *   → fill test card 4242 → /checkout/success?session_id=X
 *   → poll resolves to license key → activate API accepts the key
 *
 * Prereqs:
 *   - CLERK_TESTING_TOKEN env var
 *   - `stripe listen --forward-to localhost:8787/v1/webhooks/stripe` running
 *   - `apps/api` (wrangler dev) running on :8787
 *   - `apps/web` (next dev) running on :3000
 *
 * The harness script `scripts/e2e-commercial-flow.sh` sets all of this up.
 */

import { test, expect } from '@playwright/test'
import {
  createTestUser,
  setupClerkTestingToken,
} from './fixtures/test-user'

test.describe('Pro checkout flow', () => {
  test.setTimeout(180_000)

  test('paying user reaches success page and receives a license key', async ({
    page,
    request,
  }) => {
    await setupClerkTestingToken(page)
    const user = createTestUser()
    const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8787'

    // 1. Sign up first so Clerk session exists for /checkout
    await page.goto('/sign-up')
    await page.getByLabel(/email/i).first().fill(user.email)
    await page.getByLabel(/password/i).first().fill(user.password)
    await page.getByRole('button', { name: /continue|sign up/i }).first().click()
    await page.waitForURL(/\/dashboard/, { timeout: 30_000 })

    // 2. Navigate to checkout
    await page.goto('/checkout?plan=pro&billing=monthly')
    await expect(page.getByRole('heading', { level: 1 })).toContainText(
      /subscribe.*pro/i
    )

    // 3. Click "Continue to Payment"
    await page
      .getByRole('button', { name: /continue to payment/i })
      .click()

    // 4. Stripe-hosted checkout page
    await page.waitForURL(/checkout\.stripe\.com/, { timeout: 30_000 })

    // Stripe renders inputs inside iframes. We target by label text.
    await page.getByLabel('Email').fill(user.email)
    await page.getByLabel('Card number').fill('4242 4242 4242 4242')
    await page.getByLabel('Expiration').fill('12 / 35')
    await page.getByLabel('CVC').fill('123')
    await page.getByLabel('Cardholder name').fill('E2E Test')

    // Country/ZIP may or may not be shown depending on Stripe test settings
    const zipInput = page.getByLabel(/zip|postal/i)
    if (await zipInput.count()) {
      await zipInput.first().fill('94103')
    }

    await page.getByTestId('hosted-payment-submit-button').click()

    // 5. Redirect back to success page
    await page.waitForURL(/\/checkout\/success\?session_id=cs_/, {
      timeout: 60_000,
    })

    // 6. License key reveal (polling handles webhook lag)
    const licenseKey = page
      .locator('code')
      .filter({ hasText: /^RM-/ })
      .first()
    await expect(licenseKey).toBeVisible({ timeout: 30_000 })
    const keyText = (await licenseKey.textContent())?.trim()
    expect(keyText).toMatch(/^RM-[A-Z0-9-]+$/)

    // 7. Activate the license via API — end-to-end proof
    const fingerprint = 'a'.repeat(32) // valid 32-char hex
    const activateRes = await request.post(
      `${apiUrl}/v1/license/activate`,
      {
        data: {
          license_key: keyText,
          machine_fingerprint: fingerprint,
          machine_name: 'e2e-test-machine',
          fingerprint_type: 'developer_workstation',
        },
      }
    )
    expect(activateRes.status()).toBe(200)
    const activateBody = (await activateRes.json()) as {
      activated: boolean
      license_blob: string
      plan: string
    }
    expect(activateBody.activated).toBe(true)
    expect(activateBody.license_blob).toBeTruthy()
    expect(activateBody.plan).toBe('pro')
  })
})
