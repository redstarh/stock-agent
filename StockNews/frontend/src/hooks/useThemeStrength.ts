import { useQuery } from '@tanstack/react-query';
import { fetchThemeStrength } from '../api/themes';
import type { ThemeItem } from '../types/theme';

export function useThemeStrength(market: string) {
  return useQuery<ThemeItem[]>({
    queryKey: ['themeStrength', market],
    queryFn: () => fetchThemeStrength(market),
  });
}
