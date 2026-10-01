'use client';

// See clerk-provider.tsx for why this imports @clerk/clerk-react instead of
// @clerk/nextjs.
import { useUser } from '@clerk/clerk-react';
import { ClerkGate } from '@/components/auth-components';
import { DashboardLicenseSection } from '@/components/dashboard/dashboard-license-section';

function WelcomeHeadingWithUser() {
  const { user } = useUser();
  const displayName =
    user?.firstName || user?.primaryEmailAddress?.emailAddress || 'User';

  return (
    <h1 className="text-3xl font-bold text-foreground mb-2">
      Welcome, {displayName}
    </h1>
  );
}

export default function DashboardPage() {
  return (
    <div className="min-h-screen bg-background pt-20">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <ClerkGate
          fallback={
            <h1 className="text-3xl font-bold text-foreground mb-2">
              Welcome
            </h1>
          }
        >
          <WelcomeHeadingWithUser />
        </ClerkGate>
        <p className="text-muted-foreground mb-8">Your RepliMap Dashboard</p>

        {/* License + devices are loaded client-side (from the browser) so
            Cloudflare Bot Fight Mode does not block the request. Gated by
            ClerkGate: useLicense() calls useAuth(), which throws without a
            <ClerkProvider> ancestor (see auth-components.tsx). */}
        <ClerkGate>
          <DashboardLicenseSection />
        </ClerkGate>
      </div>
    </div>
  );
}
