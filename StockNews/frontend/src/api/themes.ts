import { apiClient } from './client';
import type { ThemeItem } from '../types/theme';
import type { NewsItem } from '../types/news';

/** 테마 강도 순위 조회 */
export function fetchThemeStrength(market?: string, date?: string): Promise<ThemeItem[]> {
  const params = new URLSearchParams();
  if (market) params.set('market', market);
  if (date) params.set('date', date);
  const query = params.toString();
  return apiClient.get<ThemeItem[]>(`/theme/strength${query ? `?${query}` : ''}`);
}

/** 국외 영향 뉴스 항목 */
export interface UsImpactNewsItem {
  id: number;
  title: string;
  stock_code: string;
  stock_name: string | null;
  sentiment: string;
  news_score: number;
  source: string;
  source_url: string | null;
  market: string;
  published_at: string | null;
  impact: number;
  direction: 'up' | 'down' | 'neutral';
}

/** 테마별 뉴스 응답 */
export interface ThemeNewsResponse {
  kr_news: NewsItem[];
  kr_total: number;
  us_news: UsImpactNewsItem[];
  us_total: number;
}

/** 테마별 국내+국외 뉴스 조회 */
export function fetchThemeNews(theme: string, limit = 20): Promise<ThemeNewsResponse> {
  const params = new URLSearchParams({ theme, limit: String(limit) });
  return apiClient.get<ThemeNewsResponse>(`/theme/news?${params}`);
}
