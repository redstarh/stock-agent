/** Accuracy trend line chart using Recharts. */

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import type { MLModel } from '../../types/training';

interface Props {
  models: MLModel[];
}

export default function AccuracyTrendChart({ models }: Props) {
  const data = models
    .filter(m => m.cv_accuracy != null && m.created_at)
    .sort((a, b) => (a.created_at ?? '').localeCompare(b.created_at ?? ''))
    .map(m => ({
      name: m.model_name,
      date: m.created_at ? new Date(m.created_at).toLocaleDateString() : '',
      accuracy: Number(((m.cv_accuracy ?? 0) * 100).toFixed(1)),
      type: m.model_type,
      tier: m.feature_tier,
    }));

  if (data.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center rounded-lg border bg-white">
        <p className="text-sm text-gray-400">No model data to display</p>
      </div>
    );
  }

  return (
    <div className="rounded-lg border bg-white p-4 shadow-sm">
      <h3 className="mb-4 text-sm font-semibold text-gray-500">Accuracy Trend</h3>
      <ResponsiveContainer width="100%" height={240}>
        <LineChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis dataKey="date" tick={{ fontSize: 11 }} />
          <YAxis domain={[40, 80]} tick={{ fontSize: 11 }} tickFormatter={v => `${v}%`} />
          <Tooltip formatter={(value) => [`${value}%`, 'CV Accuracy']} />
          <ReferenceLine y={55} stroke="#ef4444" strokeDasharray="4 4" label={{ value: '55% min', fontSize: 10 }} />
          <Line type="monotone" dataKey="accuracy" stroke="#3b82f6" strokeWidth={2} dot={{ r: 4 }} activeDot={{ r: 6 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
