#!/usr/bin/env node
// Prebuild gate for the static export (see CLAUDE.md landmine 9).
//
// CI/local builds run with no Clerk key by design — clerk-provider.tsx
// skips <ClerkProvider> and the app renders a harmless fallback. That must
// keep succeeding unconditionally.
//
// The Cloudflare deploy build sets REQUIRE_CLERK_KEY=1 and must fail fast,
// before `next build` spends time compiling, if a real publishable key
// isn't present — otherwise we'd ship a static site with auth silently
// disabled. The key itself is never logged.
//
// This runs as a plain Node script (not through `next build`'s own env
// loader), so it loads .env.local / .env itself — same files
// apps/web/.env.local already documents in .env.example. Real process.env
// values (e.g. a CI secret) still win; dotenv never overrides an
// already-set variable.
import { config } from 'dotenv';

config({ path: '.env.local' });
config();

const requireKey = process.env.REQUIRE_CLERK_KEY === '1';

if (!requireKey) {
  process.exit(0);
}

const key = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;

if (!key || !key.startsWith('pk_')) {
  console.error(
    '[check-clerk-key] REQUIRE_CLERK_KEY=1 but NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY ' +
      'is missing or does not start with "pk_". Refusing to build a deploy ' +
      'artifact with auth silently disabled. Set a real Clerk publishable key ' +
      '(from apps/web/.env.local or the deploy environment) and retry.'
  );
  process.exit(1);
}

process.exit(0);
