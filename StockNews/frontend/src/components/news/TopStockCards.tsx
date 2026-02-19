import type { NewsTopItem } from '../../types/news';
import { formatSentiment } from '../../utils/format';
import { SENTIMENT_COLORS } from '../../utils/constants';

interface TopStockCardsProps {
  items: NewsTopItem[];
  onStockClick?: (stockCode: string) => void;
}

const DIRECTION_COLORS = {
  up: '#ef4444', // red (Korean convention)
  down: '#3b82f6', // blue
  neutral: '#6b7280', // gray
};

const DIRECTION_ARROWS = {
  up: '▲',
  down: '▼',
  neutral: '—',
};

const DIRECTION_LABELS = {
  up: '상승 예측',
  down: '하락 예측',
  neutral: '중립',
};

export default function TopStockCards({ items, onStockClick }: TopStockCardsProps) {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {items.map((item) => {
        const direction = item.direction ?? 'neutral';
        const predictionScore = item.prediction_score;
        const displayScore = predictionScore != null ? predictionScore.toFixed(1) : 'N/A';

        return (
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
            <p
              className="mt-2 text-2xl font-bold"
              style={{ color: DIRECTION_COLORS[direction] }}
            >
              {DIRECTION_ARROWS[direction]} {displayScore}
            </p>
            <p className="text-xs text-gray-500">
              {DIRECTION_LABELS[direction]} | 뉴스 {item.news_count}건
            </p>
          </button>
        );
      })}
    </div>
  );
}
