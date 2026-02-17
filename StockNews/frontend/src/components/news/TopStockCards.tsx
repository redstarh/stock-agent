import type { NewsTopItem } from '../../types/news';
import { formatScore, formatSentiment } from '../../utils/format';
import { SENTIMENT_COLORS } from '../../utils/constants';

interface TopStockCardsProps {
  items: NewsTopItem[];
  onStockClick?: (stockCode: string) => void;
}

export default function TopStockCards({ items, onStockClick }: TopStockCardsProps) {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {items.map((item) => (
        <button
          key={item.stock_code}
          className="rounded-lg border bg-white p-4 text-left shadow-sm transition hover:shadow-md"
          onClick={() => onStockClick?.(item.stock_code)}
        >
          <div className="flex items-center justify-between">
            <span className="font-semibold text-gray-900">
              {item.stock_name ?? item.stock_code}
            </span>
            <span
              className="rounded-full px-2 py-0.5 text-xs font-medium text-white"
              style={{ backgroundColor: SENTIMENT_COLORS[item.sentiment] ?? '#6b7280' }}
            >
              {formatSentiment(item.sentiment)}
            </span>
          </div>
          <p className="mt-2 text-2xl font-bold text-blue-600">{formatScore(item.news_score)}</p>
          <p className="text-xs text-gray-500">뉴스 {item.news_count}건</p>
        </button>
      ))}
    </div>
  );
}
