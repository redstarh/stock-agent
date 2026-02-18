"use client";

import { useEffect, useState } from "react";
import type { AccountBalance } from "@/lib/types";

export default function Dashboard() {
  const [balance, setBalance] = useState<AccountBalance | null>(null);

  useEffect(() => {
    fetch("http://localhost:8000/api/v1/account/balance")
      .then((res) => res.json())
      .then((data) => setBalance(data))
      .catch(() => {});
  }, []);

  if (!balance) {
    return <div>로딩 중...</div>;
  }

  const pnlColor = balance.daily_pnl >= 0 ? "text-green-600" : "text-red-600";

  return (
    <div className="space-y-4">
      <div className="rounded border p-4">
        <h2 className="text-lg font-semibold">계좌 현황</h2>
        <dl className="mt-2 grid grid-cols-2 gap-4">
          <div>
            <dt className="text-sm text-gray-500">예수금</dt>
            <dd className="text-xl font-bold">
              {balance.cash.toLocaleString()}
            </dd>
          </div>
          <div>
            <dt className="text-sm text-gray-500">총 평가</dt>
            <dd className="text-xl font-bold">
              {balance.total_eval.toLocaleString()}
            </dd>
          </div>
          <div>
            <dt className="text-sm text-gray-500">일일 손익</dt>
            <dd data-testid="daily-pnl" className={`text-xl font-bold ${pnlColor}`}>
              {balance.daily_pnl >= 0 ? "+" : ""}
              {balance.daily_pnl.toLocaleString()}
            </dd>
          </div>
        </dl>
      </div>
    </div>
  );
}
