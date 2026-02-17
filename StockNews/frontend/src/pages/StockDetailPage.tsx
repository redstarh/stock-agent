import { useParams, useNavigate } from 'react-router-dom';
import { useNewsScore } from '../hooks/useNewsScore';
import Loading from '../components/common/Loading';
import ScoreTimeline from '../components/charts/ScoreTimeline';
import SentimentPie from '../components/charts/SentimentPie';
import { formatScore } from '../utils/format';

export default function StockDetailPage() {
  const { code } = useParams<{ code: string }>();
  const navigate = useNavigate();
  const { score, timeline } = useNewsScore(code ?? '');

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

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <section>
          <h3 className="mb-3 font-semibold text-gray-700">스코어 타임라인</h3>
          {timeline.isLoading ? (
            <Loading message="타임라인 로딩 중..." />
          ) : (
            <ScoreTimeline data={timeline.data ?? []} />
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
    </div>
  );
}
