'use client';

import Link from 'next/link';
import { graceDays, machinesToFingerprints } from '@/lib/license-view';
import { useLicense, type LicenseState } from '@/hooks/useLicense';
import { useMachines, type MachinesState } from '@/hooks/useMachines';
import { LicenseCard } from '@/components/license-card';
import { DeviceList } from '@/components/device-list';
import { GracePeriodInfo } from '@/components/grace-period-info';
import { Card, CardContent } from '@/components/ui/card';

/**
 * License detail page body. License AND devices load from the browser
 * (see useLicense/useMachines) so Cloudflare Bot Fight Mode does not block
 * the requests.
 */
export function LicensePageContent() {
  const { state } = useLicense();
  const licenseKey = state.status === 'ready' ? state.licenseKey : null;
  const machines = useMachines(licenseKey);

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

        <LicenseBody
          state={state}
          machines={machines.state}
          reloadMachines={machines.reload}
        />
      </div>
    </div>
  );
}

function LicenseBody({
  state,
  machines,
  reloadMachines,
}: {
  state: LicenseState;
  machines: MachinesState;
  reloadMachines: () => void;
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
      <GracePeriodInfo graceDays={graceDays(license)} plan={license.plan} />
      <DevicesSection
        machines={machines}
        licenseKey={licenseKey}
        onDeactivated={reloadMachines}
      />
    </div>
  );
}

/** Device list with its own loading / error / ready states. */
function DevicesSection({
  machines,
  licenseKey,
  onDeactivated,
}: {
  machines: MachinesState;
  licenseKey: string;
  onDeactivated: () => void;
}) {
  if (machines.status === 'loading' || machines.status === 'idle') {
    return (
      <Card>
        <CardContent className="py-8 text-center" aria-busy="true">
          <div className="text-3xl mb-2 animate-pulse">📱</div>
          <p className="text-sm text-muted-foreground">Loading devices…</p>
        </CardContent>
      </Card>
    );
  }

  if (machines.status === 'error') {
    return (
      <Card className="border-red-500/30 bg-red-500/5">
        <CardContent className="py-6 text-center">
          <p className="text-sm text-muted-foreground">⚠️ {machines.message}</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <DeviceList
      devices={machinesToFingerprints(machines.data.machines)}
      licenseKey={licenseKey}
      machinesLimit={machines.data.limit}
      onDeactivated={onDeactivated}
    />
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
