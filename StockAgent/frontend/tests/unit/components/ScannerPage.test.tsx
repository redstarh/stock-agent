/**
 * @jest-environment <rootDir>/tests/jest-env-jsdom.ts
 */

import { render, screen, waitFor } from "@testing-library/react";
import { server } from "@/mocks/server";
import ScannerPage from "../../../src/components/ScannerPage";

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe("ScannerPage", () => {
  test("displays real-time top N stocks", async () => {
    render(<ScannerPage />);
    await waitFor(() => {
      expect(screen.getByText(/거래대금 TOP/)).toBeInTheDocument();
    });
  });

  test("displays stock data with code, name, and trade value", async () => {
    render(<ScannerPage />);
    await waitFor(() => {
      expect(screen.getByText("005930")).toBeInTheDocument();
      expect(screen.getByText("삼성전자")).toBeInTheDocument();
      expect(screen.getByText(/1,500,000,000/)).toBeInTheDocument();
    });
  });

  test("displays volume surge indicator", async () => {
    render(<ScannerPage />);
    await waitFor(() => {
      const surgeIndicators = screen.getAllByText(/거래량 급증/);
      expect(surgeIndicators.length).toBeGreaterThanOrEqual(1);
    });
  });

  test("displays current price", async () => {
    render(<ScannerPage />);
    await waitFor(() => {
      expect(screen.getByText(/71,000/)).toBeInTheDocument();
    });
  });
});
