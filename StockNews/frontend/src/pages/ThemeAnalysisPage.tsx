import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useThemeStrength } from '../hooks/useThemeStrength';
import { fetchThemeNews } from '../api/themes';
import type { Market } from '../utils/constants';
import MarketSelector from '../components/common/MarketSelector';
import Loading from '../components/common/Loading';
import ThemeStrengthChart from '../components/charts/ThemeStrengthChart';
import { formatDateTime } from '../utils/format';

const DIRECTION_STYLE = {
  up: { color: '#ef4444', arrow: '▲', label: '상승' },
  down: { color: '#3b82f6', arrow: '▼', label: '하락' },
  neutral: { color: '#6b7280', arrow: '—', label: '중립' },
} as const;

function getRiseDirection(riseIndex: number) {
  if (riseIndex >= 60) return 'up';
  if (riseIndex < 40) return 'down';
  return 'neutral';
}

function scoreColor(score: number) {
  if (score >= 60) return '#ef4444'; // red (상승)
  if (score < 40) return '#3b82f6'; // blue (하락)
  return '#6b7280'; // gray (중립)
}

function ThemeNewsCard({ title, stockName, source, publishedAt, score, label }: {
  title: string;
  stockName: string;
  source: string;
  publishedAt: string | null;
  score: number;
  label: string;
}) {
  const color = scoreColor(score);
  return (
    <article className="rounded-lg border bg-white p-4">
      <div className="flex items-start justify-between gap-2">
        <h3 className="font-medium text-gray-900">{title}</h3>
        <span
          className="shrink-0 rounded-full px-2.5 py-1 text-sm font-bold text-white"
          style={{ backgroundColor: color }}
        >
          {score.toFixed(0)}
        </span>
      </div>
      <div className="mt-2 flex flex-wrap items-center gap-3 text-xs text-gray-500">
        <span className="font-medium text-gray-700">{stockName}</span>
        <span className="rounded bg-gray-100 px-1.5 py-0.5">{label}</span>
        <span>{source}</span>
        <span>{formatDateTime(publishedAt)}</span>
      </div>
    </article>
  );
}

export default function ThemeAnalysisPage() {
  const [market, setMarket] = useState<Market>('KR');
  const [expandedTheme, setExpandedTheme] = useState<string | null>(null);
  const { data, isLoading } = useThemeStrength(market);

  const sorted = [...(data ?? [])].sort((a, b) => b.rise_index - a.rise_index);

  const themeNews = useQuery({
    queryKey: ['themeNews', expandedTheme],
    queryFn: () => fetchThemeNews(expandedTheme!, 30),
    enabled: !!expandedTheme,
  });

  const handleThemeClick = (theme: string) => {
    setExpandedTheme(expandedTheme === theme ? null : theme);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-gray-900">테마 분석</h2>
        <MarketSelector selected={market} onChange={setMarket} />
      </div>

      {isLoading ? (
        <Loading message="테마 로딩 중..." />
      ) : (
        <>
          <section>
            <h3 className="mb-3 font-semibold text-gray-700">테마 강도 차트</h3>
            <ThemeStrengthChart data={sorted} />
          </section>

          <section>
            <h3 className="mb-3 font-semibold text-gray-700">테마 상세</h3>
            <div className="flex flex-col gap-3">
              {sorted.map((item) => {
                const dir = getRiseDirection(item.rise_index);
                const style = DIRECTION_STYLE[dir];
                const isExpanded = expandedTheme === item.theme;

                return (
                  <div key={item.theme}>
                    <button
                      className={`flex w-full items-center justify-between rounded-lg border bg-white p-4 text-left transition hover:shadow-md ${
                        isExpanded ? 'ring-2 ring-blue-300' : ''
                      }`}
                      onClick={() => handleThemeClick(item.theme)}
                    >
                      <div className="flex items-center gap-3">
                        <span className="font-semibold text-gray-900">{item.theme}</span>
                        <span
                          className="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-bold text-white"
                          style={{ backgroundColor: style.color }}
                        >
                          {style.arrow} {style.label}
                        </span>
                      </div>
                      <div className="flex items-center gap-4 text-sm text-gray-500">
                        <span className="text-base font-bold" style={{ color: style.color }}>
                          {item.rise_index.toFixed(1)}
                        </span>
                        <span>뉴스 {item.news_count}건</span>
                        <span className="text-gray-400">{isExpanded ? '▾' : '▸'}</span>
                      </div>
                    </button>

                    {isExpanded && (
                      <div className="mt-2 ml-4 space-y-4">
                        {themeNews.isLoading ? (
                          <Loading message="관련 뉴스 로딩 중..." />
                        ) : themeNews.isError ? (
                          <p className="text-red-500">뉴스를 불러올 수 없습니다</p>
                        ) : (
                          <>
                            {/* 국내 뉴스 */}
                            <div className="rounded-lg border bg-gray-50 p-4">
                              <h4 className="mb-2 text-sm font-semibold text-gray-700">
                                국내 뉴스 ({themeNews.data?.kr_total ?? 0}건)
                              </h4>
                              <div className="flex flex-col gap-3">
                                {(themeNews.data?.kr_news ?? []).length === 0 ? (
                                  <p className="py-4 text-center text-gray-400">뉴스가 없습니다</p>
                                ) : (
                                  themeNews.data?.kr_news.map((n) => (
                                    <ThemeNewsCard
                                      key={n.id}
                                      title={n.title}
                                      stockName={n.stock_name ?? n.stock_code}
                                      source={n.source}
                                      publishedAt={n.published_at}
                                      score={n.news_score}
                                      label="국내"
                                    />
                                  ))
                                )}
                              </div>
                            </div>

                            {/* 국외 영향 뉴스 */}
                            {(themeNews.data?.us_total ?? 0) > 0 && (
                              <div className="rounded-lg border border-blue-200 bg-blue-50 p-4">
                                <h4 className="mb-2 text-sm font-semibold text-blue-700">
                                  국외 영향 뉴스 ({themeNews.data?.us_total ?? 0}건)
                                </h4>
                                <div className="flex flex-col gap-3">
                                  {themeNews.data?.us_news.map((n) => (
                                    <ThemeNewsCard
                                      key={n.id}
                                      title={n.title}
                                      stockName={n.stock_name ?? n.stock_code}
                                      source={n.source}
                                      publishedAt={n.published_at}
                                      score={Math.round(n.impact * 100)}
                                      label="국외"
                                    />
                                  ))}
                                </div>
                              </div>
                            )}
                          </>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </section>
        </>
      )}
    </div>
  );
}
