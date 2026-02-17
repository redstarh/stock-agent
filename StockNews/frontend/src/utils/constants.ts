/** 앱 상수 */

export const MARKETS = ['KR', 'US'] as const;
export type Market = (typeof MARKETS)[number];

export const REFRESH_INTERVAL_MS = 30_000;

export const SENTIMENT_COLORS: Record<string, string> = {
  positive: '#22c55e',
  neutral: '#6b7280',
  negative: '#ef4444',
};
