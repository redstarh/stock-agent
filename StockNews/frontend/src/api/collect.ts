import type { StockCollectRequest, StockCollectResponse } from '../types/collect';

/** 종목별 수동 뉴스 수집 */
export function collectStockNews(req: StockCollectRequest): Promise<StockCollectResponse> {
  return fetch('/api/v1/collect/stock', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(req),
  }).then(async (response) => {
    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }
    return response.json() as Promise<StockCollectResponse>;
  });
}
