import type { NewsItem } from '../../types/news';
import { formatDateTime, formatScore, formatSentiment } from '../../utils/format';
import { SENTIMENT_COLORS } from '../../utils/constants';

interface NewsCardProps {
  item: NewsItem;
}

export default function NewsCard({ item }: NewsCardProps) {
  const sentimentColor = SENTIMENT_COLORS[item.sentiment] ?? '#6b7280';

  return (
    <article className="rounded-lg border bg-white p-4">
      <div className="flex items-start justify-between gap-2">
        <h3 className="font-medium text-gray-900">{item.title}</h3>
        <div className="flex shrink-0 items-center gap-1.5">
          <span
            className="rounded-full px-2 py-0.5 text-xs font-medium text-white"
            style={{ backgroundColor: sentimentColor }}
          >
            {formatSentiment(item.sentiment)}
          </span>
          {item.sentiment_score != null && item.sentiment_score !== 0 && (
            <span
              className="text-xs font-semibold"
              style={{ color: sentimentColor }}
            >
              {item.sentiment_score > 0 ? '+' : ''}{item.sentiment_score.toFixed(2)}
            </span>
          )}
        </div>
      </div>
      {item.summary && (
        <p className="mt-2 line-clamp-2 text-sm text-gray-600">{item.summary}</p>
      )}
      <div className="mt-2 flex flex-wrap items-center gap-3 text-xs text-gray-500">
        <span className="font-medium text-gray-700">{item.stock_name ?? item.stock_code}</span>
        <span>Score: <span className="font-semibold text-blue-600">{formatScore(item.news_score)}</span></span>
        {item.theme && (
          <span className="rounded bg-gray-100 px-1.5 py-0.5 text-gray-600">{item.theme}</span>
        )}
        <span>{item.source}</span>
        <span>{formatDateTime(item.published_at)}</span>
      </div>
    </article>
  );
}
