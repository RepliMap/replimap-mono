'use client';

import Link from 'next/link';
import { getMachinesLimit } from '@/lib/api';
import { licenseFingerprints } from '@/lib/license-view';
import { useLicense, type LicenseState } from '@/hooks/useLicense';
import { LicenseCard } from '@/components/license-card';
import { DeviceList } from '@/components/device-list';
import { GracePeriodInfo } from '@/components/grace-period-info';

/**
 * License detail page body. Loads the license from the browser (see useLicense)
 * so Cloudflare Bot Fight Mode does not block it.
 */
export function LicensePageContent() {
  const { state, reload } = useLicense();

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

        <LicenseBody state={state} reload={reload} />
      </div>
    </div>
  );
}

function LicenseBody({
  state,
  reload,
}: {
  state: LicenseState;
  reload: () => void;
}) {
  if (state.status === 'loading') {
    return <LoadingState />;
  }

  if (state.status === 'error') {
    return <ErrorState message={state.message} />;
  }

  // Provisioning succeeded but the details lookup failed — the user has a
  // license, so this is an error to retry, not an empty state.
  if (!state.license) {
    return <ErrorState message="Failed to load license details." />;
  }

  const { license, licenseKey } = state;
  return (
    <div className="space-y-6">
      <LicenseCard license={license} />
      <GracePeriodInfo
        graceDays={license.offline_grace_days}
        plan={license.plan}
      />
      <DeviceList
        devices={licenseFingerprints(license)}
        licenseKey={licenseKey}
        machinesLimit={getMachinesLimit(license.plan)}
        onDeactivated={reload}
      />
    </div>
  );
}

function LoadingState() {
  return (
    <div
      className="p-8 rounded-lg border border-border bg-card text-center"
      aria-busy="true"
    >
      <div className="text-4xl mb-4 animate-pulse">🔑</div>
      <p className="text-muted-foreground">Loading your license…</p>
    </div>
  );
}

function ErrorState({ message }: { message: string }) {
  return (
    <div className="p-8 rounded-lg border border-red-500/30 bg-red-500/5 text-center">
      <div className="text-6xl mb-4">⚠️</div>
      <h2 className="text-xl font-semibold mb-2">Failed to Load License</h2>
      <p className="text-muted-foreground">{message}</p>
    </div>
  );
}
