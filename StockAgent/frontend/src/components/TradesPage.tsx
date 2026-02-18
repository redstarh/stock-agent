/** 매매 내역 페이지 */

"use client";

import { useEffect, useState } from "react";
import { apiClient } from "@/lib/api";
import type { Trade, PaginatedResponse } from "@/lib/types";

export default function TradesPage() {
  const [data, setData] = useState<PaginatedResponse<Trade> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchTrades = async () => {
      try {
        setLoading(true);
        const result = await apiClient.getTrades({ page: 1, size: 10 });
        setData(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        setLoading(false);
      }
    };

    fetchTrades();
  }, []);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!data) return null;

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">매매 내역</h1>
      <table className="w-full border-collapse border border-gray-300">
        <thead>
          <tr className="bg-gray-100">
            <th className="border border-gray-300 px-4 py-2">날짜</th>
            <th className="border border-gray-300 px-4 py-2">종목코드</th>
            <th className="border border-gray-300 px-4 py-2">종목명</th>
            <th className="border border-gray-300 px-4 py-2">매수/매도</th>
            <th className="border border-gray-300 px-4 py-2">수량</th>
            <th className="border border-gray-300 px-4 py-2">손익</th>
          </tr>
        </thead>
        <tbody>
          {data.items.map((trade) => (
            <tr key={trade.trade_id}>
              <td className="border border-gray-300 px-4 py-2">{trade.date}</td>
              <td className="border border-gray-300 px-4 py-2">{trade.stock_code}</td>
              <td className="border border-gray-300 px-4 py-2">{trade.stock_name}</td>
              <td className="border border-gray-300 px-4 py-2">
                {trade.side === "buy" ? "매수" : "매도"}
              </td>
              <td className="border border-gray-300 px-4 py-2">{trade.quantity}</td>
              <td
                className={`border border-gray-300 px-4 py-2 ${
                  trade.pnl >= 0 ? "text-green-600" : "text-red-600"
                }`}
              >
                {trade.pnl.toLocaleString()}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="mt-4">
        페이지: {data.page} / 총 {data.total}건
      </div>
    </div>
  );
}
