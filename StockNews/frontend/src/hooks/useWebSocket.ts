import { useCallback, useEffect, useRef, useState } from 'react';
import type { WebSocketMessage, BreakingNewsData } from '../types/api';

export interface Notification {
  id: string;
  message: WebSocketMessage;
  timestamp: number;
  read: boolean;
}

export function useWebSocket(
  url: string,
  onBreakingNews?: (data: BreakingNewsData) => void
) {
  const [isConnected, setIsConnected] = useState(false);
  const [messages, setMessages] = useState<WebSocketMessage[]>([]);
  const [notifications, setNotifications] = useState<Notification[]>([]);
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

        // Handle breaking news
        if (msg.type === 'breaking_news' && msg.data) {
          const notification: Notification = {
            id: `${Date.now()}-${Math.random()}`,
            message: msg,
            timestamp: Date.now(),
            read: false,
          };
          setNotifications((prev) => [notification, ...prev].slice(0, 10)); // Keep last 10

          if (onBreakingNews) {
            onBreakingNews(msg.data as BreakingNewsData);
          }
        }
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

  const markAsRead = useCallback((id: string) => {
    setNotifications((prev) =>
      prev.map((notif) => (notif.id === id ? { ...notif, read: true } : notif))
    );
  }, []);

  const markAllAsRead = useCallback(() => {
    setNotifications((prev) => prev.map((notif) => ({ ...notif, read: true })));
  }, []);

  const clearNotifications = useCallback(() => {
    setNotifications([]);
  }, []);

  const unreadCount = notifications.filter((n) => !n.read).length;

  useEffect(() => {
    connect();
    return () => {
      manualClose.current = true;
      wsRef.current?.close();
    };
  }, [connect]);

  return {
    isConnected,
    messages,
    notifications,
    unreadCount,
    disconnect,
    clearMessages,
    markAsRead,
    markAllAsRead,
    clearNotifications,
  };
}
