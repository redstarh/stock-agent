/**
 * T-F10: 리스크 설정 UI 테스트
 */
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import RiskSettings from "@/components/RiskSettings";
import { server } from "@/mocks/server";

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe("RiskSettings", () => {
  test("renders risk settings form", async () => {
    render(<RiskSettings />);
    await waitFor(() => {
      expect(screen.getByLabelText(/손절률/)).toBeInTheDocument();
      expect(screen.getByLabelText(/최대 비중/)).toBeInTheDocument();
    });
  });

  test("loads current risk config", async () => {
    render(<RiskSettings />);
    await waitFor(() => {
      expect(screen.getByDisplayValue("3")).toBeInTheDocument();
      expect(screen.getByDisplayValue("10")).toBeInTheDocument();
    });
  });

  test("emergency sell button requires confirmation", async () => {
    const user = userEvent.setup();
    render(<RiskSettings />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /비상 청산/ })).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: /비상 청산/ }));
    expect(screen.getByText(/정말 전체 청산/)).toBeInTheDocument();
  });
});
