"use client";

import { useEffect, useState } from "react";
import { apiClient } from "@/lib/api";
import type { ScannerResult } from "@/lib/types";

export default function ScannerPage() {
  const [scannerData, setScannerData] = useState<ScannerResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchScannerData = async () => {
      try {
        setLoading(true);
        const data = await apiClient.getScannerTop({ top_n: 10 });
        setScannerData(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to fetch scanner data");
      } finally {
        setLoading(false);
      }
    };

    fetchScannerData();
  }, []);

  if (loading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">거래대금 TOP</h1>

      <div className="overflow-x-auto">
        <table className="min-w-full bg-white border border-gray-300">
          <thead>
            <tr className="bg-gray-100">
              <th className="px-4 py-2 border-b text-left">종목코드</th>
              <th className="px-4 py-2 border-b text-left">종목명</th>
              <th className="px-4 py-2 border-b text-right">현재가</th>
              <th className="px-4 py-2 border-b text-right">거래대금</th>
              <th className="px-4 py-2 border-b text-center">거래량 급증</th>
            </tr>
          </thead>
          <tbody>
            {scannerData.map((stock) => (
              <tr key={stock.code} className="hover:bg-gray-50">
                <td className="px-4 py-2 border-b">{stock.code}</td>
                <td className="px-4 py-2 border-b">{stock.name}</td>
                <td className="px-4 py-2 border-b text-right">
                  {stock.current_price.toLocaleString()}
                </td>
                <td className="px-4 py-2 border-b text-right">
                  {stock.trade_value.toLocaleString()}
                </td>
                <td className="px-4 py-2 border-b text-center">
                  {stock.volume_surge && (
                    <span className="inline-block px-2 py-1 text-xs bg-red-100 text-red-800 rounded">
                      거래량 급증
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
