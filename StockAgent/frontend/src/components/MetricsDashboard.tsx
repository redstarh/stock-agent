"use client";

import { useEffect, useState } from "react";
import { apiClient } from "@/lib/api";
import type { MetricsData } from "@/lib/types";

export default function MetricsDashboard() {
  const [metrics, setMetrics] = useState<MetricsData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchMetrics() {
      try {
        setLoading(true);
        const data = await apiClient.getReportMetrics();
        setMetrics(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load metrics");
      } finally {
        setLoading(false);
      }
    }

    fetchMetrics();
  }, []);

  if (loading) {
    return (
      <div className="p-4">
        <p>Loading metrics...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 text-red-600">
        <p>Failed to load metrics: {error}</p>
      </div>
    );
  }

  // Use the latest metrics data (first item)
  const latestMetrics = metrics[0] || {
    date: "",
    win_rate: 0,
    total_pnl: 0,
    max_drawdown: 0,
    total_trades: 0,
  };

  const formatNumber = (num: number): string => {
    return new Intl.NumberFormat("en-US").format(num);
  };

  const formatPercent = (num: number): string => {
    return `${num.toFixed(1)}%`;
  };

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-6">Learning Metrics Dashboard</h2>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-sm text-gray-600 mb-2">Win Rate</h3>
          <p className="text-2xl font-bold text-green-600">
            {formatPercent(latestMetrics.win_rate)}
          </p>
        </div>

        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-sm text-gray-600 mb-2">Total P&L</h3>
          <p className="text-2xl font-bold text-blue-600">
            {formatNumber(latestMetrics.total_pnl)}
          </p>
        </div>

        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-sm text-gray-600 mb-2">Max Drawdown</h3>
          <p className="text-2xl font-bold text-red-600">
            {formatPercent(latestMetrics.max_drawdown)}
          </p>
        </div>

        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-sm text-gray-600 mb-2">Total Trades</h3>
          <p className="text-2xl font-bold text-gray-800">
            {latestMetrics.total_trades}
          </p>
        </div>
      </div>

      {/* Daily Summary Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <h3 className="text-lg font-semibold p-4 border-b">Daily Summary</h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Date
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Win Rate
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Total P&L
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Max Drawdown
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Trades
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {metrics.map((metric, index) => (
                <tr key={index} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm text-gray-900">
                    {metric.date}
                  </td>
                  <td className="px-4 py-3 text-sm text-right text-green-600">
                    {formatPercent(metric.win_rate)}
                  </td>
                  <td className="px-4 py-3 text-sm text-right text-blue-600">
                    {formatNumber(metric.total_pnl)}
                  </td>
                  <td className="px-4 py-3 text-sm text-right text-red-600">
                    {formatPercent(metric.max_drawdown)}
                  </td>
                  <td className="px-4 py-3 text-sm text-right text-gray-900">
                    {metric.total_trades}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
