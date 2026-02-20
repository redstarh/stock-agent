/** ML Dashboard data hook. */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { trainingApi } from '../api/training';

export function useMLDashboard(market: string) {
  const queryClient = useQueryClient();

  const stats = useQuery({
    queryKey: ['training-stats'],
    queryFn: () => trainingApi.getStats(),
    staleTime: 30_000,
  });

  const models = useQuery({
    queryKey: ['ml-models', market],
    queryFn: () => trainingApi.getModels(market),
    staleTime: 30_000,
  });

  const trainMutation = useMutation({
    mutationFn: (params: { market: string; modelType: string; featureTier: number }) =>
      trainingApi.trainModel(params.market, params.modelType, params.featureTier),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ml-models'] });
      queryClient.invalidateQueries({ queryKey: ['training-stats'] });
    },
  });

  const activateMutation = useMutation({
    mutationFn: (modelId: number) => trainingApi.activateModel(modelId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ml-models'] });
    },
  });

  const evaluateMutation = useMutation({
    mutationFn: (market: string) => trainingApi.evaluateModel(market),
  });

  const activeModel = models.data?.find(m => m.is_active) ?? null;

  return {
    stats: stats.data,
    models: models.data ?? [],
    activeModel,
    isLoading: stats.isLoading || models.isLoading,
    error: stats.error || models.error,
    trainModel: trainMutation.mutate,
    isTraining: trainMutation.isPending,
    trainResult: trainMutation.data,
    activateModel: activateMutation.mutate,
    evaluateModel: evaluateMutation.mutate,
    isEvaluating: evaluateMutation.isPending,
    evaluateResult: evaluateMutation.data,
  };
}
