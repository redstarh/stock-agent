import { renderHook, act } from '@testing-library/react';
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

  it('receives breaking_news messages', async () => {
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
          data: { title: '속보: 삼성전자', stock_code: '005930' },
        }),
      });
    });

    expect(result.current.messages).toHaveLength(1);
    expect(result.current.messages[0].type).toBe('breaking_news');

    act(() => result.current.disconnect());
  });

  it('receives score_update messages', async () => {
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
