import { cn } from '@/lib/utils';
import type { FingerprintType } from '@/types/license';

interface FingerprintBadgeProps {
  type: FingerprintType;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
}

const config: Record<
  FingerprintType,
  { icon: string; label: string; bg: string }
> = {
  machine: {
    icon: '💻',
    label: 'Local Machine',
    bg: 'bg-blue-500/10',
  },
  ci: {
    icon: '🔄',
    label: 'CI/CD',
    bg: 'bg-green-500/10',
  },
  container: {
    icon: '📦',
    label: 'Container',
    bg: 'bg-purple-500/10',
  },
};

export function FingerprintBadge({
  type,
  size = 'md',
  showLabel = false,
}: FingerprintBadgeProps) {
  const { icon, label, bg } = config[type] ?? config.machine;

  const sizeClasses = {
    sm: 'w-8 h-8 text-lg',
    md: 'w-10 h-10 text-xl',
    lg: 'w-12 h-12 text-2xl',
  };

  return (
    <div className="flex items-center gap-2">
      <div
        className={cn(
          'rounded-lg flex items-center justify-center',
          sizeClasses[size],
          bg
        )}
      >
        {icon}
      </div>
      {showLabel && <span className="text-sm font-medium">{label}</span>}
    </div>
  );
}

/**
 * Get device label based on fingerprint type and metadata
 */
export function getDeviceLabel(
  type: FingerprintType,
  ciProvider?: string | null,
  containerType?: string | null
): string {
  switch (type) {
    case 'machine':
      return 'Local Machine';
    case 'ci':
      return ciProvider
        ? `${ciProvider.charAt(0).toUpperCase() + ciProvider.slice(1)} CI`
        : 'CI/CD Pipeline';
    case 'container':
      return containerType || 'Container';
    default:
      return 'Unknown Device';
  }
}

/**
 * Truncate fingerprint for display
 */
export function truncateFingerprint(fingerprint: string): string {
  if (fingerprint.length < 12) {
    return fingerprint;
  }
  return `${fingerprint.slice(0, 8)}...${fingerprint.slice(-4)}`;
}
