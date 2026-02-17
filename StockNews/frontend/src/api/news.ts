import { apiClient } from './client';
import type { NewsScore, NewsTopItem, NewsItem } from '../types/news';
import type { NewsListResponse } from '../types/api';

/** Top 종목 뉴스 조회 */
export function fetchTopNews(market: string, limit?: number): Promise<NewsTopItem[]> {
  const params = new URLSearchParams({ market });
  if (limit) params.set('limit', String(limit));
  return apiClient.get<NewsTopItem[]>(`/news/top?${params}`);
}

/** 최신 뉴스 리스트 (페이지네이션) */
export function fetchLatestNews(
  offset = 0,
  limit = 20,
  market?: string,
): Promise<NewsListResponse> {
  const params = new URLSearchParams({ offset: String(offset), limit: String(limit) });
  if (market) params.set('market', market);
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
