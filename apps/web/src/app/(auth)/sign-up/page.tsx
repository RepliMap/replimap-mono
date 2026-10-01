"use client";

// @clerk/clerk-react (unlike @clerk/nextjs's SignUp) has no "use client"
// directive of its own — this page must declare the boundary itself so
// Next's RSC compiler treats SignUp's hooks/context as client-side.
//
// Static export prerenders every page at build time (no force-dynamic
// escape hatch), and CI/local builds run with no Clerk key by design (see
// CLAUDE.md landmine 9). <SignUp> throws if rendered without a
// <ClerkProvider> ancestor, and ClerkProviderWrapper deliberately doesn't
// mount one without a valid key — so this page must not render <SignUp>
// unconditionally, mirroring the isClerkConfigured() guard pattern used in
// auth-components.tsx and dashboard/page.tsx.
import { SignUp } from "@clerk/clerk-react";

const isClerkConfigured = (): boolean => {
  const key = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;
  return Boolean(key && key.startsWith("pk_"));
};

function SignUpWidget() {
  return (
    <SignUp
      routing="hash"
      appearance={{
        elements: {
          rootBox: "mx-auto",
          card: "bg-[#030712] border border-slate-800 shadow-2xl",
        },
      }}
    />
  );
}

export default function SignUpPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      {isClerkConfigured() ? (
        <SignUpWidget />
      ) : (
        <p className="text-muted-foreground text-sm">
          Sign-up is not configured in this environment.
        </p>
      )}
    </div>
  );
}
