import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';

interface GracePeriodInfoProps {
  graceDays: number;
  plan: string;
}

export function GracePeriodInfo({ graceDays, plan }: GracePeriodInfoProps) {
  if (graceDays === 0) {
    return (
      <Card className="border-amber-500/30 bg-amber-500/5">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-base">Offline Mode</CardTitle>
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-500/10 text-amber-500">
              Online Required
            </span>
          </div>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Your <span className="font-semibold capitalize">{plan}</span> plan
            requires an internet connection to validate your license. Consider
            upgrading for offline grace period.
          </p>
          <div className="mt-4">
            <UpgradeHint currentPlan={plan} />
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="border-emerald-500/30 bg-emerald-500/5">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">Offline Mode</CardTitle>
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-500">
            {graceDays} Days Grace
          </span>
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground">
          Your license can work offline for up to{' '}
          <span className="font-semibold">{graceDays} days</span> without
          contacting the server. After that, you&apos;ll need to reconnect to
          continue using RepliMap.
        </p>

        {graceDays >= 365 && (
          <div className="mt-3 p-3 rounded bg-emerald-500/10">
            <div className="flex items-center gap-2">
              <span className="text-lg">🏛️</span>
              <span className="font-semibold text-emerald-400">
                Sovereign Grade
              </span>
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Suitable for air-gapped and highly regulated environments.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function UpgradeHint({ currentPlan }: { currentPlan: string }) {
  const upgrades: Record<string, { plan: string; days: number }> = {
    community: { plan: 'Pro', days: 7 },
    pro: { plan: 'Team', days: 14 },
    team: { plan: 'Sovereign', days: 365 },
  };

  const hint = upgrades[currentPlan];

  if (!hint) return null;

  return (
    <p className="text-xs text-muted-foreground">
      💡 Upgrade to <span className="font-semibold">{hint.plan}</span> for{' '}
      {hint.days} days offline grace.
    </p>
  );
}
