/** 테마 강도 항목 */
export interface ThemeItem {
  theme: string;
  strength_score: number;
  news_count: number;
  sentiment_avg: number;
  rise_index: number;  // 0-100, 국내+국외 종합 상승지수
  date: string;
  market: string;
}
