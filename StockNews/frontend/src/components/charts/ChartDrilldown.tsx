import type { NewsItem } from '../../types/news';
import NewsCard from '../news/NewsCard';

interface ChartDrilldownProps {
  date: string | null;
  news: NewsItem[];
  onClose: () => void;
}

export default function ChartDrilldown({ date, news, onClose }: ChartDrilldownProps) {
  if (!date) return null;

  return (
    <div className="mt-4 rounded-lg border bg-white p-4 shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <h4 className="font-semibold text-gray-700">{date} 뉴스</h4>
        <button
          onClick={onClose}
          className="text-sm text-gray-400 hover:text-gray-600"
        >
          닫기
        </button>
      </div>
      {news.length === 0 ? (
        <p className="text-sm text-gray-400">해당 날짜의 뉴스가 없습니다</p>
      ) : (
        <div className="flex flex-col gap-2 max-h-60 overflow-y-auto">
          {news.map((item) => (
            <NewsCard key={item.id} item={item} />
          ))}
        </div>
      )}
    </div>
  );
}
