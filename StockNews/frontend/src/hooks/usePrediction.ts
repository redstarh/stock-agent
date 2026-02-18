import { useQuery } from '@tanstack/react-query';
import { fetchPrediction } from '../api/stocks';

export function usePrediction(stockCode: string) {
  return useQuery({
    queryKey: ['prediction', stockCode],
    queryFn: () => fetchPrediction(stockCode),
    enabled: !!stockCode,
  });
}
