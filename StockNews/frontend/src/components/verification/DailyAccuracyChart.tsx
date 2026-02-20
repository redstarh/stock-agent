import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import type { DailyTrend } from '../../types/verification';

interface DailyAccuracyChartProps {
  data: DailyTrend[];
}

export default function DailyAccuracyChart({ data }: DailyAccuracyChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center rounded-lg border bg-white">
        <p className="text-gray-400">데이터가 없습니다</p>
      </div>
    );
  }

  return (
    <div className="rounded-lg border bg-white p-4">
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 12 }}
            tickFormatter={(value) => value.slice(5)} // MM-DD
          />
          <YAxis
            domain={[0, 100]}
            tick={{ fontSize: 12 }}
            tickFormatter={(value) => `${value}%`}
          />
          <Tooltip contentStyle={{ fontSize: 12 }} />
          <Line
            type="monotone"
            dataKey="accuracy"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={{ r: 3 }}
            name="accuracy"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
