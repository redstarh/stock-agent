import { useState, useCallback, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchLatestNews } from '../api/news';
import { useMarket } from '../contexts/MarketContext';
import FilterPanel, { DEFAULT_FILTERS, type NewsFilters } from '../components/common/FilterPanel';
import Loading from '../components/common/Loading';
import NewsList from '../components/news/NewsList';
import { useManualCollect } from '../hooks/useManualCollect';

const THEMES = ['반도체', '2차전지', 'AI/로봇', '바이오', '자동차', '에너지', '금융', '엔터'];

export default function NewsPage() {
  const { market } = useMarket();
  const today = new Date().toISOString().split('T')[0];
  const initialFilters: NewsFilters = { ...DEFAULT_FILTERS, dateFrom: today, dateTo: today };
  const [filters, setFilters] = useState<NewsFilters>(initialFilters);
  const [appliedFilters, setAppliedFilters] = useState<NewsFilters>(initialFilters);
  const [collectQuery, setCollectQuery] = useState('');
  const [collectCode, setCollectCode] = useState('');
  const [addToScope, setAddToScope] = useState(false);
  const manualCollect = useManualCollect();

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
      </div>

      <FilterPanel
        filters={filters}
        themes={THEMES}
        onChange={handleFilterChange}
        onApply={handleApply}
        showStockSearch={true}
      />

      {/* 수동 수집 섹션 */}
      <div className="rounded-lg border border-gray-200 bg-white p-4">
        <h3 className="mb-3 font-semibold text-gray-700">수동 수집</h3>
        <div className="flex flex-wrap items-center gap-3">
          <input
            type="text"
            placeholder="종목명"
            value={collectQuery}
            onChange={(e) => setCollectQuery(e.target.value)}
            className="rounded-md border border-gray-300 px-3 py-1.5 text-sm focus:border-blue-500 focus:outline-none"
          />
          <input
            type="text"
            placeholder="종목코드"
            value={collectCode}
            onChange={(e) => setCollectCode(e.target.value)}
            className="rounded-md border border-gray-300 px-3 py-1.5 text-sm focus:border-blue-500 focus:outline-none"
          />
          <label className="flex items-center gap-1.5 text-sm text-gray-600">
            <input
              type="checkbox"
              checked={addToScope}
              onChange={(e) => setAddToScope(e.target.checked)}
              className="rounded border-gray-300"
            />
            일일 수집에 추가
          </label>
          <button
            onClick={() =>
              manualCollect.mutate({
                query: collectQuery,
                stock_code: collectCode,
                market,
                add_to_scope: addToScope,
              })
            }
            disabled={!collectQuery || !collectCode || manualCollect.isPending}
            className="rounded-md bg-blue-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
          >
            {manualCollect.isPending ? '수집 중...' : '수집'}
          </button>
        </div>
        {manualCollect.isSuccess && manualCollect.data && (
          <p className="mt-2 text-sm text-green-600">
            수집 완료: {manualCollect.data.collected}건 수집, {manualCollect.data.saved}건 저장
            {manualCollect.data.added_to_scope && ' (일일 수집에 추가됨)'}
          </p>
        )}
        {manualCollect.isError && (
          <p className="mt-2 text-sm text-red-500">수집 실패: {(manualCollect.error as Error).message}</p>
        )}
      </div>

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
