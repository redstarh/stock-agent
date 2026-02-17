import { SENTIMENT_COLORS } from '../../utils/constants';
import { formatSentiment } from '../../utils/format';

interface SentimentIndicatorProps {
  sentiment: string;
  value?: number;
}

export default function SentimentIndicator({ sentiment, value }: SentimentIndicatorProps) {
  return (
    <span className="inline-flex items-center gap-1.5">
      <span
        className="rounded-full px-2 py-0.5 text-xs font-medium text-white"
        style={{ backgroundColor: SENTIMENT_COLORS[sentiment] ?? '#6b7280' }}
      >
        {formatSentiment(sentiment)}
      </span>
      {value !== undefined && (
        <span className="text-xs text-gray-500">{value}</span>
      )}
    </span>
  );
}
