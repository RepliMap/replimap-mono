"use client";

// Static export note: this deliberately imports the framework-agnostic
// @clerk/clerk-react ClerkProvider instead of @clerk/nextjs's. @clerk/nextjs's
// App Router ClerkProvider unconditionally imports Server Action modules
// (its "keyless mode" dev-convenience feature) — merely importing it, even
// behind our own isClerkConfigured() runtime branch, makes `next build`
// fail under `output: 'export'` ("Server Actions are not supported with
// static export"), because Next's action-manifest scan walks the whole
// module graph regardless of which branch actually renders. The app has no
// server runtime left anyway (static export + client-side auth only), so
// @clerk/clerk-react's plain SPA provider is the correct fit, not a
// workaround. Hooks/components behave identically — @clerk/nextjs's Core 2
// re-exports them from @clerk/clerk-react unmodified.
import { ClerkProvider as BaseClerkProvider } from "@clerk/clerk-react";
import { dark } from "@clerk/themes";

const clerkAppearance = {
  baseTheme: dark,
  variables: {
    colorPrimary: "#10b981",
    colorBackground: "#030712",
    colorInputBackground: "#0a0a0a",
    colorInputText: "#f5f5f5",
    colorText: "#f5f5f5",
    colorTextSecondary: "#94a3b8",
  },
  elements: {
    formButtonPrimary: "bg-emerald-500 hover:bg-emerald-600 text-white",
    card: "bg-[#030712] border border-slate-800 shadow-2xl",
    headerTitle: "text-white",
    headerSubtitle: "text-slate-400",
    socialButtonsBlockButton:
      "bg-slate-800 border-slate-700 text-white hover:bg-slate-700",
    socialButtonsBlockButtonText: "text-white",
    formFieldLabel: "text-slate-300",
    formFieldInput:
      "bg-slate-900 border-slate-700 text-white placeholder:text-slate-500",
    footerActionLink: "text-emerald-400 hover:text-emerald-300",
    identityPreviewText: "text-white",
    identityPreviewEditButton: "text-emerald-400",
  },
} as const;

export function ClerkProviderWrapper({
  children,
}: {
  children: React.ReactNode;
}) {
  const publishableKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;

  // Skip Clerk if no valid key (allows build without credentials)
  if (!publishableKey || !publishableKey.startsWith("pk_")) {
    return <>{children}</>;
  }

  // Hardcoded fallbacks (not just `|| ""`): @clerk/nextjs's own
  // mergeNextClerkPropsWithEnv falls back to "" when these env vars are
  // absent, which silently sends users to Clerk's hosted Account Portal and
  // back to "/" instead of "/dashboard" — a design-reviewer-flagged risk if
  // the Cloudflare deploy build environment ever omits one of these while
  // still carrying a real publishable key. These match .env.example.
  return (
    <BaseClerkProvider
      publishableKey={publishableKey}
      signInUrl={process.env.NEXT_PUBLIC_CLERK_SIGN_IN_URL || "/sign-in"}
      signUpUrl={process.env.NEXT_PUBLIC_CLERK_SIGN_UP_URL || "/sign-up"}
      signInFallbackRedirectUrl={
        process.env.NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL || "/dashboard"
      }
      signUpFallbackRedirectUrl={
        process.env.NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL || "/dashboard"
      }
      appearance={clerkAppearance}
    >
      {children}
    </BaseClerkProvider>
  );
}
