import { useQuery } from '@tanstack/react-query';
import {
  fetchAccuracy,
  fetchDailyResults,
  fetchThemeAccuracy,
  fetchVerificationStatus,
} from '../api/verification';

export function useAccuracy(days: number, market: string) {
  return useQuery({
    queryKey: ['verification', 'accuracy', days, market],
    queryFn: () => fetchAccuracy(days, market),
  });
}

export function useDailyResults(date: string, market: string) {
  return useQuery({
    queryKey: ['verification', 'daily', date, market],
    queryFn: () => fetchDailyResults(date, market),
    enabled: !!date,
  });
}

export function useThemeAccuracy(date: string, market: string) {
  return useQuery({
    queryKey: ['verification', 'themes', date, market],
    queryFn: () => fetchThemeAccuracy(date, market),
    enabled: !!date,
  });
}

export function useVerificationStatus() {
  return useQuery({
    queryKey: ['verification', 'status'],
    queryFn: fetchVerificationStatus,
  });
}
