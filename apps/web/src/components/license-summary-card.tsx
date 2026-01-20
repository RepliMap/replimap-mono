import Link from 'next/link';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import type { LicenseDetails } from '@/types/license';

interface LicenseSummaryCardProps {
  license: LicenseDetails | null;
}

export function LicenseSummaryCard({ license }: LicenseSummaryCardProps) {
  if (!license) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">License</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-2xl font-bold text-muted-foreground">No License</p>
          <p className="text-sm text-muted-foreground mt-1">
            Run{' '}
            <code className="text-emerald-400">replimap auth login</code> to
            activate
          </p>
        </CardContent>
      </Card>
    );
  }

  const planColors: Record<string, string> = {
    community: 'text-gray-400',
    pro: 'text-emerald-400',
    team: 'text-purple-400',
    sovereign: 'text-amber-400',
  };

  const statusConfig: Record<string, { color: string; label: string }> = {
    active: { color: 'bg-emerald-500', label: 'Active' },
    canceled: { color: 'bg-amber-500', label: 'Canceled' },
    past_due: { color: 'bg-amber-500', label: 'Past Due' },
    expired: { color: 'bg-red-500', label: 'Expired' },
    revoked: { color: 'bg-red-500', label: 'Revoked' },
  };

  const status = statusConfig[license.status] ?? {
    color: 'bg-gray-500',
    label: license.status,
  };

  return (
    <Link href="/dashboard/license">
      <Card className="hover:border-emerald-500/50 transition-colors cursor-pointer h-full">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-base">License</CardTitle>
            <div className="flex items-center gap-1.5">
              <span
                className={`w-2 h-2 rounded-full ${status.color}`}
                aria-hidden="true"
              />
              <span className="text-xs text-muted-foreground">
                {status.label}
              </span>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <p
            className={`text-2xl font-bold capitalize ${planColors[license.plan] ?? ''}`}
          >
            {license.plan}
          </p>
          <p className="text-sm text-muted-foreground mt-1">
            {license.offline_grace_days > 0
              ? `${license.offline_grace_days} days offline grace`
              : 'Requires internet connection'}
          </p>
        </CardContent>
      </Card>
    </Link>
  );
}
