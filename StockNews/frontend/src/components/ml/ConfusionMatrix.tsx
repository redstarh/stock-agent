/** Confusion matrix heatmap display. */

interface Props {
  matrix: number[][] | null;
  labels: string[] | null;
}

export default function ConfusionMatrix({ matrix, labels }: Props) {
  if (!matrix || !labels || matrix.length === 0) {
    return (
      <div className="flex h-48 items-center justify-center rounded-lg border bg-white">
        <p className="text-sm text-gray-400">No evaluation data</p>
      </div>
    );
  }

  const maxVal = Math.max(...matrix.flat());

  return (
    <div className="rounded-lg border bg-white p-4 shadow-sm">
      <h3 className="mb-4 text-sm font-semibold text-gray-500">Confusion Matrix</h3>
      <div className="overflow-x-auto">
        <table className="mx-auto">
          <thead>
            <tr>
              <th className="p-2 text-xs text-gray-400">Pred \ Actual</th>
              {labels.map(l => (
                <th key={l} className="p-2 text-xs font-medium text-gray-600">{l}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {matrix.map((row, i) => (
              <tr key={i}>
                <td className="p-2 text-xs font-medium text-gray-600">{labels[i]}</td>
                {row.map((val, j) => {
                  const intensity = maxVal > 0 ? val / maxVal : 0;
                  const isDiagonal = i === j;
                  return (
                    <td
                      key={j}
                      className="p-2 text-center text-sm font-medium"
                      style={{
                        backgroundColor: isDiagonal
                          ? `rgba(59, 130, 246, ${0.1 + intensity * 0.6})`
                          : `rgba(239, 68, 68, ${intensity * 0.3})`,
                        color: intensity > 0.5 ? '#fff' : '#374151',
                      }}
                    >
                      {val}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
