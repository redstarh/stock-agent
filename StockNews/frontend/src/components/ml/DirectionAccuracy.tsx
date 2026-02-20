/** Per-direction accuracy display. */

interface Props {
  precision: Record<string, number> | null;
  recall: Record<string, number> | null;
  f1: Record<string, number> | null;
}

const DIRECTION_CONFIG: Record<string, { label: string; color: string }> = {
  up: { label: 'Up', color: 'text-green-600' },
  down: { label: 'Down', color: 'text-red-600' },
  neutral: { label: 'Neutral', color: 'text-gray-600' },
};

export default function DirectionAccuracy({ precision, recall, f1 }: Props) {
  if (!precision || !recall || !f1) {
    return (
      <div className="flex h-48 items-center justify-center rounded-lg border bg-white">
        <p className="text-sm text-gray-400">No evaluation data</p>
      </div>
    );
  }

  const directions = Object.keys(precision);

  return (
    <div className="rounded-lg border bg-white p-4 shadow-sm">
      <h3 className="mb-4 text-sm font-semibold text-gray-500">Direction Accuracy</h3>
      <div className="space-y-3">
        {directions.map(dir => {
          const config = DIRECTION_CONFIG[dir] ?? { label: dir, color: 'text-gray-600' };
          const p = (precision[dir] * 100).toFixed(1);
          const r = (recall[dir] * 100).toFixed(1);
          const f = (f1[dir] * 100).toFixed(1);

          return (
            <div key={dir} className="flex items-center justify-between">
              <span className={`text-sm font-medium ${config.color}`}>{config.label}</span>
              <div className="flex gap-4 text-xs text-gray-500">
                <span>P: {p}%</span>
                <span>R: {r}%</span>
                <span className="font-medium text-gray-700">F1: {f}%</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
