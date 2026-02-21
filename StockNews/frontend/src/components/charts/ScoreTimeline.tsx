import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import type { TimelinePoint } from '../../types/news';

interface ScoreTimelineProps {
  data: TimelinePoint[];
  onPointClick?: (date: string) => void;
}

export default function ScoreTimeline({ data, onPointClick }: ScoreTimelineProps) {
  if (data.length === 0) {
    return <p className="py-8 text-center text-gray-400">타임라인 데이터가 없습니다</p>;
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any -- Recharts onClick types are incomplete
  const handleClick = (data: any) => {
    if (data && data.activePayload && data.activePayload[0]) {
      const point = data.activePayload[0].payload as TimelinePoint;
      onPointClick?.(point.date);
    }
  };

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart
        data={data}
        margin={{ top: 5, right: 20, bottom: 5, left: 0 }}
        onClick={handleClick}
      >
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="date" tick={{ fontSize: 12 }} />
        <YAxis domain={[0, 100]} />
        <Tooltip />
        <Line
          type="monotone"
          dataKey="score"
          stroke="#3b82f6"
          strokeWidth={2}
          dot={{ r: 4 }}
          activeDot={{ r: 6, style: { cursor: 'pointer' } }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
