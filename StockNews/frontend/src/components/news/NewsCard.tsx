import type { NewsItem } from '../../types/news';
import { formatDateTime, formatScore, formatSentiment } from '../../utils/format';
import { SENTIMENT_COLORS } from '../../utils/constants';

interface NewsCardProps {
  item: NewsItem;
}

export default function NewsCard({ item }: NewsCardProps) {
  return (
    <article className="rounded-lg border bg-white p-4">
      <div className="flex items-start justify-between gap-2">
        <h3 className="font-medium text-gray-900">{item.title}</h3>
        <span
          className="shrink-0 rounded-full px-2 py-0.5 text-xs font-medium text-white"
          style={{ backgroundColor: SENTIMENT_COLORS[item.sentiment] ?? '#6b7280' }}
        >
          {formatSentiment(item.sentiment)}
        </span>
      </div>
      <div className="mt-2 flex items-center gap-3 text-xs text-gray-500">
        <span>{item.stock_name ?? item.stock_code}</span>
        <span>Score: {formatScore(item.news_score)}</span>
        <span>{item.source}</span>
        <span>{formatDateTime(item.published_at)}</span>
      </div>
    </article>
  );
}
