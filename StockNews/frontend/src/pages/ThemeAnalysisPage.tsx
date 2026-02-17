import { useState } from 'react';
import { useThemeStrength } from '../hooks/useThemeStrength';
import type { Market } from '../utils/constants';
import MarketSelector from '../components/common/MarketSelector';
import Loading from '../components/common/Loading';
import ThemeStrengthChart from '../components/charts/ThemeStrengthChart';
import SentimentIndicator from '../components/common/SentimentIndicator';
import { formatScore } from '../utils/format';

export default function ThemeAnalysisPage() {
  const [market, setMarket] = useState<Market>('KR');
  const { data, isLoading } = useThemeStrength(market);

  const sorted = [...(data ?? [])].sort((a, b) => b.strength_score - a.strength_score);

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
              {sorted.map((item) => (
                <div
                  key={item.theme}
                  className="flex items-center justify-between rounded-lg border bg-white p-4"
                >
                  <div className="flex items-center gap-3">
                    <span className="font-semibold text-gray-900">{item.theme}</span>
                    <SentimentIndicator
                      sentiment={item.sentiment_avg >= 0.3 ? 'positive' : item.sentiment_avg <= -0.3 ? 'negative' : 'neutral'}
                      value={Number(item.sentiment_avg.toFixed(2))}
                    />
                  </div>
                  <div className="flex items-center gap-4 text-sm text-gray-500">
                    <span>강도: {formatScore(item.strength_score)}</span>
                    <span>뉴스 {item.news_count}건</span>
                  </div>
                </div>
              ))}
            </div>
          </section>
        </>
      )}
    </div>
  );
}
