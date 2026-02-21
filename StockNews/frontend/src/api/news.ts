import { apiClient } from './client';
import type { NewsScore, NewsTopItem, NewsItem } from '../types/news';
import type { NewsListResponse } from '../types/api';

export interface NewsFilterParams {
  market?: string;
  stock?: string;
  sentiment?: string;
  theme?: string;
  dateFrom?: string;
  dateTo?: string;
}

/** Top 종목 뉴스 조회 */
export function fetchTopNews(market: string, limit?: number, date?: string): Promise<NewsTopItem[]> {
  const params = new URLSearchParams({ market });
  if (limit) params.set('limit', String(limit));
  if (date) params.set('date', date);
  return apiClient.get<NewsTopItem[]>(`/news/top?${params}`);
}

/** 최신 뉴스 리스트 (페이지네이션) */
export function fetchLatestNews(
  offset = 0,
  limit = 20,
  filters?: NewsFilterParams,
): Promise<NewsListResponse> {
  const params = new URLSearchParams({ offset: String(offset), limit: String(limit) });

  if (filters?.market) params.set('market', filters.market);
  if (filters?.stock) params.set('stock', filters.stock);
  if (filters?.sentiment && filters.sentiment !== 'all') params.set('sentiment', filters.sentiment);
  if (filters?.theme) params.set('theme', filters.theme);
  if (filters?.dateFrom) params.set('date_from', filters.dateFrom);
  if (filters?.dateTo) params.set('date_to', filters.dateTo);

  return apiClient.get<NewsListResponse>(`/news/latest?${params}`);
}

/** 종목별 뉴스 스코어 */
export function fetchNewsScore(stockCode: string): Promise<NewsScore> {
  return apiClient.get<NewsScore>(`/news/score?stock=${stockCode}`);
}

/** 특정 날짜 뉴스 조회 */
export function fetchNewsByDate(
  stockCode: string,
  date: string,
): Promise<NewsItem[]> {
  return apiClient.get<NewsItem[]>(`/news/latest?stock=${stockCode}&date=${date}`);
}
