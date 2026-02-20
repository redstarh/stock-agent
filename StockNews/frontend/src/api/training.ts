/** Training API client. */

import { apiClient } from './client';
import type { MLModel, TrainingStats, TrainResult, EvaluateResult } from '../types/training';

export const trainingApi = {
  getStats: () =>
    apiClient.get<TrainingStats>('/training/stats'),

  getModels: (market?: string) =>
    apiClient.get<MLModel[]>(`/training/models${market ? `?market=${market}` : ''}`),

  trainModel: (market: string, modelType: string, featureTier: number) =>
    fetch(`/api/v1/training/train?market=${market}&model_type=${modelType}&feature_tier=${featureTier}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    }).then(r => r.json() as Promise<TrainResult>),

  activateModel: (modelId: number) =>
    fetch(`/api/v1/training/models/${modelId}/activate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    }).then(r => r.json()),

  evaluateModel: (market: string) =>
    fetch(`/api/v1/training/evaluate?market=${market}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    }).then(r => r.json() as Promise<EvaluateResult>),
};
