"use client";

import { useEffect, useState } from "react";
import type { Position } from "@/lib/types";

export default function PositionList() {
  const [positions, setPositions] = useState<Position[] | null>(null);

  useEffect(() => {
    fetch("http://localhost:8000/api/v1/account/positions")
      .then((res) => res.json())
      .then((data) => setPositions(data))
      .catch(() => setPositions([]));
  }, []);

  if (positions === null) {
    return <div>로딩 중...</div>;
  }

  if (positions.length === 0) {
    return <div className="text-gray-500 p-4">보유 종목 없음</div>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b text-left">
            <th className="p-2">종목코드</th>
            <th className="p-2">종목명</th>
            <th className="p-2 text-right">수량</th>
            <th className="p-2 text-right">평균가</th>
            <th className="p-2 text-right">현재가</th>
            <th className="p-2 text-right">평가손익</th>
          </tr>
        </thead>
        <tbody>
          {positions.map((p) => (
            <tr key={p.stock_code} className="border-b">
              <td className="p-2">{p.stock_code}</td>
              <td className="p-2">{p.stock_name}</td>
              <td className="p-2 text-right">{p.quantity}</td>
              <td className="p-2 text-right">{p.avg_price.toLocaleString()}</td>
              <td className="p-2 text-right">{p.current_price.toLocaleString()}</td>
              <td
                className={`p-2 text-right ${
                  p.unrealized_pnl >= 0 ? "text-green-600" : "text-red-600"
                }`}
              >
                {p.unrealized_pnl >= 0 ? "+" : ""}
                {p.unrealized_pnl.toLocaleString()}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
