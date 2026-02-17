import type { NewsItem } from '../../types/news';
import NewsCard from './NewsCard';

interface NewsListProps {
  items: NewsItem[];
}

export default function NewsList({ items }: NewsListProps) {
  if (items.length === 0) {
    return <p className="py-8 text-center text-gray-400">뉴스가 없습니다</p>;
  }

  return (
    <div className="flex flex-col gap-3">
      {items.map((item) => (
        <NewsCard key={item.id} item={item} />
      ))}
    </div>
  );
}
