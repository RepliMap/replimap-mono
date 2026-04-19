/**
 * E2E: Community tier signup flow (fully automated).
 *
 * Covers:
 *   Landing → Click "Get Started Free" → Clerk sign-up → Dashboard
 *   → Community license auto-provisioned → License visible
 *
 * Prereqs: CLERK_TESTING_TOKEN env var (see e2e/README.md).
 */

import { test, expect } from '@playwright/test'
import {
  createTestUser,
  setupClerkTestingToken,
} from './fixtures/test-user'

test.describe('Community signup flow', () => {
  test('new user can sign up, reach dashboard, and see a community license', async ({
    page,
  }) => {
    await setupClerkTestingToken(page)

    const user = createTestUser()

    // 1. Landing page
    await page.goto('/')
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible()

    // 2. Click hero "Get Started Free"
    await page
      .getByRole('link', { name: /get started free/i })
      .first()
      .click()

    // 3. Clerk sign-up page
    await page.waitForURL(/sign-up/, { timeout: 10_000 })

    // Clerk renders in an iframe for the modal variant, but our custom
    // /sign-up route renders inline. Wait for the email input.
    const emailInput = page.getByLabel(/email/i).first()
    await emailInput.waitFor({ timeout: 15_000 })
    await emailInput.fill(user.email)

    const passwordInput = page.getByLabel(/password/i).first()
    await passwordInput.fill(user.password)

    await page.getByRole('button', { name: /continue|sign up/i }).first().click()

    // 4. Dashboard (Clerk testing token skips email verification)
    await page.waitForURL(/\/dashboard/, { timeout: 30_000 })

    // 5. License visible with community plan
    // LicenseSummaryCard renders the plan name; wait for it.
    await expect(page.getByText(/community/i).first()).toBeVisible({
      timeout: 15_000,
    })
  })

  test('API directly provisions a community license for a new email (sanity check)', async ({
    request,
  }) => {
    const user = createTestUser()
    const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8787'

    const response = await request.post(
      `${apiUrl}/v1/license/provision-community`,
      {
        data: { email: user.email },
      }
    )

    // 201 (created) on first call, 200 (existed) on retry
    expect([200, 201]).toContain(response.status())

    const body = (await response.json()) as {
      license_key: string
      plan: string
      created: boolean
    }
    expect(body.plan).toBe('community')
    expect(body.license_key).toMatch(/^RM-[A-Z0-9-]+$/)
    expect(body.created).toBe(true)

    // Second call returns the same license (idempotency)
    const retry = await request.post(
      `${apiUrl}/v1/license/provision-community`,
      {
        data: { email: user.email },
      }
    )
    const retryBody = (await retry.json()) as {
      license_key: string
      created: boolean
    }
    expect(retryBody.license_key).toBe(body.license_key)
    expect(retryBody.created).toBe(false)
  })
})
