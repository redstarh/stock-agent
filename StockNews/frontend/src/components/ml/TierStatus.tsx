/** Tier progress status panel. */

interface TierInfo {
  tier: number;
  features: number;
  minSamples: number;
  label: string;
}

const TIERS: TierInfo[] = [
  { tier: 1, features: 8, minSamples: 200, label: 'Core' },
  { tier: 2, features: 16, minSamples: 500, label: 'Extended' },
  { tier: 3, features: 20, minSamples: 1000, label: 'Advanced' },
];

interface Props {
  currentSamples: number;
  activeTier: number | null;
}

export default function TierStatus({ currentSamples, activeTier }: Props) {
  return (
    <div className="rounded-lg border bg-white p-6 shadow-sm">
      <h3 className="mb-4 text-sm font-semibold text-gray-500">Tier Status</h3>
      <div className="space-y-3">
        {TIERS.map(t => {
          const isActive = activeTier === t.tier;
          const isReady = currentSamples >= t.minSamples;
          const progress = Math.min((currentSamples / t.minSamples) * 100, 100);

          return (
            <div key={t.tier} className="space-y-1">
              <div className="flex items-center justify-between text-sm">
                <span className={isActive ? 'font-bold text-blue-600' : isReady ? 'text-green-600' : 'text-gray-500'}>
                  T{t.tier}: {t.label} ({t.features}f)
                </span>
                <span className="text-xs text-gray-400">
                  {isActive ? 'Active' : isReady ? 'Ready' : `${currentSamples}/${t.minSamples}`}
                </span>
              </div>
              <div className="h-1.5 w-full rounded-full bg-gray-100">
                <div
                  className={`h-1.5 rounded-full transition-all ${isActive ? 'bg-blue-500' : isReady ? 'bg-green-400' : 'bg-gray-300'}`}
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
