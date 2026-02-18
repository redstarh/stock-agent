"use client";

import { useEffect, useRef, useState } from "react";

interface StatusData {
  status: "running" | "stopped" | "error";
  uptime: number;
  active_positions: number;
}

type ConnectionState = "connecting" | "connected" | "disconnected";

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws/live";

export default function SystemStatus() {
  const [connectionState, setConnectionState] = useState<ConnectionState>("connecting");
  const [statusData, setStatusData] = useState<StatusData | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnectionState("connected");
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === "system_status") {
          setStatusData(msg.data);
        }
      } catch (e) {
        // ignore parse errors
      }
    };

    ws.onclose = () => {
      setConnectionState("disconnected");
    };

    ws.onerror = () => {
      setConnectionState("disconnected");
    };

    return () => {
      ws.close();
    };
  }, []);

  if (connectionState === "connecting") {
    return <div className="p-4 text-yellow-600">연결 중...</div>;
  }

  if (connectionState === "disconnected") {
    return <div className="p-4 text-red-600">연결 끊김</div>;
  }

  return (
    <div className="p-4">
      <h2 className="text-xl font-bold mb-4">시스템 상태</h2>
      {statusData ? (
        <div className="space-y-2">
          <div>
            상태: <span className={statusData.status === "running" ? "text-green-600" : "text-red-600"}>
              {statusData.status}
            </span>
          </div>
          <div>활성 포지션: {statusData.active_positions}</div>
          <div>가동시간: {Math.floor(statusData.uptime / 60)}분</div>
        </div>
      ) : (
        <div>데이터 대기 중...</div>
      )}
    </div>
  );
}
