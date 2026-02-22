import { useState, useMemo } from 'react';
import { useMarket } from '../contexts/MarketContext';
import {
  useAdvanRuns,
  useAdvanRun,
  useAdvanRunByStock,
  useAdvanRunByTheme,
} from '../hooks/useSimulationAdvan';
import type { AdvanSimulationRunDetail } from '../types/simulationAdvan';
import type { AdvanStockResult, AdvanThemeResult } from '../api/simulationAdvan';
import Loading from '../components/common/Loading';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
  CartesianGrid,
} from 'recharts';

export default function SystemComparisonPage() {
  const { market } = useMarket();
  const [userSelectedRunId, setUserSelectedRunId] = useState<number | null>(null);
  const [userCompareRunId, setUserCompareRunId] = useState<number | null>(null);

  // Advan system data
  const runsQuery = useAdvanRuns({ market });

  // Get completed Advan runs
  const completedRuns = useMemo(
    () => (runsQuery.data ?? []).filter((r) => r.status === 'completed'),
    [runsQuery.data]
  );

  // Derive selected run: user's choice or latest completed
  const selectedRunId = useMemo(() => {
    if (userSelectedRunId !== null && completedRuns.some((r) => r.id === userSelectedRunId)) {
      return userSelectedRunId;
    }
    if (completedRuns.length > 0) {
      return [...completedRuns].sort((a, b) => b.id - a.id)[0].id;
    }
    return null;
  }, [userSelectedRunId, completedRuns]);

  // Derive compare run: user's choice or second-latest
  const compareRunId = useMemo(() => {
    if (userCompareRunId !== null && completedRuns.some((r) => r.id === userCompareRunId)) {
      return userCompareRunId;
    }
    if (selectedRunId && completedRuns.length >= 2) {
      const otherRuns = completedRuns.filter((r) => r.id !== selectedRunId);
      if (otherRuns.length > 0) {
        return [...otherRuns].sort((a, b) => b.id - a.id)[0].id;
      }
    }
    return null;
  }, [userCompareRunId, selectedRunId, completedRuns]);

  // Derive selected run from completedRuns
  const selectedRun = useMemo(
    () => completedRuns.find((r) => r.id === selectedRunId) ?? null,
    [completedRuns, selectedRunId]
  );

  const advanDetail = useAdvanRun(selectedRun?.id ?? null);
  const advanByStock = useAdvanRunByStock(selectedRun?.id ?? null);
  const advanByTheme = useAdvanRunByTheme(selectedRun?.id ?? null);

  // Comparison run data
  const compareDetail = useAdvanRun(compareRunId);
  const compareByStock = useAdvanRunByStock(compareRunId);
  const compareByTheme = useAdvanRunByTheme(compareRunId);

  const hasAdvanRun = selectedRun !== null && advanDetail.data;
  const hasCompareRun = compareRunId !== null && compareDetail.data;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900">
          Advan 예측 시뮬레이션 비교
        </h2>
        <p className="mt-1 text-sm text-gray-600">
          이벤트 기반 예측 정책별 시뮬레이션 결과 비교
        </p>
      </div>

      {/* Controls */}
      <div className="flex flex-wrap items-center gap-4">
        {completedRuns.length > 0 && (
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium text-gray-700">Advan 실행:</label>
            <select
              value={selectedRunId ?? ''}
              onChange={(e) => setUserSelectedRunId(e.target.value ? Number(e.target.value) : null)}
              className="rounded-lg border px-3 py-1 text-sm"
            >
              {completedRuns.map((run) => (
                <option key={run.id} value={run.id}>
                  #{run.id} {run.name} ({(run.accuracy_rate * 100).toFixed(1)}%)
                </option>
              ))}
            </select>
          </div>
        )}
        {completedRuns.length > 0 && (
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium text-gray-700">비교 실행:</label>
            <select
              value={compareRunId ?? ''}
              onChange={(e) => setUserCompareRunId(e.target.value ? Number(e.target.value) : null)}
              className="rounded-lg border px-3 py-1 text-sm"
            >
              <option value="">선택 안함</option>
              {completedRuns
                .filter((run) => run.id !== selectedRunId)
                .map((run) => (
                  <option key={run.id} value={run.id}>
                    #{run.id} {run.name} ({(run.accuracy_rate * 100).toFixed(1)}%)
                  </option>
                ))}
            </select>
          </div>
        )}
      </div>

      {runsQuery.isLoading ? (
        <Loading message="데이터 로딩 중..." />
      ) : (
        <>
          {/* Section 1: Overall Accuracy Comparison */}
          <div className="grid gap-6 md:grid-cols-2">
            <AdvanAccuracyCard
              hasRun={!!hasAdvanRun}
              advanDetail={advanDetail.data}
              totalRuns={completedRuns.length}
              selectedRun={selectedRun}
              isPrimary={true}
            />
            {hasCompareRun ? (
              <CompareAccuracyCard
                compareDetail={compareDetail.data}
                compareRun={completedRuns.find((r) => r.id === compareRunId) ?? null}
              />
            ) : (
              <div className="rounded-lg border border-pink-200 bg-white p-6 shadow-sm">
                <div className="mb-4 flex items-center gap-2">
                  <div className="h-3 w-3 rounded-full bg-pink-500" />
                  <h3 className="text-lg font-semibold text-pink-900">비교 실행</h3>
                </div>
                <div className="flex items-center justify-center py-12">
                  <p className="text-gray-500">비교할 실행을 선택해주세요</p>
                </div>
              </div>
            )}
          </div>

          {/* Section 2: Stock-level Comparison */}
          <StockComparisonSection
            primaryStocks={advanByStock.data ?? []}
            compareStocks={compareByStock.data ?? []}
            primaryRunId={selectedRunId}
            compareRunId={compareRunId}
            hasCompareRun={hasCompareRun}
          />

          {/* Section 3: Theme-level Comparison */}
          <ThemeComparisonSection
            primaryThemes={advanByTheme.data ?? []}
            compareThemes={compareByTheme.data ?? []}
            primaryRunId={selectedRunId}
            compareRunId={compareRunId}
            hasCompareRun={hasCompareRun}
          />

          {/* Section 4: Advan Inter-Run Comparison */}
          {hasCompareRun && hasAdvanRun && (
            <AdvanRunComparisonSection
              primaryRun={advanDetail.data!}
              compareRun={compareDetail.data!}
            />
          )}
        </>
      )}
    </div>
  );
}

// ─── Sub-components ───

function AdvanAccuracyCard({
  hasRun,
  advanDetail,
  totalRuns,
  selectedRun,
}: {
  hasRun: boolean;
  advanDetail: AdvanSimulationRunDetail | undefined;
  totalRuns: number;
  selectedRun: { id: number; name: string } | null;
  isPrimary?: boolean;
}) {
  if (!hasRun) {
    return (
      <div className="rounded-lg border border-purple-200 bg-white p-6 shadow-sm">
        <div className="mb-4 flex items-center gap-2">
          <div className="h-3 w-3 rounded-full bg-purple-500" />
          <h3 className="text-lg font-semibold text-purple-900">Advan 예측</h3>
        </div>
        <div className="space-y-3 py-4">
          <div className="rounded-lg border-l-4 border-purple-400 bg-purple-50 p-4">
            <p className="text-sm font-medium text-purple-800">시뮬레이션 미실행</p>
            <p className="mt-1 text-xs text-purple-600">
              Advan 시뮬레이션 페이지에서 실행 후 비교할 수 있습니다
            </p>
          </div>
        </div>
      </div>
    );
  }

  const run = advanDetail!.run;
  const dirStats = advanDetail!.direction_stats;

  return (
    <div className="rounded-lg border border-purple-200 bg-white p-6 shadow-sm">
      <div className="mb-4 flex items-center gap-2">
        <div className="h-3 w-3 rounded-full bg-purple-500" />
        <h3 className="text-lg font-semibold text-purple-900">
          Advan 예측
          {selectedRun && (
            <span className="ml-2 text-sm font-normal text-purple-600">
              ({selectedRun.name})
            </span>
          )}
        </h3>
        <span className="ml-auto rounded-full bg-purple-100 px-2 py-0.5 text-xs text-purple-700">
          {totalRuns}회 실행
        </span>
      </div>

      <div className="mb-4 text-center">
        <div className="text-sm text-gray-600">전체 정확도</div>
        <div className="text-4xl font-bold text-purple-700">
          {(run.accuracy_rate * 100).toFixed(1)}%
        </div>
        <div className="mt-1 text-sm text-gray-500">
          {run.correct_count} / {run.total_predictions} 정답
          {run.abstain_count > 0 && ` (기권: ${run.abstain_count})`}
        </div>
      </div>

      <div className="space-y-2">
        {(['Up', 'Down', 'Flat'] as const).map((dir) => {
          const d = dirStats[dir] ?? dirStats[dir.toLowerCase()];
          if (!d) return null;
          const label = dir === 'Up' ? '상승' : dir === 'Down' ? '하락' : '중립';
          const acc = (d.accuracy ?? 0) * 100;
          const barColor = dir === 'Up' ? '#a855f7' : dir === 'Down' ? '#ec4899' : '#8b5cf6';
          return (
            <div key={dir} className="flex items-center justify-between text-sm">
              <span className="text-gray-600">{label}</span>
              <div className="flex items-center gap-2">
                <div className="h-2 w-24 overflow-hidden rounded-full bg-gray-200">
                  <div className="h-full transition-all" style={{ width: `${acc}%`, backgroundColor: barColor }} />
                </div>
                <span className="w-16 text-right font-medium">{acc.toFixed(1)}%</span>
                <span className="w-12 text-right text-xs text-gray-400">{d.correct}/{d.total}</span>
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-4 grid grid-cols-2 gap-2">
        {[
          { label: 'Brier', value: run.brier_score, fmt: (v: number) => v.toFixed(3) },
          { label: 'AUC', value: run.auc_score, fmt: (v: number) => v.toFixed(3) },
        ].map(({ label, value, fmt }) => (
          <div key={label} className="rounded bg-purple-50 px-3 py-2 text-center">
            <div className="text-xs text-gray-500">{label}</div>
            <div className="text-sm font-bold text-purple-800">{value != null ? fmt(value) : '-'}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function CompareAccuracyCard({
  compareDetail,
  compareRun,
}: {
  compareDetail: AdvanSimulationRunDetail | undefined;
  compareRun: { id: number; name: string } | null;
}) {
  if (!compareDetail || !compareRun) {
    return (
      <div className="rounded-lg border border-pink-200 bg-white p-6 shadow-sm">
        <div className="mb-4 flex items-center gap-2">
          <div className="h-3 w-3 rounded-full bg-pink-500" />
          <h3 className="text-lg font-semibold text-pink-900">비교 실행</h3>
        </div>
        <div className="flex items-center justify-center py-12">
          <p className="text-gray-500">비교할 실행을 선택해주세요</p>
        </div>
      </div>
    );
  }

  const run = compareDetail.run;
  const dirStats = compareDetail.direction_stats;

  return (
    <div className="rounded-lg border border-pink-200 bg-white p-6 shadow-sm">
      <div className="mb-4 flex items-center gap-2">
        <div className="h-3 w-3 rounded-full bg-pink-500" />
        <h3 className="text-lg font-semibold text-pink-900">
          비교 실행
          <span className="ml-2 text-sm font-normal text-pink-600">
            ({compareRun.name})
          </span>
        </h3>
      </div>

      <div className="mb-4 text-center">
        <div className="text-sm text-gray-600">전체 정확도</div>
        <div className="text-4xl font-bold text-pink-700">
          {(run.accuracy_rate * 100).toFixed(1)}%
        </div>
        <div className="mt-1 text-sm text-gray-500">
          {run.correct_count} / {run.total_predictions} 정답
          {run.abstain_count > 0 && ` (기권: ${run.abstain_count})`}
        </div>
      </div>

      <div className="space-y-2">
        {(['Up', 'Down', 'Flat'] as const).map((dir) => {
          const d = dirStats[dir] ?? dirStats[dir.toLowerCase()];
          if (!d) return null;
          const label = dir === 'Up' ? '상승' : dir === 'Down' ? '하락' : '중립';
          const acc = (d.accuracy ?? 0) * 100;
          const barColor = dir === 'Up' ? '#ec4899' : dir === 'Down' ? '#f43f5e' : '#f472b6';
          return (
            <div key={dir} className="flex items-center justify-between text-sm">
              <span className="text-gray-600">{label}</span>
              <div className="flex items-center gap-2">
                <div className="h-2 w-24 overflow-hidden rounded-full bg-gray-200">
                  <div className="h-full transition-all" style={{ width: `${acc}%`, backgroundColor: barColor }} />
                </div>
                <span className="w-16 text-right font-medium">{acc.toFixed(1)}%</span>
                <span className="w-12 text-right text-xs text-gray-400">{d.correct}/{d.total}</span>
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-4 grid grid-cols-2 gap-2">
        {[
          { label: 'Brier', value: run.brier_score, fmt: (v: number) => v.toFixed(3) },
          { label: 'AUC', value: run.auc_score, fmt: (v: number) => v.toFixed(3) },
        ].map(({ label, value, fmt }) => (
          <div key={label} className="rounded bg-pink-50 px-3 py-2 text-center">
            <div className="text-xs text-gray-500">{label}</div>
            <div className="text-sm font-bold text-pink-800">{value != null ? fmt(value) : '-'}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Stock-level Comparison ───

function StockComparisonSection({
  primaryStocks,
  compareStocks,
  primaryRunId,
  compareRunId,
  hasCompareRun,
}: {
  primaryStocks: AdvanStockResult[];
  compareStocks: AdvanStockResult[];
  primaryRunId: number | null;
  compareRunId: number | null;
  hasCompareRun: boolean;
}) {
  // Build merged stock data
  const mergedStocks = useMemo(() => {
    const primaryMap = new Map(primaryStocks.map((s) => [s.stock_code, s]));
    const compareMap = new Map(compareStocks.map((s) => [s.stock_code, s]));
    const allCodes = new Set([
      ...primaryStocks.map((s) => s.stock_code),
      ...compareStocks.map((s) => s.stock_code),
    ]);

    return Array.from(allCodes)
      .map((code) => {
        const primary = primaryMap.get(code);
        const compare = compareMap.get(code);
        return {
          stock_code: code,
          stock_name: primary?.stock_name ?? compare?.stock_name ?? code,
          primary_prediction: primary?.latest_prediction ?? null,
          primary_label: primary?.latest_label ?? null,
          primary_realized_ret: primary?.latest_realized_ret ?? null,
          compare_prediction: compare?.latest_prediction ?? null,
          compare_label: compare?.latest_label ?? null,
          compare_realized_ret: compare?.latest_realized_ret ?? null,
        };
      })
      .filter((stock) => {
        // 예측 데이터가 있는 종목만 표시 (Abstain 제외)
        const hasPrimary = stock.primary_prediction !== null && stock.primary_prediction !== 'Abstain';
        const hasCompare = stock.compare_prediction !== null && stock.compare_prediction !== 'Abstain';
        return hasPrimary || hasCompare;
      });
  }, [primaryStocks, compareStocks]);

  return (
    <div className="rounded-lg border bg-white shadow-sm">
      <div className="border-b bg-gray-50 px-6 py-4">
        <h3 className="text-lg font-semibold text-gray-900">주가별 예측 비교</h3>
        <p className="mt-1 text-sm text-gray-500">
          개별 종목의 상승/하락 예측 정확도 비교
        </p>
      </div>

      {mergedStocks.length === 0 ? (
        <div className="flex items-center justify-center py-12">
          <p className="text-sm text-gray-400">예측 데이터가 없습니다</p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left font-semibold text-gray-700">종목</th>
                <th className="px-4 py-3 text-center font-semibold text-purple-700" colSpan={2}>
                  Primary (#{primaryRunId})
                </th>
                {hasCompareRun && (
                  <th className="px-4 py-3 text-center font-semibold text-pink-700" colSpan={2}>
                    Compare (#{compareRunId})
                  </th>
                )}
                <th className="px-4 py-3 text-center font-semibold text-gray-700" colSpan={2}>실제</th>
              </tr>
              <tr className="text-xs text-gray-500">
                <th className="px-4 py-1"></th>
                <th className="px-4 py-1 text-center">예측</th>
                <th className="px-4 py-1 text-center">결과</th>
                {hasCompareRun && (
                  <>
                    <th className="px-4 py-1 text-center">예측</th>
                    <th className="px-4 py-1 text-center">결과</th>
                  </>
                )}
                <th className="px-4 py-1 text-center">방향</th>
                <th className="px-4 py-1 text-center">변동률</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {mergedStocks.slice(0, 20).map((stock) => (
                <tr key={stock.stock_code} className="hover:bg-gray-50">
                  <td className="px-4 py-2">
                    <div className="font-medium text-gray-900">{stock.stock_name}</div>
                    <div className="text-xs text-gray-400">{stock.stock_code}</div>
                  </td>
                  <td className="px-4 py-2 text-center">
                    {stock.primary_prediction ? (
                      <AdvanDirectionBadge direction={stock.primary_prediction} />
                    ) : (
                      <span className="text-xs text-gray-300">-</span>
                    )}
                  </td>
                  <td className="px-4 py-2 text-center">
                    {stock.primary_label ? (
                      stock.primary_prediction === stock.primary_label ? (
                        <span className="text-green-600 font-medium">O</span>
                      ) : stock.primary_prediction === 'Abstain' ? (
                        <span className="text-gray-400">-</span>
                      ) : (
                        <span className="text-red-500 font-medium">X</span>
                      )
                    ) : (
                      <span className="text-gray-300">-</span>
                    )}
                  </td>
                  {hasCompareRun && (
                    <>
                      <td className="px-4 py-2 text-center">
                        {stock.compare_prediction ? (
                          <AdvanDirectionBadge direction={stock.compare_prediction} />
                        ) : (
                          <span className="text-xs text-gray-300">-</span>
                        )}
                      </td>
                      <td className="px-4 py-2 text-center">
                        {stock.compare_label ? (
                          stock.compare_prediction === stock.compare_label ? (
                            <span className="text-green-600 font-medium">O</span>
                          ) : stock.compare_prediction === 'Abstain' ? (
                            <span className="text-gray-400">-</span>
                          ) : (
                            <span className="text-red-500 font-medium">X</span>
                          )
                        ) : (
                          <span className="text-gray-300">-</span>
                        )}
                      </td>
                    </>
                  )}
                  <td className="px-4 py-2 text-center">
                    {(() => {
                      const ret = stock.primary_realized_ret ?? stock.compare_realized_ret;
                      if (ret === null) return <span className="text-gray-300">-</span>;
                      const dir = ret > 2 ? '상승' : ret < -2 ? '하락' : '중립';
                      const color = ret > 2 ? 'text-red-600' : ret < -2 ? 'text-blue-600' : 'text-gray-500';
                      return <span className={`text-xs font-medium ${color}`}>{dir}</span>;
                    })()}
                  </td>
                  <td className="px-4 py-2 text-center">
                    {(() => {
                      const ret = stock.primary_realized_ret ?? stock.compare_realized_ret;
                      if (ret === null) return <span className="text-gray-300">-</span>;
                      return (
                        <span className={`text-sm font-medium ${ret > 0 ? 'text-red-600' : ret < 0 ? 'text-blue-600' : 'text-gray-500'}`}>
                          {ret > 0 ? '+' : ''}{ret.toFixed(2)}%
                        </span>
                      );
                    })()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {mergedStocks.length > 20 && (
            <div className="border-t px-6 py-3 text-center text-xs text-gray-400">
              상위 20개 종목 표시 (전체 {mergedStocks.length}개)
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function AdvanDirectionBadge({ direction }: { direction: string }) {
  const config: Record<string, { bg: string; text: string; label: string }> = {
    Up: { bg: 'bg-purple-100', text: 'text-purple-700', label: '상승' },
    Down: { bg: 'bg-pink-100', text: 'text-pink-700', label: '하락' },
    Flat: { bg: 'bg-gray-100', text: 'text-gray-600', label: '중립' },
    Abstain: { bg: 'bg-yellow-100', text: 'text-yellow-600', label: '기권' },
  };
  const c = config[direction] ?? { bg: 'bg-gray-100', text: 'text-gray-500', label: direction };
  return (
    <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${c.bg} ${c.text}`}>
      {c.label}
    </span>
  );
}

// ─── Theme-level Comparison ───

function ThemeComparisonSection({
  primaryThemes,
  compareThemes,
  primaryRunId,
  compareRunId,
  hasCompareRun,
}: {
  primaryThemes: AdvanThemeResult[];
  compareThemes: AdvanThemeResult[];
  primaryRunId: number | null;
  compareRunId: number | null;
  hasCompareRun: boolean;
}) {
  // Merge themes from both runs
  const mergedChartData = useMemo(() => {
    const allThemes = new Set([
      ...primaryThemes.map((t) => t.theme),
      ...compareThemes.map((t) => t.theme),
    ]);
    const primaryMap = new Map(primaryThemes.map((t) => [t.theme, t]));
    const compareMap = new Map(compareThemes.map((t) => [t.theme, t]));

    return Array.from(allThemes)
      .map((theme) => ({
        theme,
        Primary: primaryMap.get(theme)?.accuracy_rate ?? null,
        Compare: compareMap.get(theme)?.accuracy_rate ?? null,
        primaryStocks: primaryMap.get(theme)?.total_stocks ?? 0,
        compareStocks: compareMap.get(theme)?.total_stocks ?? 0,
      }))
      .filter((d) => d.Primary !== null || d.Compare !== null)
      .sort((a, b) => {
        const aMax = Math.max(a.Primary ?? 0, a.Compare ?? 0);
        const bMax = Math.max(b.Primary ?? 0, b.Compare ?? 0);
        return bMax - aMax;
      });
  }, [primaryThemes, compareThemes]);

  return (
    <div className="rounded-lg border bg-white shadow-sm">
      <div className="border-b bg-gray-50 px-6 py-4">
        <h3 className="text-lg font-semibold text-gray-900">테마별 예측 비교</h3>
        <p className="mt-1 text-sm text-gray-500">
          산업 테마별 주가 예측 정확도 비교
        </p>
      </div>

      {mergedChartData.length === 0 ? (
        <div className="flex items-center justify-center py-12">
          <p className="text-sm text-gray-400">테마 데이터가 없습니다</p>
        </div>
      ) : (
        <div className="p-6 space-y-6">
          {/* Bar chart comparison */}
          <div>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={mergedChartData.slice(0, 10)} barGap={2}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="theme"
                  tick={{ fontSize: 11 }}
                  angle={-30}
                  textAnchor="end"
                  height={60}
                />
                <YAxis domain={[0, 100]} tickFormatter={(v: number) => `${v}%`} />
                <Tooltip
                  formatter={(value: number | string) =>
                    value !== null ? `${Number(value).toFixed(1)}%` : '데이터 없음'
                  }
                />
                <Legend />
                <Bar dataKey="Primary" fill="#a855f7" name={`Primary (#${primaryRunId})`} radius={[4, 4, 0, 0]} />
                {hasCompareRun && (
                  <Bar dataKey="Compare" fill="#ec4899" name={`Compare (#${compareRunId})`} radius={[4, 4, 0, 0]} />
                )}
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Theme detail table */}
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-2 text-left font-semibold text-gray-700">테마</th>
                  <th className="px-4 py-2 text-center font-semibold text-purple-700">Primary</th>
                  <th className="px-4 py-2 text-center font-semibold text-purple-600">종목수</th>
                  {hasCompareRun && (
                    <>
                      <th className="px-4 py-2 text-center font-semibold text-pink-700">Compare</th>
                      <th className="px-4 py-2 text-center font-semibold text-pink-600">종목수</th>
                      <th className="px-4 py-2 text-center font-semibold text-gray-600">차이</th>
                    </>
                  )}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {mergedChartData.map((row) => {
                  const diff =
                    row.Primary !== null && row.Compare !== null
                      ? row.Compare - row.Primary
                      : null;
                  return (
                    <tr key={row.theme} className="hover:bg-gray-50">
                      <td className="px-4 py-2 font-medium text-gray-900">{row.theme}</td>
                      <td className="px-4 py-2 text-center">
                        {row.Primary !== null ? (
                          <span style={{ color: getAccuracyColor(row.Primary) }} className="font-medium">
                            {row.Primary.toFixed(1)}%
                          </span>
                        ) : (
                          <span className="text-gray-300">-</span>
                        )}
                      </td>
                      <td className="px-4 py-2 text-center text-xs text-gray-500">
                        {row.primaryStocks || '-'}
                      </td>
                      {hasCompareRun && (
                        <>
                          <td className="px-4 py-2 text-center">
                            {row.Compare !== null ? (
                              <span style={{ color: getAccuracyColor(row.Compare) }} className="font-medium">
                                {row.Compare.toFixed(1)}%
                              </span>
                            ) : (
                              <span className="text-gray-300">-</span>
                            )}
                          </td>
                          <td className="px-4 py-2 text-center text-xs text-gray-500">
                            {row.compareStocks || '-'}
                          </td>
                          <td className="px-4 py-2 text-center">
                            {diff !== null ? (
                              <span
                                className={`text-sm font-medium ${
                                  diff > 0 ? 'text-green-600' : diff < 0 ? 'text-red-600' : 'text-gray-500'
                                }`}
                              >
                                {diff > 0 ? '+' : ''}{diff.toFixed(1)}%p
                              </span>
                            ) : (
                              <span className="text-gray-300">-</span>
                            )}
                          </td>
                        </>
                      )}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Advan Inter-Run Comparison ───

function AdvanRunComparisonSection({
  primaryRun,
  compareRun,
}: {
  primaryRun: AdvanSimulationRunDetail;
  compareRun: AdvanSimulationRunDetail;
}) {
  const metrics = [
    {
      label: '전체 정확도',
      primary: primaryRun.run.accuracy_rate * 100,
      compare: compareRun.run.accuracy_rate * 100,
      format: (v: number) => `${v.toFixed(1)}%`,
      higherBetter: true,
    },
    {
      label: 'Brier Score',
      primary: primaryRun.run.brier_score,
      compare: compareRun.run.brier_score,
      format: (v: number | null) => (v != null ? v.toFixed(4) : '-'),
      higherBetter: false,
    },
    {
      label: 'AUC',
      primary: primaryRun.run.auc_score,
      compare: compareRun.run.auc_score,
      format: (v: number | null) => (v != null ? v.toFixed(4) : '-'),
      higherBetter: true,
    },
    {
      label: 'F1',
      primary: primaryRun.run.f1_score,
      compare: compareRun.run.f1_score,
      format: (v: number | null) => (v != null ? v.toFixed(4) : '-'),
      higherBetter: true,
    },
    {
      label: '총 예측 수',
      primary: primaryRun.run.total_predictions,
      compare: compareRun.run.total_predictions,
      format: (v: number) => v.toString(),
      higherBetter: null,
    },
    {
      label: '기권 수',
      primary: primaryRun.run.abstain_count,
      compare: compareRun.run.abstain_count,
      format: (v: number) => v.toString(),
      higherBetter: null,
    },
  ];

  // Direction comparison chart data
  const directionChartData = useMemo(() => {
    const dirs = [
      { key: 'Up', label: '상승' },
      { key: 'Down', label: '하락' },
      { key: 'Flat', label: '중립' },
    ];
    return dirs.map(({ key, label }) => {
      const primaryDir = primaryRun.direction_stats[key] ?? primaryRun.direction_stats[key.toLowerCase()];
      const compareDir = compareRun.direction_stats[key] ?? compareRun.direction_stats[key.toLowerCase()];
      return {
        direction: label,
        [`Run #${primaryRun.run.id}`]: primaryDir ? (primaryDir.accuracy ?? 0) * 100 : 0,
        [`Run #${compareRun.run.id}`]: compareDir ? (compareDir.accuracy ?? 0) * 100 : 0,
      };
    });
  }, [primaryRun, compareRun]);

  return (
    <div className="rounded-lg border bg-white shadow-sm">
      <div className="border-b bg-gray-50 px-6 py-4">
        <h3 className="text-lg font-semibold text-gray-900">Advan 실행 간 비교</h3>
        <p className="mt-1 text-sm text-gray-500">
          Run #{primaryRun.run.id} vs Run #{compareRun.run.id}
        </p>
      </div>

      <div className="p-6 space-y-6">
        {/* Metrics Comparison Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left font-semibold text-gray-700">메트릭</th>
                <th className="px-4 py-3 text-right font-semibold text-purple-700">
                  Run #{primaryRun.run.id}
                </th>
                <th className="px-4 py-3 text-right font-semibold text-pink-700">
                  Run #{compareRun.run.id}
                </th>
                <th className="px-4 py-3 text-right font-semibold text-gray-700">차이</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {metrics.map((metric) => {
                const primaryVal = typeof metric.primary === 'number' ? metric.primary : null;
                const compareVal = typeof metric.compare === 'number' ? metric.compare : null;
                const diff = primaryVal !== null && compareVal !== null ? primaryVal - compareVal : null;

                let diffColor = 'text-gray-500';
                if (diff !== null && metric.higherBetter !== null) {
                  if (metric.higherBetter) {
                    diffColor = diff > 0 ? 'text-green-600' : diff < 0 ? 'text-red-600' : 'text-gray-500';
                  } else {
                    diffColor = diff < 0 ? 'text-green-600' : diff > 0 ? 'text-red-600' : 'text-gray-500';
                  }
                }

                return (
                  <tr key={metric.label} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-medium text-gray-900">{metric.label}</td>
                    <td className="px-4 py-3 text-right text-purple-700">
                      {metric.format(metric.primary)}
                    </td>
                    <td className="px-4 py-3 text-right text-pink-700">
                      {metric.format(metric.compare)}
                    </td>
                    <td className={`px-4 py-3 text-right font-medium ${diffColor}`}>
                      {diff !== null
                        ? metric.label.includes('%') || metric.label.includes('정확도')
                          ? `${diff > 0 ? '+' : ''}${diff.toFixed(1)}%p`
                          : `${diff > 0 ? '+' : ''}${diff.toFixed(4)}`
                        : '-'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Direction Accuracy Comparison Chart */}
        <div>
          <h4 className="mb-3 text-sm font-semibold text-gray-700">방향별 정확도 비교</h4>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={directionChartData} barGap={4}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="direction" />
              <YAxis domain={[0, 100]} tickFormatter={(v: number) => `${v}%`} />
              <Tooltip formatter={(value: number | string) => `${Number(value).toFixed(1)}%`} />
              <Legend />
              <Bar
                dataKey={`Run #${primaryRun.run.id}`}
                fill="#a855f7"
                name={`Run #${primaryRun.run.id}`}
                radius={[4, 4, 0, 0]}
                isAnimationActive={false}
              />
              <Bar
                dataKey={`Run #${compareRun.run.id}`}
                fill="#ec4899"
                name={`Run #${compareRun.run.id}`}
                radius={[4, 4, 0, 0]}
                isAnimationActive={false}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}

// ─── Helpers ───

function getAccuracyColor(accuracy: number): string {
  if (accuracy >= 70) return '#10b981';
  if (accuracy >= 50) return '#f59e0b';
  return '#ef4444';
}
