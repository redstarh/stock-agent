interface PredictionSignalProps {
  direction: 'up' | 'down' | 'neutral' | null;
  confidence: number | null;
}

export default function PredictionSignal({ direction, confidence }: PredictionSignalProps) {
  if (!direction) {
    return (
      <div className="rounded-lg border bg-gray-50 p-4 text-center text-gray-500">
        예측 없음
      </div>
    );
  }

  const signalConfig = {
    up: { bg: 'bg-green-500', text: '▲ 상승' },
    down: { bg: 'bg-red-500', text: '▼ 하락' },
    neutral: { bg: 'bg-gray-400', text: '— 중립' },
  };

  const config = signalConfig[direction];

  return (
    <div className="space-y-2">
      <div
        data-testid="prediction-signal"
        className={`${config.bg} rounded-lg px-4 py-3 text-center font-semibold text-white`}
      >
        {config.text}
      </div>
      {confidence !== null && (
        <div className="text-center text-sm text-gray-600">
          신뢰도: {Math.round(confidence * 100)}%
        </div>
      )}
    </div>
  );
}
