import { useMutation, useQueryClient } from '@tanstack/react-query';
import { collectStockNews } from '../api/collect';

/** 종목별 수동 수집 mutation */
export function useManualCollect() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: collectStockNews,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['latestNews'] });
    },
  });
}
