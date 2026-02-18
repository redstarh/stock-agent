/**
 * T-F11: 주문 모니터링 컴포넌트 테스트
 */
import { render, screen, waitFor, act } from "@testing-library/react";
import { server } from "@/mocks/server";
import { http, HttpResponse } from "msw";
import OrderMonitor from "@/components/OrderMonitor";

// MSW 서버 라이프사이클
beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

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

describe("OrderMonitor", () => {
  test("displays order list from API", async () => {
    render(<OrderMonitor />);

    await waitFor(() => {
      expect(screen.getByText("ORD001")).toBeInTheDocument();
      expect(screen.getByText("005930")).toBeInTheDocument();
      expect(screen.getByText("매수")).toBeInTheDocument();
    });
  });

  test("displays real-time order updates via WebSocket", async () => {
    render(<OrderMonitor />);

    await waitFor(() => {
      expect(MockWebSocket.instances.length).toBe(1);
    });

    act(() => {
      MockWebSocket.instances[0].simulateMessage({
        type: "order_update",
        data: {
          order_id: "ORD001",
          stock_code: "005930",
          side: "buy",
          quantity: 10,
          price: 71000,
          status: "filled",
        },
      });
    });

    await waitFor(() => {
      expect(screen.getByText("체결")).toBeInTheDocument();
    });
  });

  test("updates order status from pending to filled", async () => {
    render(<OrderMonitor />);

    // Initial state (pending) from MSW
    await waitFor(() => {
      expect(screen.getByText("대기")).toBeInTheDocument();
    });

    // WebSocket update to filled
    await waitFor(() => {
      expect(MockWebSocket.instances.length).toBe(1);
    });

    act(() => {
      MockWebSocket.instances[0].simulateMessage({
        type: "order_update",
        data: {
          order_id: "ORD001",
          stock_code: "005930",
          side: "buy",
          quantity: 10,
          price: 71000,
          status: "filled",
        },
      });
    });

    await waitFor(() => {
      expect(screen.getByText("체결")).toBeInTheDocument();
      expect(screen.queryByText("대기")).not.toBeInTheDocument();
    });
  });

  test("displays multiple orders with different statuses", async () => {
    render(<OrderMonitor />);

    await waitFor(() => {
      expect(MockWebSocket.instances.length).toBe(1);
    });

    // Add multiple order updates
    act(() => {
      MockWebSocket.instances[0].simulateMessage({
        type: "order_update",
        data: {
          order_id: "ORD002",
          stock_code: "035720",
          side: "sell",
          quantity: 5,
          price: 50000,
          status: "cancelled",
        },
      });
    });

    await waitFor(() => {
      expect(screen.getByText("취소")).toBeInTheDocument();
      expect(screen.getByText("035720")).toBeInTheDocument();
      expect(screen.getByText("매도")).toBeInTheDocument();
    });
  });

  test("displays error when API fetch fails", async () => {
    server.use(
      http.get("http://localhost:8000/api/v1/orders", () => {
        return HttpResponse.json(
          { detail: "Internal server error" },
          { status: 500 }
        );
      })
    );

    render(<OrderMonitor />);

    await waitFor(() => {
      expect(screen.getByText(/오류:/)).toBeInTheDocument();
    });
  });

  test("handles invalid WebSocket message gracefully", async () => {
    render(<OrderMonitor />);

    // Wait for WebSocket connection
    await waitFor(() => {
      expect(MockWebSocket.instances.length).toBe(1);
    });

    // Send invalid JSON message
    act(() => {
      MockWebSocket.instances[0].onmessage?.({ data: "invalid json" });
    });

    // Component should not crash - orders from initial API call still visible
    await waitFor(() => {
      expect(screen.getByText("ORD001")).toBeInTheDocument();
    });
  });

  test("handles WebSocket error event", async () => {
    render(<OrderMonitor />);

    // Wait for WebSocket connection
    await waitFor(() => {
      expect(MockWebSocket.instances.length).toBe(1);
    });

    // Trigger error event
    act(() => {
      MockWebSocket.instances[0].onerror?.(new Event("error"));
    });

    // Component should not crash - orders still visible
    await waitFor(() => {
      expect(screen.getByText("ORD001")).toBeInTheDocument();
    });
  });
});
