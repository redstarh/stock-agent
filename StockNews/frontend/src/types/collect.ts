export interface StockCollectRequest {
  query: string;
  stock_code: string;
  market: string;
  add_to_scope: boolean;
}

export interface StockCollectResponse {
  status: string;
  query: string;
  stock_code: string;
  collected: number;
  saved: number;
  added_to_scope: boolean;
}
