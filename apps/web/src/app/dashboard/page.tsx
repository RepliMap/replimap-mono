import { currentUser } from '@clerk/nextjs/server';
import { redirect } from 'next/navigation';
import { DashboardLicenseSection } from '@/components/dashboard/dashboard-license-section';

// Force dynamic rendering - this page requires auth
export const dynamic = 'force-dynamic';

export default async function DashboardPage() {
  const user = await currentUser();

  if (!user) {
    redirect('/sign-in');
  }

  const displayName =
    user.firstName || user.emailAddresses[0]?.emailAddress || 'User';

  return (
    <div className="min-h-screen bg-background pt-20">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-foreground mb-2">
          Welcome, {displayName}
        </h1>
        <p className="text-muted-foreground mb-8">Your RepliMap Dashboard</p>

        {/* License + devices are loaded client-side (from the browser) so
            Cloudflare Bot Fight Mode does not block the request. */}
        <DashboardLicenseSection />
      </div>
    </div>
  );
}
