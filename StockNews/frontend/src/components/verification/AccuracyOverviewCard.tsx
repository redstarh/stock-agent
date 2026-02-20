import type { AccuracyResponse } from '../../types/verification';

interface AccuracyOverviewCardProps {
  data?: AccuracyResponse;
}

export default function AccuracyOverviewCard({ data }: AccuracyOverviewCardProps) {
  if (!data) {
    return (
      <div className="rounded-lg border bg-white p-6">
        <p className="text-center text-gray-400">데이터가 없습니다</p>
      </div>
    );
  }

  const accuracy = data.overall_accuracy ?? 0;
  const accuracyColor = accuracy >= 70 ? 'text-green-600' : accuracy >= 50 ? 'text-yellow-600' : 'text-red-600';

  return (
    <div className="rounded-lg border bg-white p-6">
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-4">
        {/* Overall Accuracy */}
        <div className="flex flex-col items-center justify-center border-r">
          <p className="text-sm text-gray-500">전체 정확도</p>
          <p className={`text-4xl font-bold ${accuracyColor}`}>
            {accuracy.toFixed(1)}%
          </p>
        </div>

        {/* Total/Correct/Incorrect */}
        <div className="flex flex-col justify-center gap-2">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">총 예측</span>
            <span className="font-semibold text-gray-900">{data.total_predictions}건</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">정답</span>
            <span className="font-semibold text-green-600">{data.correct_predictions}건</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">오답</span>
            <span className="font-semibold text-red-600">
              {data.total_predictions - data.correct_predictions}건
            </span>
          </div>
        </div>

        {/* Direction Breakdown */}
        <div className="flex flex-col justify-center gap-2 lg:col-span-2">
          <h4 className="text-sm font-semibold text-gray-700">방향별 정확도</h4>
          <div className="grid grid-cols-3 gap-2">
            <div className="rounded-lg bg-red-50 p-3 text-center">
              <p className="text-xs text-gray-600">상승 예측</p>
              <p className="text-lg font-bold text-red-600">
                {data.by_direction.up.accuracy.toFixed(1)}%
              </p>
              <p className="text-xs text-gray-500">
                {data.by_direction.up.correct}/{data.by_direction.up.total}
              </p>
            </div>
            <div className="rounded-lg bg-blue-50 p-3 text-center">
              <p className="text-xs text-gray-600">하락 예측</p>
              <p className="text-lg font-bold text-blue-600">
                {data.by_direction.down.accuracy.toFixed(1)}%
              </p>
              <p className="text-xs text-gray-500">
                {data.by_direction.down.correct}/{data.by_direction.down.total}
              </p>
            </div>
            <div className="rounded-lg bg-gray-50 p-3 text-center">
              <p className="text-xs text-gray-600">중립 예측</p>
              <p className="text-lg font-bold text-gray-600">
                {data.by_direction.neutral.accuracy.toFixed(1)}%
              </p>
              <p className="text-xs text-gray-500">
                {data.by_direction.neutral.correct}/{data.by_direction.neutral.total}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
