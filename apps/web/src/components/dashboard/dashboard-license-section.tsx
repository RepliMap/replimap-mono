'use client';

import Link from 'next/link';
import { getMachinesLimit } from '@/lib/api';
import { useLicense } from '@/hooks/useLicense';
import { LicenseSummaryCard } from '@/components/license-summary-card';
import { DeviceSummaryCard } from '@/components/device-summary-card';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';

/**
 * License + devices overview for the main dashboard. Loads the license from the
 * browser (see useLicense) so Cloudflare Bot Fight Mode does not block it.
 */
export function DashboardLicenseSection() {
  const { state } = useLicense();

  if (state.status === 'loading') {
    return <LicenseSectionSkeleton />;
  }

  // A details failure degrades to the "No License" summary here (same as the
  // previous server-rendered behavior); only a provisioning failure surfaces
  // the actionable error banner.
  const license = state.status === 'ready' ? state.license : null;
  const licenseError = state.status === 'error' ? state.message : null;

  return (
    <>
      {licenseError && (
        <div
          role="alert"
          className="mb-6 p-4 rounded-lg border border-red-500/30 bg-red-500/5 text-sm text-foreground"
        >
          ⚠️ {licenseError}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <LicenseSummaryCard license={license} />
        <DeviceSummaryCard
          devices={license?.fingerprints ?? []}
          limit={getMachinesLimit(license?.plan ?? 'community')}
        />
        <QuickStartCard hasLicense={!!license} />
      </div>

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
    </>
  );
}

function LicenseSectionSkeleton() {
  return (
    <div
      className="grid grid-cols-1 md:grid-cols-3 gap-6"
      aria-busy="true"
      aria-label="Loading your license"
    >
      {[0, 1, 2].map((i) => (
        <Card key={i} className="h-full">
          <CardHeader>
            <div className="h-4 w-24 rounded bg-muted animate-pulse" />
          </CardHeader>
          <CardContent>
            <div className="h-8 w-32 rounded bg-muted animate-pulse" />
            <div className="mt-2 h-3 w-40 rounded bg-muted animate-pulse" />
          </CardContent>
        </Card>
      ))}
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
