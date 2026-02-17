import { useQuery } from '@tanstack/react-query';
import { fetchNewsScore } from '../api/news';
import { fetchStockTimeline } from '../api/stocks';
import type { NewsScore, TimelinePoint } from '../types/news';

export function useNewsScore(stockCode: string) {
  const score = useQuery<NewsScore>({
    queryKey: ['newsScore', stockCode],
    queryFn: () => fetchNewsScore(stockCode),
    enabled: !!stockCode,
  });

  const timeline = useQuery<TimelinePoint[]>({
    queryKey: ['stockTimeline', stockCode],
    queryFn: () => fetchStockTimeline(stockCode),
    enabled: !!stockCode,
  });

  return { score, timeline };
}
