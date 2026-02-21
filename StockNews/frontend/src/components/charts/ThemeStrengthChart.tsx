import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import type { ThemeItem } from '../../types/theme';

interface ThemeStrengthChartProps {
  data: ThemeItem[];
}

function barColor(riseIndex: number): string {
  if (riseIndex >= 60) return '#ef4444'; // red - bullish
  if (riseIndex < 40) return '#3b82f6'; // blue - bearish
  return '#6b7280'; // gray - neutral
}

export default function ThemeStrengthChart({ data }: ThemeStrengthChartProps) {
  if (!data || data.length === 0) {
    return <p className="py-8 text-center text-gray-400">테마 데이터가 없습니다</p>;
  }

  const chartHeight = Math.max(250, Math.min(500, data.length * 32));

  return (
    <ResponsiveContainer width="100%" height={chartHeight}>
      <BarChart data={data} layout="vertical" margin={{ left: 10 }}>
        <XAxis type="number" domain={[0, 100]} />
        <YAxis type="category" dataKey="theme" width={70} tick={{ fontSize: 12 }} />
        <Tooltip
          formatter={(value: number) => [`${value.toFixed(1)}`, '강도']}
          labelFormatter={(label: string) => `테마: ${label}`}
        />
        <Bar dataKey="rise_index" radius={[0, 4, 4, 0]} isAnimationActive={false}>
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={barColor(entry.rise_index)} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
