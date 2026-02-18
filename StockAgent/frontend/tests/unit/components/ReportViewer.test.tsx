/**
 * @jest-environment <rootDir>/tests/jest-env-jsdom.ts
 */

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { server } from "@/mocks/server";
import ReportViewer from "@/components/ReportViewer";

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe("ReportViewer", () => {
  test("loads and displays daily report", async () => {
    render(<ReportViewer />);

    // 날짜 입력 후 조회
    const dateInput = screen.getByLabelText(/날짜/);
    await userEvent.clear(dateInput);
    await userEvent.type(dateInput, "2026-01-15");
    await userEvent.click(screen.getByRole("button", { name: /조회/ }));

    await waitFor(() => {
      expect(screen.getByText(/승률/)).toBeInTheDocument();
    });
  });

  test("displays initial state with guidance message", () => {
    render(<ReportViewer />);
    expect(screen.getByText(/날짜를 선택하고 조회 버튼을 클릭하세요/)).toBeInTheDocument();
  });

  test("displays report data correctly", async () => {
    render(<ReportViewer />);

    const dateInput = screen.getByLabelText(/날짜/);
    await userEvent.type(dateInput, "2026-01-15");
    await userEvent.click(screen.getByRole("button", { name: /조회/ }));

    await waitFor(() => {
      expect(screen.getByText(/총 거래수/)).toBeInTheDocument();
      expect(screen.getByText("12")).toBeInTheDocument();
      expect(screen.getByText(/승률/)).toBeInTheDocument();
      expect(screen.getByText("66.7%")).toBeInTheDocument();
      expect(screen.getByText(/총 손익/)).toBeInTheDocument();
      expect(screen.getByText("150,000원")).toBeInTheDocument();
      expect(screen.getByText(/최적 패턴/)).toBeInTheDocument();
      expect(screen.getByText("volume_leader")).toBeInTheDocument();
      expect(screen.getByText(/최악 패턴/)).toBeInTheDocument();
      expect(screen.getByText("news_breakout")).toBeInTheDocument();
    });
  });

  test("shows loading state during fetch", async () => {
    const { http, HttpResponse, delay } = await import("msw");
    server.use(
      http.get("http://localhost:8000/api/v1/reports/daily", async () => {
        await delay(100);
        return HttpResponse.json({
          date: "2026-01-15",
          total_trades: 12,
          win_rate: 66.7,
          total_pnl: 150000,
          best_pattern: "volume_leader",
          worst_pattern: "news_breakout",
        });
      })
    );

    render(<ReportViewer />);

    const dateInput = screen.getByLabelText(/날짜/);
    await userEvent.type(dateInput, "2026-01-15");
    await userEvent.click(screen.getByRole("button", { name: /조회/ }));

    expect(screen.getByText(/로딩 중/)).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.queryByText(/로딩 중/)).not.toBeInTheDocument();
    });
  });

  test("handles error state", async () => {
    const { http, HttpResponse } = await import("msw");
    server.use(
      http.get("http://localhost:8000/api/v1/reports/daily", () =>
        HttpResponse.json({ detail: "Report not found" }, { status: 404 })
      )
    );

    render(<ReportViewer />);

    const dateInput = screen.getByLabelText(/날짜/);
    await userEvent.type(dateInput, "2026-01-15");
    await userEvent.click(screen.getByRole("button", { name: /조회/ }));

    await waitFor(() => {
      expect(screen.getByText(/에러/)).toBeInTheDocument();
      expect(screen.getByText(/Report not found/)).toBeInTheDocument();
    });
  });
});
