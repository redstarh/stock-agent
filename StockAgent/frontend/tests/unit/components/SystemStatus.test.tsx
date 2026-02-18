/**
 * T-F6: 실시간 상태 컴포넌트 테스트
 */
import { render, screen, waitFor, act } from "@testing-library/react";
import SystemStatus from "@/components/SystemStatus";

// Simple WebSocket mock
class MockWebSocket {
  static instances: MockWebSocket[] = [];
  onopen: (() => void) | null = null;
  onmessage: ((event: { data: string }) => void) | null = null;
  onclose: (() => void) | null = null;
  onerror: ((event: unknown) => void) | null = null;
  readyState = 0;

  constructor(public url: string) {
    MockWebSocket.instances.push(this);
    setTimeout(() => {
      this.readyState = 1;
      this.onopen?.();
    }, 0);
  }

  send(_data: string) {}
  close() {
    this.readyState = 3;
    this.onclose?.();
  }

  // Test helper: simulate server message
  simulateMessage(data: unknown) {
    this.onmessage?.({ data: JSON.stringify(data) });
  }
}

beforeEach(() => {
  MockWebSocket.instances = [];
  (globalThis as any).WebSocket = MockWebSocket;
});

afterEach(() => {
  MockWebSocket.instances.forEach((ws) => ws.close());
});

describe("SystemStatus", () => {
  test("shows connecting state initially", () => {
    render(<SystemStatus />);
    expect(screen.getByText(/연결 중/)).toBeInTheDocument();
  });

  test("displays system status after WebSocket message", async () => {
    render(<SystemStatus />);

    await waitFor(() => {
      expect(MockWebSocket.instances.length).toBe(1);
    });

    act(() => {
      MockWebSocket.instances[0].simulateMessage({
        type: "system_status",
        data: { status: "running", uptime: 3600, active_positions: 3 },
      });
    });

    await waitFor(() => {
      expect(screen.getByText(/running/i)).toBeInTheDocument();
      expect(screen.getByText(/3/)).toBeInTheDocument();
    });
  });

  test("shows disconnected state when WebSocket closes", async () => {
    render(<SystemStatus />);

    await waitFor(() => {
      expect(MockWebSocket.instances.length).toBe(1);
    });

    act(() => {
      MockWebSocket.instances[0].close();
    });

    await waitFor(() => {
      expect(screen.getByText(/연결 끊김/)).toBeInTheDocument();
    });
  });
});
