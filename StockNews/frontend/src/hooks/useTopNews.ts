import { useQuery } from '@tanstack/react-query';
import { fetchTopNews } from '../api/news';
import { REFRESH_INTERVAL_MS } from '../utils/constants';
import type { NewsTopItem } from '../types/news';

export function useTopNews(market: string, date?: string) {
  return useQuery<NewsTopItem[]>({
    queryKey: ['topNews', market, date],
    queryFn: () => fetchTopNews(market, undefined, date),
    refetchInterval: date ? false : REFRESH_INTERVAL_MS,
  });
}
