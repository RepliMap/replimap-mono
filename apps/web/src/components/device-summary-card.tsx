import Link from 'next/link';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import type { Fingerprint } from '@/types/license';

interface DeviceSummaryCardProps {
  devices: Fingerprint[];
  limit: number;
}

export function DeviceSummaryCard({ devices, limit }: DeviceSummaryCardProps) {
  const limitText = limit === -1 ? 'Unlimited' : `${devices.length}/${limit}`;

  // Count by type
  const counts = {
    machine: devices.filter((d) => d.type === 'machine').length,
    ci: devices.filter((d) => d.type === 'ci').length,
    container: devices.filter((d) => d.type === 'container').length,
  };

  return (
    <Link href="/dashboard/license">
      <Card className="hover:border-emerald-500/50 transition-colors cursor-pointer h-full">
        <CardHeader>
          <CardTitle className="text-base">Active Devices</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-2xl font-bold">{limitText}</p>

          {devices.length > 0 ? (
            <div className="flex gap-3 mt-2">
              {counts.machine > 0 && (
                <span className="text-sm text-muted-foreground">
                  💻 {counts.machine}
                </span>
              )}
              {counts.ci > 0 && (
                <span className="text-sm text-muted-foreground">
                  🔄 {counts.ci}
                </span>
              )}
              {counts.container > 0 && (
                <span className="text-sm text-muted-foreground">
                  📦 {counts.container}
                </span>
              )}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground mt-1">
              No devices activated yet
            </p>
          )}
        </CardContent>
      </Card>
    </Link>
  );
}
