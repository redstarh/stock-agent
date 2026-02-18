/**
 * T-F3: 인증 UI 테스트
 */
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import AuthSettings from "@/components/AuthSettings";

describe("AuthSettings", () => {
  test("API key input renders", () => {
    render(<AuthSettings />);
    expect(screen.getByLabelText(/API Key/i)).toBeInTheDocument();
  });

  test("API secret input renders", () => {
    render(<AuthSettings />);
    expect(screen.getByLabelText(/API Secret/i)).toBeInTheDocument();
  });

  test("saves API key on submit", async () => {
    const user = userEvent.setup();
    render(<AuthSettings />);
    await user.type(screen.getByLabelText(/API Key/i), "test-key");
    await user.type(screen.getByLabelText(/API Secret/i), "test-secret");
    await user.click(screen.getByRole("button", { name: /저장/i }));
    expect(screen.getByText(/저장 완료/i)).toBeInTheDocument();
  });
});
