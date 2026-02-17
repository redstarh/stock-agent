import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import type { ThemeItem } from '../../types/theme';

interface ThemeStrengthChartProps {
  data: ThemeItem[];
}

export default function ThemeStrengthChart({ data }: ThemeStrengthChartProps) {
  if (data.length === 0) {
    return <p className="py-8 text-center text-gray-400">테마 데이터가 없습니다</p>;
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data} layout="vertical" margin={{ left: 60 }}>
        <XAxis type="number" domain={[0, 100]} />
        <YAxis type="category" dataKey="theme" width={80} />
        <Tooltip />
        <Bar dataKey="strength_score" fill="#3b82f6" radius={[0, 4, 4, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
