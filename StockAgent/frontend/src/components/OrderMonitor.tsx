"use client";

import { useEffect, useState } from "react";
import { apiClient } from "@/lib/api";
import type { OrderInfo } from "@/lib/types";

const WS_URL =
  process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/api/v1/ws";

export default function OrderMonitor() {
  const [orders, setOrders] = useState<OrderInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Fetch initial orders
    apiClient
      .getOrders()
      .then((data) => {
        setOrders(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });

    // Connect to WebSocket for real-time updates
    const ws = new WebSocket(WS_URL);

    ws.onopen = () => {
      console.log("OrderMonitor WebSocket connected");
    };

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        if (message.type === "order_update" && message.data) {
          const updatedOrder: OrderInfo = message.data;
          setOrders((prev) => {
            const existing = prev.find(
              (o) => o.order_id === updatedOrder.order_id
            );
            if (existing) {
              // Update existing order
              return prev.map((o) =>
                o.order_id === updatedOrder.order_id ? updatedOrder : o
              );
            } else {
              // Add new order
              return [...prev, updatedOrder];
            }
          });
        }
      } catch (err) {
        console.error("Failed to parse WebSocket message:", err);
      }
    };

    ws.onerror = (err) => {
      console.error("OrderMonitor WebSocket error:", err);
    };

    ws.onclose = () => {
      console.log("OrderMonitor WebSocket disconnected");
    };

    return () => {
      ws.close();
    };
  }, []);

  const getStatusBadge = (status: OrderInfo["status"]) => {
    switch (status) {
      case "filled":
        return (
          <span className="px-2 py-1 text-xs font-semibold rounded bg-green-100 text-green-800">
            체결
          </span>
        );
      case "pending":
        return (
          <span className="px-2 py-1 text-xs font-semibold rounded bg-yellow-100 text-yellow-800">
            대기
          </span>
        );
      case "cancelled":
        return (
          <span className="px-2 py-1 text-xs font-semibold rounded bg-gray-100 text-gray-800">
            취소
          </span>
        );
    }
  };

  const getSideBadge = (side: OrderInfo["side"]) => {
    return side === "buy" ? (
      <span className="px-2 py-1 text-xs font-semibold rounded bg-blue-100 text-blue-800">
        매수
      </span>
    ) : (
      <span className="px-2 py-1 text-xs font-semibold rounded bg-red-100 text-red-800">
        매도
      </span>
    );
  };

  if (loading) {
    return <div className="p-4">주문 정보를 불러오는 중...</div>;
  }

  if (error) {
    return <div className="p-4 text-red-600">오류: {error}</div>;
  }

  return (
    <div className="p-4">
      <h2 className="text-2xl font-bold mb-4">주문 모니터링</h2>
      {orders.length === 0 ? (
        <p className="text-gray-500">주문 내역이 없습니다.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full border-collapse border border-gray-300">
            <thead className="bg-gray-100">
              <tr>
                <th className="border border-gray-300 px-4 py-2 text-left">
                  주문번호
                </th>
                <th className="border border-gray-300 px-4 py-2 text-left">
                  종목코드
                </th>
                <th className="border border-gray-300 px-4 py-2 text-left">
                  매수/매도
                </th>
                <th className="border border-gray-300 px-4 py-2 text-right">
                  수량
                </th>
                <th className="border border-gray-300 px-4 py-2 text-right">
                  가격
                </th>
                <th className="border border-gray-300 px-4 py-2 text-left">
                  상태
                </th>
              </tr>
            </thead>
            <tbody>
              {orders.map((order) => (
                <tr key={order.order_id} className="hover:bg-gray-50">
                  <td className="border border-gray-300 px-4 py-2">
                    {order.order_id}
                  </td>
                  <td className="border border-gray-300 px-4 py-2">
                    {order.stock_code}
                  </td>
                  <td className="border border-gray-300 px-4 py-2">
                    {getSideBadge(order.side)}
                  </td>
                  <td className="border border-gray-300 px-4 py-2 text-right">
                    {order.quantity.toLocaleString()}
                  </td>
                  <td className="border border-gray-300 px-4 py-2 text-right">
                    {order.price.toLocaleString()}원
                  </td>
                  <td className="border border-gray-300 px-4 py-2">
                    {getStatusBadge(order.status)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
