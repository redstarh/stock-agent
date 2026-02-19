import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { useTopNews } from '../hooks/useTopNews';
import { fetchThemeStrength } from '../api/themes';
import { useMarket } from '../contexts/MarketContext';
import Loading from '../components/common/Loading';
import TopStockCards from '../components/news/TopStockCards';
import ThemeStrengthChart from '../components/charts/ThemeStrengthChart';

export default function DashboardPage() {
  const { market } = useMarket();
  const navigate = useNavigate();

  const topNews = useTopNews(market);
  const themes = useQuery({
    queryKey: ['themeStrength', market],
    queryFn: () => fetchThemeStrength(market),
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-gray-900">대시보드</h2>
      </div>

      <section>
        <h3 className="mb-3 font-semibold text-gray-700">Top 종목</h3>
        {topNews.isLoading ? (
          <Loading message="Top 종목 로딩 중..." />
        ) : topNews.isError ? (
          <p className="text-red-500">데이터를 불러올 수 없습니다</p>
        ) : (
          <TopStockCards
            items={topNews.data ?? []}
            onStockClick={(code) => navigate(`/stocks/${code}`)}
          />
        )}
      </section>

      <section>
        <h3 className="mb-3 font-semibold text-gray-700">테마 강도</h3>
        {themes.isLoading ? (
          <Loading message="테마 로딩 중..." />
        ) : (
          <ThemeStrengthChart data={themes.data ?? []} />
        )}
      </section>
    </div>
  );
}
