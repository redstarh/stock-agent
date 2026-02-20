import { apiClient } from './client';
import type {
  AccuracyResponse,
  DailyVerificationResponse,
  ThemeAccuracyResponse,
  VerificationStatusResponse,
} from '../types/verification';

/** 정확도 통계 조회 */
export function fetchAccuracy(days: number, market: string): Promise<AccuracyResponse> {
  const params = new URLSearchParams({ days: String(days), market });
  return apiClient.get<AccuracyResponse>(`/verification/accuracy?${params}`);
}

/** 일별 검증 결과 조회 */
export function fetchDailyResults(date: string, market: string): Promise<DailyVerificationResponse> {
  const params = new URLSearchParams({ date, market });
  return apiClient.get<DailyVerificationResponse>(`/verification/daily?${params}`);
}

/** 테마별 정확도 조회 */
export function fetchThemeAccuracy(date: string, market: string): Promise<ThemeAccuracyResponse> {
  const params = new URLSearchParams({ date, market });
  return apiClient.get<ThemeAccuracyResponse>(`/verification/themes?${params}`);
}

/** 검증 상태 조회 */
export function fetchVerificationStatus(): Promise<VerificationStatusResponse> {
  return apiClient.get<VerificationStatusResponse>('/verification/status');
}
