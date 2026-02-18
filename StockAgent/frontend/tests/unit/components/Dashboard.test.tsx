/**
 * T-F4: 계좌 대시보드 테스트
 */
import { render, screen, waitFor } from "@testing-library/react";
import Dashboard from "@/components/Dashboard";
import { server } from "@/mocks/server";
import { http, HttpResponse } from "msw";

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe("Dashboard", () => {
  test("displays account balance", async () => {
    render(<Dashboard />);
    await waitFor(() => {
      expect(screen.getByText(/예수금/)).toBeInTheDocument();
      expect(screen.getByText(/10,000,000/)).toBeInTheDocument();
    });
  });

  test("displays daily PnL with positive color", async () => {
    render(<Dashboard />);
    await waitFor(() => {
      const pnl = screen.getByTestId("daily-pnl");
      expect(pnl).toHaveClass("text-green-600");
    });
  });

  test("displays daily PnL with negative color", async () => {
    server.use(
      http.get("http://localhost:8000/api/v1/account/balance", () =>
        HttpResponse.json({
          cash: 10000000,
          total_eval: 14000000,
          daily_pnl: -150000,
        })
      )
    );
    render(<Dashboard />);
    await waitFor(() => {
      const pnl = screen.getByTestId("daily-pnl");
      expect(pnl).toHaveClass("text-red-600");
    });
  });
});
