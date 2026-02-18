"use client";

import { useState } from "react";
import { apiClient } from "@/lib/api";
import type { DailyReport } from "@/lib/types";

export default function ReportViewer() {
  const [date, setDate] = useState("");
  const [report, setReport] = useState<DailyReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFetch = async () => {
    if (!date) return;

    setLoading(true);
    setError(null);
    try {
      const data = await apiClient.getDailyReport(date);
      setReport(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-4">
      <div className="mb-4 flex gap-2">
        <div>
          <label htmlFor="report-date" className="block text-sm font-medium mb-1">
            날짜
          </label>
          <input
            id="report-date"
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
            className="border rounded px-3 py-2"
          />
        </div>
        <button
          onClick={handleFetch}
          disabled={!date || loading}
          className="self-end px-4 py-2 bg-blue-500 text-white rounded disabled:bg-gray-300"
        >
          조회
        </button>
      </div>

      {loading && <p className="text-gray-500">로딩 중...</p>}

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded">
          <p className="text-red-600">에러: {error}</p>
        </div>
      )}

      {!loading && !error && !report && (
        <p className="text-gray-500">날짜를 선택하고 조회 버튼을 클릭하세요.</p>
      )}

      {report && !loading && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 bg-gray-50 rounded">
              <p className="text-sm text-gray-600">총 거래수</p>
              <p className="text-2xl font-bold">{report.total_trades}</p>
            </div>
            <div className="p-4 bg-gray-50 rounded">
              <p className="text-sm text-gray-600">승률</p>
              <p className="text-2xl font-bold">{report.win_rate}%</p>
            </div>
            <div className="p-4 bg-gray-50 rounded">
              <p className="text-sm text-gray-600">총 손익</p>
              <p className="text-2xl font-bold">{report.total_pnl.toLocaleString()}원</p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 bg-green-50 rounded">
              <p className="text-sm text-gray-600">최적 패턴</p>
              <p className="text-lg font-semibold">{report.best_pattern || "없음"}</p>
            </div>
            <div className="p-4 bg-red-50 rounded">
              <p className="text-sm text-gray-600">최악 패턴</p>
              <p className="text-lg font-semibold">{report.worst_pattern || "없음"}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
