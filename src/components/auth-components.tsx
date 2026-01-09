"use client";

import { ReactNode } from "react";
import {
  SignedIn as ClerkSignedIn,
  SignedOut as ClerkSignedOut,
  SignInButton as ClerkSignInButton,
  UserButton as ClerkUserButton,
} from "@clerk/nextjs";

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
