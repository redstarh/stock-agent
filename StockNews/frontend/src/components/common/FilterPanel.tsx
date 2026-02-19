import { useCallback } from 'react';
import type { Sentiment } from '../../types/news';

export interface NewsFilters {
  stock: string;
  dateFrom: string;
  dateTo: string;
  sentiment: Sentiment | 'all';
  theme: string;
}

interface FilterPanelProps {
  filters: NewsFilters;
  themes: string[];
  onChange: (filters: NewsFilters) => void;
  onApply?: () => void;
  showStockSearch?: boolean;
}

export const DEFAULT_FILTERS: NewsFilters = {
  stock: '',
  dateFrom: '',
  dateTo: '',
  sentiment: 'all',
  theme: '',
};

export default function FilterPanel({ filters, themes, onChange, onApply, showStockSearch = false }: FilterPanelProps) {
  const update = useCallback(
    (key: keyof NewsFilters, value: string) => {
      onChange({ ...filters, [key]: value });
    },
    [filters, onChange],
  );

  const handleReset = () => onChange({ ...DEFAULT_FILTERS });

  return (
    <div className="flex flex-wrap items-center gap-3 rounded-lg border bg-white p-3">
      {showStockSearch && (
        <div className="flex items-center gap-2">
          <label className="text-sm text-gray-500">종목</label>
          <input
            type="text"
            value={filters.stock}
            onChange={(e) => update('stock', e.target.value)}
            placeholder="종목명/코드 검색"
            className="rounded border px-2 py-1 text-sm"
          />
        </div>
      )}

      <div className="flex items-center gap-2">
        <label className="text-sm text-gray-500">기간</label>
        <input
          type="date"
          value={filters.dateFrom}
          onChange={(e) => update('dateFrom', e.target.value)}
          className="rounded border px-2 py-1 text-sm"
        />
        <span className="text-gray-400">~</span>
        <input
          type="date"
          value={filters.dateTo}
          onChange={(e) => update('dateTo', e.target.value)}
          className="rounded border px-2 py-1 text-sm"
        />
      </div>

      <div className="flex items-center gap-2">
        <label className="text-sm text-gray-500">감성</label>
        <select
          value={filters.sentiment}
          onChange={(e) => update('sentiment', e.target.value)}
          className="rounded border px-2 py-1 text-sm"
        >
          <option value="all">전체</option>
          <option value="positive">긍정</option>
          <option value="neutral">중립</option>
          <option value="negative">부정</option>
        </select>
      </div>

      <div className="flex items-center gap-2">
        <label className="text-sm text-gray-500">테마</label>
        <select
          value={filters.theme}
          onChange={(e) => update('theme', e.target.value)}
          className="rounded border px-2 py-1 text-sm"
        >
          <option value="">전체</option>
          {themes.map((t) => (
            <option key={t} value={t}>{t}</option>
          ))}
        </select>
      </div>

      {onApply && (
        <button
          onClick={onApply}
          className="rounded bg-blue-600 px-3 py-1 text-sm text-white hover:bg-blue-700"
        >
          검색
        </button>
      )}

      <button
        onClick={handleReset}
        className="rounded bg-gray-100 px-3 py-1 text-sm text-gray-500 hover:bg-gray-200"
      >
        초기화
      </button>
    </div>
  );
}
