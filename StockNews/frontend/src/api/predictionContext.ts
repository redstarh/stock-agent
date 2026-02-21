import { apiClient, API_BASE_URL } from './client';
import type {
  PredictionContext,
  LLMPredictionResponse,
  ContextRebuildResponse,
} from '../types/predictionContext';

/** 예측 컨텍스트 조회 */
export function fetchPredictionContext(market?: string): Promise<PredictionContext> {
  const params = new URLSearchParams();
  if (market) params.set('market', market);
  const query = params.toString();
  return apiClient.get<PredictionContext>(
    `/prediction-context${query ? `?${query}` : ''}`,
  );
}

/** 예측 컨텍스트 리빌드 */
export async function rebuildPredictionContext(
  days = 30,
  market?: string,
): Promise<ContextRebuildResponse> {
  const params = new URLSearchParams({ days: String(days) });
  if (market) params.set('market', market);
  const response = await fetch(
    `${API_BASE_URL}/prediction-context/rebuild?${params}`,
    { method: 'POST', headers: { 'Content-Type': 'application/json' } },
  );
  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }
  return response.json() as Promise<ContextRebuildResponse>;
}

/** LLM 기반 주가 예측 */
export function fetchLLMPrediction(
  stockCode: string,
  market = 'KR',
): Promise<LLMPredictionResponse> {
  const params = new URLSearchParams({ market });
  return apiClient.get<LLMPredictionResponse>(
    `/stocks/${stockCode}/prediction/llm?${params}`,
  );
}
