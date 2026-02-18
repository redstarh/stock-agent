/**
 * T-F10: 리스크 설정 UI 테스트
 */
import { render, screen, waitFor, act } from "@testing-library/react";
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

  test("saves updated risk config", async () => {
    jest.useFakeTimers();
    const user = userEvent.setup({ delay: null });
    render(<RiskSettings />);

    // Wait for form to load
    await waitFor(() => {
      expect(screen.getByLabelText(/손절률/)).toBeInTheDocument();
    });

    // Change stop loss value
    const stopLossInput = screen.getByLabelText(/손절률/) as HTMLInputElement;
    await user.clear(stopLossInput);
    await user.type(stopLossInput, "5");

    // Click save button
    await user.click(screen.getByRole("button", { name: /저장/ }));

    // Verify "저장 완료" appears
    await waitFor(() => {
      expect(screen.getByText(/저장 완료/)).toBeInTheDocument();
    });

    // Advance timers to verify message disappears
    act(() => {
      jest.advanceTimersByTime(2000);
    });
    await waitFor(() => {
      expect(screen.queryByText(/저장 완료/)).not.toBeInTheDocument();
    });

    jest.useRealTimers();
  });

  test("executes emergency sell", async () => {
    const user = userEvent.setup();
    render(<RiskSettings />);

    // Wait for component to load
    await waitFor(() => {
      expect(screen.getByRole("button", { name: /비상 청산/ })).toBeInTheDocument();
    });

    // Click emergency sell button
    await user.click(screen.getByRole("button", { name: /비상 청산/ }));

    // Confirm dialog should appear
    expect(screen.getByText(/정말 전체 청산/)).toBeInTheDocument();

    // Click confirm button
    await user.click(screen.getByRole("button", { name: /확인/ }));

    // Dialog should disappear
    await waitFor(() => {
      expect(screen.queryByText(/정말 전체 청산/)).not.toBeInTheDocument();
    });
  });

  test("cancels emergency sell dialog", async () => {
    const user = userEvent.setup();
    render(<RiskSettings />);

    // Wait for component to load
    await waitFor(() => {
      expect(screen.getByRole("button", { name: /비상 청산/ })).toBeInTheDocument();
    });

    // Click emergency sell button
    await user.click(screen.getByRole("button", { name: /비상 청산/ }));

    // Confirm dialog should appear
    expect(screen.getByText(/정말 전체 청산/)).toBeInTheDocument();

    // Click cancel button
    await user.click(screen.getByRole("button", { name: /취소/ }));

    // Dialog should disappear
    await waitFor(() => {
      expect(screen.queryByText(/정말 전체 청산/)).not.toBeInTheDocument();
    });
  });
});
