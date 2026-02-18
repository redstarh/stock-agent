/**
 * T-F12: 성과 분석 차트 테스트
 */
import { render, screen, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import ProfitChart from "@/components/ProfitChart";
import { server } from "@/mocks/server";

describe("T-F12: ProfitChart", () => {
  beforeAll(() => server.listen());
  afterEach(() => server.resetHandlers());
  afterAll(() => server.close());

  test("renders profit chart with data", async () => {
    render(<ProfitChart />);
    await waitFor(() => {
      expect(screen.getByTestId("profit-chart")).toBeInTheDocument();
    });
  });

  test("displays loading state", () => {
    render(<ProfitChart />);
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  test("displays total P&L metric", async () => {
    render(<ProfitChart />);
    await waitFor(() => {
      expect(screen.getByText(/total p&l/i)).toBeInTheDocument();
      expect(screen.getByText(/₩150,000/)).toBeInTheDocument();
    });
  });

  test("displays win rate metric", async () => {
    render(<ProfitChart />);
    await waitFor(() => {
      expect(screen.getByText(/win rate/i)).toBeInTheDocument();
      expect(screen.getByText(/66.7%/)).toBeInTheDocument();
    });
  });

  test("handles error state", async () => {
    server.use(
      http.get("http://localhost:8000/api/v1/reports/metrics", () => {
        return HttpResponse.json({ detail: "Internal Server Error" }, { status: 500 });
      })
    );

    render(<ProfitChart />);
    await waitFor(() => {
      expect(screen.getByText(/error loading metrics/i)).toBeInTheDocument();
    });
  });
});
