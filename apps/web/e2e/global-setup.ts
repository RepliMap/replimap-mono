/**
 * Playwright global setup — runs once before any tests.
 *
 * `clerkSetup` reads NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY + CLERK_SECRET_KEY
 * from process.env (populated by dotenv below) and registers a testing
 * token generator so individual tests can call setupClerkTestingToken().
 */

import { clerkSetup } from '@clerk/testing/playwright'
import { config as loadEnv } from 'dotenv'
import { resolve } from 'node:path'

async function globalSetup() {
  loadEnv({ path: resolve(__dirname, '..', '.env.local') })

  if (!process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY) {
    throw new Error(
      'NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY not set — check apps/web/.env.local'
    )
  }
  if (!process.env.CLERK_SECRET_KEY) {
    throw new Error(
      'CLERK_SECRET_KEY not set — check apps/web/.env.local'
    )
  }

  await clerkSetup()
}

export default globalSetup
