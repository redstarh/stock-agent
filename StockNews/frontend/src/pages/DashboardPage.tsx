import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { useTopNews } from '../hooks/useTopNews';
import { fetchLatestNews } from '../api/news';
import { fetchThemeStrength } from '../api/themes';
import type { Market } from '../utils/constants';
import MarketSelector from '../components/common/MarketSelector';
import Loading from '../components/common/Loading';
import TopStockCards from '../components/news/TopStockCards';
import NewsList from '../components/news/NewsList';
import ThemeStrengthChart from '../components/charts/ThemeStrengthChart';

export default function DashboardPage() {
  const [market, setMarket] = useState<Market>('KR');
  const navigate = useNavigate();

  const topNews = useTopNews(market);
  const latestNews = useQuery({
    queryKey: ['latestNews', market],
    queryFn: () => fetchLatestNews(0, 10, market),
  });
  const themes = useQuery({
    queryKey: ['themeStrength', market],
    queryFn: () => fetchThemeStrength(market),
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-gray-900">대시보드</h2>
        <MarketSelector selected={market} onChange={setMarket} />
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

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <section>
          <h3 className="mb-3 font-semibold text-gray-700">최신 뉴스</h3>
          {latestNews.isLoading ? (
            <Loading message="뉴스 로딩 중..." />
          ) : (
            <NewsList items={latestNews.data?.items ?? []} />
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
    </div>
  );
}
