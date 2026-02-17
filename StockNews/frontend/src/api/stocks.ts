import { apiClient } from './client';
import type { TimelinePoint } from '../types/news';

/** 종목별 뉴스 스코어 타임라인 */
export function fetchStockTimeline(stockCode: string, days = 7): Promise<TimelinePoint[]> {
  return apiClient.get<TimelinePoint[]>(`/stocks/${stockCode}/timeline?days=${days}`);
}
