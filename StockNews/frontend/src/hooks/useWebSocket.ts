import { useCallback, useEffect, useRef, useState } from 'react';
import type { WebSocketMessage } from '../types/api';

export function useWebSocket(url: string) {
  const [isConnected, setIsConnected] = useState(false);
  const [messages, setMessages] = useState<WebSocketMessage[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const manualClose = useRef(false);

  const connect = useCallback(() => {
    manualClose.current = false;
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
    };

    ws.onmessage = (event: MessageEvent) => {
      try {
        const msg: WebSocketMessage = JSON.parse(event.data);
        if (msg.type === 'ping') {
          ws.send(JSON.stringify({ type: 'pong' }));
          return;
        }
        setMessages((prev) => [...prev, msg]);
      } catch {
        // Ignore malformed messages
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      if (!manualClose.current) {
        // Auto-reconnect after 3 seconds
        setTimeout(() => connect(), 3000);
      }
    };

    ws.onerror = () => {
      ws.close();
    };
  }, [url]);

  const disconnect = useCallback(() => {
    manualClose.current = true;
    wsRef.current?.close();
    wsRef.current = null;
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  useEffect(() => {
    connect();
    return () => {
      manualClose.current = true;
      wsRef.current?.close();
    };
  }, [connect]);

  return { isConnected, messages, disconnect, clearMessages };
}
