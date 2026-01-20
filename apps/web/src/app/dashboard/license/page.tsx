import { currentUser } from '@clerk/nextjs/server';
import { redirect } from 'next/navigation';
import Link from 'next/link';
import { getLicenseDetails, getUserLicenseKey, getMachinesLimit } from '@/lib/api';
import { LicenseCard } from '@/components/license-card';
import { DeviceList } from '@/components/device-list';
import { GracePeriodInfo } from '@/components/grace-period-info';

export const dynamic = 'force-dynamic';

export default async function LicensePage() {
  const user = await currentUser();

  if (!user) {
    redirect('/sign-in');
  }

  // Get user's license key
  const licenseKey = await getUserLicenseKey(user.id);

  if (!licenseKey) {
    return (
      <div className="min-h-screen bg-background pt-20">
        <div className="max-w-4xl mx-auto px-4 py-8">
          <div className="flex items-center justify-between mb-6">
            <h1 className="text-3xl font-bold">License</h1>
            <Link
              href="/dashboard"
              className="text-sm text-muted-foreground hover:text-foreground"
            >
              ← Back to Dashboard
            </Link>
          </div>
          <NoLicenseState />
        </div>
      </div>
    );
  }

  // Get license details
  let license;
  try {
    license = await getLicenseDetails(licenseKey);
  } catch (error) {
    return (
      <div className="min-h-screen bg-background pt-20">
        <div className="max-w-4xl mx-auto px-4 py-8">
          <div className="flex items-center justify-between mb-6">
            <h1 className="text-3xl font-bold">License</h1>
            <Link
              href="/dashboard"
              className="text-sm text-muted-foreground hover:text-foreground"
            >
              ← Back to Dashboard
            </Link>
          </div>
          <ErrorState error={error} />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background pt-20">
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-bold">License</h1>
          <Link
            href="/dashboard"
            className="text-sm text-muted-foreground hover:text-foreground"
          >
            ← Back to Dashboard
          </Link>
        </div>

        <div className="space-y-6">
          {/* License overview card */}
          <LicenseCard license={license} />

          {/* Offline grace period info */}
          <GracePeriodInfo
            graceDays={license.offline_grace_days}
            plan={license.plan}
          />

          {/* Activated devices list */}
          <DeviceList
            devices={license.fingerprints}
            licenseKey={licenseKey}
            machinesLimit={getMachinesLimit(license.plan)}
          />
        </div>
      </div>
    </div>
  );
}

function NoLicenseState() {
  return (
    <div className="p-8 rounded-lg border border-border bg-card text-center">
      <div className="text-6xl mb-4">🔑</div>
      <h2 className="text-xl font-semibold mb-2">No License Found</h2>
      <p className="text-muted-foreground mb-4">
        Install the CLI and activate your license to get started.
      </p>
      <code className="bg-slate-900 text-emerald-400 px-4 py-2 rounded block max-w-md mx-auto">
        pip install replimap && replimap auth login
      </code>
    </div>
  );
}

function ErrorState({ error }: { error: unknown }) {
  return (
    <div className="p-8 rounded-lg border border-red-500/30 bg-red-500/5 text-center">
      <div className="text-6xl mb-4">⚠️</div>
      <h2 className="text-xl font-semibold mb-2">Failed to Load License</h2>
      <p className="text-muted-foreground">
        {error instanceof Error ? error.message : 'An unexpected error occurred'}
      </p>
    </div>
  );
}
