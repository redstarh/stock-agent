/**
 * T-F2: API 클라이언트 + Mock 테스트
 * @jest-environment node
 */
import { http, HttpResponse } from "msw";
import { server } from "@/mocks/server";
import { apiClient } from "@/lib/api";

// MSW 서버 라이프사이클
beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe("T-F2: API 클라이언트", () => {
  test("getHealth returns status ok", async () => {
    const data = await apiClient.getHealth();
    expect(data).toHaveProperty("status");
    expect(data.status).toBe("ok");
  });

  test("getBalance returns account data", async () => {
    const data = await apiClient.getBalance();
    expect(data).toHaveProperty("cash");
    expect(data).toHaveProperty("total_eval");
    expect(data).toHaveProperty("daily_pnl");
    expect(data.cash).toBe(10000000);
  });

  test("getPositions returns position array", async () => {
    const data = await apiClient.getPositions();
    expect(Array.isArray(data)).toBe(true);
    expect(data.length).toBeGreaterThan(0);
    expect(data[0]).toHaveProperty("stock_code");
    expect(data[0].stock_name).toBe("삼성전자");
  });

  test("API client handles 500 error gracefully", async () => {
    server.use(
      http.get("http://localhost:8000/api/v1/account/balance", () =>
        HttpResponse.json({ detail: "Internal Server Error" }, { status: 500 })
      )
    );
    await expect(apiClient.getBalance()).rejects.toThrow();
  });

  test("API client handles network error", async () => {
    server.use(
      http.get("http://localhost:8000/api/v1/account/balance", () =>
        HttpResponse.error()
      )
    );
    await expect(apiClient.getBalance()).rejects.toThrow();
  });
});
