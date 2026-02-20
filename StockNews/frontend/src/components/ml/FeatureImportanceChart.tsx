/** Feature importance horizontal bar chart. */

import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

interface Props {
  importances: Record<string, number> | null;
}

export default function FeatureImportanceChart({ importances }: Props) {
  if (!importances || Object.keys(importances).length === 0) {
    return (
      <div className="flex h-64 items-center justify-center rounded-lg border bg-white">
        <p className="text-sm text-gray-400">No feature importance data</p>
      </div>
    );
  }

  const data = Object.entries(importances)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 10)
    .map(([name, value]) => ({
      name,
      importance: Number((value * 100).toFixed(1)),
    }));

  return (
    <div className="rounded-lg border bg-white p-4 shadow-sm">
      <h3 className="mb-4 text-sm font-semibold text-gray-500">Feature Importance</h3>
      <ResponsiveContainer width="100%" height={240}>
        <BarChart data={data} layout="vertical" margin={{ top: 5, right: 20, left: 80, bottom: 5 }}>
          <XAxis type="number" tick={{ fontSize: 11 }} tickFormatter={v => `${v}%`} />
          <YAxis type="category" dataKey="name" tick={{ fontSize: 11 }} width={75} />
          <Tooltip formatter={(value) => [`${value}%`, 'Importance']} />
          <Bar dataKey="importance" radius={[0, 4, 4, 0]} fill="#3b82f6" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
