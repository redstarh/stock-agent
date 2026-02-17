import { apiClient } from './client';
import type { ThemeItem } from '../types/theme';

/** 테마 강도 순위 조회 */
export function fetchThemeStrength(market?: string): Promise<ThemeItem[]> {
  const params = new URLSearchParams();
  if (market) params.set('market', market);
  const query = params.toString();
  return apiClient.get<ThemeItem[]>(`/theme/strength${query ? `?${query}` : ''}`);
}
