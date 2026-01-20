import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import type { LicenseDetails } from '@/types/license';

interface LicenseCardProps {
  license: LicenseDetails;
}

export function LicenseCard({ license }: LicenseCardProps) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>License Details</CardTitle>
          <StatusBadge status={license.status} />
        </div>
      </CardHeader>
      <CardContent>
        <dl className="grid grid-cols-2 md:grid-cols-4 gap-6">
          <div>
            <dt className="text-sm text-muted-foreground">Plan</dt>
            <dd className="text-2xl font-bold capitalize mt-1">
              {license.plan}
            </dd>
          </div>

          <div>
            <dt className="text-sm text-muted-foreground">License Key</dt>
            <dd className="font-mono text-sm mt-1">{license.license_key}</dd>
          </div>

          <div>
            <dt className="text-sm text-muted-foreground">Expires</dt>
            <dd className="mt-1">
              {license.expires_at ? (
                <>
                  <span className="font-semibold">
                    {new Date(license.expires_at).toLocaleDateString()}
                  </span>
                  <span className="text-sm text-muted-foreground block">
                    {formatTimeUntil(new Date(license.expires_at))}
                  </span>
                </>
              ) : (
                <span className="text-emerald-500 font-semibold">Never</span>
              )}
            </dd>
          </div>

          <div>
            <dt className="text-sm text-muted-foreground">Active Devices</dt>
            <dd className="text-2xl font-bold mt-1">
              {license.fingerprints.length}
            </dd>
          </div>
        </dl>
      </CardContent>
    </Card>
  );
}

function StatusBadge({ status }: { status: string }) {
  const config: Record<
    string,
    { bg: string; text: string; label: string }
  > = {
    active: {
      bg: 'bg-emerald-500/10',
      text: 'text-emerald-500',
      label: 'Active',
    },
    canceled: {
      bg: 'bg-amber-500/10',
      text: 'text-amber-500',
      label: 'Canceled',
    },
    past_due: {
      bg: 'bg-amber-500/10',
      text: 'text-amber-500',
      label: 'Past Due',
    },
    expired: {
      bg: 'bg-red-500/10',
      text: 'text-red-500',
      label: 'Expired',
    },
    revoked: {
      bg: 'bg-red-500/10',
      text: 'text-red-500',
      label: 'Revoked',
    },
  };

  const { bg, text, label } = config[status] ?? {
    bg: 'bg-gray-500/10',
    text: 'text-gray-500',
    label: status,
  };

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${bg} ${text}`}
    >
      {label}
    </span>
  );
}

function formatTimeUntil(date: Date): string {
  const now = new Date();
  const diff = date.getTime() - now.getTime();

  if (diff < 0) {
    return 'Expired';
  }

  const days = Math.floor(diff / (1000 * 60 * 60 * 24));

  if (days === 0) {
    return 'Today';
  }
  if (days === 1) {
    return 'Tomorrow';
  }
  if (days < 30) {
    return `in ${days} days`;
  }
  if (days < 365) {
    const months = Math.floor(days / 30);
    return `in ${months} month${months > 1 ? 's' : ''}`;
  }

  const years = Math.floor(days / 365);
  return `in ${years} year${years > 1 ? 's' : ''}`;
}
