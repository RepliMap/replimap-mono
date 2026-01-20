'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogClose,
} from '@/components/ui/dialog';
import {
  FingerprintBadge,
  getDeviceLabel,
  truncateFingerprint,
} from '@/components/fingerprint-badge';
import { deactivateDevice } from '@/lib/api';
import type { Fingerprint } from '@/types/license';

interface DeviceListProps {
  devices: Fingerprint[];
  licenseKey: string;
  machinesLimit: number;
}

export function DeviceList({
  devices,
  licenseKey,
  machinesLimit,
}: DeviceListProps) {
  const router = useRouter();
  const [deactivating, setDeactivating] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleDeactivate = async (fingerprint: string) => {
    setDeactivating(fingerprint);
    setError(null);

    try {
      await deactivateDevice({
        license_key: licenseKey,
        machine_fingerprint: fingerprint,
      });
      router.refresh();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to deactivate device'
      );
    } finally {
      setDeactivating(null);
    }
  };

  const limitText =
    machinesLimit === -1
      ? `${devices.length} devices`
      : `${devices.length} / ${machinesLimit} devices`;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Active Devices</CardTitle>
          <span className="text-sm text-muted-foreground">{limitText}</span>
        </div>
      </CardHeader>
      <CardContent>
        {error && (
          <div className="mb-4 p-3 rounded bg-red-500/10 text-red-500 text-sm">
            {error}
          </div>
        )}

        {devices.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <div className="text-4xl mb-2">📱</div>
            <p>No devices activated yet</p>
            <p className="text-sm mt-1">
              Run{' '}
              <code className="text-emerald-400">replimap auth login</code> to
              activate a device
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {devices.map((device) => (
              <DeviceRow
                key={device.fingerprint}
                device={device}
                isDeactivating={deactivating === device.fingerprint}
                onDeactivate={() => handleDeactivate(device.fingerprint)}
              />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

interface DeviceRowProps {
  device: Fingerprint;
  isDeactivating: boolean;
  onDeactivate: () => void;
}

function DeviceRow({ device, isDeactivating, onDeactivate }: DeviceRowProps) {
  const [open, setOpen] = useState(false);

  const handleConfirm = () => {
    setOpen(false);
    onDeactivate();
  };

  return (
    <div className="flex items-center justify-between p-4 rounded-lg bg-muted/50">
      <div className="flex items-center gap-4">
        <FingerprintBadge type={device.type} size="lg" />

        <div>
          <div className="font-medium">
            {getDeviceLabel(
              device.type,
              device.ci_provider,
              device.container_type
            )}
          </div>

          {device.type === 'ci' && device.ci_repo && (
            <div className="text-sm text-muted-foreground">
              {device.ci_provider}: {device.ci_repo}
            </div>
          )}

          <div className="text-xs text-muted-foreground font-mono">
            {truncateFingerprint(device.fingerprint)}
          </div>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <span className="text-sm text-muted-foreground">
          {formatTimeAgo(new Date(device.last_seen))}
        </span>

        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button
              variant="ghost"
              size="sm"
              disabled={isDeactivating}
              className="text-red-500 hover:text-red-500 hover:bg-red-500/10"
            >
              {isDeactivating ? 'Removing...' : 'Remove'}
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Remove Device?</DialogTitle>
              <DialogDescription>
                This will deactivate the license on this device. The device will
                need to re-authenticate to use RepliMap again.
              </DialogDescription>
            </DialogHeader>
            <DialogFooter>
              <DialogClose asChild>
                <Button variant="outline">Cancel</Button>
              </DialogClose>
              <Button variant="destructive" onClick={handleConfirm}>
                Remove Device
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
}

function formatTimeAgo(date: Date): string {
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const seconds = Math.floor(diff / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  if (days > 0) {
    return days === 1 ? '1 day ago' : `${days} days ago`;
  }
  if (hours > 0) {
    return hours === 1 ? '1 hour ago' : `${hours} hours ago`;
  }
  if (minutes > 0) {
    return minutes === 1 ? '1 minute ago' : `${minutes} minutes ago`;
  }
  return 'Just now';
}
