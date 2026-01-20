import { currentUser } from '@clerk/nextjs/server';
import { redirect } from 'next/navigation';
import Link from 'next/link';
import { getLicenseDetails, getUserLicenseKey, getMachinesLimit } from '@/lib/api';
import { LicenseSummaryCard } from '@/components/license-summary-card';
import { DeviceSummaryCard } from '@/components/device-summary-card';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

// Force dynamic rendering - this page requires auth
export const dynamic = 'force-dynamic';

export default async function DashboardPage() {
  const user = await currentUser();

  if (!user) {
    redirect('/sign-in');
  }

  const displayName =
    user.firstName || user.emailAddresses[0]?.emailAddress || 'User';

  // Try to get license
  const licenseKey = await getUserLicenseKey(user.id);
  let license = null;

  if (licenseKey) {
    try {
      license = await getLicenseDetails(licenseKey);
    } catch {
      // Ignore error, show default state
    }
  }

  return (
    <div className="min-h-screen bg-background pt-20">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-foreground mb-2">
          Welcome, {displayName}
        </h1>
        <p className="text-muted-foreground mb-8">Your RepliMap Dashboard</p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* License overview */}
          <LicenseSummaryCard license={license} />

          {/* Device overview */}
          <DeviceSummaryCard
            devices={license?.fingerprints ?? []}
            limit={getMachinesLimit(license?.plan ?? 'community')}
          />

          {/* Quick start */}
          <QuickStartCard hasLicense={!!license} />
        </div>

        {/* Quick links if license exists */}
        {license && (
          <div className="mt-8">
            <h2 className="text-xl font-semibold mb-4">Quick Links</h2>
            <div className="flex flex-wrap gap-4">
              <Link
                href="/dashboard/license"
                className="text-emerald-500 hover:underline"
              >
                View License Details →
              </Link>
              <Link href="/docs" className="text-emerald-500 hover:underline">
                Documentation →
              </Link>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function QuickStartCard({ hasLicense }: { hasLicense: boolean }) {
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="text-base">Quick Start</CardTitle>
      </CardHeader>
      <CardContent>
        {hasLicense ? (
          <>
            <p className="text-sm text-muted-foreground mb-3">
              Run a scan to visualize your AWS infrastructure:
            </p>
            <code className="text-sm text-emerald-400 bg-slate-900 px-3 py-2 rounded block">
              replimap scan
            </code>
          </>
        ) : (
          <>
            <p className="text-sm text-muted-foreground mb-3">
              Install the CLI to get started:
            </p>
            <code className="text-sm text-emerald-400 bg-slate-900 px-3 py-2 rounded block mb-3">
              pip install replimap
            </code>
            <p className="text-sm text-muted-foreground mb-2">
              Then authenticate:
            </p>
            <code className="text-sm text-emerald-400 bg-slate-900 px-3 py-2 rounded block">
              replimap auth login
            </code>
          </>
        )}
      </CardContent>
    </Card>
  );
}
