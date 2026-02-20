import { useState } from 'react';
import type { DailyPredictionResult } from '../../types/verification';

interface StockResultsTableProps {
  results: DailyPredictionResult[];
}

type SortKey = 'stock_code' | 'predicted_score' | 'confidence' | 'actual_change_pct';

const DIRECTION_STYLE = {
  up: { color: '#ef4444', arrow: '▲' },
  down: { color: '#3b82f6', arrow: '▼' },
  neutral: { color: '#6b7280', arrow: '—' },
} as const;

export default function StockResultsTable({ results }: StockResultsTableProps) {
  const [sortKey, setSortKey] = useState<SortKey>('predicted_score');
  const [sortAsc, setSortAsc] = useState(false);

  if (!results || results.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center rounded-lg border bg-white">
        <p className="text-gray-400">검증 결과가 없습니다</p>
      </div>
    );
  }

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortAsc(!sortAsc);
    } else {
      setSortKey(key);
      setSortAsc(false);
    }
  };

  const sorted = [...results].sort((a, b) => {
    let aVal: number | string = a[sortKey] ?? 0;
    let bVal: number | string = b[sortKey] ?? 0;

    if (sortKey === 'stock_code') {
      aVal = String(a.stock_code);
      bVal = String(b.stock_code);
      return sortAsc
        ? aVal.localeCompare(bVal)
        : bVal.localeCompare(aVal);
    }

    aVal = Number(aVal);
    bVal = Number(bVal);
    return sortAsc ? aVal - bVal : bVal - aVal;
  });

  return (
    <div className="overflow-x-auto rounded-lg border bg-white">
      <table className="w-full text-sm">
        <thead className="border-b bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left font-semibold text-gray-700">
              <button onClick={() => handleSort('stock_code')} className="hover:text-blue-600">
                종목 {sortKey === 'stock_code' && (sortAsc ? '↑' : '↓')}
              </button>
            </th>
            <th className="px-4 py-3 text-center font-semibold text-gray-700">예측</th>
            <th className="px-4 py-3 text-center font-semibold text-gray-700">실제</th>
            <th className="px-4 py-3 text-right font-semibold text-gray-700">
              <button onClick={() => handleSort('actual_change_pct')} className="hover:text-blue-600">
                변동률 {sortKey === 'actual_change_pct' && (sortAsc ? '↑' : '↓')}
              </button>
            </th>
            <th className="px-4 py-3 text-center font-semibold text-gray-700">정확</th>
            <th className="px-4 py-3 text-right font-semibold text-gray-700">
              <button onClick={() => handleSort('confidence')} className="hover:text-blue-600">
                신뢰도 {sortKey === 'confidence' && (sortAsc ? '↑' : '↓')}
              </button>
            </th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((item, idx) => {
            const predStyle = DIRECTION_STYLE[item.predicted_direction];
            const actualStyle = item.actual_direction ? DIRECTION_STYLE[item.actual_direction] : null;
            const isCorrect = item.is_correct;

            return (
              <tr key={idx} className="border-b hover:bg-gray-50">
                <td className="px-4 py-3 font-medium text-gray-900">
                  {item.stock_name || item.stock_code}
                  <div className="text-xs text-gray-500">{item.stock_code}</div>
                </td>
                <td className="px-4 py-3 text-center">
                  <span className="font-semibold" style={{ color: predStyle.color }}>
                    {predStyle.arrow}
                  </span>
                </td>
                <td className="px-4 py-3 text-center">
                  {actualStyle ? (
                    <span className="font-semibold" style={{ color: actualStyle.color }}>
                      {actualStyle.arrow}
                    </span>
                  ) : (
                    <span className="text-gray-400">-</span>
                  )}
                </td>
                <td className="px-4 py-3 text-right font-medium">
                  {item.actual_change_pct !== null ? (
                    <span className={item.actual_change_pct >= 0 ? 'text-red-600' : 'text-blue-600'}>
                      {item.actual_change_pct >= 0 ? '+' : ''}
                      {item.actual_change_pct.toFixed(2)}%
                    </span>
                  ) : (
                    <span className="text-gray-400">-</span>
                  )}
                </td>
                <td className="px-4 py-3 text-center">
                  {isCorrect !== null ? (
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs font-semibold ${
                        isCorrect ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                      }`}
                    >
                      {isCorrect ? '✓' : '✗'}
                    </span>
                  ) : (
                    <span className="text-gray-400">-</span>
                  )}
                </td>
                <td className="px-4 py-3 text-right text-gray-600">
                  {(item.confidence * 100).toFixed(1)}%
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
