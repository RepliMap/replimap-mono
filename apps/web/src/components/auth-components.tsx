"use client";

import { ReactNode } from "react";
// See clerk-provider.tsx for why this imports @clerk/clerk-react instead of
// @clerk/nextjs (Server Actions incompatible with `output: 'export'`).
import {
  SignedIn as ClerkSignedIn,
  SignedOut as ClerkSignedOut,
  SignInButton as ClerkSignInButton,
  UserButton as ClerkUserButton,
  RedirectToSignIn as ClerkRedirectToSignIn,
} from "@clerk/clerk-react";

// Check if Clerk is configured
const isClerkConfigured = (): boolean => {
  const key = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;
  return Boolean(key && key.startsWith("pk_"));
};

/**
 * Renders children only when user is signed in.
 * Falls back to nothing if Clerk is not configured.
 */
export function SignedIn({ children }: { children: ReactNode }) {
  if (!isClerkConfigured()) {
    return null;
  }
  return <ClerkSignedIn>{children}</ClerkSignedIn>;
}

/**
 * Renders children only when user is signed out.
 * Falls back to always showing children if Clerk is not configured.
 */
export function SignedOut({ children }: { children: ReactNode }) {
  if (!isClerkConfigured()) {
    return <>{children}</>;
  }
  return <ClerkSignedOut>{children}</ClerkSignedOut>;
}

/**
 * Sign in button wrapper.
 * Falls back to nothing if Clerk is not configured.
 */
export function SignInButton({
  children,
  mode,
}: {
  children: ReactNode;
  mode?: "modal" | "redirect";
}) {
  if (!isClerkConfigured()) {
    return null;
  }
  return <ClerkSignInButton mode={mode}>{children}</ClerkSignInButton>;
}

/**
 * Client-side route guard for /dashboard(.*) and /checkout(.*) — replaces
 * the old clerkMiddleware() matcher now that the app is a static export
 * (no middleware/server runtime to run auth.protect() in). <SignedIn>/
 * <SignedOut> render nothing until Clerk has finished loading, so no
 * protected content flashes before auth resolves.
 *
 * Falls back to always showing children if Clerk is not configured (the
 * CI static-export build has no key — see check-clerk-key.mjs). Real
 * deploys always carry a valid key (REQUIRE_CLERK_KEY=1 enforces it), so
 * this fallback branch never gates real traffic.
 */
export function RequireAuth({ children }: { children: ReactNode }) {
  if (!isClerkConfigured()) {
    return <>{children}</>;
  }
  return (
    <>
      <ClerkSignedIn>{children}</ClerkSignedIn>
      <ClerkSignedOut>
        <ClerkRedirectToSignIn />
      </ClerkSignedOut>
    </>
  );
}

/**
 * Mounts `children` only when Clerk is configured; otherwise mounts
 * `fallback` (default: nothing).
 *
 * Use this to wrap any component tree that calls a raw Clerk hook
 * (`useUser`, `useAuth`, …) — e.g. `DashboardLicenseSection`,
 * `LicensePageContent`, `CheckoutForm`. Those hooks throw ("useUser can
 * only be used within <ClerkProvider>") if called while unconfigured, and
 * static export prerenders every page at build time (no force-dynamic to
 * defer the render), so the CI/local no-key build would otherwise fail.
 * Because this is a *rendering* branch (React never calls the child
 * component function when the fallback branch is taken), it does not
 * violate the rules of hooks the way conditionally calling the hook
 * itself would.
 */
export function ClerkGate({
  children,
  fallback = null,
}: {
  children: ReactNode;
  fallback?: ReactNode;
}) {
  if (!isClerkConfigured()) {
    return <>{fallback}</>;
  }
  return <>{children}</>;
}

/**
 * User button wrapper.
 * Falls back to nothing if Clerk is not configured.
 */
export function UserButton({
  appearance,
}: {
  appearance?: {
    elements?: Record<string, string>;
  };
}) {
  if (!isClerkConfigured()) {
    return null;
  }
  return <ClerkUserButton appearance={appearance} />;
}
