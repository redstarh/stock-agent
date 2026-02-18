import { renderHook, act } from '@testing-library/react';
import { vi } from 'vitest';
import { useWebSocket } from '../../src/hooks/useWebSocket';

// Mock WebSocket
class MockWebSocket {
  static instances: MockWebSocket[] = [];
  url: string;
  onopen: (() => void) | null = null;
  onmessage: ((e: { data: string }) => void) | null = null;
  onclose: (() => void) | null = null;
  onerror: (() => void) | null = null;
  readyState = 0; // CONNECTING
  sentMessages: string[] = [];

  constructor(url: string) {
    this.url = url;
    MockWebSocket.instances.push(this);
    // Simulate async open
    setTimeout(() => {
      this.readyState = 1; // OPEN
      this.onopen?.();
    }, 0);
  }

  send(data: string) {
    this.sentMessages.push(data);
  }

  close() {
    this.readyState = 3; // CLOSED
    this.onclose?.();
  }
}

beforeEach(() => {
  MockWebSocket.instances = [];
  vi.stubGlobal('WebSocket', MockWebSocket);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('useWebSocket', () => {
  it('establishes WebSocket connection', async () => {
    const { result } = renderHook(() => useWebSocket('ws://localhost:8000/ws/news'));

    // Wait for connection
    await act(async () => {
      await new Promise((r) => setTimeout(r, 10));
    });

    expect(MockWebSocket.instances).toHaveLength(1);
    expect(MockWebSocket.instances[0].url).toBe('ws://localhost:8000/ws/news');
    expect(result.current.isConnected).toBe(true);

    // Cleanup
    act(() => result.current.disconnect());
  });

  it('receives breaking_news messages and creates notifications', async () => {
    const { result } = renderHook(() => useWebSocket('ws://localhost:8000/ws/news'));

    await act(async () => {
      await new Promise((r) => setTimeout(r, 10));
    });

    // Simulate incoming message
    act(() => {
      const ws = MockWebSocket.instances[0];
      ws.onmessage?.({
        data: JSON.stringify({
          type: 'breaking_news',
          data: { title: '속보: 삼성전자', stock_code: '005930', news_score: 85 },
        }),
      });
    });

    expect(result.current.messages).toHaveLength(1);
    expect(result.current.messages[0].type).toBe('breaking_news');
    expect(result.current.notifications).toHaveLength(1);
    expect(result.current.unreadCount).toBe(1);

    act(() => result.current.disconnect());
  });

  it('calls onBreakingNews callback', async () => {
    const onBreakingNews = vi.fn();
    const { result } = renderHook(() =>
      useWebSocket('ws://localhost:8000/ws/news', onBreakingNews)
    );

    await act(async () => {
      await new Promise((r) => setTimeout(r, 10));
    });

    act(() => {
      const ws = MockWebSocket.instances[0];
      ws.onmessage?.({
        data: JSON.stringify({
          type: 'breaking_news',
          data: { title: '속보', stock_code: '005930', news_score: 90 },
        }),
      });
    });

    expect(onBreakingNews).toHaveBeenCalledWith({
      title: '속보',
      stock_code: '005930',
      news_score: 90,
    });

    act(() => result.current.disconnect());
  });

  it('receives score_update messages without creating notifications', async () => {
    const { result } = renderHook(() => useWebSocket('ws://localhost:8000/ws/news'));

    await act(async () => {
      await new Promise((r) => setTimeout(r, 10));
    });

    act(() => {
      const ws = MockWebSocket.instances[0];
      ws.onmessage?.({
        data: JSON.stringify({
          type: 'score_update',
          data: { stock_code: '005930', score: 90 },
        }),
      });
    });

    expect(result.current.messages).toHaveLength(1);
    expect(result.current.messages[0].type).toBe('score_update');
    expect(result.current.notifications).toHaveLength(0);

    act(() => result.current.disconnect());
  });

  it('marks notification as read', async () => {
    const { result } = renderHook(() => useWebSocket('ws://localhost:8000/ws/news'));

    await act(async () => {
      await new Promise((r) => setTimeout(r, 10));
    });

    act(() => {
      const ws = MockWebSocket.instances[0];
      ws.onmessage?.({
        data: JSON.stringify({
          type: 'breaking_news',
          data: { title: 'Test', stock_code: '005930', news_score: 85 },
        }),
      });
    });

    const notificationId = result.current.notifications[0].id;

    act(() => {
      result.current.markAsRead(notificationId);
    });

    expect(result.current.notifications[0].read).toBe(true);
    expect(result.current.unreadCount).toBe(0);

    act(() => result.current.disconnect());
  });

  it('marks all notifications as read', async () => {
    const { result } = renderHook(() => useWebSocket('ws://localhost:8000/ws/news'));

    await act(async () => {
      await new Promise((r) => setTimeout(r, 10));
    });

    act(() => {
      const ws = MockWebSocket.instances[0];
      ws.onmessage?.({
        data: JSON.stringify({
          type: 'breaking_news',
          data: { title: 'News 1', stock_code: '005930', news_score: 85 },
        }),
      });
      ws.onmessage?.({
        data: JSON.stringify({
          type: 'breaking_news',
          data: { title: 'News 2', stock_code: '000660', news_score: 90 },
        }),
      });
    });

    expect(result.current.unreadCount).toBe(2);

    act(() => {
      result.current.markAllAsRead();
    });

    expect(result.current.unreadCount).toBe(0);

    act(() => result.current.disconnect());
  });

  it('responds to ping with pong', async () => {
    const { result } = renderHook(() => useWebSocket('ws://localhost:8000/ws/news'));

    await act(async () => {
      await new Promise((r) => setTimeout(r, 10));
    });

    act(() => {
      const ws = MockWebSocket.instances[0];
      ws.onmessage?.({
        data: JSON.stringify({ type: 'ping' }),
      });
    });

    const ws = MockWebSocket.instances[0];
    expect(ws.sentMessages).toContain(JSON.stringify({ type: 'pong' }));

    act(() => result.current.disconnect());
  });

  it('marks as disconnected on close', async () => {
    const { result } = renderHook(() => useWebSocket('ws://localhost:8000/ws/news'));

    await act(async () => {
      await new Promise((r) => setTimeout(r, 10));
    });

    expect(result.current.isConnected).toBe(true);

    act(() => {
      MockWebSocket.instances[0].close();
    });

    expect(result.current.isConnected).toBe(false);

    act(() => result.current.disconnect());
  });
});
