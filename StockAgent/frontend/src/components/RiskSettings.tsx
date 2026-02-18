"use client";

import { useEffect, useState } from "react";
import type { RiskConfig } from "@/lib/types";

const API_BASE = "http://localhost:8000";

export default function RiskSettings() {
  const [config, setConfig] = useState<RiskConfig | null>(null);
  const [showConfirm, setShowConfirm] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    fetch(`${API_BASE}/api/v1/risk/config`)
      .then((r) => r.json())
      .then(setConfig);
  }, []);

  const handleSave = async () => {
    if (!config) return;
    await fetch(`${API_BASE}/api/v1/risk/config`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(config),
    });
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const handleEmergencySell = async () => {
    await fetch(`${API_BASE}/api/v1/risk/emergency-sell`, { method: "POST" });
    setShowConfirm(false);
  };

  if (!config) return <div>로딩 중...</div>;

  return (
    <div className="p-4">
      <h2 className="text-xl font-bold mb-4">리스크 설정</h2>
      <div className="space-y-4">
        <div>
          <label htmlFor="stop-loss" className="block text-sm font-medium">
            손절률 (%)
          </label>
          <input
            id="stop-loss"
            type="number"
            value={config.stop_loss_pct}
            onChange={(e) => setConfig({ ...config, stop_loss_pct: Number(e.target.value) })}
            className="border rounded px-2 py-1"
          />
        </div>
        <div>
          <label htmlFor="max-position" className="block text-sm font-medium">
            최대 비중 (%)
          </label>
          <input
            id="max-position"
            type="number"
            value={config.max_position_pct}
            onChange={(e) => setConfig({ ...config, max_position_pct: Number(e.target.value) })}
            className="border rounded px-2 py-1"
          />
        </div>
        <button onClick={handleSave} className="bg-blue-500 text-white px-4 py-2 rounded">
          저장
        </button>
        {saved && <span className="text-green-600 ml-2">저장 완료</span>}
      </div>

      <div className="mt-8 border-t pt-4">
        <button
          onClick={() => setShowConfirm(true)}
          className="bg-red-500 text-white px-4 py-2 rounded"
        >
          비상 청산
        </button>
        {showConfirm && (
          <div className="mt-2 p-4 bg-red-50 border border-red-200 rounded">
            <p className="text-red-700">정말 전체 청산하시겠습니까?</p>
            <div className="mt-2 space-x-2">
              <button onClick={handleEmergencySell} className="bg-red-600 text-white px-3 py-1 rounded">
                확인
              </button>
              <button onClick={() => setShowConfirm(false)} className="bg-gray-300 px-3 py-1 rounded">
                취소
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
