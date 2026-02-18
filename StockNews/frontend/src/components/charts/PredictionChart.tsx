interface PredictionChartProps {
  score: number | null;
  direction: 'up' | 'down' | 'neutral' | null;
  confidence: number | null;
}

export default function PredictionChart({ score, direction, confidence }: PredictionChartProps) {
  if (score === null) {
    return (
      <div className="flex h-64 items-center justify-center rounded-lg border bg-gray-50">
        <p className="text-gray-500">예측 데이터 없음</p>
      </div>
    );
  }

  // Color based on score
  let colorClass = 'text-green-600';
  if (score < 40) {
    colorClass = 'text-red-600';
  } else if (score >= 40 && score <= 60) {
    colorClass = 'text-yellow-500';
  }

  const directionText = {
    up: '상승 예측',
    down: '하락 예측',
    neutral: '중립 예측',
  };

  return (
    <div data-testid="prediction-gauge" className={`space-y-4 rounded-lg border bg-white p-6 ${colorClass}`}>
      {/* Score Display */}
      <div className="text-center">
        <div className="text-6xl font-bold">{score}</div>
        <div className="mt-2 text-sm text-gray-500">예측 점수</div>
      </div>

      {/* Direction */}
      {direction && (
        <div className="text-center text-lg font-semibold text-gray-700">
          {directionText[direction]}
        </div>
      )}

      {/* Confidence Bar */}
      {confidence !== null && (
        <div className="space-y-2">
          <div className="flex justify-between text-sm text-gray-600">
            <span>신뢰도: {Math.round(confidence * 100)}%</span>
          </div>
          <div className="h-2 overflow-hidden rounded-full bg-gray-200">
            <div
              className="h-full bg-blue-500 transition-all"
              style={{ width: `${confidence * 100}%` }}
            />
          </div>
        </div>
      )}
    </div>
  );
}
