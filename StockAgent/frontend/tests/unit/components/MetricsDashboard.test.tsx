/**
 * T-F13: 학습 메트릭 컴포넌트 테스트
 * @jest-environment <rootDir>/tests/jest-env-jsdom.ts
 */

import { render, screen, waitFor } from "@testing-library/react";
import { server } from "@/mocks/server";
import { http, HttpResponse } from "msw";
import MetricsDashboard from "@/components/MetricsDashboard";

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe("MetricsDashboard", () => {
  test("displays drawdown visualization", async () => {
    render(<MetricsDashboard />);
    await waitFor(() => {
      const headers = screen.getAllByText(/Max Drawdown/i);
      expect(headers.length).toBeGreaterThan(0);
      const values = screen.getAllByText(/5.2%/);
      expect(values.length).toBeGreaterThan(0);
    });
  });

  test("displays win rate", async () => {
    render(<MetricsDashboard />);
    await waitFor(() => {
      const headers = screen.getAllByText(/Win Rate/i);
      expect(headers.length).toBeGreaterThan(0);
      const values = screen.getAllByText(/66.7%/);
      expect(values.length).toBeGreaterThan(0);
    });
  });

  test("displays total PnL", async () => {
    render(<MetricsDashboard />);
    await waitFor(() => {
      const headers = screen.getAllByText(/Total P&L/i);
      expect(headers.length).toBeGreaterThan(0);
      const values = screen.getAllByText(/150,000/);
      expect(values.length).toBeGreaterThan(0);
    });
  });

  test("displays total trades count", async () => {
    render(<MetricsDashboard />);
    await waitFor(() => {
      const headers = screen.getAllByText(/Total Trades/i);
      expect(headers.length).toBeGreaterThan(0);
      // Check for number 12 in the table
      const tradeNumbers = screen.getAllByText("12");
      expect(tradeNumbers.length).toBeGreaterThan(0);
    });
  });

  test("handles loading state", () => {
    render(<MetricsDashboard />);
    expect(screen.getByText(/Loading metrics/i)).toBeInTheDocument();
  });

  test("handles error state", async () => {
    server.use(
      http.get("http://localhost:8000/api/v1/reports/metrics", () =>
        HttpResponse.json({ detail: "Server error" }, { status: 500 })
      )
    );

    render(<MetricsDashboard />);
    await waitFor(() => {
      expect(screen.getByText(/Failed to load metrics/i)).toBeInTheDocument();
    });
  });

  test("formats numbers correctly", async () => {
    server.use(
      http.get("http://localhost:8000/api/v1/reports/metrics", () =>
        HttpResponse.json([
          {
            date: "2026-01-15",
            win_rate: 66.7,
            total_pnl: 1500000,
            max_drawdown: 5.2,
            total_trades: 12,
          },
        ])
      )
    );

    render(<MetricsDashboard />);
    await waitFor(() => {
      // Check comma-separated number formatting
      const pnlValues = screen.getAllByText(/1,500,000/);
      expect(pnlValues.length).toBeGreaterThan(0);
      // Check percentage formatting
      const drawdownValues = screen.getAllByText(/5.2%/);
      expect(drawdownValues.length).toBeGreaterThan(0);
    });
  });

  test("displays multiple days of data", async () => {
    render(<MetricsDashboard />);
    await waitFor(() => {
      expect(screen.getByText(/2026-01-15/)).toBeInTheDocument();
      expect(screen.getByText(/2026-01-16/)).toBeInTheDocument();
    });
  });
});
