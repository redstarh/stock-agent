/** T-F8: 전략 설정 페이지 테스트 */

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { server } from "@/mocks/server";
import { http, HttpResponse } from "msw";
import StrategyPage from "@/components/StrategyPage";

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe("StrategyPage", () => {
  test("renders strategy form with current values", async () => {
    render(<StrategyPage />);
    await waitFor(() => {
      expect(screen.getByLabelText(/TOP N/)).toHaveValue(5);
    });
  });

  test("updates strategy parameters", async () => {
    render(<StrategyPage />);
    await waitFor(() => {
      expect(screen.getByLabelText(/TOP N/)).toBeInTheDocument();
    });

    await userEvent.clear(screen.getByLabelText(/TOP N/));
    await userEvent.type(screen.getByLabelText(/TOP N/), "10");
    await userEvent.click(screen.getByRole("button", { name: /저장/ }));

    await waitFor(() => {
      expect(screen.getByText(/저장 완료/)).toBeInTheDocument();
    });
  });

  test("displays error message on save failure", async () => {
    server.use(
      http.put("http://localhost:8000/api/v1/strategy/config", () => {
        return HttpResponse.json(
          { detail: "Invalid configuration" },
          { status: 400 }
        );
      })
    );

    render(<StrategyPage />);
    await waitFor(() => {
      expect(screen.getByLabelText(/TOP N/)).toBeInTheDocument();
    });

    await userEvent.click(screen.getByRole("button", { name: /저장/ }));

    await waitFor(() => {
      expect(screen.getByText(/저장 실패/)).toBeInTheDocument();
    });
  });

  test("displays all strategy parameters", async () => {
    render(<StrategyPage />);
    await waitFor(() => {
      expect(screen.getByLabelText(/TOP N/)).toBeInTheDocument();
      expect(screen.getByLabelText(/뉴스 임계값/)).toBeInTheDocument();
      expect(screen.getByLabelText(/VWAP 조건/)).toBeInTheDocument();
    });
  });

  test("handles fetch config error gracefully", async () => {
    server.use(
      http.get("http://localhost:8000/api/v1/strategy/config", () => {
        return HttpResponse.json(
          { detail: "Internal server error" },
          { status: 500 }
        );
      })
    );

    render(<StrategyPage />);

    // Component should still render with default values despite error
    await waitFor(() => {
      expect(screen.getByLabelText(/TOP N/)).toBeInTheDocument();
      expect(screen.getByLabelText(/뉴스 임계값/)).toBeInTheDocument();
      expect(screen.getByLabelText(/VWAP 조건/)).toBeInTheDocument();
    });

    // Should show default values (no crash)
    expect(screen.getByLabelText(/TOP N/)).toHaveValue(5);
    expect(screen.getByLabelText(/뉴스 임계값/)).toHaveValue(0.7);
    expect(screen.getByLabelText(/VWAP 조건/)).toBeChecked();
  });

  test("toggles vwap condition checkbox", async () => {
    render(<StrategyPage />);

    // Wait for component to load
    await waitFor(() => {
      expect(screen.getByLabelText(/VWAP 조건/)).toBeInTheDocument();
    });

    const checkbox = screen.getByLabelText(/VWAP 조건/) as HTMLInputElement;

    // Initial state should be checked (from mock data)
    expect(checkbox).toBeChecked();

    // Toggle off
    await userEvent.click(checkbox);
    expect(checkbox).not.toBeChecked();

    // Toggle on
    await userEvent.click(checkbox);
    expect(checkbox).toBeChecked();
  });
});
