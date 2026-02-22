import { useState, useMemo } from 'react';
import { useMarket } from '../contexts/MarketContext';
import {
  useAdvanRuns,
  useAdvanRun,
  useAdvanRunByStock,
  useAdvanRunByTheme,
} from '../hooks/useSimulationAdvan';
import type { AccuracyResponse, DailyPredictionResult } from '../types/verification';
import type { ThemeAccuracy } from '../types/verification';
import Loading from '../components/common/Loading';
import AccuracyOverviewCard from '../components/verification/AccuracyOverviewCard';
import DailyAccuracyChart from '../components/verification/DailyAccuracyChart';
import StockResultsTable from '../components/verification/StockResultsTable';
import ThemeAccuracyBreakdown from '../components/verification/ThemeAccuracyBreakdown';

export default function VerificationPage() {
  const { market } = useMarket();
  const [userSelectedRunId, setUserSelectedRunId] = useState<number | null>(null);

  // Fetch all completed runs for the current market
  const runs = useAdvanRuns({ market, status: 'completed' });

  // Derive selected run: user's choice or latest completed
  const selectedRunId = useMemo(() => {
    if (userSelectedRunId !== null && runs.data?.some((r) => r.id === userSelectedRunId)) {
      return userSelectedRunId;
    }
    if (runs.data && runs.data.length > 0) {
      return [...runs.data].sort((a, b) => b.id - a.id)[0].id;
    }
    return null;
  }, [userSelectedRunId, runs.data]);

  // Fetch detailed data for the selected run
  const runDetail = useAdvanRun(selectedRunId);
  const byStock = useAdvanRunByStock(selectedRunId);
  const byTheme = useAdvanRunByTheme(selectedRunId);

  // Build a map of stock_code -> stock_name from by-stock results
  const stockNameMap = useMemo(() => {
    if (!byStock.data) return new Map<string, string>();
    const map = new Map<string, string>();
    byStock.data.forEach((item) => {
      if (item.stock_name) {
        map.set(item.stock_code, item.stock_name);
      }
    });
    return map;
  }, [byStock.data]);

  // Map run detail to AccuracyResponse format
  const accuracyData = useMemo<AccuracyResponse | undefined>(() => {
    if (!runDetail.data) return undefined;
    const { run, direction_stats } = runDetail.data;

    // Evaluate the total predictions (excluding abstains)
    const totalEvaluated = run.total_predictions - run.abstain_count;

    // Map direction stats: "Up" -> up, "Down" -> down, "Flat" -> neutral
    const mapDirectionStats = (direction: string) => {
      const stat = direction_stats[direction];
      if (!stat) {
        return { total: 0, correct: 0, accuracy: 0 };
      }
      // accuracy from backend is 0-1 fraction, convert to percentage
      const acc = stat.accuracy <= 1 ? stat.accuracy * 100 : stat.accuracy;
      return {
        total: stat.total,
        correct: stat.correct,
        accuracy: Math.round(acc * 10) / 10,
      };
    };

    return {
      period_days: 0, // Not applicable for Advan runs
      market: run.market,
      // accuracy_rate might be 0-1 fraction or 0-100 percentage — check and normalize
      overall_accuracy: run.accuracy_rate > 1 ? run.accuracy_rate : run.accuracy_rate * 100,
      total_predictions: totalEvaluated,
      correct_predictions: run.correct_count,
      by_direction: {
        up: mapDirectionStats('Up'),
        down: mapDirectionStats('Down'),
        neutral: mapDirectionStats('Flat'),
      },
      daily_trend: [], // Advan doesn't have daily trend
    };
  }, [runDetail.data]);

  // Map predictions to DailyPredictionResult format for StockResultsTable
  const stockResults = useMemo<DailyPredictionResult[]>(() => {
    if (!runDetail.data) return [];
    const { predictions, labels } = runDetail.data;

    // Create a map of prediction_id -> label
    const labelMap = new Map<number, typeof labels[0]>();
    labels.forEach((label) => {
      labelMap.set(label.prediction_id, label);
    });

    // Join predictions with labels and map to table format
    return predictions
      .filter((pred) => pred.prediction !== 'Abstain') // Skip abstains
      .map((pred) => {
        const label = labelMap.get(pred.id);

        // Map prediction direction: "Up" -> "up", "Down" -> "down", "Flat" -> "neutral"
        const mapDirection = (dir: string): 'up' | 'down' | 'neutral' => {
          if (dir === 'Up') return 'up';
          if (dir === 'Down') return 'down';
          return 'neutral';
        };

        // Predicted score is the max probability
        const predictedScore = Math.max(pred.p_up, pred.p_down, pred.p_flat);

        return {
          stock_code: pred.ticker,
          stock_name: stockNameMap.get(pred.ticker) ?? null,
          predicted_direction: mapDirection(pred.prediction),
          predicted_score: predictedScore,
          confidence: predictedScore,
          actual_direction: label?.label ? mapDirection(label.label) : null,
          actual_change_pct: label?.realized_ret != null ? label.realized_ret * 100 : null,
          is_correct: label?.is_correct ?? null,
          news_count: 0, // Not applicable for Advan
          error_message: null,
        };
      });
  }, [runDetail.data, stockNameMap]);

  // Map by-theme results to ThemeAccuracy format
  const themeAccuracyData = useMemo<ThemeAccuracy[]>(() => {
    if (!byTheme.data) return [];
    return byTheme.data.map((item) => ({
      theme: item.theme,
      market: market,
      total_stocks: item.total_stocks,
      correct_count: item.correct_count,
      accuracy_rate: item.accuracy_rate,
      avg_predicted_score: 0,
      avg_actual_change_pct: null,
      rise_index: null,
    }));
  }, [byTheme.data, market]);

  const isLoading = runs.isLoading || runDetail.isLoading;

  // Get the selected run info for the banner
  const selectedRun = runs.data?.find((r) => r.id === selectedRunId);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-gray-900">예측 검증 (Advan)</h2>
        <div className="flex items-center gap-2">
          <label className="text-sm text-gray-500">시뮬레이션 실행</label>
          <select
            value={selectedRunId ?? ''}
            onChange={(e) => setUserSelectedRunId(e.target.value ? Number(e.target.value) : null)}
            className="rounded-lg border px-3 py-1.5 text-sm"
            disabled={!runs.data || runs.data.length === 0}
          >
            {runs.data && runs.data.length > 0 ? (
              [...runs.data]
                .sort((a, b) => b.id - a.id)
                .map((run) => (
                  <option key={run.id} value={run.id}>
                    {run.name} (ID: {run.id})
                  </option>
                ))
            ) : (
              <option value="">실행 데이터 없음</option>
            )}
          </select>
        </div>
      </div>

      {runs.data && runs.data.length === 0 ? (
        <div className="rounded-lg border border-gray-200 bg-gray-50 p-8 text-center">
          <p className="text-gray-500">Advan 시뮬레이션 실행 데이터가 없습니다</p>
        </div>
      ) : isLoading ? (
        <Loading message="검증 데이터 로딩 중..." />
      ) : (
        <>
          {selectedRun && (
            <div className="rounded-lg border-l-4 border-blue-500 bg-blue-50 p-3">
              <p className="text-sm font-medium text-blue-800">
                {selectedRun.name}
                <span className="ml-2 text-blue-600">
                  — {selectedRun.date_from} ~ {selectedRun.date_to}
                </span>
                {selectedRun.accuracy_rate !== null && (
                  <span className="ml-2 text-blue-600">
                    — 정확도{' '}
                    {(selectedRun.accuracy_rate > 1
                      ? selectedRun.accuracy_rate
                      : selectedRun.accuracy_rate * 100
                    ).toFixed(1)}
                    % ({selectedRun.correct_count}/
                    {selectedRun.total_predictions - selectedRun.abstain_count}건)
                  </span>
                )}
              </p>
            </div>
          )}

          <AccuracyOverviewCard data={accuracyData} />

          {accuracyData?.daily_trend && accuracyData.daily_trend.length > 0 && (
            <section>
              <h3 className="mb-3 font-semibold text-gray-700">일별 정확도 추세</h3>
              <DailyAccuracyChart data={accuracyData.daily_trend} />
            </section>
          )}

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <section>
              <h3 className="mb-3 font-semibold text-gray-700">
                종목별 검증 결과
                {stockResults.length > 0 && (
                  <span className="text-sm font-normal text-gray-400"> ({stockResults.length}건)</span>
                )}
              </h3>
              {byStock.isLoading ? (
                <Loading message="결과 로딩 중..." />
              ) : (
                <StockResultsTable results={stockResults} />
              )}
            </section>

            <section>
              <h3 className="mb-3 font-semibold text-gray-700">테마별 정확도</h3>
              {byTheme.isLoading ? (
                <Loading message="테마 로딩 중..." />
              ) : (
                <ThemeAccuracyBreakdown themes={themeAccuracyData} />
              )}
            </section>
          </div>
        </>
      )}
    </div>
  );
}
