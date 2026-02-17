import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { SENTIMENT_COLORS } from '../../utils/constants';

interface SentimentPieProps {
  positive: number;
  neutral: number;
  negative: number;
}

const LABELS: Record<string, string> = {
  positive: '긍정',
  neutral: '중립',
  negative: '부정',
};

export default function SentimentPie({ positive, neutral, negative }: SentimentPieProps) {
  const total = positive + neutral + negative;
  if (total === 0) {
    return <p className="py-8 text-center text-gray-400">감성 데이터가 없습니다</p>;
  }

  const data = [
    { name: LABELS.positive, value: positive, key: 'positive' },
    { name: LABELS.neutral, value: neutral, key: 'neutral' },
    { name: LABELS.negative, value: negative, key: 'negative' },
  ].filter((d) => d.value > 0);

  return (
    <ResponsiveContainer width="100%" height={250}>
      <PieChart>
        <Pie data={data} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label>
          {data.map((entry) => (
            <Cell key={entry.key} fill={SENTIMENT_COLORS[entry.key]} />
          ))}
        </Pie>
        <Tooltip />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  );
}
