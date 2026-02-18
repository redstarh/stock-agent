import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { useNewsScore } from '../hooks/useNewsScore';
import { usePrediction } from '../hooks/usePrediction';
import { fetchNewsByDate } from '../api/news';
import Loading from '../components/common/Loading';
import ScoreTimeline from '../components/charts/ScoreTimeline';
import SentimentPie from '../components/charts/SentimentPie';
import PredictionChart from '../components/charts/PredictionChart';
import PredictionSignal from '../components/common/PredictionSignal';
import ChartDrilldown from '../components/charts/ChartDrilldown';
import FilterPanel, { DEFAULT_FILTERS, type NewsFilters } from '../components/common/FilterPanel';
import { formatScore } from '../utils/format';
import type { NewsItem } from '../types/news';

export default function StockDetailPage() {
  const { code } = useParams<{ code: string }>();
  const navigate = useNavigate();
  const { score, timeline } = useNewsScore(code ?? '');
  const prediction = usePrediction(code ?? '');
  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const [filters, setFilters] = useState<NewsFilters>(DEFAULT_FILTERS);

  // Fetch news for selected date
  const newsForDate = useQuery<NewsItem[]>({
    queryKey: ['newsByDate', code, selectedDate],
    queryFn: () => fetchNewsByDate(code ?? '', selectedDate ?? ''),
    enabled: !!code && !!selectedDate,
  });

  const handlePointClick = (date: string) => {
    setSelectedDate(date);
  };

  const handleCloseDrilldown = () => {
    setSelectedDate(null);
  };

  // Mock themes for filter panel (in real app, fetch from API)
  const themes = ['반도체', '2차전지', 'AI/로봇', '바이오', '자동차'];

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <button
          className="rounded-md bg-gray-100 px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-200"
          onClick={() => navigate(-1)}
        >
          ← 뒤로
        </button>
        <h2 className="text-xl font-bold text-gray-900">종목 상세 — {code}</h2>
      </div>

      {score.isLoading ? (
        <Loading message="스코어 로딩 중..." />
      ) : score.isError ? (
        <p className="text-red-500">스코어를 불러올 수 없습니다</p>
      ) : score.data ? (
        <div className="rounded-lg border bg-white p-6">
          <div className="flex items-baseline gap-3">
            <h3 className="text-lg font-semibold text-gray-900">
              {score.data.stock_name ?? code}
            </h3>
            <span className="text-3xl font-bold text-blue-600">
              {formatScore(score.data.news_score)}
            </span>
          </div>
          <div className="mt-3 grid grid-cols-4 gap-4 text-sm text-gray-500">
            <div>최신성: {formatScore(score.data.recency)}</div>
            <div>빈도: {formatScore(score.data.frequency)}</div>
            <div>감성: {formatScore(score.data.sentiment_score)}</div>
            <div>공시: {formatScore(score.data.disclosure)}</div>
          </div>
        </div>
      ) : null}

      <div className="space-y-6">
        <FilterPanel filters={filters} themes={themes} onChange={setFilters} />

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <section>
            <h3 className="mb-3 font-semibold text-gray-700">스코어 타임라인</h3>
            {timeline.isLoading ? (
              <Loading message="타임라인 로딩 중..." />
            ) : (
              <>
                <ScoreTimeline data={timeline.data ?? []} onPointClick={handlePointClick} />
                {selectedDate && (
                  <ChartDrilldown
                    date={selectedDate}
                    news={newsForDate.data ?? []}
                    onClose={handleCloseDrilldown}
                  />
                )}
              </>
            )}
          </section>

          <section>
            <h3 className="mb-3 font-semibold text-gray-700">감성 분포</h3>
            {score.isLoading ? (
              <Loading message="감성 데이터 로딩 중..." />
            ) : (
              <SentimentPie
                positive={score.data?.sentiment_score ?? 0}
                neutral={Math.max(0, 100 - (score.data?.sentiment_score ?? 0) - 20)}
                negative={20}
              />
            )}
          </section>
        </div>

        {/* Prediction Section */}
        <section className="mt-6">
          <h3 className="mb-3 font-semibold text-gray-700">예측</h3>
          {prediction.isLoading ? (
            <Loading message="예측 데이터 로딩 중..." />
          ) : prediction.isError ? (
            <p className="text-red-500">예측 데이터를 불러올 수 없습니다</p>
          ) : (
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
              <PredictionChart
                score={prediction.data?.prediction_score ?? null}
                direction={prediction.data?.direction ?? null}
                confidence={prediction.data?.confidence ?? null}
              />
              <PredictionSignal
                direction={prediction.data?.direction ?? null}
                confidence={prediction.data?.confidence ?? null}
              />
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
