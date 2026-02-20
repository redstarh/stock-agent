import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import type { ThemeAccuracy } from '../../types/verification';

interface ThemeAccuracyBreakdownProps {
  themes: ThemeAccuracy[];
}

function getColor(accuracy: number) {
  if (accuracy >= 70) return '#10b981'; // green
  if (accuracy >= 50) return '#f59e0b'; // yellow
  return '#ef4444'; // red
}

export default function ThemeAccuracyBreakdown({ themes }: ThemeAccuracyBreakdownProps) {
  if (!themes || themes.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center rounded-lg border bg-white">
        <p className="text-gray-400">테마 데이터가 없습니다</p>
      </div>
    );
  }

  const sorted = [...themes].sort((a, b) => b.accuracy_rate - a.accuracy_rate);

  return (
    <div className="rounded-lg border bg-white p-4">
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={sorted}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="theme"
            tick={{ fontSize: 11 }}
            angle={-45}
            textAnchor="end"
            height={80}
          />
          <YAxis
            domain={[0, 100]}
            tick={{ fontSize: 12 }}
            tickFormatter={(value) => `${value}%`}
          />
          <Tooltip contentStyle={{ fontSize: 12 }} />
          <Bar dataKey="accuracy_rate" name="accuracy_rate">
            {sorted.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={getColor(entry.accuracy_rate)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      <div className="mt-4 space-y-2">
        {sorted.slice(0, 5).map((theme) => (
          <div key={theme.theme} className="flex items-center justify-between text-sm">
            <span className="font-medium text-gray-700">{theme.theme}</span>
            <div className="flex items-center gap-3">
              <span className="text-gray-500">{theme.total_stocks}종목</span>
              <span
                className="rounded-full px-2 py-0.5 text-xs font-semibold text-white"
                style={{ backgroundColor: getColor(theme.accuracy_rate) }}
              >
                {theme.accuracy_rate.toFixed(1)}%
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
