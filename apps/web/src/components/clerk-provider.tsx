"use client";

import { ClerkProvider as BaseClerkProvider } from "@clerk/nextjs";
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

  return (
    <BaseClerkProvider appearance={clerkAppearance}>
      {children}
    </BaseClerkProvider>
  );
}
