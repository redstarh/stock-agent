/**
 * T-F7: 매매 내역 페이지 테스트
 */
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import TradesPage from "@/components/TradesPage";
import { server } from "@/mocks/server";
import { http, HttpResponse } from "msw";

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe("TradesPage", () => {
  test("renders trade table with data", async () => {
    render(<TradesPage />);
    await waitFor(() => {
      expect(screen.getByText("005930")).toBeInTheDocument();
    });
  });

  test("displays trade details", async () => {
    render(<TradesPage />);
    await waitFor(() => {
      expect(screen.getByText("삼성전자")).toBeInTheDocument();
      expect(screen.getByText(/10,000/)).toBeInTheDocument();
    });
  });

  test("shows pagination info", async () => {
    render(<TradesPage />);
    await waitFor(() => {
      expect(screen.getByText(/페이지: 1/)).toBeInTheDocument();
    });
  });
});
