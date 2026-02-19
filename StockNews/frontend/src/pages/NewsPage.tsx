import { useState, useCallback, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchLatestNews } from '../api/news';
import type { Market } from '../utils/constants';
import MarketSelector from '../components/common/MarketSelector';
import FilterPanel, { DEFAULT_FILTERS, type NewsFilters } from '../components/common/FilterPanel';
import Loading from '../components/common/Loading';
import NewsList from '../components/news/NewsList';

const THEMES = ['반도체', '2차전지', 'AI/로봇', '바이오', '자동차', '에너지', '금융', '엔터'];

export default function NewsPage() {
  const [market, setMarket] = useState<Market>('KR');
  const [filters, setFilters] = useState<NewsFilters>(DEFAULT_FILTERS);
  const [appliedFilters, setAppliedFilters] = useState<NewsFilters>(DEFAULT_FILTERS);

  const handleApply = useCallback(() => {
    setAppliedFilters(filters);
  }, [filters]);

  const handleFilterChange = useCallback((newFilters: NewsFilters) => {
    setFilters(newFilters);
    if (
      newFilters.stock === '' &&
      newFilters.sentiment === 'all' &&
      newFilters.theme === '' &&
      newFilters.dateFrom === '' &&
      newFilters.dateTo === ''
    ) {
      setAppliedFilters(newFilters);
    }
  }, []);

  const activeFilters = useMemo(
    () => ({
      market,
      stock: appliedFilters.stock || undefined,
      sentiment: appliedFilters.sentiment !== 'all' ? appliedFilters.sentiment : undefined,
      theme: appliedFilters.theme || undefined,
      dateFrom: appliedFilters.dateFrom || undefined,
      dateTo: appliedFilters.dateTo || undefined,
    }),
    [market, appliedFilters],
  );

  const latestNews = useQuery({
    queryKey: ['latestNews', activeFilters],
    queryFn: () => fetchLatestNews(0, 50, activeFilters),
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-gray-900">최신 뉴스</h2>
        <MarketSelector selected={market} onChange={setMarket} />
      </div>

      <FilterPanel
        filters={filters}
        themes={THEMES}
        onChange={handleFilterChange}
        onApply={handleApply}
        showStockSearch={true}
      />

      <section>
        <div className="mb-3 flex items-center justify-between">
          <h3 className="font-semibold text-gray-700">
            검색 결과 {latestNews.data?.total != null && (
              <span className="text-sm font-normal text-gray-400">({latestNews.data.total}건)</span>
            )}
          </h3>
        </div>
        {latestNews.isLoading ? (
          <Loading message="뉴스 로딩 중..." />
        ) : latestNews.isError ? (
          <p className="text-red-500">뉴스를 불러올 수 없습니다</p>
        ) : (
          <NewsList items={latestNews.data?.items ?? []} />
        )}
      </section>
    </div>
  );
}
