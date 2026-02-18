import type { NewsItem } from './news';

/** 페이지네이션 응답 */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  offset: number;
  limit: number;
}

/** 뉴스 리스트 페이지네이션 응답 */
export type NewsListResponse = PaginatedResponse<NewsItem>;

/** WebSocket 메시지 */
export interface WebSocketMessage {
  type: string;
  data?: Record<string, unknown>;
  message?: string;
}

/** 속보 데이터 */
export interface BreakingNewsData {
  stock_code: string;
  stock_name: string | null;
  title: string;
  theme: string | null;
  sentiment: string | null;
  news_score: number;
  market: string;
  published_at: string | null;
}

/** Health 응답 */
export interface HealthResponse {
  status: string;
  version: string;
}
