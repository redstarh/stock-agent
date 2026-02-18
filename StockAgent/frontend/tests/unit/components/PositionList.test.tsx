/**
 * T-F5: 포지션 현황 테스트
 */
import { render, screen, waitFor } from "@testing-library/react";
import PositionList from "@/components/PositionList";
import { server } from "@/mocks/server";
import { http, HttpResponse } from "msw";

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe("PositionList", () => {
  test("renders position list", async () => {
    render(<PositionList />);
    await waitFor(() => {
      expect(screen.getByText("삼성전자")).toBeInTheDocument();
    });
  });

  test("shows stock code and quantity", async () => {
    render(<PositionList />);
    await waitFor(() => {
      expect(screen.getByText("005930")).toBeInTheDocument();
      expect(screen.getByText("10")).toBeInTheDocument();
    });
  });

  test("shows empty state when no positions", async () => {
    server.use(
      http.get("http://localhost:8000/api/v1/account/positions", () =>
        HttpResponse.json([])
      )
    );
    render(<PositionList />);
    await waitFor(() => {
      expect(screen.getByText(/보유 종목 없음/)).toBeInTheDocument();
    });
  });
});
