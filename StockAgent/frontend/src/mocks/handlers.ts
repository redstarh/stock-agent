/** MSW Mock 핸들러 */

import { http, HttpResponse } from "msw";

export const handlers = [
  // Health
  http.get("http://localhost:8000/api/v1/health", () =>
    HttpResponse.json({ status: "ok" })
  ),

  // Account Balance
  http.get("http://localhost:8000/api/v1/account/balance", () =>
    HttpResponse.json({
      cash: 10000000,
      total_eval: 15000000,
      daily_pnl: 250000,
    })
  ),

  // Positions
  http.get("http://localhost:8000/api/v1/account/positions", () =>
    HttpResponse.json([
      {
        stock_code: "005930",
        stock_name: "삼성전자",
        quantity: 10,
        avg_price: 70000,
        current_price: 71000,
        unrealized_pnl: 10000,
      },
    ])
  ),

  // Trades
  http.get("http://localhost:8000/api/v1/trades", ({ request }) => {
    const url = new URL(request.url);
    const page = Number(url.searchParams.get("page") || "1");
    return HttpResponse.json({
      items: [
        {
          trade_id: "t1",
          date: "2026-01-15",
          stock_code: "005930",
          stock_name: "삼성전자",
          side: "buy",
          entry_price: 70000,
          exit_price: 71000,
          quantity: 10,
          pnl: 10000,
          pnl_pct: 1.43,
          strategy_tag: "volume_leader",
        },
      ],
      total: 1,
      page,
      size: 10,
    });
  }),

  // Risk Config
  http.get("http://localhost:8000/api/v1/risk/config", () =>
    HttpResponse.json({
      stop_loss_pct: 3.0,
      max_position_pct: 10.0,
      daily_loss_limit: 500000,
      max_positions: 5,
    })
  ),

  http.put("http://localhost:8000/api/v1/risk/config", () =>
    HttpResponse.json({ status: "updated" })
  ),

  http.post("http://localhost:8000/api/v1/risk/emergency-sell", () =>
    HttpResponse.json({ status: "executed", sold_count: 3 })
  ),

  // Orders
  http.get("http://localhost:8000/api/v1/orders", () =>
    HttpResponse.json([
      {
        order_id: "ORD001",
        stock_code: "005930",
        side: "buy",
        quantity: 10,
        price: 71000,
        status: "pending",
        timestamp: "2026-02-18T09:30:00",
      },
    ])
  ),

  // Scanner
  http.get("http://localhost:8000/api/v1/scanner/top", () =>
    HttpResponse.json([
      {
        code: "005930",
        name: "삼성전자",
        current_price: 71000,
        trade_value: 1500000000,
        volume_surge: true,
      },
      {
        code: "000660",
        name: "SK하이닉스",
        current_price: 135000,
        trade_value: 1200000000,
        volume_surge: false,
      },
    ])
  ),

  // Strategy Config
  http.get("http://localhost:8000/api/v1/strategy/config", () =>
    HttpResponse.json({
      top_n: 5,
      news_threshold: 0.7,
      vwap_condition: true,
    })
  ),

  http.put("http://localhost:8000/api/v1/strategy/config", () =>
    HttpResponse.json({ status: "updated" })
  ),

  // Reports Metrics
  http.get("http://localhost:8000/api/v1/reports/metrics", () =>
    HttpResponse.json([
      {
        date: "2026-01-15",
        win_rate: 66.7,
        total_pnl: 150000,
        max_drawdown: 5.2,
        total_trades: 12,
      },
      {
        date: "2026-01-16",
        win_rate: 75.0,
        total_pnl: 200000,
        max_drawdown: 3.1,
        total_trades: 8,
      },
    ])
  ),

  // Daily Report
  http.get("http://localhost:8000/api/v1/reports/daily", () =>
    HttpResponse.json({
      date: "2026-01-15",
      total_trades: 12,
      win_rate: 66.7,
      total_pnl: 150000,
      best_pattern: "volume_leader",
      worst_pattern: "news_breakout",
    })
  ),
];
