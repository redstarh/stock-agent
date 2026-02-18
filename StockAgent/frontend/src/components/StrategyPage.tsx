"use client";

import { useEffect, useState } from "react";
import { apiClient } from "@/lib/api";
import type { StrategyConfig } from "@/lib/types";

export default function StrategyPage() {
  const [config, setConfig] = useState<StrategyConfig>({
    top_n: 5,
    news_threshold: 0.7,
    vwap_condition: true,
  });
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const data = await apiClient.getStrategyConfig();
        setConfig(data);
      } catch (error) {
        console.error("Failed to fetch strategy config:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchConfig();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setMessage(null);
    try {
      await apiClient.updateStrategyConfig(config);
      setMessage({ type: "success", text: "저장 완료" });
    } catch (error) {
      setMessage({ type: "error", text: "저장 실패" });
    }
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">전략 설정</h1>
      <form onSubmit={handleSubmit} className="space-y-4 max-w-md">
        <div>
          <label htmlFor="top_n" className="block text-sm font-medium mb-1">
            TOP N
          </label>
          <input
            id="top_n"
            type="number"
            min="1"
            max="20"
            value={config.top_n}
            onChange={(e) => setConfig({ ...config, top_n: Number(e.target.value) })}
            className="w-full px-3 py-2 border rounded"
          />
        </div>

        <div>
          <label htmlFor="news_threshold" className="block text-sm font-medium mb-1">
            뉴스 임계값
          </label>
          <input
            id="news_threshold"
            type="number"
            min="0"
            max="1"
            step="0.1"
            value={config.news_threshold}
            onChange={(e) => setConfig({ ...config, news_threshold: Number(e.target.value) })}
            className="w-full px-3 py-2 border rounded"
          />
        </div>

        <div>
          <label htmlFor="vwap_condition" className="flex items-center space-x-2">
            <input
              id="vwap_condition"
              type="checkbox"
              checked={config.vwap_condition}
              onChange={(e) => setConfig({ ...config, vwap_condition: e.target.checked })}
              className="w-4 h-4"
            />
            <span className="text-sm font-medium">VWAP 조건</span>
          </label>
        </div>

        <button
          type="submit"
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          저장
        </button>

        {message && (
          <div
            className={`mt-4 p-3 rounded ${
              message.type === "success" ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"
            }`}
          >
            {message.text}
          </div>
        )}
      </form>
    </div>
  );
}
