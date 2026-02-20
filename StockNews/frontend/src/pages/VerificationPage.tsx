import { useState } from 'react';
import { useMarket } from '../contexts/MarketContext';
import { useAccuracy, useDailyResults, useThemeAccuracy } from '../hooks/useVerification';
import Loading from '../components/common/Loading';
import AccuracyOverviewCard from '../components/verification/AccuracyOverviewCard';
import DailyAccuracyChart from '../components/verification/DailyAccuracyChart';
import StockResultsTable from '../components/verification/StockResultsTable';
import ThemeAccuracyBreakdown from '../components/verification/ThemeAccuracyBreakdown';

export default function VerificationPage() {
  const { market } = useMarket();
  const [days, setDays] = useState(30);
  const today = new Date().toISOString().split('T')[0];
  const [selectedDate, setSelectedDate] = useState(today);

  const accuracy = useAccuracy(days, market);
  const dailyResults = useDailyResults(selectedDate, market);
  const themeAccuracy = useThemeAccuracy(selectedDate, market);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-gray-900">예측 검증</h2>
        <div className="flex items-center gap-3">
          <input
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            className="rounded-lg border px-3 py-1.5 text-sm"
          />
          <select
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            className="rounded-lg border px-3 py-1.5 text-sm"
          >
            <option value={7}>7일</option>
            <option value={30}>30일</option>
            <option value={90}>90일</option>
          </select>
        </div>
      </div>

      {accuracy.isLoading ? (
        <Loading message="검증 데이터 로딩 중..." />
      ) : (
        <>
          <AccuracyOverviewCard data={accuracy.data} />

          <section>
            <h3 className="mb-3 font-semibold text-gray-700">일별 정확도 추세</h3>
            <DailyAccuracyChart data={accuracy.data?.daily_trend ?? []} />
          </section>

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <section>
              <h3 className="mb-3 font-semibold text-gray-700">
                종목별 검증 결과
                {dailyResults.data && (
                  <span className="text-sm font-normal text-gray-400">
                    {' '}({dailyResults.data.total}건)
                  </span>
                )}
              </h3>
              {dailyResults.isLoading ? (
                <Loading message="결과 로딩 중..." />
              ) : (
                <StockResultsTable results={dailyResults.data?.results ?? []} />
              )}
            </section>

            <section>
              <h3 className="mb-3 font-semibold text-gray-700">테마별 정확도</h3>
              {themeAccuracy.isLoading ? (
                <Loading message="테마 로딩 중..." />
              ) : (
                <ThemeAccuracyBreakdown themes={themeAccuracy.data?.themes ?? []} />
              )}
            </section>
          </div>
        </>
      )}
    </div>
  );
}
