"use client";

import { useEffect, useState } from "react";
import { apiClient } from "@/lib/api";
import type { MetricsData } from "@/lib/types";

export default function ProfitChart() {
  const [metrics, setMetrics] = useState<MetricsData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        setLoading(true);
        const data = await apiClient.getReportMetrics();
        setMetrics(data);
        setError(null);
      } catch (err) {
        setError("Error loading metrics");
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchMetrics();
  }, []);

  if (loading) {
    return <div>Loading metrics...</div>;
  }

  if (error) {
    return <div>{error}</div>;
  }

  // Get the latest metrics (first item in array)
  const latestMetrics = metrics[0];

  if (!latestMetrics) {
    return <div>No metrics data available</div>;
  }

  // Format currency in KRW
  const formatCurrency = (amount: number) => {
    return `₩${amount.toLocaleString("ko-KR")}`;
  };

  // Format percentage
  const formatPercentage = (value: number) => {
    return `${value.toFixed(1)}%`;
  };

  return (
    <div data-testid="profit-chart" className="p-4 border rounded">
      <h2 className="text-xl font-bold mb-4">성과 분석</h2>

      <div className="grid grid-cols-2 gap-4">
        <div className="p-4 bg-gray-50 rounded">
          <div className="text-sm text-gray-600">Total P&L</div>
          <div className="text-2xl font-bold">
            {formatCurrency(latestMetrics.total_pnl)}
          </div>
        </div>

        <div className="p-4 bg-gray-50 rounded">
          <div className="text-sm text-gray-600">Win Rate</div>
          <div className="text-2xl font-bold">
            {formatPercentage(latestMetrics.win_rate)}
          </div>
        </div>

        <div className="p-4 bg-gray-50 rounded">
          <div className="text-sm text-gray-600">Total Trades</div>
          <div className="text-2xl font-bold">
            {latestMetrics.total_trades}
          </div>
        </div>

        <div className="p-4 bg-gray-50 rounded">
          <div className="text-sm text-gray-600">Max Drawdown</div>
          <div className="text-2xl font-bold">
            {formatCurrency(latestMetrics.max_drawdown)}
          </div>
        </div>
      </div>

      <div className="mt-4 text-sm text-gray-500">
        As of: {latestMetrics.date}
      </div>
    </div>
  );
}
